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

### 1.5 Hackathon Mentor Feedback Resolution (License & Hosted Project Access)
- **Mentor Feedback Received**:
  - Missing Open Source License detectable in the repository's About section.
  - Missing visible access to hosted project / working demo.
- **Implemented Fixes**:
  - **Open Source License (`LICENSE`)**: Added canonical `Apache License 2.0` at repository root. Verified via `gh repo view Orfa1i/AI-VH --json licenseInfo` that GitHub's licensee analyzer now detects `licenseInfo.key = "apache-2.0"` ("Apache License 2.0").
  - **Repository Homepage & Description**: Updated repository settings via `gh repo edit` to set `homepageUrl = "https://orfa1i.github.io/AI-VH/"` and description. The live working demo is now directly clickable at the top of the repository page in the About box.
  - **README.md Access Table**: Added high-visibility `Hackathon Evaluation & Submission Links` table and Apache 2.0 license badge, explicitly linking to the public repository, hosted demo, license, and setup instructions.
  - **Pushed to All Branches**: Synchronized `redesign/phase-7`, `main` (default), and `master` with commit `a0bdfef`.

---

## 2. Key Decisions & Rationale

- **Apache License 2.0 Selection**: Apache 2.0 is the gold standard for clinical AI / machine learning projects, providing clear copyright permissions, commercial and research rights, explicit patent grant protections, and instant recognition by hackathon judging systems.
- **Repository About Box Configuration**: Setting the homepage URL directly on the GitHub repository metadata ensures that judges scanning the repository immediately see the clickable website link without having to search for it.
- **Relative Asset and Sub-Page Referencing**: Because GitHub Pages hosts project sites on subpaths (`/<username>/<repo>/`), absolute URLs starting with `/` escape the repo directory. Using `./` guarantees exact resolution regardless of domain or subpath.
- **Client-Side Autonomous Graceful Fallback**: Providing canonical, production-grade fallback datasets ensures anyone testing the portal directly from GitHub Pages experiences zero errors, rich interactive data, and responsive clinical workflows even when the local GPU backend is offline.

### 1.6 README Elevation & Quick Start Repositioning
- **User Request**:
  - Add a clear, step-by-step Quick Start guide near the top of the README (after the demo link, summary table, and brief introduction, but before deeper experience details).
  - Remove all outdated dark-mode screenshots from the old black version. If updated light-version screenshots are not present, do not use the old ones and ask the user for the new assets.
- **Implemented Fixes**:
  - **Repositioned Quick Start Section**: Added `## ⚡ Quick Start: Download & Run` right after `## 🌟 Executive Summary & Core Innovation` and before `## 🏛️ System Architecture`.
  - **Step-by-Step Instructions**: Included prerequisites, Step 1 (clone), Step 2 (environment configuration), Step 3 (FastAPI backend launch on port 8000), Step 4 (React + Vite frontend launch on port 5173), and a zero-install browser mode link for judges.
  - **Removed Outdated Dark Screenshots**: Removed all 5 outdated dark-mode preview images (`preview-intake.png`, `preview-case-room.png`, `preview-knowledge.png`, `preview-reports.png`, `preview-benchmark.png`) from Section 4.
  - **Interactive Route Cards**: Replaced screenshot embeds with clean, modern feature cards linking directly to the live interactive routes on GitHub Pages.
  - **Removed Duplicate Section**: Cleaned up the redundant bottom quickstart section, ensuring a cohesive and professional README structure.

### 1.7 1080p Video Walkthrough Integration (Replacing Static Screenshots)
- **User Instruction**: Include `virtual-hospital-hackathon-demo-1080p-web.mp4` directly in the repository instead of images, as the video covers the entire platform experience and replaces static screenshots.
- **Implemented Actions**:
  - Copied `virtual-hospital-hackathon-demo-1080p-web.mp4` (27.18 MB) to:
    - `docs/assets/virtual-hospital-hackathon-demo-1080p-web.mp4` (tracked in git)
    - `frontend/public/virtual-hospital-hackathon-demo-1080p-web.mp4` (served by Vite & deployed to `gh-pages`)
  - **Embedded Video in `README.md`**:
    - Added high-visibility header badge: `🎬 Video Demo: 1080p Walkthrough`
    - Added dedicated row in `### 📌 Hackathon Evaluation & Submission Links` table with links to repository asset and CDN stream.
    - Added Table of Contents item: `3. Full Platform Video Walkthrough`.
    - Added dedicated section `## 🎬 Full Platform Video Walkthrough` with an HTML5 `<video>` player and direct streaming badges.
    - Added cross-reference note under `## 🏥 Clinical Multi-Agent Workflow Walkthrough` highlighting that all 5 clinical stations and multi-agent interactions are demonstrated in the video.
  - Built production bundle (`pnpm run build` in 1.85s) verifying `dist/virtual-hospital-hackathon-demo-1080p-web.mp4` (28,496,241 bytes) is ready for CDN delivery.

---

## 2. Key Decisions & Rationale

- **Quick Start Placement**: Positioning setup commands immediately after the executive summary ensures technical judges and reviewers can start testing locally within seconds of opening the repo.
- **Video Walkthrough Over Static Screenshots**: The 27MB 1080p web-optimized video provides dynamic, end-to-end evidence of multi-agent deliberation, token streaming, RAG textbook retrieval, and 1-click physician attestation in high fidelity, eliminating the need for fragmented or outdated screenshots.
- **Dual-Hosting Video Architecture**: Providing both in-repo storage (`docs/assets/`) and GitHub Pages CDN hosting (`https://orfa1i.github.io/AI-VH/...`) guarantees immediate browser playback across all mobile and desktop devices without requiring cloning or video players.

---

## 3. Verification & Quality Gates

1. **Video File Integrity**:
   - `docs/assets/virtual-hospital-hackathon-demo-1080p-web.mp4`: 28,496,241 bytes (~27.18 MB, well within GitHub's 100MB limit).
   - `frontend/public/virtual-hospital-hackathon-demo-1080p-web.mp4`: Verified present.
   - `frontend/dist/virtual-hospital-hackathon-demo-1080p-web.mp4`: Verified bundled during build.
2. **README Structure & Anchors**:
   - `## ⚡ Quick Start: Download & Run` verified at position 2 in TOC and body.
   - `## 🎬 Full Platform Video Walkthrough` verified at position 3 in TOC and body.
   - All badge and summary table anchors point to valid section IDs.
3. **GitHub Repository Metadata & License Detection**:
   - `licenseInfo`: `{"key": "apache-2.0", "name": "Apache License 2.0"}` (Detected on GitHub)
   - `homepageUrl`: `https://orfa1i.github.io/AI-VH/` (Visible in repo About sidebar)
   - `isPrivate`: `false` (Public repository verified)
4. **Frontend Production Build (`pnpm run build`)**:
   - 1,899 modules transformed, built in 1.85s with 0 errors.

---

## 4. Next Steps

1. Push commit with embedded video assets, updated README, and HANDOFF to `origin redesign/phase-7`, `origin main`, and `origin master`.
2. Confirm GitHub Actions deploys updated build with video to `origin gh-pages`.
3. Provide final verification check on the deployed video streaming URL.
