# ADR-0007: Append-Only Feedback Store (SQLite + Versioned SQL Migrations)

- **Status**: Accepted
- **Date**: 2026-09-30
- **Deciders**: Engineering Team & AI Agent
- **Governing Document**: `plan/prompts/phase-6-feedback/STEP-36_P6.1_feedback-data-model.md`

---

## 1. Context

P6.1 requires nine feedback tables with database-level immutability for
`reports_original` and `audit_log`, plus a migration per schema change.
The repo has no migration framework (no alembic/sqlalchemy in dependencies);
`src/vh` persistence follows the stdlib `sqlite3` pattern
(`common/artifacts.py`, `cases/patient_repo.py`). Production Postgres
(via docker compose) remains the deployment target per CLAUDE.md; the
versioned SQL migration files are the portable contract.

## 2. Decision

- SQLite via stdlib `sqlite3`, following the existing `ArtifactRegistry` pattern.
- Versioned SQL migration files under `src/vh/feedback/migrations/`
  (`0001_initial.sql`) applied in filename order by a small runner
  (`migrations/__init__.py`) tracking `schema_migrations`; re-runs idempotent.
- Immutability via `BEFORE UPDATE/DELETE` triggers with `RAISE(ABORT, ...)`
  on `reports_original` and `audit_log` (surfaced as `sqlite3.IntegrityError`).
- Doctor corrections are structured JSON edit ops (`replace`/`add`/`remove`
  over `path` key/index lists); `apply_edits` is a pure function operating on
  a deepcopy, failing closed (KeyError/IndexError/TypeError/ValueError) with
  no partial mutation. Strict dict-str / list-int path discipline.
- Claim ratings constrained to correct | partially_correct | incorrect plus a
  `configs/feedback/taxonomy.yaml` code (9 codes); unknown codes refused.
- `final_reports.session_id` is UNIQUE: exactly one final per review session.

## 3. Consequences

- Migration SQL is Postgres-compatible by inspection (standard DDL; triggers
  would need `plpgsql` translation at deployment time — recorded here so the
  port is explicit, not forgotten).
- Replay/test bundles stay out of git (`data/replays/` ignored); feedback test
  databases live in pytest `tmp_path` and are never committed.
