# 1. Project Vision & Final System

## Project Vision

Build a 3D Virtual Hospital Simulation Environment populated by autonomous AI agents representing:

- Doctors
- Nurses
- Patients
- Radiologists
- Laboratory staff
- Reception/administrative staff
- Potentially pharmacists and other clinical roles later

The hospital should behave like a simulated healthcare environment where AI agents interact with each other, patients arrive with medical conditions, doctors investigate and diagnose them, nurses perform clinical workflows, and the system generates complete clinical reports.

**Central research objective:**

> Can autonomous medical AI agents improve their clinical decision-making and workflow behavior through expert human feedback and Reinforcement Learning?

Continuous loop the system must support:

```
Patient → Clinical Encounter → Agent Decisions → Diagnosis/Report →
Human Physician Review → Feedback → Training/Evaluation → Improved Agent
```

## Core Architecture (layered)

The project should NOT be treated as simply "MedGemma inside a 3D hospital." Separate it into layers:

```
                    VIRTUAL HOSPITAL
                         │
        ┌────────────────┴────────────────┐
        │                                 │
   3D Environment                    Simulation Engine
        │                                 │
        └────────────────┬────────────────┘
                         │
                  AGENT ORCHESTRATOR
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
    DOCTORS            NURSES           PATIENTS
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                  CLINICAL TOOLS
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
     EHR              Radiology           Lab
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                  MEDICAL KNOWLEDGE
                         │
                    RAG SYSTEM
                         │
                  MedGemma + Tools
                         │
                  Clinical Output
                         │
              HUMAN PHYSICIAN REVIEW
                         │
                     FEEDBACK
                         │
                 TRAINING PIPELINE
                         │
                RL / Preference Learning
                         │
                  EVALUATION ENGINE
```

## The Most Important Research Experiment

The strongest experiment isn't "Can AI diagnose patients?" Instead, the research question should be:

> "Can a multi-agent clinical AI system improve its decision-making and workflow performance through iterative expert feedback within a simulated hospital environment?"

Compare, measuring performance at every stage:

- **Experiment A** — Base MedGemma agent.
- **Experiment B** — MedGemma + specialty RAG.
- **Experiment C** — MedGemma + RAG + tools.
- **Experiment D** — MedGemma + RAG + tools + multi-agent environment.
- **Experiment E** — MedGemma + RAG + tools + multi-agent environment + human feedback/RL.

This gives a scientifically meaningful progression rather than simply building a flashy AI hospital.

## Final System

```
                         VIRTUAL HOSPITAL
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
    Patients                Nurses                 Doctors
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               │
                         EVENT ENGINE
                               │
                    CLINICAL WORKFLOW
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
      EHR                    LAB                  RADIOLOGY
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               │
                        MEDICAL RAG
                               │
                    SPECIALTY KNOWLEDGE
                               │
                           MEDGEMMA
                               │
                         AGENT POLICY
                               │
                         CLINICAL REPORT
                               │
                     PHYSICIAN REVIEW
                               │
                    ┌──────────┴──────────┐
                    │                     │
                 APPROVE               CORRECT
                    │                     │
                    └──────────┬──────────┘
                               │
                         FEEDBACK DATA
                               │
                       EVALUATION ENGINE
                               │
                    RL / PREFERENCE LEARNING
                               │
                         NEW AGENT VERSION
                               │
                         RE-EVALUATION
                               │
                         VIRTUAL HOSPITAL
```

### The key principle

Don't build the 3D hospital first. Build the clinical simulation loop first:

```
Patient → Nurse → Doctor → Investigation → Diagnosis → Report →
Physician Review → Feedback → Evaluation
```

Once that loop works reliably, put the 3D hospital around it. This dramatically reduces the risk of spending months building a beautiful virtual hospital before proving that the AI-agent + clinical-feedback + learning loop actually works.
