# 3. Agent Architecture (Doctors, Nurses, Patients)

## Generic Agent Config

Every agent should have a structured configuration:

```
Agent
├── Identity
├── Role
├── Specialty
├── Base Model
├── System Instructions
├── Medical Knowledge
├── Memory
├── Tools
├── Goals
├── Policies
├── Environment State
├── Decision History
└── Performance Metrics
```

## Doctor Agents

Doctor agents are the main intelligent agents. Base model: **MedGemma**, used as the medical foundation model where appropriate — but MedGemma itself is NOT the entire doctor agent. The agent should be an architecture built around the model:

```
Doctor Agent
     │
     ├── MedGemma
     ├── Specialty Knowledge
     ├── RAG
     ├── Patient Memory
     ├── Clinical Tools
     ├── Decision Policy
     ├── Environment State
     └── Evaluation / Feedback
```

### Doctor Specialties

Start with approximately 3–4 specialties:

- **Internal Medicine** — knowledge: internal medicine textbooks, clinical guidelines, appropriate medical references
- **Radiology** — knowledge: radiology textbooks, imaging references, appropriate radiology guidelines
- **Pediatrics** — knowledge: pediatric textbooks, pediatric clinical references
- **Obstetrics & Gynecology** — knowledge: obstetrics textbooks, gynecology references, appropriate guidelines

Later add: Cardiology, Neurology, Emergency medicine, Surgery, Oncology, Infectious disease.

## Nurse Agents

Nurses should NOT simply be copies of doctor agents — different role and decision policy. A nurse may:

- Receive patients
- Record vital signs
- Monitor patients
- Administer simulated medications
- Collect samples
- Prepare patients for imaging
- Communicate observations to doctors
- Monitor changes in patient status
- Escalate deterioration

Knowledge base: nursing textbooks, nursing guidelines, clinical procedures, appropriate nursing references.

## Patient Agents

One of the most important parts — patients should be simulated autonomous agents, not simple static NPCs. Each patient:

```
Patient Agent
│
├── Age
├── Sex
├── Medical History
├── Current Condition
├── Symptoms
├── Medications
├── Allergies
├── Vital Signs
├── Disease Progression
├── Personality
├── Communication Style
└── Hidden Clinical State
```

### Patient Cases (examples)

- Patient #001 — Age 62, Chief Complaint: Chest pain
- Patient #002 — Age 27, Chief Complaint: Abdominal pain
- Patient #003 — Age 8, Chief Complaint: Fever
- Patient #004 — Age 35, Chief Complaint: Shortness of breath

System should become progressively more difficult.

### Case Complexity (measurable benchmark)

- **Level 1 — Simple**: clear symptoms and diagnosis.
- **Level 2 — Moderate**: multiple possible diagnoses.
- **Level 3 — Complex**: multiple symptoms and comorbidities.
- **Level 4 — Difficult**: conflicting evidence.
- **Level 5 — High complexity**: multiple conditions, incomplete information, changing vitals and possible complications.

### Random Patient Generation

Simulation should generate patients automatically:

```
Case Generator
      ↓
Disease
      ↓
Demographics
      ↓
Symptoms
      ↓
History
      ↓
Vitals
      ↓
Medications
      ↓
Disease progression
```

The patient should not reveal all information immediately — the doctor must ask questions and request tests. Makes the environment more realistic.
