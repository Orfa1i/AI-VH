/**
 * Transport + pure presentation logic for the 2D department board.
 * Display only: departments group recorded actor/action pairs; no clinical
 * reasoning, scoring, or diagnosis happens here.
 */

const DEFAULT_BASE_URL =
  (import.meta.env.VITE_EVENT_API_URL as string | undefined) ?? 'http://127.0.0.1:8101';

export interface StreamEvent {
  event_id: string;
  run_id: string;
  sim_time: number;
  wall_time: string;
  actor: string;
  action: string;
  payload: Record<string, unknown>;
  result_ref: string | null;
}

export interface RunGroup {
  run_id: string;
  case_id: string;
  events: StreamEvent[];
}

export async function fetchEvents(baseUrl: string = DEFAULT_BASE_URL): Promise<StreamEvent[]> {
  const response = await fetch(`${baseUrl}/events?limit=1000`);
  if (!response.ok) {
    throw new Error(`Event API ${response.status} on /events`);
  }
  const body = (await response.json()) as { events: StreamEvent[] };
  return body.events;
}

export function groupByRun(events: StreamEvent[]): RunGroup[] {
  const groups = new Map<string, RunGroup>();
  for (const event of events) {
    const existing = groups.get(event.run_id);
    const caseId =
      typeof event.payload?.case_id === 'string' ? (event.payload.case_id as string) : event.run_id;
    if (existing === undefined) {
      groups.set(event.run_id, { run_id: event.run_id, case_id: caseId, events: [event] });
    } else {
      existing.events.push(event);
    }
  }
  return [...groups.values()];
}
