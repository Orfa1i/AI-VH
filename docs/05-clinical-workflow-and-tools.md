# 5. Clinical Workflow, Tools, Communication & Event Bus

## Clinical Workflow (typical ER case)

```
Patient enters ER
       ↓
Nurse receives patient
       ↓
Vital signs collected
       ↓
Doctor notified
       ↓
Doctor interviews patient
       ↓
Doctor examines patient
       ↓
Doctor generates differential diagnosis
       ↓
Doctor orders laboratory tests
       ↓
Lab agent performs simulated test
       ↓
Results returned
       ↓
Doctor orders imaging
       ↓
Radiology agent processes study
       ↓
Results returned
       ↓
Doctor reassesses patient
       ↓
Final diagnosis
       ↓
Treatment plan
       ↓
Clinical report
```

This workflow is the heart of the project.

## Clinical Tools

Agents should interact with tools rather than simply generating text:

- `get_patient_history()`
- `get_vital_signs()`
- `order_lab_test()`
- `get_lab_result()`
- `order_imaging()`
- `get_radiology_result()`
- `check_medications()`
- `check_allergies()`
- `search_medical_knowledge()`
- `write_clinical_report()`
- `notify_nurse()`

This makes the agent an actual tool-using autonomous agent.

## Agent Communication

Agents need structured communication, e.g.:

- Doctor → Nurse: "Please obtain a repeat blood pressure and temperature."
- Nurse → Doctor: "BP: 88/55, Temp: 38.7°C."
- Doctor → Laboratory: "Order CBC and CRP."
- Laboratory → Doctor: "Results available."

Do not rely exclusively on free-form chat — use structured messages/events.

## Hospital Event Bus

Create an event system:

- `PATIENT_ARRIVED`
- `VITALS_UPDATED`
- `DOCTOR_ASSIGNED`
- `LAB_ORDERED`
- `LAB_RESULT_READY`
- `IMAGING_ORDERED`
- `IMAGING_RESULT_READY`
- `DIAGNOSIS_UPDATED`
- `TREATMENT_ORDERED`
- `PATIENT_DETERIORATED`
- `REPORT_COMPLETED`
- `REVIEW_COMPLETED`

This becomes the backbone of the simulation.
