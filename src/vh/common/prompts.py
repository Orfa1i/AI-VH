"""
Versioned prompt template loader for AI Virtual Hospital (AI-VH).
Loads templates strictly via name@version from src/vh/prompt_templates/<name>/<version>.md.
"""

from pathlib import Path
from typing import Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROMPT_TEMPLATES_DIR = REPO_ROOT / "src" / "vh" / "prompt_templates"


class PromptTemplateNotFoundError(FileNotFoundError):
    """Raised when the specified prompt template or version is not found."""
    pass


def parse_prompt_spec(spec: str) -> Tuple[str, str]:
    """Parse name@version string into (name, version) tuple."""
    if "@" not in spec:
        raise ValueError(f"Invalid prompt specification '{spec}'. Format must be name@version (e.g., clinical_report@1.0.0)")
    parts = spec.split("@")
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise ValueError(f"Invalid prompt specification '{spec}'. Must contain non-empty name and version separated by '@'")
    return parts[0].strip(), parts[1].strip()


def load_prompt_template(spec: str) -> str:
    """
    Load exact text contents of a prompt template by name@version.
    Raises PromptTemplateNotFoundError if the template or version does not exist.
    """
    name, version = parse_prompt_spec(spec)
    template_path = PROMPT_TEMPLATES_DIR / name / f"{version}.md"

    if not template_path.exists():
        raise PromptTemplateNotFoundError(
            f"Prompt template '{spec}' not found at: {template_path}"
        )

    return template_path.read_text(encoding="utf-8")
