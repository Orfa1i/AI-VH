import React, { useEffect, useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { Decision, EditOp, ReportDetail, SessionDetail } from './api';
import { CLAIM_RATINGS, TAXONOMY_CODES } from './taxonomy';

export type DecideHandler = (
  decision: Decision,
  edits?: EditOp[],
) => Promise<{ final_report: unknown; decision: Decision } | void> | { final_report: unknown; decision: Decision } | void;

interface ReportViewProps {
  detail: ReportDetail;
  session: SessionDetail | null;
  onRateClaim: (claimId: string, rating: string, taxonomyCode: string) => void | Promise<void>;
  onAddComment: (text: string) => void | Promise<void>;
  onDecide: DecideHandler;
}

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName.toLowerCase();
  return tag === 'input' || tag === 'textarea' || tag === 'select' || target.isContentEditable;
}

export const ReportView: React.FC<ReportViewProps> = ({
  detail,
  session,
  onRateClaim,
  onAddComment,
  onDecide,
}) => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [ratings, setRatings] = useState<Record<string, { rating: string; code: string }>>({});
  const [rated, setRated] = useState<Record<string, boolean>>({});
  const [comment, setComment] = useState('');
  const [correcting, setCorrecting] = useState(false);
  const [editedSummary, setEditedSummary] = useState(detail.report.patient_summary ?? '');

  useEffect(() => {
    setEditedSummary(detail.report.patient_summary ?? '');
    setCorrecting(false);
    setRated({});
  }, [detail.original_id, detail.report.patient_summary]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (isTypingTarget(event.target) || event.metaKey || event.ctrlKey || event.altKey) return;
      const key = event.key.toLowerCase();
      if (key === 'a') void onDecide('approve', []);
      else if (key === 'r') void onDecide('reject', []);
      else if (key === 'c') setCorrecting(true);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onDecide]);

  const claims = detail.claims ?? [];
  const verificationEntries = Object.entries(detail.verification ?? {});

  const submitCorrection = () => {
    const edits: EditOp[] = [];
    if (editedSummary !== (detail.report.patient_summary ?? '')) {
      edits.push({ op: 'replace', path: ['patient_summary'], value: editedSummary });
    }
    void onDecide('correct', edits);
  };

  return (
    <div className="bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-md overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--ak-color-border-subtle)] flex items-center gap-2">
        <h2 className="text-xs font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)]">
          {detail.case_id}
        </h2>
        {detail.flagged && (
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--ak-color-warning-soft)] text-[var(--ak-color-danger)] border border-[var(--ak-color-border-subtle)]">
            FLAGGED
          </span>
        )}
      </div>

      {detail.flagged && (
        <div role="alert" className="px-4 py-3 bg-[var(--ak-color-warning-soft)] border-b border-[var(--ak-color-border-subtle)]">
          <p className="text-xs font-mono font-bold text-[var(--ak-color-danger)] uppercase">Verification flagged</p>
          <ul className="mt-1 space-y-0.5">
            {verificationEntries.map(([key, value]) => (
              <li key={key} className="text-xs font-sans text-[var(--ak-color-danger)]">
                {key}: {String(value)}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="px-4 py-3 space-y-4">
        <section>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)] mb-1">
            Patient summary
          </h3>
          <p className="text-xs text-[var(--ak-color-text-secondary)] font-sans">{detail.report.patient_summary}</p>
        </section>

        {(detail.report.differential ?? []).length > 0 && (
          <section>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)] mb-1">
              Differential
            </h3>
            <ul className="space-y-1">
              {(detail.report.differential ?? []).map((entry, index) => (
                <li key={index} className="text-xs text-[var(--ak-color-text-secondary)] font-sans">
                  {entry.dx}
                  {entry.likelihood ? ` (${entry.likelihood})` : ''}
                </li>
              ))}
            </ul>
          </section>
        )}

        <section>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)] mb-1">
            Claims &amp; evidence
          </h3>
          <ul className="space-y-2">
            {claims.map((claim, index) => {
              const claimId = String(claim.claim_id ?? `claim-${index}`);
              const open = expanded[claimId] ?? false;
              const draft = ratings[claimId] ?? { rating: '', code: '' };
              return (
                <li key={claimId} className="border border-[var(--ak-color-border-subtle)] rounded-md">
                  <button
                    type="button"
                    aria-expanded={open ? 'true' : 'false'}
                    onClick={() => setExpanded((prev) => ({ ...prev, [claimId]: !open }))}
                    className="w-full px-3 py-2 flex items-center gap-2 text-left cursor-pointer hover:bg-[var(--ak-color-bg-subtle)]"
                  >
                    {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    <span className="text-xs font-mono font-semibold text-[var(--ak-color-text-primary)]">{claimId}</span>
                  </button>
                  {open && (
                    <div className="px-3 pb-3 space-y-2">
                      <p className="text-xs text-[var(--ak-color-text-secondary)] font-sans">{claim.text}</p>
                      {Array.isArray(claim.evidence_ids) && claim.evidence_ids.length > 0 && (
                        <p className="text-[11px] font-mono text-[var(--ak-color-text-muted)]">
                          Evidence: {claim.evidence_ids.join(', ')}
                        </p>
                      )}
                      {typeof claim.source === 'string' && claim.source !== '' && (
                        <p className="text-[11px] font-mono text-[var(--ak-color-text-muted)]">Source: {claim.source}</p>
                      )}
                      <div className="flex flex-wrap items-center gap-2">
                        <label htmlFor={`rating-${claimId}`} className="text-[11px] font-mono text-[var(--ak-color-text-muted)]">
                          Rating for {claimId}
                        </label>
                        <select
                          id={`rating-${claimId}`}
                          value={draft.rating}
                          onChange={(event) =>
                            setRatings((prev) => ({
                              ...prev,
                              [claimId]: { rating: event.target.value, code: prev[claimId]?.code ?? '' },
                            }))
                          }
                          className="text-xs border border-[var(--ak-color-border-subtle)] rounded-md px-2 py-1 bg-white text-[var(--ak-color-text-primary)]"
                        >
                          <option value="">Select</option>
                          {CLAIM_RATINGS.map((rating) => (
                            <option key={rating} value={rating}>
                              {rating}
                            </option>
                          ))}
                        </select>
                        <label htmlFor={`taxonomy-${claimId}`} className="text-[11px] font-mono text-[var(--ak-color-text-muted)]">
                          Taxonomy for {claimId}
                        </label>
                        <select
                          id={`taxonomy-${claimId}`}
                          value={draft.code}
                          onChange={(event) =>
                            setRatings((prev) => ({
                              ...prev,
                              [claimId]: { rating: prev[claimId]?.rating ?? '', code: event.target.value },
                            }))
                          }
                          className="text-xs border border-[var(--ak-color-border-subtle)] rounded-md px-2 py-1 bg-white text-[var(--ak-color-text-primary)]"
                        >
                          <option value="">Select</option>
                          {TAXONOMY_CODES.map((entry) => (
                            <option key={entry.code} value={entry.code}>
                              {entry.label}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          disabled={draft.rating === '' || draft.code === ''}
                          onClick={() => {
                            void onRateClaim(claimId, draft.rating, draft.code);
                            setRated((prev) => ({ ...prev, [claimId]: true }));
                          }}
                          className="px-2.5 py-1 text-xs font-mono text-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary)] disabled:border-[var(--ak-color-border-subtle)] text-white rounded-md transition cursor-pointer"
                        >
                          Submit rating for {claimId}
                        </button>
                        {rated[claimId] === true && (
                          <span className="text-[11px] font-mono text-[var(--ak-color-primary)]">Rating recorded.</span>
                        )}
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </section>

        <section>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)] mb-1">
            Comments
          </h3>
          <ul className="space-y-1 mb-2">
            {(session?.comments ?? []).map((entry) => (
              <li key={entry.id} className="text-xs text-[var(--ak-color-text-secondary)] font-sans">
                <span className="font-mono text-[var(--ak-color-text-muted)]">{entry.author}: </span>
                {entry.text}
              </li>
            ))}
          </ul>
          <label htmlFor="review-comment" className="block text-[11px] font-mono text-[var(--ak-color-text-muted)] mb-1">
            Add a comment
          </label>
          <div className="flex items-center gap-2">
            <input
              id="review-comment"
              type="text"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              className="flex-1 text-xs border border-[var(--ak-color-border-subtle)] rounded-md px-2 py-1.5 bg-white text-[var(--ak-color-text-primary)]"
            />
            <button
              type="button"
              onClick={() => {
                void onAddComment(comment);
                setComment('');
              }}
              className="px-3 py-1.5 text-xs font-mono bg-[var(--ak-color-bg-subtle)] hover:border-[var(--ak-color-border-subtle)] text-[var(--ak-color-text-primary)] border border-[var(--ak-color-border-subtle)] rounded-md transition cursor-pointer"
            >
              Comment
            </button>
          </div>
        </section>

        <section className="flex flex-wrap items-center gap-2 pt-1">
          <button
            type="button"
            onClick={() => void onDecide('approve', [])}
            className="px-3 py-1.5 text-xs font-mono font-bold text-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary)] text-white rounded-md transition cursor-pointer"
          >
            Approve
          </button>
          <button
            type="button"
            onClick={() => setCorrecting((value) => !value)}
            className="px-3 py-1.5 text-xs font-mono bg-[var(--ak-color-bg-subtle)] hover:border-[var(--ak-color-border-subtle)] text-[var(--ak-color-text-primary)] border border-[var(--ak-color-border-subtle)] rounded-md transition cursor-pointer"
          >
            Correct
          </button>
          <button
            type="button"
            onClick={() => void onDecide('reject', [])}
            className="px-3 py-1.5 text-xs font-mono bg-white hover:bg-[var(--ak-color-warning-soft)] text-[var(--ak-color-danger)] border border-[var(--ak-color-border-subtle)] rounded-md transition cursor-pointer"
          >
            Reject
          </button>
        </section>

        {correcting && (
          <section className="border border-[var(--ak-color-border-subtle)] rounded-md p-3 space-y-2">
            <label htmlFor="correct-summary" className="block text-[11px] font-mono text-[var(--ak-color-text-muted)]">
              Edit patient summary
            </label>
            <textarea
              id="correct-summary"
              value={editedSummary}
              onChange={(event) => setEditedSummary(event.target.value)}
              rows={3}
              className="w-full text-xs border border-[var(--ak-color-border-subtle)] rounded-md px-2 py-1.5 bg-white text-[var(--ak-color-text-primary)] font-sans"
            />
            <button
              type="button"
              onClick={submitCorrection}
              className="px-3 py-1.5 text-xs font-mono font-bold text-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary)] text-white rounded-md transition cursor-pointer"
            >
              Submit correction
            </button>
          </section>
        )}
      </div>
    </div>
  );
};
