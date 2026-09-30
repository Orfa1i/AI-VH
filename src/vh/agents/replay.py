"""
Deterministic encounter recording and replay for AI-VH (STEP 34 / P5.4).

Every LLM output produced during an orchestrated encounter is recorded into a
:class:`ReplayBundle`. ``replay_encounter`` re-executes the same case with the
same run_id/seed while serving the recorded LLM outputs in order, and must
reproduce the canonical event log exactly (hash comparison).

Volatile identifiers (event_id, wall_time, run_id, and random report/consult
IDs such as ``rep_<hex>``) are normalized before hashing: they carry no
clinical content. All clinical fields (actor, action, sim_time, payload
content, released results, submitted report) must match exactly.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from vh.agents.environment import HospitalEnvironment
from vh.agents.events import EventStore, SimEvent
from vh.agents.orchestrator import EncounterBudget, EncounterState, HospitalOrchestrator
from vh.cases.spec import CaseSpec
from vh.generation.medgemma import ClinicalReport, MedGemmaAdapter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPLAY_DIR = REPO_ROOT / "data" / "replays"

_VOLATILE_ID_RE = re.compile(r"\b(rep|cns|evt|enc|run)_[0-9a-f]{4,16}\b")
_EXCLUDED_EVENT_KEYS = {"event_id", "wall_time", "run_id"}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _VOLATILE_ID_RE.sub("<ID>", value)
    if isinstance(value, list):
        return [_normalize_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _normalize_value(v) for k, v in value.items()}
    return value


def _canonical_event(event: Union[SimEvent, Dict[str, Any]]) -> Dict[str, Any]:
    data = event.model_dump() if isinstance(event, SimEvent) else dict(event)
    canonical: Dict[str, Any] = {
        "actor": data.get("actor"),
        "action": data.get("action"),
        "sim_time": data.get("sim_time"),
        "payload": _normalize_value(data.get("payload", {})),
        "result_ref": _normalize_value(data.get("result_ref")),
    }
    return canonical


def hash_event_log(events: List[Union[SimEvent, Dict[str, Any]]]) -> str:
    """Hash the canonical event log, excluding volatile IDs and wall-clock time."""
    canonical = [_canonical_event(e) for e in events]
    blob = json.dumps(canonical, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _sanitize_run_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "run-unknown"


class TranscriptEntry(BaseModel):
    """Single recorded LLM generation output in call order."""

    seq: int
    prompt_spec: str = ""
    input_hash: str = ""
    output_json: str = ""
    output_type: str = "dict"


class ReplayBundle(BaseModel):
    """Recorded encounter: LLM transcript, canonical event log, and final state."""

    run_id: str
    case_id: str
    seed: int = 42
    transcript: List[TranscriptEntry] = Field(default_factory=list)
    event_log: List[Dict[str, Any]] = Field(default_factory=list)
    encounter_state: Dict[str, Any] = Field(default_factory=dict)
    event_log_hash: str = ""


class RecordingAdapter(MedGemmaAdapter):
    """MedGemma adapter wrapper that records every generation output in order."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.transcript: List[TranscriptEntry] = []

    def generate(
        self,
        prompt_name_version: str,
        inputs: Dict[str, Any],
        response_schema: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        output = super().generate(
            prompt_name_version, inputs, response_schema=response_schema, **kwargs
        )
        if isinstance(output, BaseModel):
            output_json = output.model_dump_json()
            output_type = "clinical_report"
        elif isinstance(output, dict):
            output_json = json.dumps(output, sort_keys=True, default=str)
            output_type = "dict"
        else:
            output_json = json.dumps({"text": str(output)}, sort_keys=True, default=str)
            output_type = "text"
        input_blob = json.dumps(
            {"prompt": prompt_name_version, "case": str(inputs.get("case_id", ""))},
            sort_keys=True,
            default=str,
        )
        self.transcript.append(
            TranscriptEntry(
                seq=len(self.transcript),
                prompt_spec=prompt_name_version,
                input_hash=hashlib.sha256(input_blob.encode("utf-8")).hexdigest(),
                output_json=output_json,
                output_type=output_type,
            )
        )
        return output


class ReplayAdapter(MedGemmaAdapter):
    """MedGemma adapter that serves recorded outputs deterministically in order."""

    def __init__(self, transcript: List[TranscriptEntry], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._transcript: List[TranscriptEntry] = list(transcript)
        self._cursor: int = 0

    def generate(
        self,
        prompt_name_version: str,
        inputs: Dict[str, Any],
        response_schema: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        if self._cursor >= len(self._transcript):
            raise IndexError(
                "Replay transcript exhausted: encounter requested more LLM outputs "
                "than were recorded."
            )
        entry = self._transcript[self._cursor]
        self._cursor += 1
        if entry.output_type == "clinical_report":
            return ClinicalReport.model_validate_json(entry.output_json)
        parsed: Any = json.loads(entry.output_json)
        if isinstance(parsed, dict) and set(parsed.keys()) == {"text"}:
            return parsed["text"]
        return parsed


def record_encounter(
    case_spec: CaseSpec,
    seed: int = 42,
    budget: Optional[EncounterBudget] = None,
    run_id: Optional[str] = None,
) -> ReplayBundle:
    """Run an encounter while recording every LLM output and the full event log."""
    effective_run_id = run_id or f"replay-{_sanitize_run_id(case_spec.case_id)}-s{seed}"
    recorder = RecordingAdapter()
    orchestrator = HospitalOrchestrator(budget=budget, adapter=recorder)
    store = EventStore()
    state = orchestrator.run_encounter(
        case_spec, run_id=effective_run_id, seed=seed, event_store=store
    )
    events = [e.model_dump() for e in store.get_events()]
    event_hash = hash_event_log(events)
    bundle = ReplayBundle(
        run_id=effective_run_id,
        case_id=case_spec.case_id,
        seed=seed,
        transcript=list(recorder.transcript),
        event_log=events,
        encounter_state=state.model_dump(),
        event_log_hash=event_hash,
    )
    save_bundle(bundle)
    return bundle


def replay_encounter(
    bundle: ReplayBundle,
    case_spec: CaseSpec,
    budget: Optional[EncounterBudget] = None,
) -> Tuple[EncounterState, str]:
    """Re-execute a recorded encounter deterministically from its LLM transcript."""
    if bundle.case_id != case_spec.case_id:
        raise ValueError(
            f"Replay bundle case '{bundle.case_id}' does not match "
            f"provided case '{case_spec.case_id}'."
        )
    adapter = ReplayAdapter(bundle.transcript)
    orchestrator = HospitalOrchestrator(budget=budget, adapter=adapter)
    store = EventStore()
    state = orchestrator.run_encounter(
        case_spec, run_id=bundle.run_id, seed=bundle.seed, event_store=store
    )
    replayed_hash = hash_event_log([e.model_dump() for e in store.get_events()])
    return state, replayed_hash


def save_bundle(bundle: ReplayBundle, directory: Optional[Path] = None) -> Path:
    """Persist a replay bundle to disk as JSON."""
    target_dir = directory or REPLAY_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{bundle.run_id}.json"
    path.write_text(json.dumps(bundle.model_dump(), indent=2), encoding="utf-8")
    return path


def load_bundle(run_id: str, directory: Optional[Path] = None) -> ReplayBundle:
    """Load a persisted replay bundle by run_id."""
    target_dir = directory or REPLAY_DIR
    path = target_dir / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Replay bundle not found: {path}")
    return ReplayBundle.model_validate(json.loads(path.read_text(encoding="utf-8")))


def build_environment_for_replay(
    case_spec: CaseSpec, run_id: str, seed: int
) -> Tuple[HospitalEnvironment, EventStore]:
    """Helper constructing a seeded environment with an observable event store."""
    store = EventStore()
    env = HospitalEnvironment(case_spec=case_spec, seed=seed, run_id=run_id, event_store=store)
    return env, store
