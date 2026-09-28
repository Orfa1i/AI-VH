"""
OpenTelemetry tracing module for AI Virtual Hospital (AI-VH).
Propagates run_id across nested service calls and supports optional Langfuse exporter.
"""

import contextvars
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

try:
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
except ImportError:
    class InMemorySpanExporter(SpanExporter):  # type: ignore[no-redef]
        def __init__(self) -> None:
            self._spans: List[ReadableSpan] = []

        def export(self, spans: Any) -> SpanExportResult:
            self._spans.extend(spans)
            return SpanExportResult.SUCCESS

        def get_finished_spans(self) -> List[ReadableSpan]:
            return list(self._spans)

        def clear(self) -> None:
            self._spans.clear()

from .logging import set_log_context

_RUN_ID_VAR: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "vh_current_run_id", default=None
)

_IN_MEMORY_EXPORTER = InMemorySpanExporter()
_TRACER_PROVIDER: Optional[TracerProvider] = None


def get_tracer_provider() -> TracerProvider:
    """Retrieve or initialize the global TracerProvider with InMemorySpanExporter."""
    global _TRACER_PROVIDER
    if _TRACER_PROVIDER is None:
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(_IN_MEMORY_EXPORTER))
        trace.set_tracer_provider(provider)
        _TRACER_PROVIDER = provider
        _setup_optional_langfuse(provider)
    return _TRACER_PROVIDER


def _setup_optional_langfuse(provider: TracerProvider) -> None:
    """Register Langfuse exporter if enabled by configuration and package is available."""
    try:
        from .config import get_settings
        settings = get_settings()
        enable_langfuse = getattr(settings, "ENABLE_LANGFUSE_TRACING", False)
        if enable_langfuse:
            import langfuse
            # Placeholder for Langfuse OpenTelemetry SpanProcessor initialization
    except Exception:
        pass


def get_tracer(name: str = "ai-vh") -> trace.Tracer:
    """Obtain OpenTelemetry tracer instance."""
    provider = get_tracer_provider()
    return provider.get_tracer(name)


def get_current_run_id() -> Optional[str]:
    """Retrieve the current active run_id from context."""
    return _RUN_ID_VAR.get()


def get_recorded_spans() -> List[ReadableSpan]:
    """Retrieve all recorded spans captured in memory for testing and audit inspection."""
    return list(_IN_MEMORY_EXPORTER.get_finished_spans())


def clear_recorded_spans() -> None:
    """Reset captured in-memory spans."""
    _IN_MEMORY_EXPORTER.clear()


@contextmanager
def trace_span(
    name: str,
    run_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
) -> Generator[trace.Span, None, None]:
    """
    Context manager to execute a code block within an OpenTelemetry span.
    Propagates run_id down the call stack to all nested child spans.
    """
    tracer = get_tracer()
    effective_run_id = run_id or get_current_run_id()
    token = _RUN_ID_VAR.set(effective_run_id)

    # Sync with structured logging context
    if effective_run_id:
        set_log_context(run_id=effective_run_id)

    span_attributes = dict(attributes or {})
    if effective_run_id:
        span_attributes["run_id"] = effective_run_id

    with tracer.start_as_current_span(name, attributes=span_attributes) as span:
        try:
            yield span
        finally:
            _RUN_ID_VAR.reset(token)
