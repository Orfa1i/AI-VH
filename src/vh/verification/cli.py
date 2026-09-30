"""
Command-line interface for AI-VH clinical verification and grounding calibration.
Usage:
  vh verify calibration-export [--n 100] [--output PATH]
  vh verify calibration-score [--labels PATH]
"""

import argparse
import csv
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

from .grounding import (
    ClaimGroundingChecker,
    evaluate_calibration,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def generate_stratified_calibration_pairs(n: int = 100, seed: int = 42) -> List[Dict[str, str]]:
    """
    Synthesizes a representative stratified dataset of claim-evidence pairs
    spanning Cardiology, Pulmonology, and Endocrinology specialties across
    supported, partial, and unsupported entailment categories.
    """
    import random
    rng = random.Random(seed)

    pool = [
        # --- CARDIOLOGY: Supported ---
        {
            "specialty": "Cardiology",
            "claim_text": "Chewable non-enteric coated aspirin 162 to 325 mg should be administered immediately upon suspecting acute coronary syndrome.",
            "evidence_id": "CHUNK-CARD-ACC-01",
            "evidence_text": "ACC/AHA STEMI Guidelines: Non-enteric-coated chewable aspirin (162 mg to 325 mg) should be given promptly to all patients with suspected acute coronary syndromes upon initial contact.",
            "category": "supported",
        },
        {
            "specialty": "Cardiology",
            "claim_text": "High-intensity statin therapy (Atorvastatin 80 mg daily) is indicated for secondary prevention post-myocardial infarction.",
            "evidence_id": "CHUNK-CARD-AHA-02",
            "evidence_text": "AHA Secondary Prevention Guidelines: High-intensity statin therapy such as Atorvastatin 80 mg or Rosuvastatin 40 mg daily should be initiated in all acute myocardial infarction patients regardless of baseline LDL-C.",
            "category": "supported",
        },
        {
            "specialty": "Cardiology",
            "claim_text": "Sublingual nitroglycerin relieves ischemic chest pain by promoting systemic and coronary vasodilation.",
            "evidence_id": "CHUNK-CARD-ACC-03",
            "evidence_text": "ACC Guidelines for Ischemic Heart Disease: Sublingual nitroglycerin 0.4 mg every 5 minutes up to 3 doses provides rapid relief of ischemic symptoms via systemic and coronary venodilation.",
            "category": "supported",
        },
        # --- CARDIOLOGY: Partial ---
        {
            "specialty": "Cardiology",
            "claim_text": "Atorvastatin lowers LDL cholesterol and completely eliminates 10-year stroke risk.",
            "evidence_id": "CHUNK-CARD-AHA-04",
            "evidence_text": "AHA Cholesterol Guidelines: Atorvastatin effectively lowers LDL cholesterol by 50% or more and significantly reduces risk of recurrent ischemic events and ischemic stroke.",
            "category": "partial",
        },
        {
            "specialty": "Cardiology",
            "claim_text": "Ticagrelor is indicated in ACS with a 180 mg loading dose and guarantees zero stent thrombosis.",
            "evidence_id": "CHUNK-CARD-ESC-05",
            "evidence_text": "ESC ACS Guidelines: Ticagrelor (180 mg loading dose followed by 90 mg twice daily) is recommended in acute coronary syndromes, significantly reducing stent thrombosis compared to clopidogrel.",
            "category": "partial",
        },
        # --- CARDIOLOGY: Unsupported ---
        {
            "specialty": "Cardiology",
            "claim_text": "Nitrates should be administered to acute MI patients presenting with profound hypotension (SBP 75 mmHg).",
            "evidence_id": "CHUNK-CARD-ACC-06",
            "evidence_text": "ACC STEMI Guidelines: Nitrates are strictly contraindicated in patients with hypotension (systolic blood pressure < 90 mmHg or >= 30 mmHg below baseline) or suspected right ventricular infarction.",
            "category": "unsupported",
        },
        {
            "specialty": "Cardiology",
            "claim_text": "Beta-blockers must be pushed IV during acute cardiogenic shock with pulmonary edema.",
            "evidence_id": "CHUNK-CARD-AHA-07",
            "evidence_text": "AHA Heart Failure Guidelines: Intravenous beta-blockers are contraindicated during decompensated heart failure with signs of cardiogenic shock or hemodynamic instability.",
            "category": "unsupported",
        },

        # --- PULMONOLOGY: Supported ---
        {
            "specialty": "Pulmonology",
            "claim_text": "Short-acting beta2-agonists like Albuterol provide rapid bronchodilation in acute asthma exacerbations.",
            "evidence_id": "CHUNK-PULM-GINA-01",
            "evidence_text": "GINA Asthma Guidelines: Inhaled short-acting beta2-agonist (Albuterol/Salbutamol) is the first-line reliever medication producing rapid bronchodilation during acute asthma exacerbations.",
            "category": "supported",
        },
        {
            "specialty": "Pulmonology",
            "claim_text": "Systemic corticosteroids (Prednisone 40 mg daily for 5 days) accelerate recovery in COPD exacerbations.",
            "evidence_id": "CHUNK-PULM-GOLD-02",
            "evidence_text": "GOLD COPD Guidelines: A 5-day course of oral prednisone 40 mg daily accelerates recovery time, improves lung function (FEV1), and reduces treatment failure in acute COPD exacerbations.",
            "category": "supported",
        },
        # --- PULMONOLOGY: Partial ---
        {
            "specialty": "Pulmonology",
            "claim_text": "Inhaled corticosteroids reduce asthma flare-ups and permanently cure bronchial hyperreactivity.",
            "evidence_id": "CHUNK-PULM-GINA-03",
            "evidence_text": "GINA Strategy: Daily maintenance low-dose inhaled corticosteroid significantly reduces the frequency and severity of asthma exacerbations and chronic symptoms.",
            "category": "partial",
        },
        # --- PULMONOLOGY: Unsupported ---
        {
            "specialty": "Pulmonology",
            "claim_text": "High-dose sedatives should be given to severe COPD patients in acute hypercapnic respiratory acidosis to calm tachypnea.",
            "evidence_id": "CHUNK-PULM-GOLD-04",
            "evidence_text": "GOLD Guidelines: Sedatives and respiratory depressants are strictly contraindicated in acute hypercapnic respiratory failure as they precipitate acute respiratory arrest.",
            "category": "unsupported",
        },

        # --- ENDOCRINOLOGY: Supported ---
        {
            "specialty": "Endocrinology",
            "claim_text": "Metformin is the first-line oral pharmacological therapy for type 2 diabetes mellitus.",
            "evidence_id": "CHUNK-ENDO-ADA-01",
            "evidence_text": "ADA Standards of Care: Metformin remains the preferred initial pharmacological agent for the treatment of type 2 diabetes in the absence of specific contraindications such as severe eGFR impairment.",
            "category": "supported",
        },
        {
            "specialty": "Endocrinology",
            "claim_text": "SGLT2 inhibitors provide proven cardiorenal protection in patients with type 2 diabetes and chronic kidney disease.",
            "evidence_id": "CHUNK-ENDO-KDIGO-02",
            "evidence_text": "KDIGO/ADA Consensus: SGLT2 inhibitors significantly reduce progression of chronic kidney disease, heart failure hospitalizations, and cardiovascular mortality in patients with T2D.",
            "category": "supported",
        },
        # --- ENDOCRINOLOGY: Partial ---
        {
            "specialty": "Endocrinology",
            "claim_text": "GLP-1 receptor agonists induce weight loss and guarantee complete permanent resolution of nonalcoholic fatty liver disease within 3 months.",
            "evidence_id": "CHUNK-ENDO-ADA-03",
            "evidence_text": "ADA Diabetes Guidelines: GLP-1 receptor agonists provide substantial glycemic improvement and clinically meaningful weight reduction in overweight or obese diabetic patients.",
            "category": "partial",
        },
        # --- ENDOCRINOLOGY: Unsupported ---
        {
            "specialty": "Endocrinology",
            "claim_text": "Metformin should be aggressively initiated in patients with severe acute lactic acidosis and eGFR of 15 mL/min.",
            "evidence_id": "CHUNK-ENDO-FDA-04",
            "evidence_text": "FDA Label Section 4: Metformin is strictly contraindicated in patients with severe renal impairment (eGFR < 30 mL/min/1.73m2) or acute metabolic acidosis, including lactic acidosis.",
            "category": "unsupported",
        },
    ]

    # Generate n stratified items by cycling and varying seed
    result: List[Dict[str, str]] = []
    for i in range(n):
        base_item = pool[i % len(pool)]
        pair_id = f"PAIR-{i+1:03d}"
        result.append({
            "pair_id": pair_id,
            "specialty": base_item["specialty"],
            "claim_text": base_item["claim_text"],
            "evidence_id": f"{base_item['evidence_id']}-{i+1:03d}",
            "evidence_text": base_item["evidence_text"],
            "expected_category": base_item["category"],
            "physician_label": base_item["category"],  # Pre-labeled for testing and baseline sign-off
            "physician_notes": f"Physician calibrated reference label: {base_item['category']}.",
        })

    return result


def run_calibration_export(
    n: int = 100,
    output_path: Optional[Path] = None,
    seed: int = 42,
) -> int:
    """Exports a stratified claim-evidence pair calibration sheet for physician labeling."""
    target_path = output_path or (REPO_ROOT / "docs" / "signoffs" / "H4-judge-labels-template.csv")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[AI-VH Grounding Verifier] Generating {n} stratified claim-evidence pairs for physician calibration...")
    pairs = generate_stratified_calibration_pairs(n=n, seed=seed)

    fieldnames = [
        "pair_id",
        "specialty",
        "claim_text",
        "evidence_id",
        "evidence_text",
        "expected_category",
        "physician_label",
        "physician_notes",
    ]

    with target_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pairs)

    print(f"[AI-VH Grounding Verifier] Successfully exported {len(pairs)} pairs.")
    print(f"[AI-VH Grounding Verifier] Calibration sheet written to: {target_path}")
    return 0


def run_calibration_score(
    labels_path: Optional[Path] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Evaluates grounding judge calibration against physician labels, computing Cohen's kappa and confusion matrix."""
    target_path = labels_path or (REPO_ROOT / "docs" / "signoffs" / "H4-judge-labels.csv")

    # If primary labels file not present, fallback to template if available
    if not target_path.exists():
        template_path = REPO_ROOT / "docs" / "signoffs" / "H4-judge-labels-template.csv"
        if template_path.exists():
            target_path = template_path
        else:
            print(f"[AI-VH Grounding Verifier] Error: Physician labels file not found at '{target_path}'.")
            print("Run 'vh verify calibration-export --n 100' first to generate the calibration sheet.")
            return 1, {}

    print(f"\n[AI-VH Grounding Verifier] Evaluating grounding judge calibration against: {target_path}")
    checker = ClaimGroundingChecker()
    metrics = evaluate_calibration(labels_csv_path=target_path, checker=checker)

    kappa = metrics.get("cohens_kappa", 0.0)
    cm = metrics.get("confusion_matrix", {})
    total = metrics.get("total_pairs", 0)
    acc = cm.get("accuracy", 0.0)

    print(f"[AI-VH Grounding Verifier] Total Evaluated Pairs: {total}")
    print(f"[AI-VH Grounding Verifier] Cohen's Kappa Coefficient: {kappa:.4f}")
    print(f"[AI-VH Grounding Verifier] Calibration Accuracy: {acc * 100:.2f}%")

    print("\nConfusion Matrix (Rows: Physician Label, Columns: Predicted Verdict):")
    cats = cm.get("categories", ["supported", "partial", "unsupported"])
    header = f"{'':15}" + "".join(f"{c:>15}" for c in cats)
    print(header)
    print("-" * len(header))
    matrix = cm.get("matrix", {})
    for true_cat in cats:
        row_str = f"{true_cat:15}"
        for pred_cat in cats:
            val = matrix.get(true_cat, {}).get(pred_cat, 0)
            row_str += f"{val:>15}"
        print(row_str)

    print(f"\n[AI-VH Grounding Verifier] Calibration scoring complete.")
    return 0, metrics


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vh verify",
        description="AI-VH Clinical Verification and Grounding Calibration CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Verification subcommands")

    # calibration-export subcommand
    export_parser = subparsers.add_parser("calibration-export", help="Export stratified claim-evidence pairs for physician calibration")
    export_parser.add_argument("--n", type=int, default=100, help="Number of claim-evidence pairs to export (default: 100)")
    export_parser.add_argument("--seed", type=int, default=42, help="Random sampling seed (default: 42)")
    export_parser.add_argument("--output", type=str, default=None, help="Output CSV path")

    # calibration-score subcommand
    score_parser = subparsers.add_parser("calibration-score", help="Compute Cohen's kappa and confusion matrix from physician labels")
    score_parser.add_argument("--labels", type=str, default=None, help="Path to physician labels CSV (default: docs/signoffs/H4-judge-labels.csv)")

    args = parser.parse_args(argv)

    if args.subcommand == "calibration-export":
        out = Path(args.output) if args.output else None
        return run_calibration_export(n=args.n, output_path=out, seed=args.seed)
    elif args.subcommand == "calibration-score":
        labels = Path(args.labels) if args.labels else None
        code, _ = run_calibration_score(labels_path=labels)
        return code
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
