# 7. Clinical Reports & Human Physician Review

## Clinical Report

Every doctor agent should generate a structured report containing:

- Patient Information
- Chief Complaint
- History of Present Illness
- Relevant Medical History
- Vital Signs
- Clinical Findings
- Differential Diagnosis
- Investigations Requested
- Investigation Results
- Final Diagnosis
- Treatment Plan
- Clinical Reasoning
- Confidence
- References

## Human Physician Review

One of the most important components. Create a dedicated physician dashboard:

```
┌─────────────────────────────────────────────┐
│ AI Clinical Review                          │
├─────────────────────────────────────────────┤
│ Case #1042                                  │
│                                             │
│ Condition                                   │
│ Diagnosis                                   │
│                                             │
│ AI Clinical Report                          │
│                                             │
│ [Doctor Comments]                           │
│                                             │
│ [Edit Diagnosis]                             │
│ [Edit Report]                                │
│                                             │
│ [Approve]       [Reject]                    │
└─────────────────────────────────────────────┘
```

## Report Dashboard

Left side: report queue.

```
Reports
──────────────
Case #1054
Case #1053
Case #1052
Case #1051
Case #1050
```

Clicking one opens:

```
Case
↓
Patient information
↓
Symptoms
↓
AI reasoning
↓
Diagnosis
↓
Investigations
↓
Results
↓
Final report
↓
Physician review
```

## Human Feedback

Never overwrite the original AI report. Store:

```
AI Original Report
        +
Physician Corrected Report
        +
Physician Feedback
        +
Approval/Rejection
```

The difference between the two becomes valuable training/evaluation data.

## Feedback Types (structured, not just free text)

- **Diagnosis**: Correct / Partially correct / Incorrect
- **Reasoning**: Correct / Missing evidence / Incorrect reasoning / Unsupported conclusion
- **Investigation**: Appropriate / Unnecessary / Missing test / Wrong test
- **Treatment**: Appropriate / Inappropriate / Missing intervention
- **Report**: Complete / Incomplete / Incorrect

This gives much better training data.
