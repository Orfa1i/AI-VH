# 8. Reinforcement Learning

## Scope

This is where the research component becomes interesting. Do NOT immediately train the entire medical foundation model. Initially use RL to optimize the agent's decision-making/policy:

```
MedGemma
     +
Agent Architecture
     +
Tools
     +
Environment
     +
Reward Function
     ↓
RL Agent
```

## RL Environment

The virtual hospital itself becomes the RL environment.

### State

- Patient condition
- Known symptoms
- Vital signs
- Medical history
- Available test results
- Current location
- Current clinical stage
- Previous actions
- Time

### Actions

The doctor agent might:

- `ask_patient_question`
- `perform_examination`
- `order_lab`
- `order_imaging`
- `consult_specialist`
- `review_history`
- `diagnose`
- `treat`
- `monitor`
- `discharge`
- `admit`

### Reward

The reward function evaluates the quality of the decision:

- Correct diagnosis → **+ reward**
- Appropriate test → **+ reward**
- Unnecessary test → **- penalty**
- Missed critical condition → **- large penalty**
- Unsafe treatment → **- large penalty**
- Good clinical report → **+ reward**
- Appropriate escalation → **+ reward**

The reward design needs to be clinically validated.

## Human Feedback → Learning Pipeline

```
AI Decision
     ↓
AI Report
     ↓
Physician Review
     ↓
Correction
     ↓
Feedback Dataset
     ↓
Evaluation
     ↓
Training / Preference Optimization
     ↓
New Agent Version
     ↓
Testing
     ↓
Deployment
```

Do not automatically deploy every physician correction directly into the live agent — use a controlled model/version pipeline.

## Agent Versioning

Every model/agent configuration should have a version, e.g.:

- `Doctor_InternalMedicine_v0.1`
- `Doctor_InternalMedicine_v0.2`
- `Doctor_InternalMedicine_v0.3`

Track: Model, Prompt, RAG version, Knowledge version, Tools, Policy, Training data, Evaluation score.

This lets you answer: **"Did the agent actually improve?"**
