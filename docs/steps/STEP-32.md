# Step Report: STEP-32 (P5.2 Specialised Agents and Tool Permissions)

- **Phase:** Phase 5: Agents & Orchestration (headless)
- **Step:** STEP 32 of 54 (P5.2)
- **Status:** DONE
- **Timestamp:** 2026-09-30T10:42:00Z
- **Tag:** `step-32-pass`

---

## 1. Built: Files Created or Changed

1. `configs/agents/permissions.yaml`:
   - Role-based tool permission matrix covering all 5 specialized hospital roles: `doctor`, `nurse`, `lab`, `radiology`, `pharmacy`.
   - Defines disjoint sets of `allowed_tools` and `forbidden_tools` for each role.
2. Prompt Templates:
   - `src/vh/prompt_templates/doctor/1.0.0.md`
   - `src/vh/prompt_templates/nurse/1.0.0.md`
   - `src/vh/prompt_templates/lab/1.0.0.md`
   - `src/vh/prompt_templates/radiology/1.0.0.md`
   - `src/vh/prompt_templates/pharmacy/1.0.0.md`
3. `src/vh/agents/roles/`:
   - `base.py`:
     - `ToolPermissionError`: PermissionError raised when forbidden or unauthorized tools are invoked.
     - `BaseAgent`: Base clinical agent enforcing strict `AgentView` data isolation (direct `CaseSpec` injection rejected), tool-layer permission checking against `permissions.yaml`, blocked action logging, and live `AgentView` environment synchronization.
   - `doctor.py`:
     - `DoctorAgent`: Attending physician agent. Can order labs and imaging, consult, diagnose, prescribe, and generate clinical assessments via `MedGemmaAdapter`.
   - `nurse.py`:
     - `NurseAgent`: Clinical nurse agent. Handles vitals, observations, and progress notes. Blocked at both tool layer and method dispatch from prescribing medications or diagnosing.
   - `lab.py`:
     - `LabAgent`: Clinical laboratory agent. Analyzes specimens and returns released quantitative values with reference ranges and abnormal flags.
   - `radiology.py`:
     - `RadiologyAgent`: Diagnostic radiologist agent. Interprets released imaging studies. Image pixel inspection tool (`inspect_image_pixels`) is stubbed with an explicit `NotImplementedError` ("stubbed until Phase 9 multi-modal integration").
   - `pharmacy.py`:
     - `PharmacyAgent`: Clinical pharmacist agent. Analyzes medication profiles, detects allergy conflicts against documented patient allergies, evaluates drug-drug interactions via P4.1 rules, and provides renal dosing adjustment guidance based on eGFR.
   - `__init__.py`:
     - Exports all specialized agents and base classes.
4. `src/vh/agents/__init__.py`:
   - Exported `BaseAgent`, `DoctorAgent`, `NurseAgent`, `LabAgent`, `RadiologyAgent`, `PharmacyAgent`, and `ToolPermissionError`.
5. `tests/test_step_32_acceptance.py`:
   - 8 acceptance and unit tests verifying permission matrix integrity, tool blocking and event logging, MedGemma adapter wrapping, data isolation, and functional contracts for all 5 roles.

---

## 2. Tests Added and Full Regression Results

### New Tests (`tests/test_step_32_acceptance.py`):
- `test_permission_matrix_schema_and_roles`: Verifies `permissions.yaml` defines all 5 roles with disjoint allowed and forbidden tool sets.
- `test_for_every_role_forbidden_tools_are_blocked_and_logged`: For every role, iterates through each forbidden tool; proves invocation raises `ToolPermissionError` and is logged in the agent's event stream as `tool_blocked`.
- `test_all_llm_calls_go_through_adapter`: Verifies via patching that LLM generation calls route directly through `MedGemmaAdapter.generate`.
- `test_agents_receive_only_agent_view_derived_data`: Verifies agents accept only `AgentView` and reject `CaseSpec` or ground truth objects.
- `test_specialized_roles_functional_behavior`: Tests core workflow for Nurse, Doctor, Lab, Radiology, and Pharmacy agents.
- `test_versioned_prompt_template_loading_across_all_roles`: Verifies prompt templates load without error across all 5 roles.
- `test_pharmacy_interactions_and_renal_dosing`: Tests drug-drug interactions and eGFR-dependent renal dose adjustments.
- `test_agent_events_propagated_to_environment_store`: Verifies events emitted by agents propagate to the environment event log.

### Test Suite Execution:
- `py -3.13 -m pytest tests/test_step_32_acceptance.py`: 8 passed in 8.15s.
- `py -3.13 scripts/test_all.py test-all`: **240 of 240 tests passed (100% green)** in 272.77s.
- Secret scanner: 0 hardcoded secrets or credentials detected.

---

## 3. Failures Found and Resolved

1. **Symptom:** `hasattr(agent_view, "_ground_truth")` raised `DataIsolationError` in `BaseAgent.__init__`.
   - **Root Cause:** In `AgentView.__getattr__`, any inquiry into forbidden fields raises `DataIsolationError` (PermissionError). `hasattr` does not catch PermissionError.
   - **Fix:** Switched the type check to `not isinstance(agent_view, AgentView) or isinstance(agent_view, CaseSpec)`.
   - **Regression Test:** Verified in `tests/test_step_32_acceptance.py::test_agents_receive_only_agent_view_derived_data`.
2. **Symptom:** `LabAgent.get_lab_result` returned `pending_or_unreleased` after `env.advance_clock(35)`.
   - **Root Cause:** `AgentView` is immutable. When `env.advance_clock` releases findings, `env._agent_view` is replaced with a new instance. If `lab.agent_view` stored a static reference to the initial view, it did not see newly released results.
   - **Fix:** Converted `BaseAgent.agent_view` into a dynamic property that queries `self.environment.agent_view` if an environment is attached.
   - **Regression Test:** Verified in `tests/test_step_32_acceptance.py::test_specialized_roles_functional_behavior`.

---

## 4. Gap Review (Acceptance Criteria Verification)

| Requirement / Criterion | File / Test Evidence | Status |
|:---|:---|:---|
| For every role, forbidden tools are blocked and logged | `tests/test_step_32_acceptance.py::test_for_every_role_forbidden_tools_are_blocked_and_logged` | PASS |
| All LLM calls go through adapter | `tests/test_step_32_acceptance.py::test_all_llm_calls_go_through_adapter` | PASS |
| Agents receive only AgentView-derived data | `tests/test_step_32_acceptance.py::test_agents_receive_only_agent_view_derived_data` | PASS |
| Permission matrix in `configs/agents/permissions.yaml` | `configs/agents/permissions.yaml` | PASS |
| Versioned prompt templates for each role | `src/vh/prompt_templates/<role>/1.0.0.md` | PASS |
| All 5 specialized roles implemented | `src/vh/agents/roles/` (`doctor.py`, `nurse.py`, `lab.py`, `radiology.py`, `pharmacy.py`) | PASS |
| Full verification suite passing | `scripts/test_all.py` (240/240 passed) | PASS |

---

## 5. Open Questions / Assumptions

None. All criteria met and certified.
