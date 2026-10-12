"""
Phase 2 pipeline feature flag.

VH_PIPELINE=legacy   -> legacy backend paths (default; pre-Phase-2 behavior)
VH_PIPELINE=grounded -> src/vh grounded assessment path with mandatory retrieval_log

Default stays legacy until Phase 3 proves grounded parity: flipping the
default to grounded broke 2 legacy encounter tests in CI (offline heuristic
mis-routed CASE-101; evidence in ADR-0018 §4). Rollback is a flag change only.
Legacy run() and medgemma_service paths are NOT deleted and must not be
deleted before Phase 6.

Owner: AI Engineer.
"""

import os

LEGACY = "legacy"
GROUNDED = "grounded"


def get_pipeline_mode() -> str:
    """Return the active pipeline mode (legacy default)."""
    mode = os.environ.get("VH_PIPELINE", LEGACY).strip().lower()
    if mode == GROUNDED:
        return GROUNDED
    return LEGACY


def is_grounded() -> bool:
    """True when the grounded assessment path is active."""
    return get_pipeline_mode() == GROUNDED
