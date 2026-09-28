"""
Reviewer packet generator for AI-VH Golden Cases.
Renders draft benchmark cases into clinical review packets in Markdown and PDF formats.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from vh.cases.schema import GoldenCase


def render_markdown_packet(cases: List[GoldenCase], packet_title: str = "Golden Set v1 Clinical Review Packet") -> str:
    """Render draft cases into Markdown packet with checkboxes per field and space for corrections."""
    lines = [
        f"# {packet_title}",
        "",
        "## Instructions for Attending Physician Reviewer",
        "Please review each clinical case specification below against standard inpatient clinical guidelines.",
        "1. Check the box for each approved clinical dimension.",
        "2. Note any medical inaccuracies, necessary differential additions, or required diagnostic tests.",
        "3. Complete the sign-off sheet in `docs/signoffs/golden-v1.md` with your approved case list.",
        "",
        f"- **Total Draft Cases for Review:** {len(cases)}",
        "- **Target Specialties:** Acute Coronary Syndrome, Community-Acquired Pneumonia, Diabetic Ketoacidosis",
        "",
        "---",
        ""
    ]

    for idx, case in enumerate(cases, start=1):
        lines.extend([
            f"### Case {idx}: {case.case_id} ({case.specialty})",
            f"- **Patient Ref:** `{case.patient_ref}` | **Status:** `{case.status}` | **Version:** `{case.version}`",
            "",
            "#### 1. Patient Presentation (Visible)",
            f"- **Chief Complaint:** {case.visible_presentation.get('chief_complaint', 'N/A')}",
            f"- **History:** {case.visible_presentation.get('history', 'N/A')}",
            f"- **Vitals:** {case.visible_presentation.get('vitals', {})}",
            f"- **Exam:** {case.visible_presentation.get('exam', 'N/A')}",
            "",
            "#### 2. Clinical Ground Truth (Evaluation Yardstick)",
            f"- [ ] **Primary Diagnosis:** `{case.ground_truth.primary_dx}`",
            f"- [ ] **Acceptable Differential:** {', '.join(case.ground_truth.acceptable_differential) if case.ground_truth.acceptable_differential else 'None'}",
            f"- [ ] **Expected Workup:** {', '.join(case.ground_truth.expected_workup) if case.ground_truth.expected_workup else 'None'}",
            f"- [ ] **Red Flags:** {', '.join(case.ground_truth.red_flags) if case.ground_truth.red_flags else 'None'}",
            "",
            "#### 3. Supporting Evidence & References",
        ])

        if case.supporting_references:
            for ref in case.supporting_references:
                lines.append(f"- [ ] **Source:** {ref.source} ({ref.locator}) : *{ref.note}*")
        else:
            lines.append("- [ ] *No supporting references listed (flagged for review)*")

        lines.extend([
            "",
            "#### 4. Physician Corrections & Feedback",
            "- [ ] **Case Approved as Golden Standard**",
            "- **Corrections / Amendments:** `________________________________________________`",
            "",
            "---",
            ""
        ])

    return "\n".join(lines)


def render_pdf_packet(cases: List[GoldenCase], pdf_path: Path, title: str = "AI-VH Golden Set v1 Reviewer Packet") -> None:
    """Render draft cases into a formatted PDF document using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib import colors

        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            "CaseHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0369a1"),
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "CaseBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e293b")
        )

        story = []
        story.append(Paragraph(title, title_style))
        story.append(Paragraph("Clinical AI Evaluation Harness : Attending Physician Review Packet", styles["Normal"]))
        story.append(Paragraph(f"Total Cases: {len(cases)} across ACS, CAP, and DKA specialties.", styles["Normal"]))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        for case in cases:
            story.append(Paragraph(f"<b>{case.case_id}</b> : {case.specialty} (Patient: {case.patient_ref})", heading_style))
            cc = case.visible_presentation.get("chief_complaint", "N/A")
            story.append(Paragraph(f"<b>Chief Complaint:</b> {cc}", body_style))
            story.append(Paragraph(f"<b>Primary Dx:</b> [ ] {case.ground_truth.primary_dx}", body_style))
            diff_str = ", ".join(case.ground_truth.acceptable_differential)
            story.append(Paragraph(f"<b>Differentials:</b> [ ] {diff_str}", body_style))
            workup_str = ", ".join(case.ground_truth.expected_workup)
            story.append(Paragraph(f"<b>Expected Workup:</b> [ ] {workup_str}", body_style))
            story.append(Spacer(1, 8))

        doc.build(story)
    except Exception as e:
        # Fallback if ReportLab has rendering error
        pdf_path.write_text(f"PDF generation note: {e}\nSee companion Markdown packet.", encoding="utf-8")


def export_reviewer_packet(
    cases_dir: Path,
    output_md_path: Path,
    output_pdf_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Export all draft cases from cases_dir to markdown and PDF packets."""
    cases: List[GoldenCase] = []
    for file_path in sorted(cases_dir.glob("*.json")):
        if file_path.name == "manifest.json":
            continue
        data = json.loads(file_path.read_text(encoding="utf-8"))
        cases.append(GoldenCase(**data))

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    md_content = render_markdown_packet(cases)
    output_md_path.write_text(md_content, encoding="utf-8")

    pdf_generated = False
    if output_pdf_path:
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        render_pdf_packet(cases, output_pdf_path)
        pdf_generated = True

    return {
        "cases_exported": len(cases),
        "markdown_packet": str(output_md_path),
        "pdf_packet": str(output_pdf_path) if pdf_generated else None
    }
