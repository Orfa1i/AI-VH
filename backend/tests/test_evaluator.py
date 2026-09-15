"""
Unit and Integration Tests for Comparative Policy Evaluator (Phase 5/7)
Verifies head-to-head benchmarking between Base MedGemma and RL DPO-aligned agents,
evaluating metrics, win-rate calculations, and REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.rl.evaluator import PolicyEvaluator, BenchmarkComparisonReport, CaseComparisonResult
from backend.clinical.cases import get_benchmark_case, BENCHMARK_CASES


def test_evaluate_case_nstemi():
    case = get_benchmark_case("CASE-101")
    result: CaseComparisonResult = PolicyEvaluator.evaluate_case(case)
    
    assert result.case_id == "CASE-101"
    assert result.winner == "RL_AGENT"
    assert result.score_delta > 2.0
    assert result.safety_gain_percent > 40.0
    assert result.base_agent_metrics.contraindications_missed >= 1
    assert result.rl_agent_metrics.contraindications_missed == 0
    assert "NSTEMI" in result.rl_agent_metrics.primary_diagnosis


def test_evaluate_case_dka():
    case = get_benchmark_case("CASE-102")
    result: CaseComparisonResult = PolicyEvaluator.evaluate_case(case)
    
    assert result.case_id == "CASE-102"
    assert result.winner == "RL_AGENT"
    assert result.rl_agent_metrics.overall_clinical_score >= 4.5
    assert result.base_agent_metrics.overall_clinical_score < 3.0
    assert result.base_agent_metrics.contraindications_missed >= 1
    assert result.rl_agent_metrics.contraindications_missed == 0


def test_evaluate_case_aki():
    case = get_benchmark_case("CASE-103")
    result: CaseComparisonResult = PolicyEvaluator.evaluate_case(case)
    
    assert result.case_id == "CASE-103"
    assert result.winner == "RL_AGENT"
    assert result.rl_agent_metrics.overall_clinical_score >= 4.5
    assert "Acute Kidney Injury" in result.rl_agent_metrics.primary_diagnosis


def test_run_full_benchmark():
    report: BenchmarkComparisonReport = PolicyEvaluator.run_full_benchmark()
    
    assert report.total_cases == len(BENCHMARK_CASES)
    assert report.rl_win_rate_percent == 100.0
    assert report.rl_agent_mean_score > report.base_agent_mean_score
    assert report.mean_score_improvement_percent > 80.0
    assert report.adverse_safety_reduction_rate == 100.0
    assert "STATISTICALLY SIGNIFICANT CLINICAL IMPROVEMENT" in report.research_verdict
    assert len(report.case_comparisons) == len(BENCHMARK_CASES)


def test_api_rl_benchmark_endpoint():
    client = TestClient(app)
    response = client.get("/api/rl/benchmark")
    assert response.status_code == 200
    data = response.json()
    
    assert "evaluation_id" in data
    assert data["total_cases"] >= 3
    assert data["rl_win_rate_percent"] == 100.0
    assert data["mean_score_improvement_percent"] > 0
    assert len(data["case_comparisons"]) >= 3


def test_api_rl_benchmark_single_case():
    client = TestClient(app)
    response = client.get("/api/rl/benchmark/cases/CASE-101")
    assert response.status_code == 200
    data = response.json()
    
    assert data["case_id"] == "CASE-101"
    assert data["winner"] == "RL_AGENT"
    assert data["safety_gain_percent"] > 0

    # Test 404 for invalid case
    res_404 = client.get("/api/rl/benchmark/cases/NON-EXISTENT-CASE")
    assert res_404.status_code == 404


def test_api_inpatient_rooms_endpoint():
    client = TestClient(app)
    response = client.get("/api/inpatient/rooms")
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) == 4
    room_numbers = [r["room_number"] for r in rooms]
    assert "101" in room_numbers
    assert "102" in room_numbers
    assert "103" in room_numbers
    assert "104" in room_numbers
    assert rooms[0]["heart_rate"] > 0
    assert "rhythm_strip" in rooms[0]


def test_api_rl_inference_compare_endpoint():
    client = TestClient(app)
    payload = {
        "case_id": "CASE-101",
        "force_gpu": False
    }
    response = client.post("/api/rl/inference/compare", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == "CASE-101"
    assert "telemetry" in data
    assert "hardware_device" in data["telemetry"]
    assert "precision" in data["telemetry"]
    assert "base_model_output" in data
    assert "dpo_model_output" in data
    assert "comparison_summary" in data

    # Check Base model vulnerabilities captured
    base = data["base_model_output"]
    assert len(base["contraindications_flagged"]) > 0
    assert base["clinical_reward_score"] < 0

    # Check DPO model improvements captured
    dpo = data["dpo_model_output"]
    assert len(dpo["contraindications_flagged"]) == 0
    assert dpo["clinical_reward_score"] > 8.0
    assert len(dpo["rag_evidence_citations"]) > 0
    assert data["comparison_summary"]["winner"] == "RL_DPO_ALIGNED"


def test_medgemma_service_all_cases_comparative_inference():
    from backend.llm.medgemma_service import medgemma_service
    for case_id in ["CASE-101", "CASE-102", "CASE-103", "CASE-104"]:
        res = medgemma_service.generate_comparative_inference(case_id=case_id)
        assert res["case_id"] == case_id
        assert res["comparison_summary"]["winner"] == "RL_DPO_ALIGNED"
        assert res["dpo_model_output"]["adverse_safety_violations"] == 0


