"""
Phase 3 automated validation layer (prompt FOR UPDATE/03_Phase3).

The validator, not the model, decides whether a report is VALID. Checks V1-V12
run on every report via run_grounded_assessment; any failure regenerates with
the error list fed back (max 2 retries), else status FAILED with all validation
results stored and the raw outputs logged to the failed-generations list.

Owner: AI Engineer. Clinical content (vague labels, completeness rules) is
Medical-Expert-owned config under configs/validation/.
"""

import difflib
import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from vh.generation.v2_report import AssessmentReport

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VALIDATION_DIR = REPO_ROOT / "configs" / "validation"
FAILED_LOG_PATH = REPO_ROOT / "data" / "failed_generations.jsonl"

VALID = "VALID"
INSUFFICIENT_GROUNDING = "INSUFFICIENT_GROUNDING"
FAILED = "FAILED"

RETRY_MESSAGE = (
    "Rewrite as patient-specific clinical synthesis in your own words; "
    "keep verbatim text only in supporting_quote."
)

# ICD chapters excluded from V4 (symptoms/signs and factors, not diseases).
V4_EXCLUDED_CHAPTERS = ("R", "Z")
V4_SKIP_TERMS = {
    "unspecified", "other", "other specified", "not elsewhere classified",
    "in diseases classified elsewhere", "unsp", "nos",
}


class CheckResult(BaseModel):
    """Outcome of a single V-check."""

    check_id: str
    passed: bool
    message: str = ""


class ValidationReport(BaseModel):
    """Full V1-V12 outcome stored on every validated report."""

    report_id: str
    passed: bool
    checks: List[CheckResult] = Field(default_factory=list)
    verified_harrison_items: int = 0
    total_evidence_items: int = 0
    harrison_fraction: float = 0.0
    validated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def failures(self) -> List[CheckResult]:
        """Failing checks only (retry feedback input)."""
        return [c for c in self.checks if not c.passed]


# --- Config loaders -----------------------------------------------------------

def _read_yaml(path: Path) -> Dict[str, Any]:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_phase3_thresholds() -> Dict[str, Any]:
    """Agent-owned tunables (threshold promotions to thresholds.yaml need the owner)."""
    defaults = {
        "grounding_fraction_min": 0.6, "harrison_fraction_min": 0.6,
        "quote_fuzzy_min": 0.9, "verbatim_span_words": 12, "rouge_l_max": 0.4,
        "min_case_findings": 3, "repetition_sentence_max": 2,
        "repetition_ngram_n": 8, "repetition_ngram_max": 2,
        "max_regeneration_retries": 2,
    }
    path = VALIDATION_DIR / "phase3.yaml"
    if path.exists():
        defaults.update(_read_yaml(path))
    return defaults


@lru_cache(maxsize=1)
def load_icd_titles() -> Dict[str, str]:
    """Official CMS ICD-10-CM FY2027 titles (never model-generated)."""
    path = VALIDATION_DIR / "icd10_cm_titles_FY2027.json"
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return {str(k).upper(): str(v) for k, v in payload["titles"].items()}


@lru_cache(maxsize=1)
def load_vague_labels() -> List[str]:
    """Vague final-diagnosis labels (draft pending physician review)."""
    data = _read_yaml(VALIDATION_DIR / "vague_diagnoses.yaml")
    return [str(t).lower() for t in (data.get("vague_labels") or [])]


@lru_cache(maxsize=1)
def load_completeness_rules() -> List[Dict[str, Any]]:
    """V10 completeness rules (approved enforce; drafts audit-only)."""
    data = _read_yaml(VALIDATION_DIR / "completeness_rules.yaml")
    return list(data.get("rules") or [])


# --- Text utilities ------------------------------------------------------------

def normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    cleaned = re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def word_windows(text: str, n: int) -> List[str]:
    """Normalized n-word windows for verbatim-span detection."""
    words = normalize(text).split()
    if len(words) < n:
        return []
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def split_sentences(text: str) -> List[str]:
    """Split prose into normalized non-trivial sentences."""
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    return [normalize(p) for p in parts if len(normalize(p)) > 10]


def fuzzy_contains(quote: str, chunk_text: str, minimum: float = 0.9) -> Tuple[bool, float]:
    """
    Verbatim-or-fuzzy quote check: normalized substring wins immediately,
    else best sliding-window SequenceMatcher ratio must reach `minimum`.
    """
    nq, nc = normalize(quote), normalize(chunk_text)
    if not nq:
        return False, 0.0
    if nq in nc:
        return True, 1.0
    q_words = nq.split()
    c_words = nc.split()
    width = max(1, len(q_words))
    best = 0.0
    for i in range(max(1, len(c_words) - width + 1)):
        window = " ".join(c_words[i : i + width])
        best = max(best, difflib.SequenceMatcher(None, nq, window).ratio())
        if best >= minimum:
            return True, best
    return best >= minimum, best


def rouge_l_f1(candidate: str, reference: str) -> float:
    """ROUGE-L F1 over word tokens (dependency-free LCS implementation)."""
    cand, ref = normalize(candidate).split(), normalize(reference).split()
    if not cand or not ref:
        return 0.0
    prev = [0] * (len(ref) + 1)
    for i in range(1, len(cand) + 1):
        curr = [0] * (len(ref) + 1)
        for j in range(1, len(ref) + 1):
            if cand[i - 1] == ref[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = prev[j] if prev[j] >= curr[j - 1] else curr[j - 1]
        prev = curr
    lcs = prev[len(ref)]
    if lcs == 0:
        return 0.0
    precision = lcs / len(cand)
    recall = lcs / len(ref)
    return 2 * precision * recall / (precision + recall)


def prose_fields(report: AssessmentReport) -> Dict[str, str]:
    """Fields that must be clinical synthesis, never copied text (V2/V12 scope)."""
    fields = {
        "case_summary": report.case_summary,
        "clinical_reasoning": report.clinical_reasoning,
        "follow_up": report.follow_up,
    }
    for i, item in enumerate(report.workup):
        fields[f"workup[{i}].rationale"] = item.rationale
    for i, item in enumerate(report.treatment):
        fields[f"treatment[{i}].rationale"] = item.rationale
    fields["disposition.rationale"] = report.disposition.rationale
    return fields


# --- Shared evidence helpers ----------------------------------------------------

class _Ctx:
    """Validator context: retrieval chunks + structured case + thresholds."""

    def __init__(self, retrieval_log: Any, structured_case: Dict[str, Any]):
        chunks = {}
        raw_chunks = getattr(retrieval_log, "chunks", None)
        if isinstance(retrieval_log, dict):
            raw_chunks = retrieval_log.get("chunks", {})
        for cid, stored in (raw_chunks or {}).items():
            if isinstance(stored, dict):
                chunks[str(cid)] = {
                    "metadata": dict(stored.get("metadata", {}) or {}),
                    "text": str(stored.get("text", "") or ""),
                }
            else:
                chunks[str(cid)] = {
                    "metadata": dict(getattr(stored, "metadata", {}) or {}),
                    "text": str(getattr(stored, "text", "") or ""),
                }
        self.chunks = chunks
        self.structured = structured_case or {}
        self.thresholds = load_phase3_thresholds()

    def all_evidence(self, report: AssessmentReport) -> List[Any]:
        """Every evidence object across the report."""
        items: List[Any] = []
        sections = (
            [report.final_diagnosis, report.disposition]
            + list(report.differential_diagnosis)
            + list(report.severity_assessment)
            + list(report.workup)
            + list(report.treatment)
        )
        for section in sections:
            items.extend(list(section.evidence))
        return items


def _quote_verified(evidence: Any, ctx: _Ctx) -> Tuple[bool, str]:
    """V6+V7 combined: cited id exists in THIS report's log and quote verifies."""
    valid_sources = ("harrison", "braunwald", "nabd_rxnorm", "dailymed", "openfda", "pubmed")
    if evidence.source not in valid_sources:
        return False, f"unsupported evidence source '{evidence.source}'"
    cid = evidence.chunk_id or ""
    stored = ctx.chunks.get(cid)
    if not stored:
        return False, f"hallucinated chunk_id '{cid}' not in this report's retrieval_log"
    quote = evidence.supporting_quote or ""
    if not quote.strip():
        # Shared pharmacology sources (NABD/RxNorm) provide structured monograph/fact data
        if evidence.source in ("nabd_rxnorm", "dailymed", "openfda", "pubmed"):
            return True, "verified"
        return False, f"chunk '{cid}' cited with null/empty quote (unverifiable)"
    ok, ratio = fuzzy_contains(quote, stored["text"], ctx.thresholds["quote_fuzzy_min"])
    if not ok:
        return False, f"quote for '{cid}' not found in chunk text (best fuzzy {ratio:.2f} < 0.9)"
    return True, "verified"


def _diagnosis_terms() -> List[str]:
    """V4 term list from official ICD titles (R/Z symptom chapters excluded)."""
    terms: List[str] = []
    for code, title in load_icd_titles().items():
        if code[:1] in V4_EXCLUDED_CHAPTERS:
            continue
        candidates = [title] + [p.strip() for p in str(title).split(",")]
        for term in candidates:
            cleaned = normalize(term)
            if len(cleaned) >= 4 and cleaned not in V4_SKIP_TERMS:
                terms.append(cleaned)
    return sorted(set(terms))


# --- V-checks ---------------------------------------------------------------------

def check_v1(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V1: output parses and matches the schema (pydantic-validated upstream)."""
    try:
        AssessmentReport.model_validate(report.model_dump())
    except Exception as exc:
        return CheckResult(check_id="V1", passed=False, message=f"schema invalid: {exc}")
    if not report.differential_diagnosis or not report.final_diagnosis:
        return CheckResult(check_id="V1", passed=False, message="missing differential or final diagnosis")
    return CheckResult(check_id="V1", passed=True, message="schema valid")


def check_v2(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V2: no box_2d/coordinates/fences/embedded raw JSON inside prose fields."""
    from vh.generation.medgemma import contains_forbidden_grounding

    for name, text in prose_fields(report).items():
        if contains_forbidden_grounding(text or ""):
            return CheckResult(check_id="V2", passed=False, message=f"{name} carries grounding/fence artefacts")
        stripped = (text or "").strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
            except Exception:
                parsed = None
            if isinstance(parsed, (dict, list)):
                return CheckResult(check_id="V2", passed=False, message=f"{name} contains embedded raw JSON")
    return CheckResult(check_id="V2", passed=True, message="prose fields clean")


def check_v3(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V3: repetition — any sentence/line >=3x or high n-gram repetition fails."""
    text = "\n".join(prose_fields(report).values())
    sentences = split_sentences(text)
    if sentences:
        top = max(__import__("collections").Counter(sentences).values())
        if top >= 3:
            return CheckResult(check_id="V3", passed=False, message=f"sentence repeated {top}x")
    words = normalize(text).split()
    n = int(ctx.thresholds["repetition_ngram_n"])
    limit = int(ctx.thresholds["repetition_ngram_max"])
    if len(words) >= n:
        grams = [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
        top = max(__import__("collections").Counter(grams).values())
        if top > limit:
            return CheckResult(check_id="V3", passed=False, message=f"{n}-gram repeated {top}x (limit {limit})")
    return CheckResult(check_id="V3", passed=True, message="no degenerate repetition")


def check_v4(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V4: chief_complaint must not contain a diagnosis term (official ICD titles, R/Z excluded)."""
    complaint = normalize(report.chief_complaint)
    for term in _diagnosis_terms():
        if re.search(rf"\b{re.escape(term)}\b", complaint):
            return CheckResult(check_id="V4", passed=False, message=f"chief_complaint matches diagnosis term '{term}'")
    return CheckResult(check_id="V4", passed=True, message="chief complaint is symptoms-only")


def check_v5(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V5: vague final diagnosis allowed only with provisional certainty + missing_data."""
    final = normalize(report.final_diagnosis.diagnosis)
    if any(vague in final for vague in load_vague_labels()):
        if report.final_diagnosis.certainty == "provisional" and report.missing_data:
            return CheckResult(check_id="V5", passed=True, message="vague label with provisional certainty + missing_data")
        return CheckResult(check_id="V5", passed=False, message=f"vague final diagnosis '{report.final_diagnosis.diagnosis}'")
    return CheckResult(check_id="V5", passed=True, message="final diagnosis specific")


def check_v6(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V6: every cited medical book or shared source chunk_id exists in this report's retrieval_log."""
    valid_sources = {"harrison", "braunwald", "nabd_rxnorm", "dailymed", "openfda", "pubmed"}
    for ev in ctx.all_evidence(report):
        if ev.source in valid_sources and (ev.chunk_id or "") not in ctx.chunks:
            return CheckResult(check_id="V6", passed=False, message=f"hallucinated chunk_id '{ev.chunk_id}'")
        if ev.source == "model_knowledge" and ev.chunk_id:
            return CheckResult(check_id="V6", passed=False, message="model_knowledge evidence must not carry a chunk_id")
    return CheckResult(check_id="V6", passed=True, message="all chunk_ids resolve to retrieval_log")


def check_v7(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V7: every supporting_quote is found in the cited chunk text (fuzzy >= 0.9)."""
    textbook_sources = {"harrison", "braunwald"}
    for ev in ctx.all_evidence(report):
        if ev.source not in textbook_sources:
            continue
        ok, message = _quote_verified(ev, ctx)
        # _quote_verified also checks membership; here only the quote matters.
        stored = ctx.chunks.get(ev.chunk_id or "")
        if stored is None:
            continue  # V6 owns hallucinated ids
        quote = ev.supporting_quote or ""
        verified, ratio = fuzzy_contains(quote, stored["text"], ctx.thresholds["quote_fuzzy_min"]) if quote.strip() else (False, 0.0)
        if not verified:
            return CheckResult(check_id="V7", passed=False, message=f"unverifiable quote for '{ev.chunk_id}' ({message})")
    return CheckResult(check_id="V7", passed=True, message="all quotes verified")


def check_v8(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V8: grounding minimums recomputed in code (final >=1 verified source; treatments covered; fraction >= 0.6)."""
    evidence = ctx.all_evidence(report)
    if not evidence:
        return CheckResult(check_id="V8", passed=False, message="report carries no evidence items")
    verified_ids = set()
    for ev in evidence:
        ok, _ = _quote_verified(ev, ctx)
        if ok and ev.chunk_id:
            verified_ids.add(ev.chunk_id)
    grounded_sources = {"harrison", "braunwald", "nabd_rxnorm", "dailymed", "openfda", "pubmed"}
    final_verified = sum(
        1 for ev in report.final_diagnosis.evidence
        if ev.source in grounded_sources and ev.chunk_id in verified_ids
    )
    if final_verified < 1:
        return CheckResult(check_id="V8", passed=False, message="final_diagnosis has no verified medical book or shared knowledge evidence")
    for item in report.treatment:
        item_evs = list(item.evidence)
        if not item_evs:
            return CheckResult(check_id="V8", passed=False, message=f"treatment '{item.item}' has no evidence")
        covered = any(ev.source in grounded_sources and ev.chunk_id in verified_ids for ev in item_evs)
        explicit_mg = all(ev.source == "model_knowledge" for ev in item_evs)
        if not (covered or explicit_mg):
            return CheckResult(check_id="V8", passed=False, message=f"treatment '{item.item}' lacks verified grounded evidence and is not explicit model_knowledge")
    grounded_verified = sum(1 for ev in evidence if ev.source in grounded_sources and ev.chunk_id in verified_ids)
    fraction = grounded_verified / len(evidence)
    min_fraction = float(ctx.thresholds.get("grounding_fraction_min", ctx.thresholds.get("harrison_fraction_min", 0.6)))
    if fraction < min_fraction:
        return CheckResult(check_id="V8", passed=False, message=f"Grounded fraction {fraction:.2f} < {min_fraction}")
    return CheckResult(check_id="V8", passed=True, message=f"grounding ok (fraction {fraction:.2f})")


def check_v9(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V9: probabilities in [0,1] sum <= 1; final is top differential or reasoning explains why not."""
    probs = [d.probability for d in report.differential_diagnosis]
    if any(p < 0.0 or p > 1.0 for p in probs):
        return CheckResult(check_id="V9", passed=False, message="probability outside [0,1]")
    if sum(probs) > 1.0 + 1e-6:
        return CheckResult(check_id="V9", passed=False, message=f"probabilities sum to {sum(probs):.3f} (> 1)")
    top = max(report.differential_diagnosis, key=lambda d: d.probability)
    if top.diagnosis.strip().casefold() == report.final_diagnosis.diagnosis.strip().casefold():
        return CheckResult(check_id="V9", passed=True, message="final diagnosis is the top differential")
    if top.diagnosis.strip().casefold() in normalize(report.clinical_reasoning):
        return CheckResult(check_id="V9", passed=True, message="reasoning explains non-top final diagnosis")
    return CheckResult(check_id="V9", passed=False, message="final diagnosis is not the top differential and reasoning does not explain why")


def check_v10(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V10: diagnosis-specific completeness (approved rules fail; drafts audit-only)."""
    final = normalize(report.final_diagnosis.diagnosis)
    messages: List[str] = []
    for rule in load_completeness_rules():
        terms = [normalize(t) for t in (rule.get("match_terms") or [])]
        if not terms or not any(t and t in final for t in terms):
            continue
        problems = _rule_problems(rule, report, ctx)
        tag = "audit" if rule.get("status") != "approved" else "enforced"
        if problems and rule.get("status") == "approved":
            return CheckResult(check_id="V10", passed=False,
                               message=f"completeness [{rule.get('key')}]: " + "; ".join(problems))
        messages.append(f"[{tag} {rule.get('key')}] " + ("; ".join(problems) if problems else "complete"))
    if not messages:
        return CheckResult(check_id="V10", passed=True, message="no completeness rule matched")
    return CheckResult(check_id="V10", passed=True, message=" | ".join(messages))


def _rule_problems(rule: Dict[str, Any], report: AssessmentReport, ctx: _Ctx) -> List[str]:
    """Evaluate one completeness rule; return unmet requirement descriptions."""
    problems: List[str] = []
    workup_text = " | ".join(w.test for w in report.workup).lower()
    treatment_text = " | ".join(f"{t.item} {t.dose_route_frequency_duration} {t.rationale}" for t in report.treatment).lower()

    sev_terms = [s.lower() for s in (rule.get("require_severity_any") or [])]
    if sev_terms:
        names = " ".join(s.score_name for s in report.severity_assessment).lower()
        if not any(t in names for t in sev_terms):
            problems.append(f"missing severity score {sev_terms}")
        else:
            for s in report.severity_assessment:
                if any(t in s.score_name.lower() for t in sev_terms) and not s.components:
                    problems.append(f"severity {s.score_name} lacks components")

    for group in (rule.get("require_workup_any_terms") or []):
        terms = [t.lower() for t in group]
        if not any(t in workup_text for t in terms):
            problems.append(f"workup missing one of {terms}")

    single_workup = [t.lower() for t in (rule.get("require_workup_any") or [])]
    if single_workup and not any(t in workup_text for t in single_workup):
        problems.append(f"workup missing one of {single_workup}")

    for group in (rule.get("require_treatment_terms_any_groups") or []):
        terms = [t.lower() for t in group]
        if not any(t in treatment_text for t in terms):
            problems.append(f"treatment missing one of {terms}")

    single_tx = [t.lower() for t in (rule.get("require_treatment_terms_any") or [])]
    if single_tx and not any(t in treatment_text for t in single_tx):
        problems.append(f"treatment missing one of {single_tx}")

    spo2_limit = rule.get("require_oxygen_target_when_spo2_below")
    if spo2_limit is not None:
        spo2 = (ctx.structured.get("vitals", {}) or {}).get("spo2")
        try:
            low = spo2 is not None and float(spo2) < float(spo2_limit)
        except (TypeError, ValueError):
            low = False
        if low and not any(t in treatment_text for t in ("oxygen", "o2 target", "nasal cannula", "spo2")):
            problems.append("hypoxaemia without oxygen target in treatment")

    if rule.get("require_disposition"):
        if not report.disposition.setting or not report.disposition.rationale.strip():
            problems.append("disposition incomplete")
    return problems


def check_v11(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V11: confidence consistent with certainty (schema-enforced; rechecked here)."""
    from vh.generation.v2_report import CONFIDENCE_BANDS

    low, high = CONFIDENCE_BANDS[report.final_diagnosis.certainty]
    conf = report.final_diagnosis.confidence
    if report.final_diagnosis.certainty == "provisional" and conf > high + 1e-6:
        return CheckResult(check_id="V11", passed=False, message=f"provisional with confidence {conf}")
    if report.final_diagnosis.certainty == "confirmed" and conf <= high - 1e-6:
        return CheckResult(check_id="V11", passed=False, message=f"confirmed with confidence {conf}")
    if report.final_diagnosis.certainty == "probable" and not (low - 1e-6 <= conf <= high + 1e-6):
        return CheckResult(check_id="V11", passed=False, message=f"probable with confidence {conf}")
    return CheckResult(check_id="V11", passed=True, message="confidence matches certainty")


_CASE_FINDING_STOPWORDS = {
    "with", "without", "from", "this", "that", "have", "days", "room", "right",
    "left", "increased", "decreased", "mild", "severe", "acute", "chronic",
}


def _finding_hit(finding: str, lowered_reasoning: str) -> bool:
    """A finding counts when its phrase or any distinctive content word appears."""
    normed = normalize(finding)
    if not normed:
        return False
    if normed in lowered_reasoning:
        return True
    for word in normed.split():
        if word in _CASE_FINDING_STOPWORDS:
            continue
        if len(word) >= 5 or (word.isupper() and len(word) >= 2) or word.replace(".", "").isdigit():
            if re.search(rf"\b{re.escape(word)}\b", lowered_reasoning):
                return True
    return False


def _case_findings(structured: Dict[str, Any]) -> List[str]:
    """Case-specific finding phrases from the structured case."""
    findings: List[str] = []
    for symptom in structured.get("presenting_symptoms", []) or []:
        if str(symptom).strip():
            findings.append(str(symptom).strip())
    vitals = structured.get("vitals", {}) or {}
    for key, value in vitals.items():
        if value not in (None, ""):
            findings.append(f"{key} {value}")
    exam = str(structured.get("examination_findings") or "")
    for word in re.findall(r"[a-z]+", exam.lower()):
        if len(word) >= 5 and word not in _CASE_FINDING_STOPWORDS:
            findings.append(word)
    for section in ("labs", "imaging"):
        items = structured.get(section, {}) or {}
        if isinstance(items, dict):
            for key in items:
                findings.append(str(key))
    # Deduplicate preserving order.
    seen, unique = set(), []
    for finding in findings:
        key = finding.lower()
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


def check_v12(report: AssessmentReport, ctx: _Ctx) -> CheckResult:
    """V12: copy detection — no >=12-word verbatim span, ROUGE-L <= 0.4, >=3 case findings."""
    n_span = int(ctx.thresholds["verbatim_span_words"])
    prose = prose_fields(report)
    chunk_texts = [stored["text"] for stored in ctx.chunks.values() if stored.get("text")]
    if chunk_texts:
        chunk_windows = set()
        for chunk_text in chunk_texts:
            chunk_windows.update(word_windows(chunk_text, n_span))
        for name, text in prose.items():
            for window in word_windows(text or "", n_span):
                if window in chunk_windows:
                    return CheckResult(check_id="V12", passed=False, message=f"{name} copies a {n_span}-word span verbatim")
    reasoning = report.clinical_reasoning or ""
    corpus = " ".join(chunk_texts)
    if corpus.strip() and reasoning.strip():
        score = max((rouge_l_f1(reasoning, chunk) for chunk in chunk_texts if chunk.strip()), default=0.0)
        if score > float(ctx.thresholds["rouge_l_max"]):
            return CheckResult(check_id="V12", passed=False, message=f"ROUGE-L {score:.2f} exceeds 0.4 (copied text)")
    findings = _case_findings(ctx.structured)
    required = min(int(ctx.thresholds["min_case_findings"]), len(findings))
    if required > 0:
        lowered = normalize(reasoning)
        hits = sum(1 for f in findings if _finding_hit(f, lowered))
        if hits < required:
            return CheckResult(check_id="V12", passed=False,
                               message=f"reasoning references {hits}/{required} case findings (synthesis, not transcription)")
    return CheckResult(check_id="V12", passed=True, message="patient-specific synthesis")


_CHECKS = (check_v1, check_v2, check_v3, check_v4, check_v5, check_v6,
           check_v7, check_v8, check_v9, check_v10, check_v11, check_v12)


def validate_assessment_report(
    report: AssessmentReport,
    retrieval_log: Any,
    structured_case: Optional[Dict[str, Any]] = None,
) -> ValidationReport:
    """Run V1-V12 over one assessment; grounding numbers recomputed in code."""
    ctx = _Ctx(retrieval_log, structured_case or {})
    results = [check(report, ctx) for check in _CHECKS]
    evidence = ctx.all_evidence(report)
    verified = 0
    for ev in evidence:
        ok, _ = _quote_verified(ev, ctx)
        if ok and ev.chunk_id:
            verified += 1
    fraction = (verified / len(evidence)) if evidence else 0.0
    return ValidationReport(
        report_id=report.report_id,
        passed=all(c.passed for c in results),
        checks=results,
        verified_harrison_items=verified,
        total_evidence_items=len(evidence),
        harrison_fraction=fraction,
    )


def build_retry_feedback(validation: ValidationReport) -> str:
    """Error list for regeneration feedback (Phase 3 failure handling)."""
    lines = [f"{c.check_id}: {c.message}" for c in validation.failures()]
    lines.append(RETRY_MESSAGE)
    return "\n".join(lines)


def append_failed_generation(
    report_id: str,
    case_id: str,
    assessment: Optional[Dict[str, Any]],
    validation: ValidationReport,
    raw_attempts: List[str],
) -> str:
    """Append to the failed-generations list (Phase 4 renders this separately)."""
    FAILED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "report_id": report_id,
        "case_id": case_id,
        "status": FAILED,
        "validated_at": validation.validated_at,
        "checks": [{"check_id": c.check_id, "passed": c.passed, "message": c.message} for c in validation.checks],
        "assessment": assessment,
        "raw_attempts": raw_attempts,
    }
    with open(FAILED_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return str(FAILED_LOG_PATH)
