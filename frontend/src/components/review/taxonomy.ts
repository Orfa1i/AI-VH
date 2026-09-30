/** Reviewer-facing picklists. Validation stays server-side (taxonomy.yaml). */

export const CLAIM_RATINGS = ['correct', 'partially_correct', 'incorrect'] as const;

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
