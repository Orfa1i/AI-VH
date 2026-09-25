# AI Virtual Hospital — Complete Google Stitch Redesign Brief

## Purpose and product truth

Redesign **AI Virtual Hospital (AI-VH)** as a sophisticated desktop-first clinical AI simulation and research platform. It is used by clinical researchers, physician reviewers, and hospital simulation operators to run synthetic multi-agent hospital encounters, inspect AI-supported clinical outputs, collect structured physician feedback, and evaluate whether policy alignment improves quality and safety.

This is **not** a consumer telehealth product, an EHR replacement, or a live autonomous clinical decision maker. Prominently and calmly communicate: **Research simulation only — no autonomous diagnosis, prescribing, or patient care. Human clinician review required.** The interface must feel credible, measured, and safety-conscious rather than futuristic for its own sake.

The product’s defining loop is:

`Admit simulated case → run multi-agent encounter → inspect trace and report → physician review/correction → build preference data → evaluate model versions → improve the policy.`

The existing product is technically capable but visually fragmented: a dense tabbed operations portal, several large modals, an independent 2D/3D simulation view, and verbose telemetry. The redesign must make the loop visible and easy to follow, keep the 3D hospital as an optional spatial visualization rather than the primary workflow, and consolidate context instead of repeatedly opening modals.

## Existing capability inventory — do not omit

### Platform foundation

- Local MedGemma model with DPO/LoRA alignment, Harrison’s textbook RAG, tool-using doctor/nurse/patient/lab/radiology/pharmacy agents, FastAPI API, SQLite fallback / PostgreSQL target, live simulation events through WebSockets, and synthetic benchmark cases.
- An active manual intake workflow: name, age, sex, acuity, department, bed, complaint, HPI, history, medications, allergies, and baseline vitals. A new admission can launch an encounter.
- A patient directory and bed board with search, filters, patient chart, admission state, and discharge.
- A staff roster, staff profile, duty state, staff creation, and Dr. Marcus Vance as the flagship Internal Medicine attending. Retain the physician portrait as an intentional, professional anchor—not as decorative celebrity UI.
- AI clinical reports containing patient context, vitals, physical findings, investigations and results, differential diagnosis, primary diagnosis, confidence, clinical reasoning, treatment plan, disposition, citations, and pharmacist safety review.
- A physician review workflow with structured grades for diagnosis, reasoning, tests, and treatment; overall score; free-text comments; corrected diagnosis/treatment; approve or return-for-revision outcome. Preserve original AI output alongside review data.
- Direct Dr. Vance clinical chat with conversational intent handling, patient context, structured differential/workup/therapy/contraindications, citations, streaming capability, voice playback, and scenario starters.
- Formal specialist consultation with abnormal-lab input and cited evidence brief.
- Pharmacy medication safety review with prescriptions, diagnosis, allergies/contraindications, renal adjustments, warnings, interventions, approved medication list, and dispensing status.
- Harrison’s semantic/keyword knowledge search with specialty selection, relevance results, citations, excerpts, and book/chapter/page metadata.
- RL/DPO corpus inspection and export, benchmark comparison, benchmark-case drill-down, and comparative live inference for base MedGemma vs physician-aligned DPO model.
- Inpatient telemetry for four rooms with live vitals/rhythm/status; label it clearly as simulated/seeded demo telemetry until it is wired to patient state.
- A live event stream plus a 2D clinical flow diagram and optional 3D hospital with reception, triage, internal medicine, laboratory, radiology, pharmacy, and inpatient wing. The 3D mode supports first-person exploration and station interaction.

## Product strategy and experience principles

1. **One operational home.** Replace the many top-level tabs and modal launches with a persistent application shell and contextual detail panels. Every core object—case, encounter, report, review, model run—must be directly addressable and deep-linkable.
2. **Case context follows the user.** When a user selects a patient/encounter, show its name, MRN/case ID, acuity, simulation status, location, assigned bed, and safety state in a persistent context strip. Never make users reselect a case in each tool.
3. **Safety is information architecture, not a badge.** Show simulation status, data provenance, model version, RAG/knowledge version, reviewer state, and blocking warnings exactly where decisions happen. Use color plus icon/text; never communicate medical urgency through color alone.
4. **Calm clinical density.** Make the interface highly scannable with strong hierarchy, grouped content, table/card hybrids, progressive disclosure, and generous whitespace. Avoid a wall of small neon panels, gimmicky glow, excessive uppercase labels, emoji-as-icon UI, and always-animated decoration.
5. **Evidence before confidence.** Any diagnosis, recommendation, metric, or claimed improvement should reveal sources, model/version provenance, and the underlying simulation trace. Confidence must not overpower evidence or safety status.
6. **3D is optional and synchronized.** Treat the 3D view as a visual lens into the selected encounter, not as a separate application. It should inherit selected case and live event state, and open its tools in an adjacent inspector instead of generic modals.
7. **Designed for expert review.** Enable side-by-side comparison, keyboard navigation, clear unsaved states, auditability, and short paths for repetitive review work.

## Primary users and jobs

| User | Primary job | Success signal |
|---|---|---|
| Simulation operator | Admit a synthetic case, assign acuity/bed, run an encounter, monitor it | Can launch and supervise an encounter without hunting across screens |
| Physician reviewer | Evaluate an AI report, inspect evidence/trace, correct it, approve or send back | Can make a defensible review rapidly with original output preserved |
| Clinical researcher | Compare agents/model versions and assess safety/quality over cases | Can distinguish real results, benchmark results, and demo values |
| Research lead | Track experiment health, review throughput, and improvement evidence | Sees trustworthy trends, version provenance, and outstanding risk |

## Recommended information architecture

Use a desktop shell with a 280 px collapsible left navigation, a concise global header, an optional right contextual inspector, and an unobtrusive bottom status strip. On smaller screens, collapse navigation into a drawer and turn multi-column layouts into deliberate vertical stacks; do not attempt to preserve dense desktop tables unchanged.

### Persistent shell

- **Header:** AI-VH wordmark, environment switcher (`Research / Sandbox`), global search/command palette, database/service state, notifications, user menu. The status should distinguish `Connected`, `Degraded`, and `Offline`; do not hard-code “DB Connected.”
- **Simulation safety banner:** slim, dismissible per session, copy: “Research simulation. Synthetic data only. Outputs require qualified human review.”
- **Navigation:** Overview; Cases; Simulation; Review Queue; Knowledge & Consults; Evaluation; Learning Data; Hospital Explorer; Administration. Group low-frequency configuration under Administration.
- **Context bar:** appears after choosing a case or encounter. Include patient/case identifier, age/sex only when necessary, acuity, current workflow stage, department/bed, model/policy version, and `Open chart` / `Change case` actions.
- **Right inspector:** opens for citations, patient snapshot, event detail, agent detail, or evidence. It should be resizeable, keyboard-dismissible, and preserve the underlying page state.
- **Status strip:** API, event stream, model runtime (local GPU / fallback), knowledge base, and last synchronization time. Use compact text and tooltips rather than persistent technical noise.

### Routes/screens

1. **Overview** — operational and research overview; landing page after sign-in.
2. **Cases** — case list / bed board, patient chart, intake, and discharge.
3. **Simulation** — selected encounter command center and live workflow trace.
4. **Review Queue** — report queue plus review workspace.
5. **Knowledge & Consults** — RAG search, formal consult, Dr. Vance chat, and pharmacy safety review as tabs within one evidence workspace.
6. **Evaluation** — benchmark summary, model/version comparison, run detail, and methodology.
7. **Learning Data** — feedback corpus, DPO pair inspector, export history, data-quality states.
8. **Hospital Explorer** — 2D/3D spatial lens synchronized to an encounter.
9. **Administration** — staff, roles, model/knowledge configuration, system health, and audit history.

## Screen-by-screen specification

### 1. Overview — “Research Operations”

Create an executive but actionable overview, not a generic analytics page. At the top, show a `Today / 7 days / 30 days` period control and four concise KPI cards: Active encounters, Reports awaiting review, Review approval rate, and Safety flags needing attention. Each card links to the appropriate filtered screen and states its source/time window.

Below, use a two-column layout:

- **Left, wider:** “Active simulation board” with 3–6 active/recent encounter rows. Each row has patient/case ID, acuity, current stage, department, elapsed simulation time, assigned agents, and a clear continue action. Use a small stage rail, not a huge progress animation.
- **Right:** “Review priorities” ranked by severity/age and “System health” for API, events, local model, knowledge base, and database.
- **Lower section:** “Evidence of improvement” line/bar chart comparing base, RAG, tool-use, multi-agent, and DPO policies; include a methodology link and explicit `Benchmark / simulated` label. Beside it, show a compact “Recent feedback” feed.

Empty state: guide an operator to `Create simulated case`. Loading state: preserve page structure with skeletons. Error state: contextual retry and a meaningful error—not only red text.

### 2. Cases — unified patient directory, bed board, and intake

The default page is a list-plus-board view. Header: `Cases` title, search by patient/case/MRN/complaint, filters for status, acuity, department, and date, plus primary `New simulated case` button. Use a segmented control for **List** and **Bed board**. The bed board is a clear department grid with occupied/available/attention states; it must not look like a real-live hospital census without the simulation label.

Each list row should show name/ID, acuity chip, complaint, current status, department/bed, last event, and next required action. Selecting a row opens the patient chart in the right inspector or a dedicated detail route with tabs: Snapshot, Encounter history, Reports, Medications & allergies, and Audit trail. Make discharge a guarded secondary action with an explicit confirmation including case name.

`New simulated case` opens a full-page stepper, not a cramped modal:

1. Patient/case identity and synthetic-data notice.
2. Triage and placement: ESI acuity, department, bed.
3. Clinical presentation: complaint, HPI, history, medications, allergies.
4. Baseline vitals and review.

Use inline validation, plain-language input help, unit labels, structured chips for medications/allergies, autosave draft, and `Save draft` / `Admit & start simulation`. Do not prefill plausible real patient records. Benchmark scenarios may be offered under a clearly labelled “Load synthetic benchmark” drawer.

### 3. Simulation — encounter command center

This is the visual heart of the product. Start with an encounter selector and a context strip. Structure the desktop page as a 12-column layout:

- **Main 8 columns:** a horizontally readable clinical-stage timeline: Arrival → Triage → Assessment → Investigations → Reassessment → Pharmacy safety → Report ready → Physician review. The active stage has a strong outline and status label, past stages are completed, blocked/error stages explain why. Clicking a stage opens the relevant events and artifacts.
- **Right 4 columns:** `Live patient snapshot` with current vitals, trend sparklines, acuity, safety alerts, and latest clinician/agent action. Vitals use clinically conventional layout and unit notation; status is never shown by blinking alone.
- **Below main:** chronological event trace with filters by agent, department, event type, and severity. Event entries use structured, readable language such as “Laboratory agent published troponin result” rather than raw telemetry payloads. An event detail panel shows source, target, timestamp, payload, tool call, and link to downstream consequence.
- **Below/secondary:** `Agent activity` cards for patient, nurse, physician, lab, radiology, and pharmacist with their present status and last action. Include “Open evidence” rather than displaying internal chain-of-thought. Show a human-readable rationale summary only where the backend has a safe output.

Top actions: `Run simulation` (primary), `Pause / resume` if supported, `Restart from intake`, `Open report`, and `Explore hospital`. Confirm re-running an existing encounter. During run, lock destructive edits, show elapsed time and run state, and offer a non-blocking route away while the event stream continues.

### 4. Review Queue — physician review workspace

This should be the most polished, high-trust screen. Use a three-pane desktop layout:

- **Left queue:** filter by awaiting review, returned, approved, acuity, model version, reviewer, and date. Each row states patient/case ID, diagnosis, confidence, flags, status, and time waiting. Include counts and keyboard `j/k` selection.
- **Center report:** patient snapshot, chief complaint/HPI, timeline, key vitals and results, differential diagnosis (ranked with supporting/opposing evidence), primary diagnosis/confidence, investigations, plan, disposition, pharmacist review, and citations. Use section anchors and collapse less-relevant details.
- **Right review form:** diagnosis, reasoning, test appropriateness, and treatment safety rubric controls; 1–5 score; comments; corrected diagnosis; corrected treatment plan; `Approve` and `Return for revision` actions. Keep original AI report immutable and visibly separate from reviewer changes. Display an unsaved-changes warning and explicit post-submit success state.

Make safety-critical elements visually prioritized: contraindications, allergy conflicts, unsafe treatment flags, insufficient evidence, and low confidence. Do not use red for every negative grade. The screen must surface audit metadata: report time, model/policy version, knowledge retrieval version, citations count, and prior review history.

### 5. Knowledge & Consults — evidence workspace

Use a shared patient/encounter context and tabs rather than separate floating modals.

- **Search:** search bar with suggested queries, specialty filter, result count, and cards showing source, chapter, page, relevance, excerpt, and `Add to case evidence`. The detail view should show the full permitted excerpt/citation metadata and retrieval context.
- **Consult Dr. Vance:** structured input for clinical scenario and abnormal labs; results use sections for evidence brief, differential, immediate workup, guideline therapy, contraindications, and citations. Include `Attach to review` and `Start chat from this consult`.
- **Chat:** a focused conversation pane with message history, quick scenario chips, input, safe streaming status, voice controls, and a persistent note that chat is research support. For clinical messages, render structured response cards beneath the prose response. Greetings must produce simple conversational answers—not spurious diagnoses, workups, or citations.
- **Pharmacy safety:** select prescriptions from the current plan or enter orders; show safety clearance, approved medications, contraindications, renal adjustments, allergy warnings, interventions, and dispensing status. High-risk flags are pinned at the top.

### 6. Evaluation — model comparison that earns trust

Top-level control selects cohort, case difficulty, date range, policy/version(s), and benchmark vs live simulation data. State exactly what each metric means and how many cases it represents.

The summary uses: diagnostic accuracy, safety score, guideline adherence, investigation appropriateness, median time/actions per case, report completeness, and physician approval. Include confidence intervals or `insufficient data` states; never fabricate an improvement curve or use absolute language such as “100% safe.”

For side-by-side comparison, use columns for Base MedGemma and DPO-aligned agent with a thin neutral comparison gutter. Compare diagnosis, confidence, workup, treatment plan, cited evidence, contraindications, reward score, latency, and model metadata. The winner state must explain the metric and link to supporting benchmark cases. Live comparative inference is a separate clearly labelled tab with case picker/custom vignette, explicit GPU/fallback runtime status, run button, output state, and exportable result detail.

### 7. Learning Data — DPO/feedback corpus

Present this as a research data-management workspace. Header shows total pairs, human-reviewed count, calibration count, safety-critical count, average reward margin, and recent export. Main table filters by source, case, model version, safety criticality, reviewer status, and date.

Selecting a pair opens a side-by-side chosen/rejected inspector: prompt/context, candidate outputs, scores, score delta, citations, reviewer feedback, safety tags, model/knowledge version, and source report/review links. Include data-quality states for missing review, invalid schema, unresolved safety flag, or excluded item. Export uses a confirmation sheet summarizing count, filters, output format/location, and non-production data warning; show export history and reproducibility metadata.

### 8. Hospital Explorer — 2D/3D encounter lens

Offer an initial **2D workflow map** because it communicates clinical state better than 3D at a glance. It visualizes physical locations and the path of the selected patient through Reception, Triage, Internal Medicine, Lab, Radiology, Pharmacy, and Inpatient Wing. Location states should derive from current events.

Make **3D** a prominent toggle, not a different URL/app. The scene is clean, architectural, and legible: a modern simulated hospital cutaway with discrete zones, agent markers, patient marker, selected department highlighting, and camera presets. First-person controls are secondary and discoverable. Avoid uncanny humanoid prominence and game-like HUD clutter. Clicking a department or agent opens the shared right inspector; it must retain selected encounter context. Overlay only the vital essentials: current department, event connection state, selected patient, simple legend, camera/reset, and return to 2D. Provide reduced-motion and low-performance fallback behavior.

### 9. Administration — staff, system, and audit

Use sub-navigation for Staff directory, Models & knowledge, System health, and Audit log. Staff cards/list show real profile information, credentials, specialty, role, department, current duty state, and a professional portrait where available. Creation/editing is a deliberate form; deleting or changing duty status uses confirmation and activity history.

System health explains DB backend, API, WebSocket events, model loaded/not loaded, GPU availability, RAG corpus count and last index, with enough detail for operations but no exposed secrets. Audit log records case actions, simulation runs, reviews, exports, and configuration changes with actor/time/object/result.

## Design system direction

Create an original, restrained **clinical research workstation** visual system.

- **Theme:** default deep blue-black/slate for focused data work, with a polished light mode that is not an afterthought. Backgrounds should have distinct elevation rather than relying on glass blur everywhere.
- **Color roles:** ink/navy neutrals; clinical blue for interactive/system information; teal for live/active state; green for completed/approved only; amber for caution/review-needed; red for safety-critical/error only; violet reserved for model/research comparison. Colors need AA contrast and text/icon labels.
- **Typography:** contemporary humanist sans for UI (for example Inter, Geist, or IBM Plex Sans) paired with a compact tabular/monospace face for IDs, values, timestamps, and model versions. Use sentence case labels and readable 14–16 px body text; do not overuse tiny 10–11 px type.
- **Components:** 8 px spacing rhythm; 10–12 px card radius; subtle 1 px borders; small soft shadows; data tables with sticky headers; segmented controls; chips; timeline/event rows; sparklines; tooltips; drawers; confirmation sheets; toast notifications; accessible empty/loading/error states.
- **Icons:** use a single outline icon family such as Lucide; replace corrupted glyphs/emoji controls with semantic SVG icons and text labels. Use avatars only for identifiable staff/agents.
- **Motion:** short, purposeful transitions (150–250 ms). Event progress may gently update; do not use continuous pulse/ping/bounce animations except when they convey a currently changing live connection. Respect `prefers-reduced-motion`.

## Content and safety requirements

- Use realistic but clearly synthetic, non-identifiable sample data. Never present real patient records or claim a clinical action happened in the real world.
- Place the simulation/research disclaimer in the shell and close to run/review/consult actions. Do not bury it in the footer.
- Do not expose model chain-of-thought. Show structured clinical rationale, evidence citations, action logs, and output provenance instead.
- Never hard-code status claims such as “DB connected,” “100% cleared,” “guideline compliant,” or a fixed GPU memory figure. Use data-driven live status; if unavailable, render `Unavailable`, `Not run`, or `Demo data`.
- Clearly distinguish benchmark metrics, synthetic simulation output, manually entered synthetic cases, and any future connected data source.
- Include confirmation, error, retry, stale-data, permission-denied, no-results, no-case-selected, no-reports, no-review-needed, unavailable-model, disconnected-stream, and partially-complete simulation states.
- Ensure full keyboard support, visible focus, semantic forms, ARIA live announcements for important simulation/review updates, non-color status indicators, 44 px minimum hit areas for touch targets, and responsive layouts from 1280 px desktop down to tablet/mobile.

## Google Stitch execution prompt

Copy everything below into Google Stitch:

> Design a complete responsive web application redesign for **AI Virtual Hospital (AI-VH)**, a clinician-facing AI simulation and research platform. It is not a consumer healthcare app and not an EHR. Its users are simulation operators, physician reviewers, clinical researchers, and research leads. The product runs synthetic multi-agent hospital encounters using MedGemma, textbook RAG, lab/radiology/pharmacy tools, and physician feedback to evaluate and improve model policies.
>
> Product loop: **Admit simulated case → run encounter → inspect clinical trace and report → physician review/correction → build DPO preference data → benchmark/evaluate model versions.** Make that loop the center of the experience. Present a persistent safety label: “Research simulation. Synthetic data only. Outputs require qualified human review.” Never imply autonomous real-world care, diagnosis, prescribing, or live patient monitoring.
>
> Create a desktop-first clinical research workstation with a 280 px collapsible left navigation, concise global header, selected-case context strip, optional right inspector drawer, and small system status strip. Navigation: Research Operations, Cases, Simulation, Review Queue, Knowledge & Consults, Evaluation, Learning Data, Hospital Explorer, Administration. Header includes AI-VH brand, Research/Sandbox environment, command search, system state, notifications, and user menu. Do not use a dense top tab bar or modal-heavy workflow.
>
> Visual direction: original, calm, high-trust clinical research software. Use deep navy/slate surfaces with a polished light mode; clear elevation with borders rather than excessive glassmorphism; contemporary humanist sans typography, tabular mono for IDs/metrics; generous spacing; sentence case; semantic Lucide-style icons. Accent roles: blue = system/action, teal = active/live, green = completed/approved, amber = caution/review needed, red = safety-critical/error, violet = research/model comparisons. Meet WCAG AA; use text/icons alongside color. Avoid neon cyberpunk, emoji icons, fake telemetry, cluttered card grids, excessive uppercase, decorative pulse animations, and game-like UI.
>
> Design these linked screens with real content, empty/loading/error states, and responsive behavior:
>
> 1. **Research Operations overview:** KPI cards for active encounters, awaiting review, approval rate, safety flags; active simulation board; prioritized review list; honest system-health card; evidence-of-improvement chart that clearly labels benchmark/simulated data and links to methodology.
> 2. **Cases:** searchable/filterable case list plus bed-board toggle; patient/case rows with acuity, complaint, status, department/bed, last event, next action. Case detail tabs: Snapshot, Encounter history, Reports, Medications & allergies, Audit trail. `New simulated case` is a full-page four-step intake: identity/synthetic-data notice, triage/placement, clinical presentation, baseline vitals/review. Include save draft and `Admit & start simulation`.
> 3. **Simulation command center:** selected encounter context; 8/4 desktop layout. Main area has a clickable clinical timeline: Arrival, Triage, Assessment, Investigations, Reassessment, Pharmacy safety, Report ready, Physician review. Include a readable filtered event trace and agent activity cards. Right panel shows current patient snapshot, conventional vitals layout with units/trends, acuity, safety alerts, and latest action. Actions: Run simulation, restart, open report, explore hospital. Never expose chain-of-thought; show safe structured rationale, evidence, tool calls, and event metadata.
> 4. **Review Queue:** premium three-pane physician workspace: filtered report queue, structured AI clinical report, and review rubric panel. Report includes patient context, vitals/results, ranked differential with evidence, diagnosis/confidence, workup, plan, pharmacist review, citations, and provenance. Review panel grades diagnosis/reasoning/tests/treatment, score 1–5, comments, corrected diagnosis/treatment, approve and return-for-revision. Preserve AI original output separately from reviewer edits and show audit/model/knowledge metadata.
> 5. **Knowledge & Consults:** shared-case evidence workspace with tabs for RAG Search, Consult Dr. Vance, Chat, and Pharmacy Safety. Search shows book/chapter/page/relevance/excerpt and Add to case evidence. Consult presents evidence brief, differential, workup, therapy, contraindications, citations. Chat handles general greetings normally and clinical questions with structured cards and citations. Pharmacy safety shows clearance, approved medication list, contraindications, renal adjustments, allergy warnings, interventions, dispensing status; pin high-risk flags at top.
> 6. **Evaluation:** cohort/version/case filters and honest metric cards: diagnostic accuracy, safety, guideline adherence, investigation appropriateness, time/actions per case, report completeness, approval rate. Clearly represent `insufficient data`. Side-by-side Base MedGemma versus DPO-aligned model compares diagnosis, confidence, workup, treatment, citations, contraindications, reward, latency, and model metadata. Include a separate live comparative-inference tab with custom vignette, runtime state, results, and exportable detail.
> 7. **Learning Data:** DPO preference-corpus statistics, filters, a data table, and side-by-side chosen/rejected pair inspector with prompt, outputs, scores, safety tags, reviewer feedback, citations, provenance, and source links. Include data-quality flags and export confirmation/history.
> 8. **Hospital Explorer:** default to a simple 2D workflow/location map for the selected encounter, with an optional 3D modern hospital cutaway toggle. Show Reception, Triage, Internal Medicine, Lab, Radiology, Pharmacy, and Inpatient Wing. 3D is a synchronized contextual lens, not a separate app; click a location/agent to open the shared inspector. Keep overlays minimal; include legend, selected case, connection state, camera/reset, reduced-motion fallback.
> 9. **Administration:** Staff directory, professional Dr. Marcus Vance profile with portrait, roles/duty state, model and knowledge configuration, system health, and audit log. Use confirmations for destructive actions.
>
> Build a coherent component system: buttons, status chips, filters, searchable data tables, timeline, event feed, compact metric cards, evidence citation cards, vitals/sparkline widgets, drawers, confirmation sheets, toasts, empty/loading/error states, and keyboard-visible focus. Keep content realistic but synthetic. Never hard-code “DB connected,” “100% safe,” fixed GPU figures, or fake patient/telemetry claims; use `Demo data`, `Unavailable`, or `Not run` states where needed. Make every key screen feel connected by the current case, encounter, model version, and safety/review status.

## Acceptance checklist for the Stitch output

- The primary case-to-learning loop is understandable in under 10 seconds from the overview and Simulation screens.
- A user can navigate from an alert or case to its trace, report, evidence, review, feedback pair, and evaluation detail without losing context.
- The visual design differentiates operational workflow, clinical evidence, safety, and research comparison without becoming color-saturated.
- The 3D hospital is useful context rather than the main navigation mechanism.
- Every current capability is represented: intake, patients/bed board, staff, reports/reviews, RAG search, formal consult, Dr. Vance chat, pharmacy safety, telemetry, event trace, simulation, flow/3D explorer, DPO data, benchmarks, and comparative inference.
- The product looks trustworthy to a clinician and rigorous to a researcher, while remaining explicit that it is a synthetic research simulation.
