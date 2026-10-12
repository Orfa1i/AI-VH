# Asklevia UI/UX Audit & Quality Assurance Report

**Audit Conducted By:** Agent 3 (QA Specialist Agent)  
**Target Application:** AI-VH Asklevia Clinical Operating System  
**Design Standards:** `BRAND-CONTRACT.md`, `DESIGN-SYSTEM-USAGE.md`, `asklevia-ui-kit`  
**Target Recipient:** Agent 4 (Fixer Agent) & Parent Orchestrator  
**Audit Status:** Complete — Deficiencies Cataloged with Remediation Blueprints  

---

## 1. Executive Summary & Defect Scorecard

While the Phase 1–7 foundation established strong token architecture, our comprehensive QA audit revealed critical design contract violations, visual regressions, and accessibility gaps that bypassed the shallow `lint:brand.js` script (which only checked `bg|text|border|ring|fill|stroke` prefixes).

| Audit Dimension | Standard / Target | Current State / Defect Count | Severity |
| :--- | :--- | :--- | :--- |
| **Typography & Scale** | ≥ 12px throughout (`BRAND-CONTRACT §3`) | **193 sub-12px occurrences** (`text-[11px]`, `text-[10px]`, `text-[9px]`, `fontSize: 10`) across 19 files | 🔴 High |
| **Color & Theme** | Light Canvas (`#F7F8FB`), Zero dark sections (`§1`) | **14 dark container artifacts** (`bg-[var(--ak-color-text-primary)]`), pitch-black ECG strip, dark headers | 🔴 High |
| **Token Integrity** | Valid CSS variable syntax | **9 corrupted token typos** (`)]0`, e.g. `hover:bg-[var(--ak-color-primary-soft)]0`) | 🔴 High |
| **Tailwind Palette Bypass** | 0 hardcoded palette classes | **15 un-tokenized Tailwind utility leaks** (`from-sky-500`, `to-indigo-600`, `shadow-purple-600/30`, etc.) | 🟠 Medium |
| **Legacy HUD Residue** | Modern Asklevia clinical cards | **4 legacy `.hud-bracket` classes** remaining in core dashboard views | 🟡 Low |
| **Neural Spectrum Usage** | Strictly `.ak-progress--spectrum`, `.ak-badge--ai`, ≤1 divider/page (`§2`) | **4 spectrum violations**: Static diff Dx bar using spectrum, arbitrary purple/sky gradient buttons | 🔴 High |
| **Button Labels & Casing** | Action verbs in sentence case (`§8`) | **19 button label violations** (ALL CAPS, Title Case, missing action verbs) | 🟠 Medium |
| **Button Accessibility** | Visible focus, `aria-label` on icon-only buttons (`§6`, `§9`) | **18 icon-only buttons missing `aria-label`** (including star rating buttons in review dashboard) | 🔴 High |
| **Modal Scroll Containment** | `max-h-[90vh]` with `overflow-y-auto` | **`Dialog.tsx` primitive lacks max-height containment**; modals overflow viewport on laptop/tablets | 🔴 High |
| **Voice & Tone** | No emojis, no exclamation marks, never "diagnosed by AI" (`§8`) | **11 emojis**, **3 exclamation marks**, **1 "diagnosed by AI"** badge | 🔴 High |
| **Accessibility (WCAG 2.2 AA)**| Valid landmark hierarchy & keyboard skip link (`§9`) | **Illegal nested `<main>` tags**; **Missing skip link** (`#main-content`) | 🟠 Medium |

---

## 2. In-Depth Audit Findings by Category

### Category A: Typography & Scale (Section 3 of Brand Contract)

#### Findings:
1. **Widespread Sub-12px Illegible Text (193 occurrences across 19 files):**
   - `BRAND-CONTRACT.md` Section 3 explicitly mandates: **"Nothing below 12px. Headings are sentence case. Use one heading level per section."**
   - The codebase has 193 instances of `text-[11px]`, `text-[10px]`, `text-[9px]`, `fontSize: 10`, `fontSize: 11`, and `fontSize: '0.6875rem'`.
   - **Key Offending Locations:**
     - `src/components/diagram/HospitalFlowDiagram.tsx`: 45 instances (`text-[9px]`, `text-[10px]`, `text-[11px]` on telemetry metrics, rhythm lead, station badges).
     - `src/components/rl/PolicyBenchmarkModal.tsx`: 45 instances (`text-[9px]`, `text-[10px]`, `text-[11px]` on metrics, delta comparisons, chip badges).
     - `src/components/synthea/SyntheticTimelineModal.tsx`: 16 instances (`text-[10px]`, `text-[11px]`).
     - `src/components/synthea/DemoPatientsSection.tsx`: 13 instances (`text-[10px]`, `text-[11px]`).
     - `src/components/specialists/DoctorChatModal.tsx`: 11 instances (`text-[10px]`, `text-[11px]` on timestamp, citations, shortcut guide).
     - `src/components/dashboard/VitalsMonitorHUD.tsx`: 8 instances (`text-[10px]`, `text-[11px]` on bpm, mmHg units).
     - `src/components/review/ReportView.tsx`: 8 instances (`text-[10px]`, `text-[11px]`).
     - `src/components/specialists/DepartmentStationModal.tsx`: 7 instances (`text-[11px]`).
     - `src/components/specialists/InternalMedicineConsultModal.tsx`: 6 instances (`text-[11px]`).
     - `src/components/hospital/PatientCard.tsx`: 4 instances (`text-[11px]`).
     - `src/components/hospital/DepartmentBoard.tsx`: 3 instances (`text-[11px]`).
     - `src/components/reviewing/ReviewedReportsSection.tsx`: Line 341 uses `fontSize: '0.6875rem'` (11px).
     - `src/components/notifications/LeftNotificationDrawer.tsx`: Line 131 (`fontSize: 10`), Line 166 (`fontSize: 11`), Line 275 (`fontSize: 11`).
     - `src/components/ui/Badge.tsx`: Line 22 sets `size === 'sm' ? 'text-[10px] px-1.5 py-0.2' : ''`.
     - `src/App.tsx`: Line 248 sets `style={{ fontSize: 10, color: 'var(--text-tertiary)' }}` on the UTC clock badge.

#### Action for Agent 4 (Fixer):
- Refactor all sub-12px text to the standard Asklevia typography tokens:
  - Utility labels and telemetry units -> `caption` (`12px / 16px`, `--text-caption-size` or `text-xs`).
  - Small badges -> `text-xs` (12px) with compact padding `py-0.5 px-2`.
  - Fix `src/components/ui/Badge.tsx:22` so `size="sm"` is `text-xs px-2 py-0.5` (12px minimum).
  - Fix `src/App.tsx:248` to `fontSize: 12`.
  - Fix `LeftNotificationDrawer.tsx` unread badge to 12px.

---

### Category B: Color, Contrast & Unintended Dark-Mode Artifacts (Section 1 & 2)

#### Findings:
1. **Inverted Dark Containers (`bg-[var(--ak-color-text-primary)]`):**
   - Brand Contract Section 1 states: **"Light mode only. No dark mode, no dark sections, no tinted page backgrounds."**
   - During Phase 7 cleanup, several dark backgrounds were blindly replaced with `bg-[var(--ak-color-text-primary)]` (which is `#0F1222`, pitch dark navy). This created jarring, high-contrast inverted black boxes on an otherwise light canvas:
     - `src/components/diagram/HospitalFlowDiagram.tsx:197`:
       `<div className="flex-1 min-w-[220px] max-w-lg h-14 bg-[var(--ak-color-text-primary)] rounded-lg relative overflow-hidden flex items-center px-3">`
       This rhythm strip has a pitch-black box with `text-white/90` and `stroke-white/80`.
     - `src/components/dashboard/VitalsMonitorHUD.tsx:46`:
       `<div className="h-9 w-full bg-[var(--ak-color-text-primary)] rounded-lg mb-3 flex items-center ...">`
     - `src/components/dashboard/CaseSelector.tsx:47`:
       `<header className="h-16 px-6 bg-[var(--ak-color-text-primary)]/90 backdrop-blur-md border-b text-[var(--ak-color-text-primary)] ...">`
     - `src/components/synthea/SyntheticTimelineModal.tsx:405`:
       `<div className="bg-[var(--ak-color-text-primary)] text-[var(--ak-color-text-muted)] p-4 rounded-lg">`
2. **Corrupted Token Typo `)]0` (9 locations):**
   - Faulty global find-and-replace injected invalid strings:
     - `CaseSelector.tsx`: Line 58, 156, 168, 179 (`bg-[var(--ak-color-primary-soft)]0/10`, `bg-[var(--ak-color-primary-soft)]0`)
     - `DemoPatientsSection.tsx`: Line 273, 406, 524, 547 (`hover:bg-[var(--ak-color-primary-soft)]0`, `bg-[var(--ak-color-success-soft)]0`)
     - `SyntheticTimelineModal.tsx`: Line 242 (`hover:bg-[var(--ak-color-primary-soft)]0`)
3. **Tailwind Palette Bypasses (15 occurrences):**
   - `lint-brand.js` failed to catch `from-`, `to-`, `shadow-`, and `accent-` classes:
     - `CaseSelector.tsx:50`: `from-sky-500 to-indigo-600 shadow-sky-500/20`
     - `CaseSelector.tsx:89`: `from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 shadow-sky-500/25`
     - `CaseSelector.tsx:107, 117, 127`: `shadow-emerald-900/30`, `shadow-purple-900/30`, `shadow-indigo-900/30`
     - `PolicyBenchmarkModal.tsx:620, 805, 815, 825, 835, 855`: `shadow-purple-600/30`, `from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500`
     - `DemoPatientsSection.tsx:456`: `accent-sky-600`
4. **Legacy HUD Artifacts:**
   - Remaining `.hud-bracket` class in `App.tsx:472`, `DoctorReviewSection.tsx:99`, `DepartmentBoardSection.tsx:91`, `DepartmentBoard3DSection.tsx:48`.
5. **Raw `bg-white` classes instead of token:**
   - `App.tsx:472, 528`, `DoctorReviewSection.tsx:99, 117`, `DepartmentBoardSection.tsx:91, 107`, `DepartmentBoard3DSection.tsx:48, 72`, `ReportView.tsx:183, 269, 285`, `PolicyBenchmarkModal.tsx:353, 849`.

#### Action for Agent 4 (Fixer):
- Convert `HospitalFlowDiagram.tsx:197` ECG rhythm strip to clinical light theme: background `var(--bg-subtle)`, border hairline `var(--border-default)`, ECG trace `var(--action-primary)` or `var(--text-primary)`, telemetry text `var(--text-secondary)`.
- Replace `bg-[var(--ak-color-text-primary)]` containers with `bg-[var(--ak-color-bg-surface)]` or `bg-[var(--ak-color-bg-subtle)]`.
- Fix all `)]0` typos to proper tokens: `bg-[var(--ak-color-primary-soft)]`, `hover:bg-[var(--action-primary-hover)]`.
- Remove legacy `.hud-bracket` classes and replace arbitrary `shadow-*` and `from-*/to-*` gradients with standard Asklevia Button and Card primitives.
- Update `scripts/lint-brand.js` to scan `from-`, `to-`, `via-`, `shadow-`, `accent-` utility classes to prevent future regressions.

---

### Category C: Neural Spectrum Restrictions (Section 2 of Brand Contract)

#### Findings:
1. **Differential Diagnosis Static Progress Bar Violation:**
   - `src/components/dashboard/PhysicianReviewDashboard.tsx:602`:
     `variant={idx === 0 ? 'spectrum' : 'primary'}`
   - The #1 differential diagnosis condition percentage bar renders with `.ak-progress--spectrum`.
   - Brand Contract Section 2 is uncompromising:
     > "Neural Spectrum appears in exactly three UI places:
     > 1. the spectrum progress bar (.ak-progress--spectrum), meaning 'AI at work';
     > 2. the AI badge (.ak-badge--ai), meaning AI-produced content;
     > 3. the spectrum divider (.ak-divider--spectrum), at most one per page.
     > Never apply the spectrum gradient to arbitrary buttons, borders, text, or cards. No other gradients."
   - A static probability bar is NOT "AI at work". It should use `variant="primary"` (`--action-primary`) or semantic status colors.
2. **Arbitrary Gradients in Interactive Components:**
   - `CaseSelector.tsx:50, 89`: `bg-gradient-to-br from-sky-500 to-indigo-600` and `from-sky-500 to-indigo-600`.
   - `PolicyBenchmarkModal.tsx:855`: `bg-gradient-to-r from-purple-600 to-indigo-600`.

#### Action for Agent 4 (Fixer):
- Change `PhysicianReviewDashboard.tsx:602` to `variant="primary"`.
- Remove the non-standard sky and purple gradients; replace with standard Asklevia primary buttons (`<Button variant="primary">`).

---

### Category D: Button Labels, Casing & Interactive States (Section 8 & 9)

#### Findings:
1. **Non-Verb & ALL-CAPS Button Labels:**
   - `src/components/reviewing/ReviewedReportsSection.tsx:194`:
     `<Button variant="primary">MANUAL MODEL TRAINING</Button>` (ALL CAPS, non-verb).
   - `src/components/management/CaseIntakeAdmissionSection.tsx:188`:
     `<Button variant="secondary">Normal Baseline Vitals</Button>` (Non-verb, Title Case).
   - `src/components/management/StaffManagementSection.tsx:404`:
     `<Button variant="secondary">Cancel</Button>` (Non-verb single word).
   - `src/components/review/ReportView.tsx:257, 264, 271`:
     `Approve`, `Correct`, `Reject` (Bare verbs without object context).
   - `src/components/notifications/LeftNotificationDrawer.tsx:291`:
     `<button ...>Clear</button>` (Bare single word).
   - `src/components/specialists/DoctorChatModal.tsx:327`:
     `<Button ...>Reset</Button>` (Bare single word).
   - `src/components/specialists/DoctorChatModal.tsx:589`:
     `<Button ...>Send</Button>` (Bare single word).
2. **Title Case Button Labels:**
   - `src/components/management/PatientDirectorySection.tsx:132`: `Refresh Census` -> should be `Refresh census`.
   - `src/components/management/CaseIntakeAdmissionSection.tsx:196`: `Reset Form` -> `Reset form`.
   - `src/components/management/CaseIntakeAdmissionSection.tsx:658`: `Reset Fields` -> `Reset fields`.
   - `src/components/management/CaseIntakeAdmissionSection.tsx:669`: `Admit Patient to Record System` -> `Admit patient to record system`.
   - `src/components/dashboard/PhysicianReviewDashboard.tsx:658`: `Reset Records to Zero` -> `Reset records to zero`.
   - `src/components/dashboard/PhysicianReviewDashboard.tsx:700`: `Reset Review Queue` -> `Reset review queue`.
   - `src/components/dashboard/PhysicianReviewDashboard.tsx:714`: `Run Automated Audit` -> `Run automated audit`.
   - `src/components/dashboard/PhysicianReviewDashboard.tsx:892`: `Approve Verdict` -> `Approve verdict`.
   - `src/components/dashboard/PhysicianReviewDashboard.tsx:903`: `Reject / Flag Case` -> `Reject report`.
   - `src/components/rl/PolicyBenchmarkModal.tsx:382`: `Re-Run Benchmark` -> `Rerun benchmark`.
   - `src/components/rl/PolicyBenchmarkModal.tsx:394`: `Voice Readout` -> `Read aloud`.
   - `src/components/rl/PolicyBenchmarkModal.tsx:858`: `Run Comparative Inference` -> `Run comparative inference`.
   - `src/components/synthea/DemoPatientsSection.tsx:276`: `Generate Patients` -> `Generate synthetic patients`.
   - `src/components/synthea/DemoPatientsSection.tsx:398`: `View Case Details` -> `View case details`.
   - `src/components/synthea/DemoPatientsSection.tsx:410`: `Admit` -> `Admit patient`.
   - `src/components/synthea/DemoPatientsSection.tsx:550`: `Run Generator` -> `Generate population`.
   - `src/pages/DesignSystemShowcase.tsx:267, 277`: `View Chart` -> `View chart`.
3. **Missing `aria-label` on Icon-Only Buttons (18 instances):**
   - `src/components/dashboard/PhysicianReviewDashboard.tsx:764-785`: Star rating 1–5 buttons have no `aria-label` or accessible names!
   - `src/components/specialists/DoctorChatModal.tsx:330`: Close modal `<Button><X /></Button>` missing `aria-label="Close conversation"`.
   - `src/components/specialists/InternalMedicineConsultModal.tsx:145`: Close `<Button><X /></Button>` missing `aria-label="Close consult"`.
   - `src/components/diagram/PatientJourneyFlowPage.tsx:241`: Audio toggle `<Button>` missing `aria-label`.
   - `src/components/synthea/DemoPatientsSection.tsx:257, 437`: Reload repository & modal close missing `aria-label`.
   - `src/components/synthea/SyntheticTimelineModal.tsx:220, 240, 260`: Timeline controls missing `aria-label`.

#### Action for Agent 4 (Fixer):
- Rename buttons to clear, sentence-case action verb phrases:
  - `MANUAL MODEL TRAINING` -> `Start manual training`
  - `Normal Baseline Vitals` -> `Load normal vitals`
  - `Cancel` -> `Dismiss` or `Cancel registration`
  - `Approve` / `Correct` / `Reject` -> `Approve report` / `Correct summary` / `Reject report`
  - `Send` -> `Send message`
  - `Reset` -> `Reset conversation`
- Add `aria-label={`Rate ${star} out of 5 stars`}` to star buttons in `PhysicianReviewDashboard.tsx`.
- Add `aria-label` to all icon-only buttons.

---

### Category E: Responsive Design & Modal Scroll Containment

#### Findings:
1. **Modal Viewport Overflow in `Dialog.tsx` Primitive:**
   - In `src/components/ui/Dialog.tsx`, the modal dialog container `.ak-dialog` lacks `max-height: min(90vh, 100%)` and `overflow-hidden`.
   - Its body container `.ak-dialog__body` lacks `max-height: calc(90vh - 140px)` with `overflow-y: auto`.
   - **Impact:** When `StaffManagementSection` opens the 8-field Clinician Registration Dialog, or `PatientDirectorySection` opens the comprehensive Patient EHR Record Dialog, the modal stretches beyond the bottom of the viewport on 768px/900px displays. The footer action buttons (`Dismiss`, `Register professional`) are pushed completely off-screen and become inaccessible.
2. **`DoctorChatModal.tsx` Fixed Height:**
   - Uses `h-[90vh]` instead of responsive `max-h-[90vh]`.
3. **`DemoPatientsSection.tsx` Population Generator Modal:**
   - Uses fixed custom overlay without `max-h-[90vh] overflow-y-auto`.
4. **Table Horizontal Responsiveness:**
   - In `src/components/ui/DisplayPrimitives.tsx`, `Table` wraps `<table className="ak-table">` inside `.ak-table-wrap`. However, in `PolicyBenchmarkModal.tsx` and custom telemetry tables, raw tables without `.ak-table-wrap` or `overflow-x-auto` can cause layout blowouts on small screens.
5. **LeftNotificationDrawer Layout:**
   - The drawer uses fixed docking `left: 0, top: 96`. On mobile screens (<640px), the drawer should take full width `width: 100vw` without side gap.
   - The empty state in `LeftNotificationDrawer.tsx:309` uses an ad-hoc inline div instead of the standard `<EmptyState>` primitive.

#### Action for Agent 4 (Fixer):
- In `src/components/ui/Dialog.tsx`:
  - Add `max-height: 90vh; display: flex; flex-direction: column;` to `.ak-dialog`.
  - Add `overflow-y: auto; flex: 1;` to `.ak-dialog__body`.
- Update `DoctorChatModal.tsx` to `max-h-[90vh] h-full sm:h-[90vh]`.
- Convert `DemoPatientsSection.tsx` generator modal to use `<Dialog>` or add `max-h-[90vh] overflow-y-auto`.
- Use `<EmptyState>` inside `LeftNotificationDrawer.tsx`.

---

### Category F: Voice & Tone (Section 8 of Brand Contract)

#### Findings:
1. **Exclamation Marks (3 violations):**
   - Brand Contract Section 8 states: **"No exclamation marks, no emoji and no hype words (revolutionary, magic, game-changing, cutting-edge)."**
   - Violations:
     - `src/components/reviewing/ReviewedReportsSection.tsx:132`:
       `Model fine-tuning completed successfully! Adapter saved to ${result.adapter_path || 'models/medgemma-dpo-lora'}`
     - `src/components/rl/PolicyBenchmarkModal.tsx:402`:
       `<span>{copied ? 'Copied!' : 'Copy JSON'}</span>`
     - `src/components/synthea/DemoPatientsSection.tsx:116`:
       `Successfully generated ${data.population_generated} synthetic patients!`
2. **Emojis in Clinical Interface (11 violations):**
   - `src/components/management/StaffManagementSection.tsx:287-291`:
     Renders role emojis directly in the UI: `👨‍⚕️` (Doctor), `👩‍⚕️` (Nurse), `🔬` (Lab scientist), `🩻` (Radiologist), `📋` (Receptionist).
   - `src/components/rl/PolicyBenchmarkModal.tsx:1038`:
     Renders `📖` (Book emoji) before textbook citations.
   - `src/components/reviewing/ReviewedReportsSection.tsx:271, 348`:
     Renders raw star unicode `★` in filter chips and card footer.
   - `src/components/dashboard/CaseSelector.tsx:51, 109`:
     Renders `🏥` and `🩺` emojis.
3. **"Diagnosed by AI" Rule Violation (Section 8):**
   - Brand Contract Section 8 states: **"Write 'AI-assisted'. Never write 'diagnosed by AI'."**
   - `src/pages/DesignSystemShowcase.tsx:157`:
     `<Badge variant="ai">MedGemma Diagnosed</Badge>`
   - `src/pages/DesignSystemShowcase.tsx:177`:
     `label="Autonomous Diagnosis Encounter"`

#### Action for Agent 4 (Fixer):
- Remove all exclamation points: replace with clinical periods ("Model fine-tuning completed successfully. Adapter saved to...", "Copied", "Generated ${count} synthetic patients.").
- Replace all emojis with official Lucide outline icons (`Stethoscope`, `Activity`, `FlaskConical`, `FileScan`, `ClipboardList`, `BookOpen`, `Star`).
- Replace `MedGemma Diagnosed` with `AI-assisted diagnosis` or `MedGemma AI-assisted`.

---

### Category G: Accessibility (WCAG 2.2 AA Compliance)

#### Findings:
1. **Illegal Landmark Nesting (Nested `<main>` tags):**
   - In `src/App.tsx:428`: `<main className="flex-1 overflow-hidden flex flex-col relative bg-[var(--ak-color-bg-app)]">` wraps all portal views.
   - Inside the views, `src/components/layout/Templates.tsx` (`AppPage`, `DetailPage`, `FlowPage`) renders another `<main id="main-content">`.
   - **Violation:** WCAG 2.2 / ARIA specifies that an HTML document must have only one top-level `<main>` landmark. Nesting `<main>` inside `<main>` breaks screen reader landmark navigation.
2. **Missing Skip Link:**
   - Brand Contract Section 9 states: **"Semantic HTML, labelled form fields, keyboard access to every control and a skip link."**
   - Neither `index.html` nor `App.tsx` contains an accessible skip-to-content link (`<a href="#main-content" className="ak-skip-link">Skip to main content</a>`).

#### Action for Agent 4 (Fixer):
- In `src/App.tsx:428`, change the outer container from `<main>` to a neutral semantic `<div>` or `<section id="app-viewport">`, allowing `AppPage`'s `<main id="main-content">` to serve as the single canonical landmark.
- Add `<a href="#main-content" className="ak-skip-link">Skip to clinical content</a>` in `App.tsx` or `index.html`, styled with `.ak-skip-link` in `asklevia.css`.

---

## 3. Prioritized Implementation Blueprint for Agent 4 (Fixer Agent)

| Step | Priority | Target Files | Remediation Description |
| :--- | :--- | :--- | :--- |
| **P1** | 🔴 Critical | `src/components/ui/Dialog.tsx`, `asklevia.css` | Fix modal scroll containment: enforce `max-h-[90vh]` on `.ak-dialog` and `overflow-y-auto` on `.ak-dialog__body`. |
| **P2** | 🔴 Critical | `HospitalFlowDiagram.tsx`, `CaseSelector.tsx`, `VitalsMonitorHUD.tsx`, `SyntheticTimelineModal.tsx` | Eliminate inverted pitch-black containers (`bg-[var(--ak-color-text-primary)]`), convert ECG strip to clinical light theme, resolve 9 `)]0` typos. |
| **P3** | 🔴 Critical | `PhysicianReviewDashboard.tsx`, `CaseSelector.tsx`, `PolicyBenchmarkModal.tsx` | Fix spectrum misuse: convert diff Dx static progress bar to `variant="primary"`, remove arbitrary sky and purple gradients. |
| **P4** | 🔴 Critical | 19 tsx files with sub-12px text | Upgrade all 193 sub-12px font occurrences to minimum 12px (`caption` token / `text-xs`). |
| **P5** | 🔴 Critical | `StaffManagementSection.tsx`, `ReviewedReportsSection.tsx`, `PolicyBenchmarkModal.tsx`, `CaseSelector.tsx`, `DesignSystemShowcase.tsx` | Eliminate 11 emojis, 3 exclamation marks, and replace "MedGemma Diagnosed" with "AI-assisted diagnosis". |
| **P6** | 🟠 High | `PhysicianReviewDashboard.tsx`, `DoctorChatModal.tsx`, `InternalMedicineConsultModal.tsx`, `PatientJourneyFlowPage.tsx`, `DemoPatientsSection.tsx` | Add missing `aria-label` to all 18 icon-only buttons (especially star rating buttons). |
| **P7** | 🟠 High | All workstation files | Standardize button labels to sentence-case action verb phrases; convert `MANUAL MODEL TRAINING` and bare verbs (`Approve`, `Correct`, `Reject`). |
| **P8** | 🟠 High | `App.tsx`, `Templates.tsx`, `index.html`, `asklevia.css` | Fix nested `<main>` landmark violation and install accessible `.ak-skip-link`. |
| **P9** | 🟡 Medium | `scripts/lint-brand.js` | Expand regex to scan `from-`, `to-`, `via-`, `shadow-`, `accent-` utility classes to permanently prevent style debt leakage. |

---

*QA Audit completed by Agent 3. Ready for handoff to Agent 4 (Fixer Agent).*
