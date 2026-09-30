/**
 * Typed client for the doctor review API (STEP 37). Pure HTTP transport only:
 * no clinical logic lives in the frontend.
 */

const DEFAULT_BASE_URL =
  (import.meta.env.VITE_FEEDBACK_API_URL as string | undefined) ?? 'http://127.0.0.1:8100';

export interface QueueItem {
  assignment_id: string;
  original_id: string;
  case_id: string;
  flagged: boolean;
  status: string;
}

export interface ClaimView {
  claim_id?: string;
  text: string;
  evidence_ids?: string[];
  source?: string;
  [key: string]: unknown;
}

export interface DifferentialView {
  dx: string;
  likelihood?: string;
}

export interface RecommendationView {
  text: string;
}

export interface ReportBody {
  patient_summary?: string;
  differential?: DifferentialView[];
  recommendations?: RecommendationView[];
  claims?: ClaimView[];
  findings?: string[];
}

export interface ReportDetail {
  original_id: string;
  case_id: string;
  report: ReportBody;
  claims: ClaimView[];
  verification: Record<string, unknown>;
  flagged: boolean;
}

export interface SessionDetail {
  session: { id: string; assignment_id: string; decision: string | null };
  edits: Array<Record<string, unknown>>;
  claim_ratings: Array<Record<string, unknown>>;
  comments: Array<{ id: number; author: string; text: string }>;
}

export interface EditOp {
  op: 'replace' | 'add' | 'remove';
  path: Array<string | number>;
  value?: unknown;
}

export type Decision = 'approve' | 'correct' | 'reject';

export interface DecisionResult {
  decision: Decision;
  final_report: ReportBody | null;
}

export class ReviewApiClient {
  private readonly token: string;
  private readonly baseUrl: string;

  constructor(token: string, baseUrl: string = DEFAULT_BASE_URL) {
    this.token = token;
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        'X-Reviewer-Token': this.token,
        ...(init.headers ?? {}),
      },
    });
    if (!response.ok) {
      throw new Error(`Review API ${response.status} on ${path}`);
    }
    return (await response.json()) as T;
  }

  queue(): Promise<QueueItem[]> {
    return this.request<QueueItem[]>('/reviews/queue');
  }

  report(originalId: string): Promise<ReportDetail> {
    return this.request<ReportDetail>(`/reviews/reports/${originalId}`);
  }

  startSession(assignmentId: string): Promise<{ session_id: string }> {
    return this.request<{ session_id: string }>(`/reviews/assignments/${assignmentId}/start`, {
      method: 'POST',
    });
  }

  session(sessionId: string): Promise<SessionDetail> {
    return this.request<SessionDetail>(`/reviews/sessions/${sessionId}`);
  }

  rateClaim(sessionId: string, claimId: string, rating: string, taxonomyCode: string): Promise<unknown> {
    return this.request(`/reviews/sessions/${sessionId}/claims/${claimId}/rating`, {
      method: 'POST',
      body: JSON.stringify({ rating, taxonomy_code: taxonomyCode }),
    });
  }

  addComment(sessionId: string, text: string): Promise<unknown> {
    return this.request(`/reviews/sessions/${sessionId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  addEdit(sessionId: string, edit: EditOp): Promise<unknown> {
    return this.request(`/reviews/sessions/${sessionId}/edits`, {
      method: 'POST',
      body: JSON.stringify(edit),
    });
  }

  decide(sessionId: string, decision: Decision, edits: EditOp[] = [], comment?: string): Promise<DecisionResult> {
    return this.request<DecisionResult>(`/reviews/sessions/${sessionId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, edits, comment }),
    });
  }
}
