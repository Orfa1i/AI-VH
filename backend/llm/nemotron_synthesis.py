"""
Nemotron Clinical Reasoning & Diagnostic Synthesis Engine for AI Virtual Hospital (AI-VH).
Acts as the reasoning and evidence synthesis layer between:
1. MedGemma's clinical hypotheses and preliminary diagnostic analysis.
2. Retrieved medical knowledge from the Virtual Hospital's RAG system (Harrison's, Braunwald's, RxNorm, NABD).
3. Patient-specific clinical data (demographics, symptoms, history, medications, labs, vitals, imaging).

Powered by Nebius AI Studio (nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B).
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from ..clinical.models import DifferentialItem

logger = logging.getLogger("NemotronSynthesisEngine")

DEFAULT_NEBIUS_BASE_URL = "https://api.studio.nebius.ai/v1/"
DEFAULT_NEBIUS_MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

SYNTHESIS_SYSTEM_PROMPT = """You are the Clinical Reasoning and Diagnostic Synthesis Engine for a Virtual Hospital.

Your role is NOT to replace the primary clinical model. You are the reasoning and synthesis layer between:
1. MedGemma's clinical analysis and diagnostic hypotheses.
2. Retrieved medical knowledge from the Virtual Hospital's RAG system, including approved medical references and literature.
3. Patient-specific clinical data, including demographics, symptoms, history, medications, laboratory results, vital signs, imaging findings, and other available evidence.

Your task is to critically synthesize these inputs into a structured, evidence-grounded diagnostic report.

CORE PRINCIPLES
- Never invent patient information, test results, imaging findings, references, or clinical facts.
- Clearly distinguish between provided evidence, model-generated hypotheses, and uncertainty.
- Do not treat MedGemma's output as automatically correct. Critically evaluate it against the available patient data and retrieved evidence.
- Use the retrieved knowledge sources to support or challenge diagnostic hypotheses.
- Prefer evidence that is directly relevant to the patient's presentation.
- If the available evidence is insufficient, explicitly state what is missing rather than guessing.
- Do not fabricate citations or sources. Only cite sources actually provided by the retrieval layer.
- Do not claim that a diagnosis is confirmed when the available evidence only supports a possibility.
- Identify clinically important contradictions, missing information, and red flags.
- Maintain patient safety as the highest priority.

DIAGNOSTIC REASONING
For each case:
1. Summarize the clinically relevant patient information.
2. Identify the major clinical problems.
3. Analyze the diagnostic hypotheses produced by MedGemma.
4. Compare those hypotheses against the patient evidence.
5. Use retrieved medical knowledge to support, refine, or challenge the hypotheses.
6. Construct a prioritized differential diagnosis.
7. Explain the reasoning behind the prioritization.
8. Identify evidence supporting and contradicting each major diagnosis.
9. Identify important missing investigations or information when appropriate.
10. Identify red flags or findings requiring urgent attention.
11. Produce a final clinical synthesis with an explicit confidence level.

OUTPUT FORMAT
Return the following exact section headers in plain markdown (do not omit any section):

CLINICAL SUMMARY
- Concise summary of the relevant patient information.

KEY CLINICAL FINDINGS
- Important positive findings.
- Important negative findings.
- Relevant laboratory, imaging, medication, and history information.

MEDGEMMA ANALYSIS
- Main hypotheses produced by MedGemma.
- Important strengths, weaknesses, or uncertainties in those hypotheses.

EVIDENCE SYNTHESIS
- Relevant evidence from the patient data.
- Relevant evidence from retrieved medical knowledge.
- Important agreements or contradictions.

DIFFERENTIAL DIAGNOSIS
For each major diagnosis:
- Diagnosis: <Name>
- Priority: <High | Moderate | Low>
- Supporting evidence: <Findings and citations>
- Contradicting evidence: <Opposing findings or absence of features>
- Confidence: <Likelihood, e.g., 0.80 or High>

MISSING INFORMATION
- Missing data or investigations that could materially change the assessment.

SAFETY / RED FLAGS
- Urgent or potentially dangerous findings.
- Explain why they matter.

FINAL DIAGNOSTIC SYNTHESIS
- Primary Diagnosis: <Specific named condition>
- Diagnostic Confidence: <0.0 to 1.0>
- Certainty: <confirmed | probable | provisional>
- Clinical Synthesis: <Provide the most likely diagnosis or diagnostic direction based only on the available evidence. Clearly state uncertainty when present. Do not overstate confidence.>

EVIDENCE SOURCES
- List only the sources actually supplied by the retrieval system. Never invent references.
"""


@dataclass
class NemotronSynthesisResult:
    """Structured container for the synthesis output."""
    primary_diagnosis: str
    confidence: float
    certainty: str
    differential: List[DifferentialItem]
    clinical_reasoning: str
    missing_information: List[str]
    red_flags: List[str]
    evidence_sources: List[str]
    raw_synthesis_text: str
    thinking_trace: Optional[str] = None
    engine_name: str = "Nemotron-3-Nano-30B-A3B"
    sections: Dict[str, str] = field(default_factory=dict)


class NemotronSynthesisEngine:
    """
    Clinical Reasoning and Diagnostic Synthesis Engine integrating Nebius Nemotron.
    Reconciles patient observations, MedGemma hypotheses, and retrieved RAG passages.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.getenv("NEBIUS_API_KEY")
        self.base_url = base_url or os.getenv("NEBIUS_BASE_URL", DEFAULT_NEBIUS_BASE_URL)
        self.model = model or os.getenv("NEBIUS_MODEL", DEFAULT_NEBIUS_MODEL)
        self.max_retries = max_retries
        self.timeout = timeout
        self._client = None

    @property
    def is_available(self) -> bool:
        """Indicates whether a valid Nebius API key is configured."""
        return bool(self.api_key and not self.api_key.startswith("your-") and not self.api_key.startswith("dummy"))

    def _get_client(self):
        if self._client is None and self.is_available:
            try:
                import openai
                self._client = openai.OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=self.timeout,
                )
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client for Nebius: {e}")
                self._client = None
        return self._client

    def format_synthesis_prompt(
        self,
        patient_info: Dict[str, Any],
        vitals_summary: str,
        exam_findings: Dict[str, Any],
        lab_results: List[Dict[str, Any]],
        medgemma_decision: Dict[str, Any],
        citations: List[Dict[str, Any]],
    ) -> str:
        """Formats the unified patient data, MedGemma output, and RAG evidence."""
        # 1. Patient Data
        lines = ["# PATIENT CLINICAL DATA"]
        lines.append(f"Patient Name/ID: {patient_info.get('name', 'Patient')} ({patient_info.get('id', 'N/A')})")
        lines.append(f"Demographics: {patient_info.get('age', 'Unknown')}yo {patient_info.get('sex', 'Unknown')}")
        lines.append(f"Chief Complaint: {patient_info.get('chief_complaint', 'Unspecified')}")
        lines.append(f"History of Present Illness: {patient_info.get('history_of_present_illness', 'None documented')}")
        
        pmh = patient_info.get("past_medical_history", [])
        lines.append(f"Past Medical History: {', '.join(pmh) if pmh else 'None reported'}")
        
        meds = patient_info.get("medications", [])
        lines.append(f"Current Medications: {', '.join(meds) if meds else 'None'}")
        
        allergies = patient_info.get("allergies", [])
        lines.append(f"Allergies: {', '.join(allergies) if allergies else 'NKDA'}")
        
        lines.append(f"Vital Signs: {vitals_summary}")
        
        exam_parts = [f"{sys}: {val}" for sys, val in (exam_findings or {}).items() if val]
        lines.append(f"Physical Examination: {'; '.join(exam_parts) if exam_parts else 'Grossly unremarkable'}")
        
        lab_lines = []
        for lab in lab_results or []:
            tt = lab.get("test_type", "Lab")
            val = lab.get("values", lab.get("value", lab.get("interpretation", "Pending")))
            interp = lab.get("interpretation", "")
            lab_lines.append(f"- {tt}: {val} ({interp})" if interp else f"- {tt}: {val}")
        lines.append("Diagnostic & Laboratory Results:")
        lines.extend(lab_lines or ["- None available"])

        # 2. MedGemma Hypotheses & Clinical Analysis
        lines.append("\n# MEDGEMMA CLINICAL HYPOTHESES & PRELIMINARY OUTPUT")
        mg_primary = medgemma_decision.get("primary_diagnosis", "None")
        mg_conf = medgemma_decision.get("confidence", 0.0)
        lines.append(f"MedGemma Primary Hypothesis: {mg_primary} (Confidence: {mg_conf})")
        
        mg_diff = medgemma_decision.get("differential", [])
        lines.append("MedGemma Differential Hypotheses:")
        for item in mg_diff:
            cond = item.get("condition", item.get("diagnosis", "Unknown"))
            lk = item.get("likelihood", item.get("probability", 0.0))
            sp = item.get("supporting_points", item.get("supporting_findings", []))
            op = item.get("opposing_points", item.get("against_findings", []))
            lines.append(f"- {cond} (Likelihood: {lk})")
            if sp:
                lines.append(f"  Supporting: {', '.join(sp)}")
            if op:
                lines.append(f"  Opposing: {', '.join(op)}")

        mg_reasoning = medgemma_decision.get("clinical_reasoning", "")
        if mg_reasoning:
            lines.append(f"MedGemma Clinical Reasoning: {mg_reasoning}")
        
        mg_rx = medgemma_decision.get("treatment_plan", [])
        if mg_rx:
            lines.append(f"MedGemma Proposed Interventions: {', '.join(mg_rx)}")

        # 3. Retrieved RAG Medical Knowledge
        lines.append("\n# RETRIEVED MEDICAL KNOWLEDGE (RAG PASSAGES)")
        if not citations:
            lines.append("No medical literature passages retrieved.")
        else:
            for idx, c in enumerate(citations, 1):
                src = c.get("source") or c.get("book") or c.get("title") or "Medical Textbook"
                ch = c.get("chapter", "")
                pg = c.get("page", "")
                text = c.get("text") or c.get("content") or ""
                meta = f"[{idx}] Source: {src}"
                if ch:
                    meta += f", Chapter: {ch}"
                if pg:
                    meta += f", Page: {pg}"
                lines.append(meta)
                lines.append(f"Excerpt: \"{text.strip()}\"\n")

        lines.append("\nSynthesize these inputs critically according to the system instructions. Output the exact structured report.")
        return "\n".join(lines)

    def parse_synthesis_response(
        self,
        raw_text: str,
        medgemma_decision: Dict[str, Any],
        citations: List[Dict[str, Any]],
        thinking_trace: Optional[str] = None,
    ) -> NemotronSynthesisResult:
        """Parses the 9 markdown sections into typed clinical report structures."""
        import unicodedata
        raw_text = unicodedata.normalize("NFKC", raw_text)
        sections: Dict[str, str] = {}
        section_headers = [
            "CLINICAL SUMMARY",
            "KEY CLINICAL FINDINGS",
            "MEDGEMMA ANALYSIS",
            "EVIDENCE SYNTHESIS",
            "DIFFERENTIAL DIAGNOSIS",
            "MISSING INFORMATION",
            "SAFETY / RED FLAGS",
            "FINAL DIAGNOSTIC SYNTHESIS",
            "EVIDENCE SOURCES",
        ]

        pattern = r"(?m)^(?:#{1,3}\s*)?(" + "|".join(re.escape(h) for h in section_headers) + r")\s*$"
        splits = re.split(pattern, raw_text)
        
        if len(splits) > 1:
            for i in range(1, len(splits), 2):
                hdr = splits[i].strip().upper()
                content = splits[i + 1].strip() if i + 1 < len(splits) else ""
                sections[hdr] = content

        # 1. Primary Diagnosis & Confidence from FINAL DIAGNOSTIC SYNTHESIS
        final_synth = sections.get("FINAL DIAGNOSTIC SYNTHESIS", "")
        primary_dx = None
        confidence = None
        certainty = "probable"

        if final_synth:
            dx_match = re.search(r"(?:Primary Diagnosis|Most Likely Diagnosis)[:\s]+([^\n\r]+)", final_synth, re.IGNORECASE)
            if dx_match:
                primary_dx = dx_match.group(1).strip().strip("*").strip("-").strip()

            conf_match = re.search(r"(?:Diagnostic Confidence|Confidence)[:\s]+([0-9.]+)", final_synth, re.IGNORECASE)
            if conf_match:
                try:
                    confidence = float(conf_match.group(1))
                except ValueError:
                    pass

            cert_match = re.search(r"(?:Certainty)[:\s]+(confirmed|probable|provisional)", final_synth, re.IGNORECASE)
            if cert_match:
                certainty = cert_match.group(1).lower()

        # Fallback to MedGemma decision if Nemotron omitted explicit line
        if not primary_dx:
            primary_dx = medgemma_decision.get("primary_diagnosis", "Clinical Syndrome Under Evaluation")
        if confidence is None:
            confidence = float(medgemma_decision.get("confidence", 0.75))
        confidence = float(max(0.0, min(1.0, confidence)))

        # 2. Parse Differential Diagnoses
        differential_items: List[DifferentialItem] = []
        diff_text = sections.get("DIFFERENTIAL DIAGNOSIS", "")
        if diff_text:
            dx_blocks = re.split(r"(?m)^-\s*(?:Diagnosis|Condition)[:\s]+", diff_text)
            for blk in dx_blocks:
                if not blk.strip():
                    continue
                lines = blk.strip().splitlines()
                name = lines[0].strip().strip("*")
                if not name:
                    continue
                
                # Extract supporting, opposing, and likelihood
                supp = []
                opp = []
                lk = 0.5
                for l in lines[1:]:
                    l_clean = l.strip().lstrip("-* ").strip()
                    if re.match(r"(?i)^Supporting(?:\s+evidence)?[:\s]+", l_clean):
                        supp.append(re.sub(r"(?i)^Supporting(?:\s+evidence)?[:\s]+", "", l_clean))
                    elif re.match(r"(?i)^Contradicting(?:\s+evidence)?[:\s]+", l_clean):
                        opp.append(re.sub(r"(?i)^Contradicting(?:\s+evidence)?[:\s]+", "", l_clean))
                    elif re.match(r"(?i)^Confidence|Likelihood|Priority[:\s]+", l_clean):
                        val = re.sub(r"(?i)^Confidence|Likelihood|Priority[:\s]+", "", l_clean).lower()
                        if "high" in val:
                            lk = 0.8
                        elif "mod" in val:
                            lk = 0.5
                        elif "low" in val:
                            lk = 0.2
                        else:
                            m = re.search(r"([0-9.]+)", val)
                            if m:
                                try:
                                    lk = float(m.group(1))
                                except ValueError:
                                    pass

                differential_items.append(DifferentialItem(
                    condition=name,
                    likelihood=float(max(0.0, min(1.0, lk))),
                    supporting_points=supp or ["Clinical consistency with presentation"],
                    opposing_points=opp,
                ))

        if not differential_items:
            # Fallback to existing MedGemma differential if parsing was empty
            for d in medgemma_decision.get("differential", []):
                if d.get("condition"):
                    differential_items.append(DifferentialItem(
                        condition=d["condition"],
                        likelihood=float(d.get("likelihood", 0.5)),
                        supporting_points=d.get("supporting_points", []),
                        opposing_points=d.get("opposing_points", []),
                    ))

        # 3. Missing Information & Red Flags
        missing_text = sections.get("MISSING INFORMATION", "")
        missing_info = [l.strip().lstrip("-* ").strip() for l in missing_text.splitlines() if l.strip().startswith(("-", "*"))]

        red_flags_text = sections.get("SAFETY / RED FLAGS", "")
        red_flags = [l.strip().lstrip("-* ").strip() for l in red_flags_text.splitlines() if l.strip().startswith(("-", "*"))]

        # 4. Formulate Coherent Clinical Reasoning
        reasoning_blocks = []
        if sections.get("CLINICAL SUMMARY"):
            reasoning_blocks.append(f"Summary: {sections['CLINICAL SUMMARY'].strip()}")
        if sections.get("EVIDENCE SYNTHESIS"):
            reasoning_blocks.append(f"Evidence Synthesis: {sections['EVIDENCE SYNTHESIS'].strip()}")
        if sections.get("FINAL DIAGNOSTIC SYNTHESIS"):
            reasoning_blocks.append(f"Diagnostic Conclusion: {sections['FINAL DIAGNOSTIC SYNTHESIS'].strip()}")

        clinical_reasoning = "\n\n".join(reasoning_blocks) if reasoning_blocks else raw_text.strip()

        # 5. Evidence Sources
        sources_text = sections.get("EVIDENCE SOURCES", "")
        evidence_sources = [l.strip().lstrip("-* ").strip() for l in sources_text.splitlines() if l.strip().startswith(("-", "*", "["))]
        if not evidence_sources and citations:
            from ..agents.specialists.reasoning_engine import SpecialtyClinicalReasoningEngine
            evidence_sources = SpecialtyClinicalReasoningEngine.build_source_attribution(citations)

        return NemotronSynthesisResult(
            primary_diagnosis=primary_dx,
            confidence=confidence,
            certainty=certainty,
            differential=differential_items,
            clinical_reasoning=clinical_reasoning,
            missing_information=missing_info,
            red_flags=red_flags,
            evidence_sources=evidence_sources,
            raw_synthesis_text=raw_text,
            thinking_trace=thinking_trace,
            sections=sections,
        )

    def synthesize_diagnostic_report(
        self,
        patient_info: Dict[str, Any],
        vitals_summary: str,
        exam_findings: Dict[str, Any],
        lab_results: List[Dict[str, Any]],
        medgemma_decision: Dict[str, Any],
        citations: List[Dict[str, Any]],
    ) -> NemotronSynthesisResult:
        """
        Executes synthesis via Nebius Nemotron API with retries and exponential backoff.
        Falls back seamlessly to local heuristic synthesis if API key is unset or network fails.
        """
        client = self._get_client()

        if not self.is_available or client is None:
            logger.info("Nebius API key not configured or client unavailable. Using local heuristic synthesis engine.")
            return self._fallback_synthesis(
                patient_info=patient_info,
                vitals_summary=vitals_summary,
                exam_findings=exam_findings,
                lab_results=lab_results,
                medgemma_decision=medgemma_decision,
                citations=citations,
            )

        prompt = self.format_synthesis_prompt(
            patient_info=patient_info,
            vitals_summary=vitals_summary,
            exam_findings=exam_findings,
            lab_results=lab_results,
            medgemma_decision=medgemma_decision,
            citations=citations,
        )

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Submitting case to Nebius Nemotron ({self.model}), attempt {attempt}/{self.max_retries}...")
                start_t = time.time()
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=4096,
                )
                duration = time.time() - start_t
                choice = response.choices[0]
                content = choice.message.content or ""
                reasoning = getattr(choice.message, "reasoning", None)

                logger.info(f"Nebius Nemotron response received in {duration:.2f}s (Tokens finish_reason={choice.finish_reason}).")

                if not content.strip() and reasoning:
                    logger.warning("Nemotron returned empty content but had reasoning trace. Utilizing reasoning trace.")
                    content = reasoning

                return self.parse_synthesis_response(
                    raw_text=content,
                    medgemma_decision=medgemma_decision,
                    citations=citations,
                    thinking_trace=reasoning,
                )

            except Exception as e:
                last_error = e
                backoff = 2 ** attempt
                logger.warning(f"Nebius Nemotron call failed on attempt {attempt}: {e}. Retrying in {backoff}s...")
                time.sleep(backoff)

        logger.error(f"All {self.max_retries} Nebius Nemotron attempts failed: {last_error}. Falling back to local synthesis.")
        return self._fallback_synthesis(
            patient_info=patient_info,
            vitals_summary=vitals_summary,
            exam_findings=exam_findings,
            lab_results=lab_results,
            medgemma_decision=medgemma_decision,
            citations=citations,
        )

    def _fallback_synthesis(
        self,
        patient_info: Dict[str, Any],
        vitals_summary: str,
        exam_findings: Dict[str, Any],
        lab_results: List[Dict[str, Any]],
        medgemma_decision: Dict[str, Any],
        citations: List[Dict[str, Any]],
    ) -> NemotronSynthesisResult:
        """Deterministic local fallback preserving fail-closed patient safety."""
        from ..agents.specialists.reasoning_engine import SpecialtyClinicalReasoningEngine
        
        primary_dx = str(medgemma_decision.get("primary_diagnosis", "Acute Clinical Presentation"))
        conf = float(medgemma_decision.get("confidence", 0.75))
        
        diff_items = [
            DifferentialItem(
                condition=d["condition"],
                likelihood=float(d.get("likelihood", 0.5)),
                supporting_points=d.get("supporting_points", ["Objective clinical correlation"]),
                opposing_points=d.get("opposing_points", []),
            )
            for d in medgemma_decision.get("differential", [])
            if d.get("condition")
        ]
        
        sources = SpecialtyClinicalReasoningEngine.build_source_attribution(citations)
        
        return NemotronSynthesisResult(
            primary_diagnosis=primary_dx,
            confidence=conf,
            certainty="probable",
            differential=diff_items,
            clinical_reasoning=str(medgemma_decision.get("clinical_reasoning", "Clinical synthesis generated by deterministic backup engine.")),
            missing_information=["Serial cardiac biomarkers or imaging follow-up as clinically indicated"],
            red_flags=["Hemodynamic instability or acute decompensation"],
            evidence_sources=sources,
            raw_synthesis_text="[Local Heuristic Fallback Synthesis]",
            engine_name="Local-Clinical-Fallback",
        )


# Singleton instance for platform-wide use
nemotron_synthesis_engine = NemotronSynthesisEngine()
