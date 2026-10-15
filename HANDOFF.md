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

---

## 2. Key Decisions & Rationale

- **GitHub Pages as Always-On Redundancy**: Cloudflare Quick Tunnels are transient and subject to session resets. Deploying to GitHub Pages provides an immutable 99.9% uptime static demonstration that judges, hackathon reviewers, and clinicians can open on their mobile phones at any time.
- **Client-Side Simulation Fallback**: Instead of letting static demo visitors see an empty case room when the backend API is disconnected, the frontend autonomously falls back to full local deliberation simulation.

---

## 3. Verification & Quality Gates

1. **GitHub Pages Live Status Check**:
   - `https://orfa1i.github.io/AI-VH/`: HTTP `200 OK` (983,545 bytes rendered).
   - `https://orfa1i.github.io/AI-VH/case-room.html`: HTTP `200 OK` (275,843 bytes rendered).
2. **Frontend Production Build (`pnpm run build`)**:
   - 1,899 modules transformed, built in 1.41s with 0 errors.
3. **Frontend Linter (`pnpm run lint`)**:
   - 0 errors across 75 files.
4. **Backend Test Suite (`py -3.13 -m pytest tests/test_trajectory_graph_suite.py`)**:
   - 4/4 passed in 15.61s (100% green).
5. **Git Branches Synchronized**:
   - `gh-pages`: Live static site
   - `main`: Default branch
   - `master`, `redesign/phase-7`: Synchronized

---

## 4. Next Steps

1. Review the live mobile demo on phone via `https://orfa1i.github.io/AI-VH/`.
2. Finalize submission links on Devpost with the GitHub Pages URL.
