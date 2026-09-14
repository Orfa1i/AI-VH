"""
Unit Tests for DPO Training Pipeline (Phase 6 & 7)
Verifies dataset loading, format validation, and adapter output generation.
"""

import os
import json
import pytest
from backend.rl.train_dpo import DPOTrainingConfig, run_dpo_training, load_and_validate_dpo_dataset


def test_dpo_dataset_validation():
    dataset_path = "data/dpo_preference_dataset.jsonl"
    assert os.path.exists(dataset_path), "Preference dataset must exist"
    records = load_and_validate_dpo_dataset(dataset_path)
    assert len(records) >= 3
    for rec in records:
        assert "prompt" in rec and len(rec["prompt"]) > 10
        assert "chosen" in rec and len(rec["chosen"]) > 10
        assert "rejected" in rec and len(rec["rejected"]) > 10
        assert "reward_margin" in rec and rec["reward_margin"] > 0


def test_dpo_training_execution(tmp_path):
    output_dir = str(tmp_path / "test_lora_output")
    config = DPOTrainingConfig(
        model_name_or_path="google/medgemma-4b",
        dataset_path="data/dpo_preference_dataset.jsonl",
        output_dir=output_dir,
        epochs=2,
        dry_run=True,
    )
    result = run_dpo_training(config)
    assert result["pairs_trained"] >= 3
    assert result["epochs"] == 2
    assert os.path.exists(os.path.join(output_dir, "adapter_config.json"))
    assert os.path.exists(os.path.join(output_dir, "training_summary.json"))

    with open(os.path.join(output_dir, "adapter_config.json"), "r") as f:
        adapter = json.load(f)
        assert adapter["peft_type"] == "LORA"
        assert adapter["r"] == 16
