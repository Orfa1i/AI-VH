# 6. Data Architecture

## Database

Use **PostgreSQL** as the primary database. Potentially use: PostgreSQL, pgvector, Redis.

PostgreSQL stores:

- users
- agents
- patients
- cases
- encounters
- symptoms
- vitals
- medications
- allergies
- lab_orders
- lab_results
- imaging_orders
- imaging_results
- diagnoses
- clinical_reports
- agent_actions
- agent_decisions
- agent_versions
- human_reviews
- feedback
- training_examples
- evaluation_runs

## Vector Database

Use **pgvector** initially instead of adding another database unnecessarily. Store:

- medical knowledge embeddings
- book chunks
- guideline chunks
- case knowledge
- possibly historical approved examples

Keeps the initial architecture simpler.

## Obsidian

Obsidian can be extremely useful, but it should NOT be the production database. Use it as the project's **Knowledge Management + Research + Architecture Documentation System**:

```
Obsidian/
│
├── Architecture/
├── Agents/
├── Doctors/
├── Nurses/
├── Patients/
├── Medical Knowledge/
├── RL/
├── Evaluation/
├── Experiments/
├── Research Papers/
├── Decisions/
└── Roadmap/
```

**PostgreSQL = application data. Obsidian = human project knowledge/documentation.**
