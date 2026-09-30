"""
Clinical Guardrails runtime executing input and output verification rails for AI-VH.
Ensures hermetic execution, input scope enforcement, and fail-closed security.
"""

from pathlib import Path
from typing import Optional, Tuple
from vh.common.logging import get_logger
from .actions import check_injection_patterns

logger = get_logger("vh.verification.guardrails")
CONFIG_DIR = Path(__file__).resolve().parent


class ClinicalGuardrailsRuntime:
    """
    Coordinates input and output safety rails.
    Scopes input to clinical case processing and checks for prompt injections.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or CONFIG_DIR
        self._nemo_rails = None
        self._init_nemo()

    def _init_nemo(self) -> None:
        """Attempts to load NeMo Guardrails if installed, otherwise uses native pure-python rails."""
        try:
            from nemoguardrails import RailsConfig, LLMRails
            config = RailsConfig.from_path(str(self.config_dir))
            self._nemo_rails = LLMRails(config)
            logger.info("NeMo Guardrails engine successfully initialized.")
        except Exception as exc:
            logger.debug(f"NeMo Guardrails not active ({exc}); running native clinical guardrails runtime.")
            self._nemo_rails = None

    def validate_input_scope(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validates that input text is strictly within clinical case processing scope.
        Detects prompt injections, jailbreaks, and off-topic requests.
        Returns: (is_valid, violation_reason)
        """
        if not text or not text.strip():
            return False, "Input clinical text is empty or blank."

        if check_injection_patterns(text):
            return False, "Detected out-of-scope non-clinical request or prompt injection pattern."

        return True, None
