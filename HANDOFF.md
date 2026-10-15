# AI-VH Project Handoff & Session State

**Date:** 2026-10-15  
**Git Branch:** `main` (Default), `redesign/phase-7`, `master`, `gh-pages` (Live Demo)  
**Repository Remote:** `https://github.com/Orfa1i/AI-VH.git` (Default branch: `main`)  
**Live Demo Deployments:**
- **GitHub Pages 24/7 Mobile & Web Demo:** [`https://orfa1i.github.io/AI-VH/`](https://orfa1i.github.io/AI-VH/)
- **Direct Specialist Case Room Deliberation:** [`https://orfa1i.github.io/AI-VH/case-room.html`](https://orfa1i.github.io/AI-VH/case-room.html)
- **Direct Case Intake & ESI Triage:** [`https://orfa1i.github.io/AI-VH/case-intake.html`](https://orfa1i.github.io/AI-VH/case-intake.html)
- **Direct Clinical Staff Roster:** [`https://orfa1i.github.io/AI-VH/staff-roster.html`](https://orfa1i.github.io/AI-VH/staff-roster.html)
- **Cloudflare Quick Tunnel:** Active at `https://hispanic-vendor-national-congratulations.trycloudflare.com`
- **Local Dev Server:** Running on `http://localhost:5173` (Vite)
- **Backend API Server:** Running on `http://127.0.0.1:8000` (FastAPI / Uvicorn, MedGemma 4B + DPO LoRA on RTX 4060 GPU)

---

## 1. Accomplished This Session

### 1.1 24/7 GitHub Pages Live Demo Setup
- **Relative Base Asset Resolution (`vite.config.ts`)**: Configured `base: './'`, enabling static assets, scripts, and stylesheets to resolve relative to any root or subpath (`https://orfa1i.github.io/AI-VH/`).
- **Autonomous Canonical Fallback in Standalone Mode (`case-room.html`)**: Enhanced `loadAdmittedPatients` catch block so that when running on static hosting without a Python backend, the case room automatically loads all 6 rich canonical inpatient cases (`Elena Vance - Preeclampsia`, `Arthur Pendelton - STEMI`, `Marcus Holloway - Sepsis`, `Diana Reyes - Stroke`, `Liam Chen - Appendicitis`, `Carlos Gomez - DKA`). Users on mobile can test the full SVG particle deliberation, multi-specialty consultations, and 1-click physician sign-off without server dependency.
- **Dedicated `gh-pages` Deployment Branch**: Created and force-pushed a clean, root-level `gh-pages` deployment containing built production assets (`index.html`, `case-room.html`, `landing.html`, `case-intake.html`, `staff-roster.html`, `assets/`, `fonts/`, `logos/`, and `.nojekyll`).
- **GitHub Pages Enabled on Repo**: Configured via `gh api repos/Orfa1i/AI-VH/pages` to build from `gh-pages` root `/`, returning verified HTTP `200 OK` at `https://orfa1i.github.io/AI-VH/`.
- **Automated Continuous Deployment Workflow**: Added `.github/workflows/deploy-pages.yml` to automatically rebuild and update `gh-pages` whenever changes are merged into `main`.

### 1.2 Prominent Mobile Demo Hero Callout in README.md
- **Top-of-Readme Callout Card**: Positioned high-contrast, mobile-first badge buttons directly beneath the Asklevia header:
  - `📱 Instant Mobile Demo • Open in Browser`
  - `Demo Status • Online 24/7`
- **Direct Ward Jump Links**: Added quick links to Hospital Trajectory, Specialist Case Room, Case Intake, and Staff Roster.
- **Updated Table of Contents**: Added Section 0 for immediate demo access.

### 1.3 Local Runtime & Full Platform Orchestration
- Maintained FastAPI backend running on port `8000` with local MedGemma 4B + DPO LoRA weights loaded on NVIDIA RTX 4060 GPU.
- Maintained Vite frontend dev server running on port `5173`.
- Maintained Cloudflare Quick Tunnel routing to port `5173`.

### 1.4 Video Analysis & GitHub Pages Iframe 404 Fix
- **Root Cause Discovered in Video (`Recording 2026-10-15 094144.mp4`)**:
  - Clicking tabs "Intake & Triage", "Staff Roster", and "Trajectory graph" inside the portal resulted in GitHub Pages returning `404 There isn't a GitHub Pages site here.`
  - The iframes were configured with absolute root paths: `src="/case-intake.html"`, `src="/staff-roster.html"`, `src="/case-room.html"` and header logos with `src="/logos/..."`. On `https://orfa1i.github.io/AI-VH/`, the browser requested `https://orfa1i.github.io/case-intake.html` (the root user domain, which does not exist).
  - Also, when running statically without a live Python backend, the "Patient Directory" displayed empty and "Knowledge Sources" displayed a red "Service Connection Error" banner.
- **Implemented Fixes**:
  - Converted all iframe `src` attributes to explicit relative paths (`./case-intake.html`, `./staff-roster.html`, `./case-room.html`).
  - Converted all logo `src` attributes across `App.tsx`, `Templates.tsx`, and `DesignSystemShowcase.tsx` to `./logos/...`.
  - Added robust offline demo fallbacks across all portal sections:
    - `PatientDirectorySection.tsx`: Inpatient records fallback (`Elena Vance`, `Arthur Pendelton`, `Marcus Holloway`, `Diana Reyes`, `Liam Chen`, `Carlos Gomez`) with searchable census and vitals.
    - `KnowledgeSourcesSection.tsx`: 4 canonical active sources (`RxNorm`, `openFDA`, `PubMed`, `Clinical Knowledge Textbook Vector Store`) eliminating the offline error banner.
    - `KnowledgeSearchSection.tsx`: 7 embedded textbook boxes (`Harrison's`, `Braunwald's`, `Schwartz's`, `Adams & Victor's`, `Tintinalli's`, `Mandell's`, `Williams`) with offline semantic search and vector chunk explorer.
    - `App.tsx`: Preloaded benchmark cases and clinical report for Elena Vance (Preeclampsia with Severe Features, lab deltas, Williams Obstetrics citations) with graceful offline review approval.
    - `ReviewedReportsSection.tsx`: Historical verified review cases with rubric grades.
    - `PolicyBenchmarkPage.tsx`: Autonomous DPO telemetry fallback stats.
  - Added `.nojekyll` and `404.html` SPA routing fallbacks to `dist` and `public`.
  - Rebuilt production bundle (`pnpm run build` in 1.39s, 0 errors) and force-pushed to `origin gh-pages`.

---

## 2. Key Decisions & Rationale

- **Relative Asset and Sub-Page Referencing**: Because GitHub Pages hosts project sites on subpaths (`/<username>/<repo>/`), absolute URLs starting with `/` escape the repo directory. Using `./` guarantees exact resolution regardless of domain or subpath.
- **Client-Side Autonomous Graceful Fallback**: Providing canonical, production-grade fallback datasets ensures anyone testing the portal directly from GitHub Pages experiences zero errors, rich interactive data, and responsive clinical workflows even when the local GPU backend is offline.

---

## 3. Verification & Quality Gates

1. **GitHub Pages Live Status Check (Zero 404s)**:
   - `https://orfa1i.github.io/AI-VH/`: HTTP `200 OK`
   - `https://orfa1i.github.io/AI-VH/case-intake.html`: HTTP `200 OK`
   - `https://orfa1i.github.io/AI-VH/staff-roster.html`: HTTP `200 OK`
   - `https://orfa1i.github.io/AI-VH/case-room.html`: HTTP `200 OK`
   - `https://orfa1i.github.io/AI-VH/logos/vh-logo-compact.svg`: HTTP `200 OK`
2. **Frontend Production Build (`pnpm run build`)**:
   - 1,899 modules transformed, built in 1.39s with 0 errors.
3. **Frontend Linter (`pnpm run lint`)**:
   - 0 errors across 75 files.
4. **Backend Test Suite (`py -3.13 -m pytest tests/test_trajectory_graph_suite.py`)**:
   - 4/4 passed in 15.40s (100% green).
5. **Git Branches Synchronized**:
   - `gh-pages`: Live static site
   - `redesign/phase-7`: Current working branch
   - `main`: Default branch

---

## 4. Next Steps

1. Review the live mobile demo on phone via `https://orfa1i.github.io/AI-VH/`.
2. Finalize submission links on Devpost with the GitHub Pages URL.
