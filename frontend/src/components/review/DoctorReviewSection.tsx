import React, { useCallback, useState } from 'react';
import { Stethoscope } from 'lucide-react';
import { ReviewApiClient } from './api';
import type { Decision, EditOp, QueueItem, ReportDetail, SessionDetail } from './api';
import { ReportView } from './ReportView';
import { ReviewQueue } from './ReviewQueue';

type StatusMessage = { kind: 'ok' | 'error'; text: string } | null;

export const DoctorReviewSection: React.FC = () => {
  const [token, setToken] = useState('');
  const [client, setClient] = useState<ReviewApiClient | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusMessage>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshQueue = useCallback(
    async (active: ReviewApiClient) => {
      setQueue(await active.queue());
    },
    [],
  );

  const connect = async () => {
    try {
      const next = new ReviewApiClient(token.trim());
      await next.queue();
      setClient(next);
      setQueue(await next.queue());
      setError(null);
      setStatus(null);
    } catch {
      setError('Connection failed. Check the token and the review API.');
    }
  };

  const selectReport = async (originalId: string) => {
    if (client === null) return;
    try {
      const items = await client.queue();
      setQueue(items);
      const item = items.find((entry) => entry.original_id === originalId);
      if (item === undefined) throw new Error('Report is no longer in the queue.');
      const started = await client.startSession(item.assignment_id);
      const [reportDetail, sessionDetail] = await Promise.all([
        client.report(originalId),
        client.session(started.session_id),
      ]);
      setSelectedId(originalId);
      setDetail(reportDetail);
      setSession(sessionDetail);
      setSessionId(started.session_id);
      setError(null);
      setStatus(null);
    } catch {
      setError('Could not open the report.');
    }
  };

  const reloadSession = async (active: ReviewApiClient, id: string) => {
    setSession(await active.session(id));
  };

  const handleRateClaim = async (claimId: string, rating: string, code: string) => {
    if (client === null || sessionId === null) return;
    await client.rateClaim(sessionId, claimId, rating, code);
    await reloadSession(client, sessionId);
  };

  const handleAddComment = async (text: string) => {
    if (client === null || sessionId === null || text.trim() === '') return;
    await client.addComment(sessionId, text);
    await reloadSession(client, sessionId);
  };

  const handleDecide = async (decision: Decision, edits: EditOp[] = []) => {
    if (client === null || sessionId === null) return;
    const result = await client.decide(sessionId, decision, edits);
    if (decision === 'approve') setStatus({ kind: 'ok', text: 'Report approved.' });
    else if (decision === 'correct') setStatus({ kind: 'ok', text: 'Correction submitted.' });
    else setStatus({ kind: 'ok', text: 'Report rejected.' });
    if (result.final_report !== null) {
      const summary = result.final_report.patient_summary;
      if (typeof summary === 'string' && summary !== '') {
        setStatus((prev) => (prev === null ? prev : { ...prev, text: `${prev.text} ${summary}` }));
      }
    }
    await reloadSession(client, sessionId);
    await refreshQueue(client);
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-4">
        <div className="p-4 bg-white border border-[var(--ak-color-border-subtle)] rounded-xl shadow-md hud-bracket">
          <div className="flex items-center gap-2 mb-3">
            <Stethoscope className="w-4 h-4 text-[var(--ak-color-primary)]" aria-hidden="true" />
            <h1 className="text-sm font-mono font-bold uppercase tracking-wide text-[var(--ak-color-text-primary)]">
              Doctor review
            </h1>
          </div>
          {client === null ? (
            <div className="flex flex-wrap items-end gap-2">
              <div className="flex-1 min-w-52">
                <label htmlFor="reviewer-token" className="block text-[11px] font-mono text-[var(--ak-color-text-muted)] mb-1">
                  Reviewer token
                </label>
                <input
                  id="reviewer-token"
                  type="password"
                  value={token}
                  onChange={(event) => setToken(event.target.value)}
                  className="w-full text-xs border border-[var(--ak-color-border-subtle)] rounded-md px-2 py-1.5 bg-white text-[var(--ak-color-text-primary)] font-mono"
                />
              </div>
              <button
                type="button"
                onClick={() => void connect()}
                className="px-4 py-1.5 text-xs font-mono font-bold text-[var(--ak-color-primary)] hover:bg-[var(--ak-color-primary)] text-white rounded-md transition cursor-pointer"
              >
                Connect
              </button>
            </div>
          ) : (
            <p className="text-xs text-[var(--ak-color-text-secondary)] font-sans">Connected to the review API.</p>
          )}
          {error !== null && (
            <p role="alert" className="mt-2 text-xs font-sans text-[var(--ak-color-danger)]">
              {error}
            </p>
          )}
        </div>

        {client !== null && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-1">
              <ReviewQueue items={queue} selectedId={selectedId} onSelect={(id) => void selectReport(id)} />
            </div>
            <div className="lg:col-span-2 space-y-4">
              {status !== null && (
                <p role="status" className="text-xs font-sans text-[var(--ak-color-primary)]">
                  {status.text}
                </p>
              )}
              {detail !== null && (
                <ReportView
                  detail={detail}
                  session={session}
                  onRateClaim={(claimId, rating, code) => void handleRateClaim(claimId, rating, code)}
                  onAddComment={(text) => void handleAddComment(text)}
                  onDecide={(decision, edits = []) => void handleDecide(decision, edits)}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
