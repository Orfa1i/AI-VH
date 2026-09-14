# 9. Evaluation System & Safety Architecture

## Evaluation System

Need a formal evaluation framework. Measure:

- **Diagnostic accuracy** — did it reach the correct diagnosis?
- **Differential diagnosis quality** — did it consider relevant alternatives?
- **Investigation quality** — did it order appropriate tests?
- **Treatment quality** — was the treatment appropriate?
- **Safety** — did it miss dangerous conditions?
- **Efficiency** — how many unnecessary actions did it perform?
- **Time** — how long did it take?
- **Report quality** — was the final report complete and clinically coherent?
- **Evidence grounding** — did its claims correspond to retrieved references?

## Benchmark Dataset

Create a controlled set of cases, e.g.:

```
100 cases
├── 20 easy
├── 30 moderate
├── 30 complex
└── 20 highly complex
```

Keep a held-out test set that agents never train on — critical, otherwise you won't know whether the model actually learned.

## Human Physician Evaluation

Recruit qualified physicians to evaluate the system. For each case:

```
AI output
       ↓
Physician score
       ↓
Correct / Incorrect
       ↓
Comments
       ↓
Suggested correction
```

Eventually have multiple physicians evaluate the same case to measure inter-rater agreement.

## Safety Architecture

Because this is a medical AI research system, implement safety controls from the beginning. The system should clearly be **a research/simulation environment, not a real clinical decision-making system**.

Important safeguards:

- No real patient data initially
- Synthetic patients
- Clear simulation labeling
- Human oversight
- Audit logs
- Agent action logs
- Model versioning
- No autonomous real-world treatment
- No real medication administration
- Controlled access
