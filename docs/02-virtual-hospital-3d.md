# 2. The Virtual Hospital (3D Layer)

## Scope discipline

The hospital should be a real interactive 3D environment, but do NOT start by building every hospital department. Start with a small but complete environment.

### Phase 1 Hospital — build:

- Reception
- Emergency Department
- Patient waiting area
- Examination rooms
- Nurse station
- Doctor station
- Radiology
- Laboratory
- Pharmacy
- Patient rooms
- Hospital corridor

### Later:

- ICU
- Operating room
- Pediatrics
- Obstetrics
- Internal medicine
- Cardiology
- Neurology
- Oncology
- Outpatient clinics
- Ambulance/emergency entrance

## How the 3D Hospital Should Work

The 3D environment is primarily the simulation/visualization layer. It should NOT contain the medical intelligence itself.

```
3D Doctor
    ↓
Agent ID: doctor_001
    ↓
Doctor Agent Backend
    ↓
Clinical reasoning
    ↓
Tools
    ↓
EHR / Lab / Radiology
```

The character you see walking around is simply the embodied representation of an AI agent. The agent's actual intelligence lives in the backend.

## Recommended 3D Technology

For the initial prototype:

**Frontend**
- React
- Next.js
- TypeScript
- Three.js
- React Three Fiber
- Drei

The hospital can initially use relatively simple 3D assets — no AAA-quality graphics needed. The important part: **the environment must accurately represent the clinical workflow.**

Later, if the project requires sophisticated simulation, consider:

- Unity
- Unreal Engine
- NVIDIA Omniverse

But don't start there unless the research requires high-fidelity simulation.
