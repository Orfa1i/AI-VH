# ICU Agent

Role: `icu`
Department: ICU
Prompt: `icu@1.0.0`
Tools: `monitor_vitals`, `assess_acuity`, `record_icu_note`

Deterministic intensive-care monitoring over the isolated AgentView:
vital-sign flagging against documented critical/watch thresholds and acuity
summaries (`stable` / `watch` / `critical`). No diagnosis, no prescribing,
no orders; escalation goes through consultation.

## Checklist (implement, test, fix, gate)

1. **Implement**: DONE (STEP 54 proof agent). Tools derive strictly from
   `agent_view.initial_vitals`; thresholds mirror red-flag criteria.
2. **Test**: `tests/test_step_54_acceptance.py` (permission gating, AgentView
   isolation, deterministic acuity) plus Phase-5 suites in the full run.
3. **Fix**: permission entry applied to `configs/agents/permissions.yaml`
   (allowed: monitor/assess/note; clinical actions forbidden); exports
   registered in `src/vh/agents/roles/__init__.py` and `src/vh/agents/__init__.py`.
4. **Gate**: full regression green before merge (see `docs/steps/STEP-54.md`).
