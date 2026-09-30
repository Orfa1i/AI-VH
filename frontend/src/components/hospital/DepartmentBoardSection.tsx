import React, { useRef, useState } from 'react';
import { Building2 } from 'lucide-react';
import { fetchEvents, groupByRun } from './api';
import type { StreamEvent } from './api';
import { DepartmentBoard } from './DepartmentBoard';

const DEFAULT_BASE_URL =
  (import.meta.env.VITE_EVENT_API_URL as string | undefined) ?? 'http://127.0.0.1:8101';

type StreamMode = 'live' | 'replay';

export const DepartmentBoardSection: React.FC = () => {
  const [mode, setMode] = useState<StreamMode>('replay');
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const parseSseFrames = async function* (
    response: Response,
  ): AsyncGenerator<StreamEvent, void, void> {
    const reader = response.body?.getReader();
    if (reader === undefined || reader === null) throw new Error('No stream body.');
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';
      for (const frame of frames) {
        let eventId = '';
        let action = 'event';
        let data = '';
        for (const line of frame.split('\n')) {
          if (line.startsWith('id: ')) eventId = line.slice(4);
          else if (line.startsWith('event: ')) action = line.slice(7);
          else if (line.startsWith('data: ')) data += line.slice(6);
        }
        if (eventId === '') continue;
        const payload = JSON.parse(data === '' ? '{}' : data) as Omit<
          StreamEvent,
          'event_id' | 'action'
        >;
        yield { ...payload, event_id: eventId, action };
      }
    }
  };

  const loadStream = () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setError(null);
    setSelectedRunId(null);
    if (mode === 'replay') {
      fetchEvents(DEFAULT_BASE_URL)
        .then((loadedEvents) => {
          setEvents(loadedEvents);
          setLoaded(true);
        })
        .catch(() => setError('Could not load the event stream.'));
      return;
    }
    fetch(`${DEFAULT_BASE_URL}/events/stream?live=1&limit=200`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const collected: StreamEvent[] = [];
        for await (const event of parseSseFrames(response)) {
          collected.push(event);
          setEvents([...collected]);
          setLoaded(true);
        }
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setError('Live stream connection failed.');
      });
  };

  // Abort any in-flight live load on unmount.
  React.useEffect(() => () => abortRef.current?.abort(), []);

  const runs = groupByRun(events);

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-md hud-bracket">
          <div className="flex items-center gap-2 mb-3">
            <Building2 className="w-4 h-4 text-sky-700" aria-hidden="true" />
            <h1 className="text-sm font-mono font-bold uppercase tracking-wide text-slate-900">
              Department board
            </h1>
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <div>
              <label htmlFor="stream-mode" className="block text-[11px] font-mono text-slate-500 mb-1">
                Stream mode
              </label>
              <select
                id="stream-mode"
                value={mode}
                onChange={(event) => setMode(event.target.value as StreamMode)}
                className="text-xs border border-slate-300 rounded-md px-2 py-1.5 bg-white text-slate-900"
              >
                <option value="replay">Replay</option>
                <option value="live">Live</option>
              </select>
            </div>
            <button
              type="button"
              onClick={loadStream}
              className="px-4 py-1.5 text-xs font-mono font-bold bg-sky-700 hover:bg-sky-600 text-white rounded-md transition cursor-pointer"
            >
              Load stream
            </button>
          </div>
          {error !== null && (
            <p role="alert" className="mt-2 text-xs font-sans text-red-800">
              {error}
            </p>
          )}
        </div>

        {loaded && (
          <DepartmentBoard
            runs={runs}
            selectedRunId={selectedRunId}
            // Direct value update (not the functional form): verified working
            // under this tree's StrictMode dev double-invocation behavior.
            onSelectRun={(runId) => setSelectedRunId(selectedRunId === runId ? null : runId)}
            mode={mode}
          />
        )}
      </div>
    </div>
  );
};
