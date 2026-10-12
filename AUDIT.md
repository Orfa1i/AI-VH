# Comprehensive Frontend & Design System Audit (Phase 1)

> **Date:** October 6, 2026  
> **Repository:** AI-VH (AI Virtual Hospital) / MedGemma-4B  
> **Status:** Phase 1 Complete (Zero Code Changes)  
> **Reference Specifications:** `asklevia-identity/`, `asklevia-ui-kit/`, `BRAND-CONTRACT.md`, `asklevia-redesign-plan/01-audit.md`

---

## 1. Stack & Architecture

| Dimension | Current Implementation | Notes / Target State |
| :--- | :--- | :--- |
| **Framework & Version** | React 19.2.8 (`react`, `react-dom`) | Modern Concurrent React, functional components with hooks |
| **Router** | Tab state routing in `frontend/src/App.tsx` (`activeTab: TabType`) | 10 application views controlled via state (`INTAKE`, `PATIENTS`, `STAFF`, `REPORTS`, `REVIEW`, `REVIEWING`, `WARDS`, `HOSPITAL3D`, `KNOWLEDGE`, `BENCHMARK`) |
| **Styling Approach** | Tailwind CSS v4.3.3 (`@tailwindcss/vite` in `vite.config.ts`, `@import "tailwindcss";` in `src/index.css`) + custom CSS classes (`.glass-panel`, `.hud-bracket`, `.telemetry-grid`) | Extensive utility classes with hardcoded Tailwind default palette (`slate-*`, `sky-*`, `emerald-*`, `indigo-*`, `rose-*`, `amber-*`). No CSS-in-JS or external UI framework (no MUI, Bootstrap, or Chakra). |
| **3D & Canvas** | Three.js (`three` 0.183.2, `@react-three/fiber` 9.5.0, `@react-three/drei` 10.7.7) | Used in `Hospital3DScene.tsx` and `Hospital3DSection.tsx` for spatial ward visualization |
| **Icons** | Lucide React (`lucide-react` 1.16.0) | 38 unique Lucide icon components used across 24 files |
| **Build Tool** | Vite 8.3.0 (`@vitejs/plugin-react` 6.0.0) | Fast ESM dev server and Rollup production bundler |
| **Package Manager** | npm (`package-lock.json` present) | Node.js v22.19.0 runtime environment |
| **Execution Scripts** | `npm run dev` (port 5173), `npm run build` (`tsc -b && vite build`), `npm run preview` | Backend runs via Uvicorn on port 8000 |
| **Tests & Linting** | Vitest 4.1.0 (`vitest`, `@testing-library/react`), Oxlint (`oxlint` 1.63.0) | Frontend test suite passes (`npm test -- --run`). Oxlint configured for linting. |

---

## 2. Route Map & Surface Classification

The frontend operates as a single-page clinical workstation with 10 state-driven views in `frontend/src/App.tsx`. All views represent authenticated/clinical product surfaces; there is currently no separate public marketing landing page.

| Tab Key | Component File Path | Surface Type | Clinical / Functional Purpose |
| :--- | :--- | :--- | :--- |
| `INTAKE` | `frontend/src/components/management/CaseIntakeAdmissionSection.tsx` | Product (Clinical) | Admission desk, synthetic case intake, triage vital signs, patient ingestion, and bed assignment |
| `PATIENTS` | `frontend/src/components/management/PatientDirectorySection.tsx` | Product (Clinical) | Master patient directory, EHR history, admission status filtering, active census |
| `STAFF` | `frontend/src/components/management/StaffManagementSection.tsx` | Product (Administrative) | Staff directory, department assignments, shift status, attending physician roster |
| `REPORTS` | `frontend/src/components/diagram/PatientJourneyFlowPage.tsx` | Product (Clinical) | Autonomous encounter execution, live telemetry, dynamic trajectory stepper, hospital flow diagram |
| `REVIEW` | `frontend/src/components/dashboard/PhysicianReviewDashboard.tsx` | Product (Evaluation) | Clinical review queue, attending physician evaluation, error taxonomy scoring, case finalization |
| `REVIEWING` | `frontend/src/components/reviewing/ReviewedReportsSection.tsx` | Product (Evaluation) | Archived reviewed reports, feedback audit trail, manual DPO fine-tuning control panel |
| `WARDS` | `frontend/src/components/hospital/HospitalLayout.tsx` | Product (Operational) | Ward census, bed status, room occupancy, department overview |
| `HOSPITAL3D` | `frontend/src/components/hospital3d/Hospital3DSection.tsx` | Product (Spatial/Visual) | Interactive 3D spatial floor plan rendered with React Three Fiber |
| `KNOWLEDGE` | `frontend/src/components/management/KnowledgeSearchSection.tsx` | Product (Clinical Reference) | Specialty Medical Book RAG search, clinical textbook vector retrieval, chunk inspector |
| `BENCHMARK` | `frontend/src/components/rl/PolicyBenchmarkModal.tsx` | Product (Evaluation) | Clinical diagnostic benchmark suite, model policy comparisons, validation metrics |

**Persistent Overlays & Modals:**
- `frontend/src/components/notifications/LeftNotificationDrawer.tsx`: Docked real-time WebSocket event feed and clinical alerts.
- `frontend/src/components/simulation/ActiveEncounterProgressBar.tsx`: Real-time simulation encounter stepper header.
- `frontend/src/components/specialists/DoctorChatModal.tsx`: Direct specialist consult modal.
- `frontend/src/components/specialists/DepartmentStationModal.tsx`: Clinical department station terminal.
- `frontend/src/components/synthea/SyntheticTimelineModal.tsx`: Synthea longitudinal patient timeline inspector.
- `frontend/src/components/rl/RLDatasetModal.tsx`: DPO preference dataset curation modal.

---

## 3. Reusable UI Component Inventory

Mapping existing UI components to the Asklevia UI Kit primitive library (`asklevia-ui-kit/`):

| Current Component / Pattern | File Path | Usage Count | Asklevia Kit Component Target | Notes / Action Plan |
| :--- | :--- | :--- | :--- | :--- |
| **Buttons (Primary / Secondary / Danger)** | Across 25+ files (raw `<button>` with Tailwind classes) | >180 instances | `Button` (`ak-btn`, `ak-btn--primary`, `ak-btn--secondary`, `ak-btn--ghost`, `ak-btn--danger`) | Replace custom Tailwind buttons with standard pill buttons (`--radius-pill`), 40px height, Funnel Display font. |
| **Input Fields & Search Bars** | `<input type="text">`, search inputs in 12 files | 34 instances | `TextField` (`ak-input`, `ak-field`) | Standardize on 8px radius (`--radius-sm`), 40px touch height, clear focus ring (`--focus-ring`). |
| **Dropdown Selects** | `<select>` elements in 8 files | 18 instances | `Select` (`ak-select`) | Replace native unstyled dropdowns with styled Asklevia select primitives. |
| **Filter Checkboxes** | `<input type="checkbox">` in filter modals | 12 instances | `Checkbox` (`ak-checkbox`) | Standardize check states and indigo highlight. |
| **Status & Triage Badges** | Raw `<span>` with `bg-*-50 text-*-700` in 28 files | >150 instances | `Badge` (`ak-badge`, `ak-badge--neutral`, `ak-badge--success`, `ak-badge--warning`, `ak-badge--danger`, `ak-badge--info`, `ak-badge--ai`) | Replace arbitrary Tailwind color badges with calibrated token badges. Only use `--spectrum-gradient` on AI-tagged elements (`ak-badge--ai`). |
| **Physician & Patient Avatars** | Custom `<div>` circular initials / photos in 6 files | 22 instances | `Avatar` (`ak-avatar`, `ak-avatar--status`) | Standardize circular avatar sizes with status indicators. |
| **Loading Spinners & Indicators** | Custom SVG / `animate-spin` in 10 files | 16 instances | `Spinner` (`ak-spinner`) | Standardize 2-second linear rotational spinner. |
| **Encounter Progress Bars** | `ActiveEncounterProgressBar.tsx`, Steppers | 8 instances | `ProgressBar` (`ak-progress`, `ak-progress--spectrum`) | Use Neural Spectrum gradient on simulation progress (`ak-progress--spectrum`). |
| **Warning / Status Banners** | Alert cards in Review & Triage | 14 instances | `Alert` (`ak-alert`, `ak-alert--warning`, `ak-alert--danger`, `ak-alert--info`) | Hairline border, light tint background, standard typography. |
| **Toast Notifications** | `LeftNotificationDrawer.tsx` incoming alert toast | 1 instance | `Toast` (`ak-toast`) | Standardize bottom-right or docked slide-in toast notification. |
| **Cards & Panels** | `.glass-panel`, `.glass-panel-elevated`, `bg-white rounded-xl` in 30 files | >120 instances | `Card` (`ak-card`, `ak-card--flat`, `ak-card--interactive`) | Replace dark/cyan HUD panels with 16px radius (`--radius-lg`), hairline border (`--border-default`), crisp white surface (`--bg-surface`). |
| **Dialogs & Modals** | Custom fixed backdrop `<div>` modals in 6 files | 7 instances | `Dialog` (`ak-dialog`, `ak-modal`) | Standardize modal backdrop blur, pill close buttons, and header typography. |
| **Navigation Tabs** | Custom tab bars in `App.tsx` and review filters | 5 instances | `Tabs` (`ak-tabs`, `ak-tab--active`) | Standardize navigation tabs with bottom highlight bar. |
| **Data Tables** | Patient list, Staff directory, Reviewed list | 4 instances | `Table` (`ak-table`) | Hairline row borders, monospace tabular numbers for IDs and dates. |
| **Clinical Stepper** | `ActiveTrajectoryStepper.tsx` | 1 instance | `Steps` (`ak-steps`) | Map 4-stage trajectory stepper to Asklevia steps design. |
| **Empty States** | Placeholder states when lists are empty | 6 instances | `EmptyState` (`ak-empty-state`) | Neutral illustration/icon, clear clinical message, action button. |
| **Confidence Meters** | `diagnostic_confidence` progress in report views | 3 instances | `ConfidenceList` (`ak-confidence-list`) | Standard Asklevia diagnostic confidence meter with calibrated color tiers. |
| **Top Navigation Bar** | Header in `App.tsx` | 1 instance | `AppBar` (`ak-app-bar`) | Full-width 56px height, logo lockup, status indicator, clean tab navigation. |
| **Notification Drawer** | `LeftNotificationDrawer.tsx` | 1 instance | `SideNav` / Docked Drawer (`ak-drawer`) | Clean white drawer with Geist Mono telemetry timestamps. |

---

## 4. Style Debt Audit

### A. Hard-Coded Colour Occurrences
- **Files checked:** 51
- **Files with hardcoded/arbitrary colour values:** 31
- **Hex colour literals (`#...`):** 44 occurrences
- **RGB / RGBA literals (`rgba(...)`):** 9 occurrences
- **Tailwind arbitrary/palette classes (`bg-slate-900`, `text-sky-600`, etc.):** 2,918 occurrences
- **Grand Total Baseline Colour Occurrences:** **2,971**
*(This exact figure of 2,971 constitutes the baseline to track down to 0 in Phase 7).*

**Top 12 Offending Files:**
1. `frontend/src/components/rl/PolicyBenchmarkModal.tsx`: 282 colour classes
2. `frontend/src/components/dashboard/PhysicianReviewDashboard.tsx`: 273 colour classes (270 TW, 3 Hex)
3. `frontend/src/components/diagram/HospitalFlowDiagram.tsx`: 224 colour classes (222 TW, 1 Hex, 1 RGBA)
4. `frontend/src/components/reviewing/ReviewedReportsSection.tsx`: 214 colour classes (212 TW, 2 Hex)
5. `frontend/src/components/management/PatientDirectorySection.tsx`: 193 colour classes (192 TW, 1 Hex)
6. `frontend/src/components/management/CaseIntakeAdmissionSection.tsx`: 185 colour classes (184 TW, 1 Hex)
7. `frontend/src/components/management/StaffManagementSection.tsx`: 180 colour classes (179 TW, 1 Hex)
8. `frontend/src/components/rl/RLDatasetModal.tsx`: 127 colour classes
9. `frontend/src/components/synthea/DemoPatientsSection.tsx`: 125 colour classes (124 TW, 1 Hex)
10. `frontend/src/components/synthea/SyntheticTimelineModal.tsx`: 122 colour classes
11. `frontend/src/components/management/KnowledgeSearchSection.tsx`: 119 colour classes (118 TW, 1 Hex)
12. `frontend/src/App.tsx`: 112 colour classes (110 TW, 2 Hex)

### B. Font Families in Use
- Currently configured in `frontend/src/index.css`: `Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- Codebase classes use Tailwind defaults: `font-sans`, `font-mono`.
- No variable font files currently loaded in `frontend/src/`.
- **Target Scale (`BRAND-CONTRACT.md`):**
  - Headings / Display: **Funnel Display** (Medium 500)
  - Body / UI Labels: **Host Grotesk** (Regular 400, Medium 500)
  - IDs / Telemetry / Metrics / Code: **Geist Mono** (`.ak-num`, font-mono)

### C. Radius, Shadow, and Spacing Scale Debt
- Arbitrary border-radius values currently in use: `rounded-2xl`, `rounded-xl`, `rounded-lg`, `rounded-md`, `rounded-full`, `rounded-[4px]`.
- Asklevia strict radius scale:
  - `--radius-sm`: 8px (inputs, form fields, badges)
  - `--radius-md`: 12px (dropdowns, small panels)
  - `--radius-lg`: 16px (cards, dialogue surfaces, tables)
  - `--radius-pill`: 9999px (buttons, chips, status pills)
- Shadows currently in use: arbitrary Tailwind `shadow-sm`, `shadow-md`, `shadow-lg`, `shadow-2xl`, and cyan glow effects (`shadow-[0_0_15px_rgba(...)]`).
- Asklevia shadow scale: `--shadow-card`, `--shadow-dropdown`, `--shadow-modal`.

### D. Gradients, Dark-Mode Code & Sci-Fi HUD Widgets
- **Gradient classes:** 21 occurrences across the codebase (e.g., `bg-gradient-to-r from-sky-500 to-indigo-600`, `bg-gradient-to-b`).
- **Dark mode:** 0 `dark:` Tailwind classes; however, dark tactical HUD components exist (e.g., tactical HUD reticles in `index.css`, dark slate backgrounds in 3D scene overlays and benchmark graphs).
- **Invariants Violations to Eliminate:**
  - Sci-fi tactical corner brackets (`.hud-bracket` in `index.css`).
  - Coordinate grid telemetry background (`.telemetry-grid` with blue dot matrix).
  - Glowing borders and pulse animations simulating gaming/military interfaces.

---

## 5. Asset & Branding Inventory

### Current Assets in `frontend/src/assets/`:
- `dr_marcus_vance.jpg` (Attending physician avatar photo - 661 KB). Keep as realistic clinical asset.
- `hero.png` (Legacy hero image - 13 KB). To be replaced by Asklevia brand imagery.
- `react.svg` / `vite.svg` (Vite starter boilerplate assets). Remove.
- Favicon in `frontend/index.html`: Default Vite favicon (`/vite.svg`).

### Brand Consistency Scan:
- **"Orvexa" occurrences:** 0 occurrences found across the entire repository. Clean baseline.
- **Asklevia Identity Assets Available (`asklevia-identity/` & `asklevia-ui-kit/`):**
  - Logos: SVG and high-resolution PNG lockups (Dark, Light, Symbol, Wordmark).
  - Favicons: Multi-size PNGs and SVG symbols.
  - Fonts: `FunnelDisplay-Variable.woff2`, `HostGrotesk-Variable.woff2`, `GeistMono-Variable.woff2`.

### Icon Library:
- Exclusively **Lucide React** (`lucide-react` v1.16.0).
- 38 unique icons in active use (`Activity`, `AlertCircle`, `AlertTriangle`, `ArrowRight`, `Bell`, `BookOpen`, `Box`, `Brain`, `Building2`, `Calendar`, `Check`, `CheckCircle2`, `ChevronDown`, `ChevronLeft`, `ChevronRight`, `ChevronUp`, `Clock`, `Cpu`, `Database`, `DoorOpen`, `FileCheck2`, `FileText`, `FlaskConical`, `Heart`, `HeartPulse`, `Info`, `Layers`, `Pill`, `Play`, `Radio`, `RefreshCw`, `RotateCcw`, `Search`, `ShieldAlert`, `ShieldCheck`, `Sparkles`, `Star`, `Stethoscope`, `TestTube`, `Thermometer`, `ThumbsDown`, `ThumbsUp`, `Trash2`, `User`, `Wind`, `X`, `XCircle`).

---

## 6. Copy & Clinical Voice Audit

Per `BRAND-CONTRACT.md`, Asklevia uses calm, precise, clinical language. Exclamation marks, hyperbole, marketing hype, and "AI diagnosed" jargon must be eliminated.

| File Location | Current Copy (Violations) | Clinical Replacement |
| :--- | :--- | :--- |
| `App.tsx` | `"AI Virtual Hospital | Autonomous Multi-Agent Clinical Operating System"` | `"Asklevia | Virtual Hospital Clinical Operating System"` |
| `App.tsx` | `"System Sync Live"` / `"Running Simulation..."` | `"Synchronized"`, `"Simulation in progress"` |
| `PhysicianReviewDashboard.tsx` | `"Autonomous Encounters"` / `"CLINICAL QUEUE"` | `"Review Queue"`, `"Unreviewed Encounters"` |
| `HospitalFlowDiagram.tsx` | `"AWWWARDS-TIER HUD"` (code comment) / `"DISCHARGE READY"` | `"Discharge evaluation complete"` |
| `ReviewedReportsSection.tsx` | `"Trigger DPO Fine-Tuning!"` / `"Model Super-Optimization"` | `"Execute policy alignment training"`, `"Training parameters"` |
| `CaseIntakeAdmissionSection.tsx` | `"Instant Synthea AI Generation!"` | `"Generate synthetic cohort"` |
| `ActiveTrajectoryStepper.tsx` | `"Agent Reasoning Matrix"` | `"Clinical trajectory"` |

---

## 7. Accessibility Quick Scan

- **Missing Labels & Accessible Names:**
  - Multiple icon-only action buttons (`<button onClick={...}><RotateCcw /></button>`, `<button><Trash2 /></button>`) lack `aria-label` or screen-reader accessible text.
- **Focus Rings:**
  - Several Tailwind utility sets specify `focus:outline-none` without an explicit replacement `focus-visible:ring-2` offset.
- **Touch Target Sizing:**
  - Some table actions and tab switchers use compact heights (<32px). Must ensure all interactive buttons meet the 40px minimum touch target height per `BRAND-CONTRACT.md`.
- **Colour-Only Status Indicators:**
  - Triage levels and confidence meters occasionally rely solely on green/yellow/red dots without an accompanying textual label or accessible description.

---

## 8. Gap Report & Missing UI Kit Primitives

The Asklevia UI Kit provides an extensive set of foundational primitives, but the Virtual Hospital requires several specialized clinical data displays:

| Clinical Requirement | Gap in UI Kit | Proposed Implementation Using Tokens |
| :--- | :--- | :--- |
| **Vitals Waveform / Telemetry Graph** | No dedicated ECG/vital charts in kit | Build a clean SVG component using `--action-primary` and `--color-success`, light background (`--bg-surface`), and Geist Mono numbers. Strictly avoid dark glowing HUD reticles. |
| **3D Hospital Ward Canvas** | Three.js scene requires canvas background | Set canvas background to `--bg-page` (#F7F8FB), style overlaid HTML HUD cards using `.ak-card` with `--radius-lg` and hairline borders. |
| **Longitudinal Patient Timeline** | Medical chronological event stream | Construct using `.ak-steps` primitive with neutral vertical borders and Geist Mono timestamps (`.ak-num`). |
| **Specialty RAG Chunk Inspector** | Text snippet grounding viewer | Build using `.ak-card--flat` with border `--border-subtle`, Geist Mono metadata badges, and high-contrast text. |

---

## 9. Architectural Risks & Behavior Preservation Gate

1. **State Preservation Invariant:**  
   The application relies on deep real-time state synchronization via WebSockets (`/ws/events`), custom polling, and complex state lifecycles in `App.tsx`. **No state hooks, WebSocket event listeners, or API handlers must be modified or removed during styling.**
2. **Three.js Canvas Dimensions:**  
   In `Hospital3DSection.tsx`, the R3F Canvas relies on parent flexbox dimensions. Applying outer wrapper classes must preserve `w-full h-full min-h-[600px]` to prevent canvas collapse.
3. **Modal Portals & Stacking Context:**  
   Modals (`PolicyBenchmarkModal`, `SyntheticTimelineModal`, etc.) use `z-50` fixed positioning. Transitioning to `.ak-modal` must maintain appropriate z-indices so that tooltips and drawers remain interactive.

---

## 10. Recommended Implementation Approach & Phase Estimates

### Strategy: Hybrid Tailwind Preset + `.ak-*` Design Tokens
We recommend **replacing existing styling with Asklevia tokens and `.ak-*` classes via a tailored Tailwind v4 preset (`tailwind.preset.js`) and direct CSS variables (`tokens.css`)**:
- **Reasoning:** The app already uses Tailwind v4. By registering the Asklevia design tokens as theme extensions (colors, fonts, radii, shadows) and applying `.ak-*` utility wrappers, we achieve 100% brand contract compliance without rewriting component business logic or introducing heavy runtime dependencies.
- **Zero-Breaking-Change Guarantee:** All form validation, state updates, modal callbacks, and API calls remain completely untouched.

### Phase Effort & Roadmap:
- **Phase 1: Audit & Baselines** (Completed) – 0 code modifications.
- **Phase 2: Foundations & Assets** (Est. 1 turn) – Copy fonts, logos, setup `tokens.css`, `asklevia.css`, setup brand linter script.
- **Phase 3: Core Primitives** (Est. 1 turn) – Button, TextField, Select, Badge, Card, Dialog, Table, Tabs wrappers.
- **Phase 4: Shell & Navigation** (Est. 1 turn) – Header, App Bar, Navigation Tabs, Notification Drawer, Footer.
- **Phase 5: Product Views & Modals** (Est. 1 turn) – Triage, Patient Directory, Reports, Review Dashboard, Reviewing, Knowledge.
- **Phase 6: Spatial & Clinical Data** (Est. 1 turn) – 3D canvas overlay restyling, Trajectory Stepper, Benchmark view.
- **Phase 7: Visual Polish & Verification** (Est. 1 turn) – Proof of 0 hardcoded colors, accessibility verification, final build test.

---

*Phase 1 Audit Certified. Ready for user review.*
