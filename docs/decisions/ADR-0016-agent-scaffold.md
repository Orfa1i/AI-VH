# ADR-0016: Agent Scaffold and Permissions-Path Fix

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: AI Agent (implementation)
- **Governing Document**: `plan/prompts/phase-9-advanced/STEP-54_P9.4_new-agent-template.md`

---

## 1. Scaffold design

- `generate_agent_scaffold` emits agent class (tool stubs raising
  `NotImplementedError`), versioned prompt (`<role>/1.0.0.md`), permission
  *snippet* (emitted for deliberate application, never auto-merged),
  starter tests, and a docs page with the implement/test/fix/gate checklist.
- `vh new-agent` routes through the existing agents CLI; repository-layout
  placement with tmp staging cleaned up afterwards.
- Proof agent ICU ships fully implemented: deterministic vital flags and
  acuity bands over the live AgentView; no diagnosis, prescribing, or orders.

## 2. FIX-LOOP: permissions config never loaded (Phase 5)

- `src/vh/agents/roles/base.py` computed its repo root one level short, so
  `PERMISSIONS_CONFIG_PATH` pointed at non-existent `src/configs/...` and
  every role loaded EMPTY permission sets. The tool layer therefore gated
  nothing: allowed tools via `invoke_tool` always raised, forbidden tools were
  blocked only vacuously, and orchestrator flows (direct method calls) never
  noticed. Fixed the depth; added `test_permissions_config_loads_with_role_entries`.
- Audited every other `REPO_ROOT` computation in `src/vh`: only this one was
  wrong (depth-4 module using a depth-3 formula).
