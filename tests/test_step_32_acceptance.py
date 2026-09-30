"""
Acceptance criteria tests for STEP 32 (P5.2):
Specialised Agents and Tool Permissions.

Criteria:
1. For every role, a test attempts each forbidden tool: blocked and logged.
2. All LLM calls go through the adapter (verified by patching).
3. Agents receive only AgentView-derived data.
4. Functional contracts for all 5 specialized roles (Doctor, Nurse, Lab, Radiology, Pharmacy).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import yaml

from vh.cases.spec import AgentView, CaseSpec, DataIsolationError, HiddenResult, VisiblePresentation
from vh.cases.schema import GroundTruth
from vh.agents.environment import HospitalEnvironment
from vh.agents.roles.base import BaseAgent, ToolPermissionError
from vh.agents.roles.doctor import DoctorAgent
from vh.agents.roles.nurse import NurseAgent
from vh.agents.roles.lab import LabAgent
from vh.agents.roles.radiology import RadiologyAgent
from vh.agents.roles.pharmacy import PharmacyAgent
from vh.generation.medgemma import MedGemmaAdapter

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def permissions_config() -> dict:
    """Load the canonical agent permission matrix from configs/agents/permissions.yaml."""
    perm_path = REPO_ROOT / "configs" / "agents" / "permissions.yaml"
    assert perm_path.exists(), f"Permission matrix not found at {perm_path}"
    with open(perm_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_case_spec() -> CaseSpec:
    """Standard clinical case specification."""
    visible = VisiblePresentation(
        presentation="64-year-old male with acute severe epigastric and chest pain.",
        demographics={"age": 64, "gender": "male"},
        history="Hypertension, peptic ulcer disease.",
        current_medications=["Lisinopril 20mg daily", "Omeprazole 20mg daily"],
        allergies=["Aspirin", "Ibuprofen"],
        initial_vitals={"bp": "160/95", "hr": 92, "rr": 20, "spo2": 96, "temp": 37.2},
        exam="Moderate epigastric tenderness, no peritoneal signs, heart regular.",
    )
    hidden = [
        HiddenResult(
            order_code="LAB-TROP",
            order_name="High-Sensitivity Troponin I",
            result="85 ng/L (elevated, ref < 14 ng/L)",
            turnaround_time_minutes=30,
            category="laboratory",
        ),
        HiddenResult(
            order_code="DX-ECG",
            order_name="12-Lead Electrocardiogram",
            result="T-wave inversions in leads V4-V6.",
            turnaround_time_minutes=10,
            category="imaging",
        ),
    ]
    ground_truth = GroundTruth(
        primary_dx="Non-ST-Elevation Myocardial Infarction",
        acceptable_differential=["Unstable Angina", "Acute Peptic Ulcer Disease", "Esophageal Spasm"],
        expected_workup=["12-Lead ECG", "Serial Troponins", "Complete Blood Count", "Metabolic Panel"],
        red_flags=["Hemodynamic instability", "Ischemic ventricular arrhythmia"],
    )
    return CaseSpec(
        case_id="CASE-SPEC-002",
        specialty="Internal Medicine",
        patient_ref="PAT-002",
        visible=visible,
        hidden=hidden,
        ground_truth=ground_truth,
        status="verified",
        version="1.0.0",
    )


def test_permission_matrix_schema_and_roles(permissions_config):
    """Verify permissions.yaml defines all 5 required roles with allowed and forbidden tools."""
    required_roles = {"doctor", "nurse", "lab", "radiology", "pharmacy"}
    assert set(permissions_config.keys()).issuperset(required_roles)

    for role in required_roles:
        cfg = permissions_config[role]
        assert "allowed_tools" in cfg
        assert "forbidden_tools" in cfg
        assert isinstance(cfg["allowed_tools"], list)
        assert isinstance(cfg["forbidden_tools"], list)
        # Allowed and forbidden sets must be disjoint
        intersection = set(cfg["allowed_tools"]) & set(cfg["forbidden_tools"])
        assert len(intersection) == 0, f"Role '{role}' has overlapping tools: {intersection}"


def test_for_every_role_forbidden_tools_are_blocked_and_logged(permissions_config, sample_case_spec):
    """
    Acceptance criterion 1:
    For every role, a test attempts each forbidden tool: blocked and logged.
    """
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)
    view = env.agent_view

    agents = {
        "doctor": DoctorAgent(agent_view=view, environment=env),
        "nurse": NurseAgent(agent_view=view, environment=env),
        "lab": LabAgent(agent_view=view, environment=env),
        "radiology": RadiologyAgent(agent_view=view, environment=env),
        "pharmacy": PharmacyAgent(agent_view=view, environment=env),
    }

    for role_name, agent in agents.items():
        forbidden_tools = permissions_config[role_name]["forbidden_tools"]
        assert len(forbidden_tools) > 0, f"Role {role_name} has no forbidden tools configured!"

        for tool_name in forbidden_tools:
            initial_event_count = len(agent.events)

            # Invoking forbidden tool must raise ToolPermissionError
            with pytest.raises(ToolPermissionError) as exc_info:
                agent.invoke_tool(tool_name, dummy_param="test")

            assert f"Role '{role_name}' is not permitted to execute tool '{tool_name}'" in str(exc_info.value)

            # Blocked attempt must be logged in agent events
            assert len(agent.events) == initial_event_count + 1
            logged_event = agent.events[-1]
            assert logged_event.actor == role_name
            assert logged_event.action == "tool_blocked"
            assert logged_event.payload["tool_name"] == tool_name
            assert logged_event.payload["reason"] == "permission_denied"


def test_all_llm_calls_go_through_adapter(sample_case_spec):
    """
    Acceptance criterion 2:
    All LLM calls go through the adapter (verified by patching).
    """
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)
    view = env.agent_view

    mock_adapter = MagicMock(spec=MedGemmaAdapter)
    mock_adapter.generate.return_value = {
        "summary": "Patient presented with acute chest pain and epigastric discomfort.",
        "differential": ["NSTEMI", "Peptic Ulcer"],
        "recommendations": ["Serial troponin", "ECG monitoring"],
    }

    doctor = DoctorAgent(agent_view=view, environment=env, adapter=mock_adapter)

    # Trigger LLM generation action on doctor
    result = doctor.generate_clinical_assessment()
    assert result is not None

    # Verify adapter.generate was called directly
    assert mock_adapter.generate.called
    call_args = mock_adapter.generate.call_args
    assert "doctor@1.0.0" in str(call_args) or "clinical_report" in str(call_args)
    assert "inputs" in call_args.kwargs or len(call_args.args) >= 2


def test_agents_receive_only_agent_view_derived_data(sample_case_spec):
    """
    Acceptance criterion 3:
    Agents receive only AgentView-derived data.
    Direct injection of CaseSpec or ground truth is strictly rejected.
    """
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)
    view = env.agent_view

    # Valid initialization with AgentView
    nurse = NurseAgent(agent_view=view, environment=env)
    assert isinstance(nurse.agent_view, AgentView)

    # Invariant: agent_view has no ground truth attributes
    with pytest.raises(DataIsolationError):
        _ = nurse.agent_view.ground_truth

    # Attempting to initialize any agent with CaseSpec raises DataIsolationError or TypeError
    with pytest.raises((DataIsolationError, TypeError)):
        DoctorAgent(agent_view=sample_case_spec, environment=env)

    with pytest.raises((DataIsolationError, TypeError)):
        NurseAgent(agent_view=sample_case_spec, environment=env)


def test_specialized_roles_functional_behavior(sample_case_spec):
    """
    Acceptance criterion 4:
    Verify functional contracts for all 5 specialized roles.
    """
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)
    view = env.agent_view

    # 1. Nurse: requests vitals, records observation; blocked from prescribing or diagnosing
    nurse = NurseAgent(agent_view=view, environment=env)
    vitals = nurse.request_vitals()
    assert vitals["bp"] == "160/95"
    obs_resp = nurse.record_observation("Patient resting comfortably in bed, diaphoretic.")
    assert obs_resp["status"] == "recorded"
    with pytest.raises(ToolPermissionError):
        nurse.order_medication("Morphine 2mg IV")
    with pytest.raises(ToolPermissionError):
        nurse.diagnose("Acute Myocardial Infarction")

    # 2. Doctor: orders lab and imaging, consults
    doctor = DoctorAgent(agent_view=view, environment=env)
    order_res = doctor.order_lab("LAB-TROP")
    assert order_res.status.value in ["pending", "released"]
    consult_res = doctor.consult(role="cardiology", query="Evaluate for urgent cardiac catheterization")
    assert consult_res["status"] == "acknowledged"

    # 3. Lab: returns released results with reference ranges and flags
    lab = LabAgent(agent_view=view, environment=env)
    # Advance clock to release troponin
    env.advance_clock(35)
    lab_finding = lab.get_lab_result("LAB-TROP")
    assert lab_finding["status"] == "released"
    assert "85 ng/L" in str(lab_finding["result"])
    assert lab_finding["flag"] == "abnormal"

    # 4. Radiology: returns report text; image pixel inspection tool is stubbed with NotImplementedError
    doctor.order_imaging("DX-ECG")
    env.advance_clock(15)
    radiology = RadiologyAgent(agent_view=view, environment=env)
    rad_finding = radiology.interpret_imaging("DX-ECG")
    assert "T-wave inversions" in str(rad_finding["report_text"])
    # STEP-51 replaced the Phase 9 stub with reference imaging tools:
    # pixel inspection now executes with typed, labeled model output.
    import numpy as np

    from vh.agents.tools.imaging import generate_fracture_phantom

    phantom = generate_fracture_phantom(seed=99, fracture=True)
    tool_out = radiology.inspect_image_pixels("DX-WRIST", image=phantom["pixels"])
    assert tool_out["finding"] == "fracture_detected"
    assert tool_out["interpretation"] == "model-output"
    assert tool_out["output_id"].startswith("IMG-")
    with pytest.raises(ValueError, match="Unknown imaging tool"):
        radiology.inspect_image_pixels("DX-WRIST", image=np.zeros((8, 8)), tool="nope")
    with pytest.raises(ValueError, match="requires an image array"):
        radiology.inspect_image_pixels("DX-WRIST")

    # 5. Pharmacy: checks medication info and performs allergy/interaction checks via P4.1 rules
    pharmacy = PharmacyAgent(agent_view=view, environment=env)
    med_info = pharmacy.get_medication_info("Lisinopril")
    assert med_info["patient_on_drug"] is True

    # Allergy check for Aspirin (patient is allergic)
    allergy_check = pharmacy.check_allergies("Aspirin 81mg po daily")
    assert allergy_check["has_allergy_conflict"] is True
    assert "Aspirin" in allergy_check["conflicting_allergies"]


def test_versioned_prompt_template_loading_across_all_roles(sample_case_spec):
    """Verify all 5 specialized agents load their versioned prompt template."""
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)
    view = env.agent_view

    agents = [
        DoctorAgent(agent_view=view, environment=env),
        NurseAgent(agent_view=view, environment=env),
        LabAgent(agent_view=view, environment=env),
        RadiologyAgent(agent_view=view, environment=env),
        PharmacyAgent(agent_view=view, environment=env),
    ]

    for agent in agents:
        prompt = agent.load_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50
        assert agent.role.capitalize() in prompt or agent.role in prompt


def test_pharmacy_interactions_and_renal_dosing(sample_case_spec):
    """Verify pharmacy agent detects drug interactions and evaluates renal dosing."""
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)
    pharmacy = PharmacyAgent(agent_view=env.agent_view, environment=env)

    # High-risk interaction: Warfarin + Aspirin
    inter_res = pharmacy.check_interactions("Warfarin", "Aspirin")
    assert inter_res["has_interaction"] is True
    assert inter_res["severity"] == "major"

    # Benign pair
    safe_res = pharmacy.check_interactions("Amoxicillin", "Acetaminophen")
    assert safe_res["has_interaction"] is False

    # Severe renal impairment: Metformin with eGFR = 20
    renal_res = pharmacy.check_renal_dosing("Metformin", egfr=20.0)
    assert renal_res["requires_adjustment"] is True
    assert "Contraindicated" in renal_res["clinical_guidance"]

    # Normal renal function: Metformin with eGFR = 90
    normal_renal = pharmacy.check_renal_dosing("Metformin", egfr=90.0)
    assert normal_renal["requires_adjustment"] is False


def test_agent_events_propagated_to_environment_store(sample_case_spec):
    """Verify agent actions are recorded in environment event store with correct actor and action."""
    env = HospitalEnvironment(case_spec=sample_case_spec, seed=42)
    doctor = DoctorAgent(agent_view=env.agent_view, environment=env)
    nurse = NurseAgent(agent_view=env.agent_view, environment=env)

    initial_events = len(env.event_store.get_events())

    nurse.record_observation("Patient resting quietly, respiration unlabored.")
    doctor.consult(role="cardiology", query="Review telemetry rhythm strip.")

    events = env.event_store.get_events()
    assert len(events) == initial_events + 2

    nurse_event = events[-2]
    assert nurse_event.actor == "nurse"
    assert nurse_event.action == "record_observation"

    doc_event = events[-1]
    assert doc_event.actor == "doctor"
    assert doc_event.action == "consult"
