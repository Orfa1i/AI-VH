import type { ReviewAssessment, ReviewErrorTaxonomy } from '../../types';

export const CLAIM_RATINGS = ['correct', 'partially_correct', 'incorrect'] as const;

export const REVIEW_ASSESSMENTS: Array<{ value: ReviewAssessment; label: string; color: string }> = [
  { value: 'CORRECT', label: 'Correct', color: 'emerald' },
  { value: 'PARTIALLY_CORRECT', label: 'Partially Correct', color: 'amber' },
  { value: 'INCORRECT', label: 'Incorrect', color: 'rose' },
];

export const STRUCTURED_ERROR_TAXONOMY: Array<{ code: ReviewErrorTaxonomy; label: string; description: string }> = [
  { code: 'MISSING_INFORMATION', label: 'Missing Information', description: 'Omitted vital clinical data or diagnostic considerations' },
  { code: 'HALLUCINATION', label: 'Hallucination', description: 'Fabricated vitals, biomarkers, tests, or clinical history' },
  { code: 'INCORRECT_DIAGNOSIS', label: 'Incorrect Diagnosis', description: 'Primary or key differential diagnosis is clinically wrong' },
  { code: 'INCORRECT_REASONING', label: 'Incorrect Reasoning', description: 'Flawed logic, internal contradiction, or invalid progression' },
  { code: 'UNSUPPORTED_RECOMMENDATION', label: 'Unsupported Recommendation', description: 'Contraindicated, inappropriate, or harmful next steps' },
  { code: 'INCORRECT_MEDICAL_FACT', label: 'Incorrect Medical Fact', description: 'Contradicts established medical science or pathophysiology' },
  { code: 'POOR_EVIDENCE_USE', label: 'Poor Evidence Use', description: 'Misapplied citations, absent grounding, or text copying' },
  { code: 'OTHER', label: 'Other', description: 'Stylistic, minor formatting, or other uncategorized issue' },
];

export const TAXONOMY_CODES: Array<{ code: string; label: string }> = [
  { code: 'wrong_diagnosis', label: 'Wrong diagnosis' },
  { code: 'missed_diagnosis', label: 'Missed diagnosis' },
  { code: 'missed_red_flag', label: 'Missed red flag' },
  { code: 'bad_citation', label: 'Bad citation' },
  { code: 'unsupported_claim', label: 'Unsupported claim' },
  { code: 'unsafe_recommendation', label: 'Unsafe recommendation' },
  { code: 'dosing_error', label: 'Dosing error' },
  { code: 'formatting', label: 'Formatting' },
  { code: 'other', label: 'Other' },
];
