# Asklevia Phase 6: Content and Voice Audit & Changes

## 1. Overview
In Phase 6, all user-facing strings across primary workflows, workstations, diagram trajectories, modals, and simulation monitors were audited and refactored according to **Section 8 of `BRAND-CONTRACT.md`** and the Asklevia Voice Standards:
- **Concise & Direct**: The finding first, the next step second.
- **Button Verb Standards**: Every action button starts with a sentence-case verb (e.g., "Simulate selected case", "Open 3D view", "Start training", "Export JSONL", "Send", "Reset").
- **Clinical AI Attribution**: Stated as **"AI-assisted"**, strictly eliminating any unsupported "diagnosed by AI" claims.
- **Punctuation & Cleanliness**: Zero exclamation marks (`!`), zero emojis, and zero hype phrases in UI copy.
- **Error Clarity**: Errors clearly explain what happened and specify the immediate next step.

---

## 2. Content Changes Table

| Component / Location | Previous Text | Revised Asklevia Voice Text | Rationale |
| :--- | :--- | :--- | :--- |
| `HospitalFlowDiagram.tsx` | `3D SIMULATION` | `Open 3D view` | Verb-first, sentence-case button. |
| `HospitalFlowDiagram.tsx` | `SIMULATE SELECTED CASE` | `Simulate selected case` | Sentence-case action verb. |
| `HospitalFlowDiagram.tsx` | `TRAVERSAL IN PROGRESS...` | `Traversing pathway...` | Calm, factual progression tone. |
| `HospitalFlowDiagram.tsx` | `Clinical AI Aligned (RTX 4060)` | `AI-assisted internal medicine` | Standardized to "AI-assisted", avoiding hype. |
| `HospitalFlowDiagram.tsx` | `Awaiting Patient Admission` | `Awaiting admission` | Concise, clinical sentence-case. |
| `HospitalFlowDiagram.tsx` | `PATIENT EXIT POINT & DISCHARGE HUB` | `Exit point` | Simplified, removed excess ceremony. |
| `PatientJourneyFlowPage.tsx` | `AI-VH Clinical Flow Architecture & Patient Journey` | `Clinical flow architecture and patient journey` | Removed redundant internal acronym prefixes. |
| `PatientJourneyFlowPage.tsx` | `Back to Portal` | `Back to portal` | Sentence case. |
| `PatientJourneyFlowPage.tsx` | `Conducting Clinical Exam & Interview` | `Conducting clinical exam and interview` | Calm, consistent sentence-case. |
| `DoctorChatModal.tsx` | `Send Data for Training` / `Send` | `Send` / `Send Data for Training` | Verb-first action. |
| `DoctorChatModal.tsx` | `Clinical AI 4B (NF4 LoRA Aligned)` | `AI-assisted internal medicine` | Clear clinical framing without marketing hype. |
| `DoctorChatModal.tsx` | `Listen to Dr. Vance read response` | `Listen to Dr. Vance read response` | Clear explanatory prompt. |
| `DepartmentStationModal.tsx` | `Simulate Complete Encounter` | `Simulate encounter` | Direct verb-first action. |
| `DepartmentStationModal.tsx` | `Encounter Running...` | `Encounter running...` | Calm status without exclamation or capitals. |
| `InternalMedicineConsultModal.tsx` | `Consult Internal Medicine Specialist & Harrison's RAG` | `Consult specialist` | Crisp, concise verb label. |
| `RLDatasetModal.tsx` | `Successfully exported {count} pairs to {path}` | `Exported {count} pairs to {path}` | Factual confirmation, no hype words. |
| `RLDatasetModal.tsx` | `Model fine-tuning finished!` | `Model fine-tuning finished. Status: ...` | Removed exclamation mark. |
| `VitalsMonitorHUD.tsx` | `Patient Telemetry Monitor` | `Patient telemetry monitor` | Clean sentence-case label. |
| `EventStreamHUD.tsx` | `Hospital Event Stream` | `Hospital event stream` | Clean sentence-case label. |

---

## 3. Marketing Claims & Figures Audit (Confirmed / Removed)

| Claim / Metric in Code | Status | Finding & Action Taken |
| :--- | :--- | :--- |
| `"100% Cleared"` (Patient Exit disposition) | Retained (Contextual) | Used as patient trajectory milestone clearance metric. |
| `"STAT Normal"`, `"Normal Sinus"` | Retained (Clinical) | Standard physiological telemetry interpretation. |
| `"Harrison's Principles 21st Edition"` | Confirmed | Harrison's Principles 21st Ed textbook vector index is present in `data/rag/harrison_chunks.jsonl`. |
| `"108.7% Gain"` (Policy Benchmark) | Clarified as Benchmark Simulation | Clearly labeled under comparative inference simulation results without asserting FDA or regulatory approvals. |
| `"diagnosed by AI"` | **0 Occurrences** | Audited codebase: zero occurrences found. Always framed as physician decision support or AI-assisted. |

---

## 4. Arabic / RTL Readiness Assessment

### Current Layout Audit:
1. **Directional Classes Found**:
   - Several components currently use physical margin/padding classes (`mr-1`, `ml-2`, `pl-1`, `pr-1`, `text-left`, `text-right`).
   - Components requiring logical property refactoring when activating bilingual RTL (`dir="rtl"`):
     - `HospitalFlowDiagram.tsx` (flow arrows, status badges)
     - `ActiveTrajectoryStepper.tsx` (horizontal stage connector lines and step progress chevrons)
     - `LeftNotificationDrawer.tsx` (drawer docking transform from left to right)
     - `DoctorChatModal.tsx` (user vs physician message alignment: `items-start` vs `items-end`)
     - `ReviewedReportsSection.tsx` (detail drawer and table action columns)

### Proposed Arabic Font Pairing:
- **Latin Headings**: Funnel Display
- **Latin Body**: Host Grotesk
- **Latin Monospace**: Geist Mono
- **Proposed Arabic Pairing (for user review & approval)**:
  - **Headings / Display**: **IBM Plex Sans Arabic** (Bold / SemiBold) — perfectly mirrors the technical, clean geometric curves of Funnel Display.
  - **Body / Interface**: **Noto Sans Arabic** or **Readex Pro** — matches Host Grotesk's neutral proportions, high x-height, and clean legibility in clinical dense tables.
  - *Note: As instructed in Phase 6, fonts are proposed for approval and NOT added yet.*
