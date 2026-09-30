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
    <div className="bg-white border border-slate-200 rounded-xl shadow-md overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
        <h2 className="text-xs font-mono font-bold uppercase tracking-wide text-slate-900">
          {detail.case_id}
        </h2>
        {detail.flagged && (
          <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-red-100 text-red-800 border border-red-300">
            FLAGGED
          </span>
        )}
      </div>

      {detail.flagged && (
        <div role="alert" className="px-4 py-3 bg-red-50 border-b border-red-300">
          <p className="text-xs font-mono font-bold text-red-800 uppercase">Verification flagged</p>
          <ul className="mt-1 space-y-0.5">
            {verificationEntries.map(([key, value]) => (
              <li key={key} className="text-xs font-sans text-red-800">
                {key}: {String(value)}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="px-4 py-3 space-y-4">
        <section>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-slate-900 mb-1">
            Patient summary
          </h3>
          <p className="text-xs text-slate-600 font-sans">{detail.report.patient_summary}</p>
        </section>

        {(detail.report.differential ?? []).length > 0 && (
          <section>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-slate-900 mb-1">
              Differential
            </h3>
            <ul className="space-y-1">
              {(detail.report.differential ?? []).map((entry, index) => (
                <li key={index} className="text-xs text-slate-600 font-sans">
                  {entry.dx}
                  {entry.likelihood ? ` (${entry.likelihood})` : ''}
                </li>
              ))}
            </ul>
          </section>
        )}

        <section>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-slate-900 mb-1">
            Claims &amp; evidence
          </h3>
          <ul className="space-y-2">
            {claims.map((claim, index) => {
              const claimId = String(claim.claim_id ?? `claim-${index}`);
              const open = expanded[claimId] ?? false;
              const draft = ratings[claimId] ?? { rating: '', code: '' };
              return (
                <li key={claimId} className="border border-slate-200 rounded-md">
                  <button
                    type="button"
                    aria-expanded={open ? 'true' : 'false'}
                    onClick={() => setExpanded((prev) => ({ ...prev, [claimId]: !open }))}
                    className="w-full px-3 py-2 flex items-center gap-2 text-left cursor-pointer hover:bg-slate-100"
                  >
                    {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    <span className="text-xs font-mono font-semibold text-slate-900">{claimId}</span>
                  </button>
                  {open && (
                    <div className="px-3 pb-3 space-y-2">
                      <p className="text-xs text-slate-600 font-sans">{claim.text}</p>
                      {Array.isArray(claim.evidence_ids) && claim.evidence_ids.length > 0 && (
                        <p className="text-[11px] font-mono text-slate-500">
                          Evidence: {claim.evidence_ids.join(', ')}
                        </p>
                      )}
                      {typeof claim.source === 'string' && claim.source !== '' && (
                        <p className="text-[11px] font-mono text-slate-500">Source: {claim.source}</p>
                      )}
                      <div className="flex flex-wrap items-center gap-2">
                        <label htmlFor={`rating-${claimId}`} className="text-[11px] font-mono text-slate-500">
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
                          className="text-xs border border-slate-300 rounded-md px-2 py-1 bg-white text-slate-900"
                        >
                          <option value="">Select</option>
                          {CLAIM_RATINGS.map((rating) => (
                            <option key={rating} value={rating}>
                              {rating}
                            </option>
                          ))}
                        </select>
                        <label htmlFor={`taxonomy-${claimId}`} className="text-[11px] font-mono text-slate-500">
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
                          className="text-xs border border-slate-300 rounded-md px-2 py-1 bg-white text-slate-900"
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
                          className="px-2.5 py-1 text-xs font-mono bg-sky-700 hover:bg-sky-600 disabled:bg-slate-300 text-white rounded-md transition cursor-pointer"
                        >
                          Submit rating for {claimId}
                        </button>
                        {rated[claimId] === true && (
                          <span className="text-[11px] font-mono text-sky-700">Rating recorded.</span>
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
          <h3 className="text-xs font-mono font-bold uppercase tracking-wide text-slate-900 mb-1">
            Comments
          </h3>
          <ul className="space-y-1 mb-2">
            {(session?.comments ?? []).map((entry) => (
              <li key={entry.id} className="text-xs text-slate-600 font-sans">
                <span className="font-mono text-slate-500">{entry.author}: </span>
                {entry.text}
              </li>
            ))}
          </ul>
          <label htmlFor="review-comment" className="block text-[11px] font-mono text-slate-500 mb-1">
            Add a comment
          </label>
          <div className="flex items-center gap-2">
            <input
              id="review-comment"
              type="text"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              className="flex-1 text-xs border border-slate-300 rounded-md px-2 py-1.5 bg-white text-slate-900"
            />
            <button
              type="button"
              onClick={() => {
                void onAddComment(comment);
                setComment('');
              }}
              className="px-3 py-1.5 text-xs font-mono bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 rounded-md transition cursor-pointer"
            >
              Comment
            </button>
          </div>
        </section>

        <section className="flex flex-wrap items-center gap-2 pt-1">
          <button
            type="button"
            onClick={() => void onDecide('approve', [])}
            className="px-3 py-1.5 text-xs font-mono font-bold bg-sky-700 hover:bg-sky-600 text-white rounded-md transition cursor-pointer"
          >
            Approve
          </button>
          <button
            type="button"
            onClick={() => setCorrecting((value) => !value)}
            className="px-3 py-1.5 text-xs font-mono bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 rounded-md transition cursor-pointer"
          >
            Correct
          </button>
          <button
            type="button"
            onClick={() => void onDecide('reject', [])}
            className="px-3 py-1.5 text-xs font-mono bg-white hover:bg-red-50 text-red-800 border border-red-300 rounded-md transition cursor-pointer"
          >
            Reject
          </button>
        </section>

        {correcting && (
          <section className="border border-slate-200 rounded-md p-3 space-y-2">
            <label htmlFor="correct-summary" className="block text-[11px] font-mono text-slate-500">
              Edit patient summary
            </label>
            <textarea
              id="correct-summary"
              value={editedSummary}
              onChange={(event) => setEditedSummary(event.target.value)}
              rows={3}
              className="w-full text-xs border border-slate-300 rounded-md px-2 py-1.5 bg-white text-slate-900 font-sans"
            />
            <button
              type="button"
              onClick={submitCorrection}
              className="px-3 py-1.5 text-xs font-mono font-bold bg-sky-700 hover:bg-sky-600 text-white rounded-md transition cursor-pointer"
            >
              Submit correction
            </button>
          </section>
        )}
      </div>
    </div>
  );
};
