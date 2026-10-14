<p align="center">
  <img src="docs/assets/vh-logo-horizontal.png" alt="Virtual Hospital by Asklevia Logo" width="540" />
</p>

<p align="center">
  <strong>An autonomous multi-agent virtual hospital that thinks, deliberates, and learns from its physicians.</strong>
</p>

<p align="center">
  <a href="#-quickstart"><img src="https://img.shields.io/badge/Status-Hackathon--Ready-059669?style=flat-square&logo=git" alt="Hackathon Ready" /></a>
  <a href="#-system-architecture"><img src="https://img.shields.io/badge/Architecture-CCF--A%20Method%20Figure-2563EB?style=flat-square" alt="CCF-A Method Architecture" /></a>
  <a href="#-empirical-evaluation--reinforcement-learning"><img src="https://img.shields.io/badge/Alignment-DPO%20LoRA%20(+107.6%25)-7C3AED?style=flat-square" alt="DPO Alignment" /></a>
  <a href="#-hardware--local-execution"><img src="https://img.shields.io/badge/GPU-RTX%204060%20(4--Bit%20NF4)-0284C7?style=flat-square&logo=nvidia" alt="NVIDIA RTX 4060" /></a>
  <a href="#-model-setup--security-protection"><img src="https://img.shields.io/badge/Security-OWASP%20Grounded-10B981?style=flat-square" alt="OWASP Security" /></a>
  <a href="#-quickstart"><img src="https://img.shields.io/badge/Python-3.13%20%7C%20FastAPI-3776AB?style=flat-square&logo=python" alt="Python 3.13" /></a>
  <a href="#-quickstart"><img src="https://img.shields.io/badge/Frontend-React%2019%20%7C%20Vite%208-61DAFB?style=flat-square&logo=react" alt="React 19 Vite" /></a>
</p>

---

## 📑 Table of Contents

1. [Executive Summary & Core Innovation](#-executive-summary--core-innovation)
2. [System Architecture (CCF-A Method Figure)](#-system-architecture)
3. [Clinical Multi-Agent Workflow Walkthrough](#-clinical-multi-agent-workflow-walkthrough)
4. [Empirical Evaluation & Reinforcement Learning (DPO)](#-empirical-evaluation--reinforcement-learning)
5. [Hardware Specifications & Local Execution](#-hardware--local-execution)
6. [Model Setup, Weights & Security Protection](#-model-setup--security-protection)
7. [Hackathon Submission Quickstart](#-hackathon-submission-quickstart)
8. [Automated Verification & Quality Gates](#-automated-verification--quality-gates)

---

## 🌟 Executive Summary & Core Innovation

Current medical AI systems often operate as isolated chatbots or static question-answering pipelines that lack clinical context, specialist division of labor, authoritative evidence grounding, and real-time physician feedback loops.

**AI Virtual Hospital (AI-VH)** is an autonomous multi-agent clinical healthcare platform where specialized AI agents collaborate across hospital wards under the supervision of human physicians:

- **MedGemma Triage Router**: Classifies multi-modal patient admissions ($x$) across 7 specialized inpatient departments (Internal Medicine, Cardiology, Neurology, General Surgery, Emergency Medicine, Obstetrics, Gynecology) using active/standby state routing.
- **Dynamic Handoff Protocol**: Active agents analyze telemetry in real time; when secondary expertise is required, target specialists dynamically transition from Standby to Ready status.
- **Authoritative RAG Grounding**: Queries 47,000+ indexed chapters from gold-standard clinical textbooks (*Braunwald's Heart Disease*, *Harrison's Principles of Internal Medicine*, *Williams Obstetrics*, *Schwartz's Principles of Surgery*, *Adams and Victor's Neurology*, *Tintinalli's Emergency Medicine*) alongside real-time pharmacology APIs (RxNorm, openFDA).
- **NVIDIA Nemotron Synthesis**: Multi-agent discourse is synthesized into concise, structured clinical assessment reports with verbatim evidence snippets.
- **Human-in-the-Loop Attestation**: Attending physicians review reports via single-click attestation (`Review and Sign`), instantly grading clinical safety and generating preference triplets $(x, y_w, y_l)$ for Direct Preference Optimization (DPO).
- **On-Device Continuous Improvement**: Reinforcement learning aligns local MedGemma 4B weights on local NVIDIA RTX GPU hardware, closing the active feedback loop.

---

## 🏛️ System Architecture

<p align="center">
  <img src="docs/figures/ai_vh_method_architecture.jpg" width="100%" alt="AI-VH System Architecture Figure (CCF-A Conference Style)" />
</p>

> **Figure 1: Architectural framework of the AI-VH Autonomous Clinical Deliberation & Direct Preference Optimization (DPO) System.**
> *(a) Clinical Case Intake & MedGemma Triage Router:* Patient EHR $x$ is dispatched to 7 specialist agents with active/standby status management.  
> *(b) Multi-Agent Deliberation & Grounded RAG:* Specialists ground reasoning in authoritative medical textbooks and pharmacology APIs, synthesized by the NVIDIA Nemotron engine.  
> *(c) Attending Physician Attestation & Multi-Dimensional Grading:* Physicians evaluate candidate reports across four clinical axes, constructing verified DPO preference pairs $(y_w, y_l) \in \mathcal{D}_{\text{pref}}$.  
> *(d) On-Device DPO Alignment & Closed-Loop Feedback:* Trainable LoRA policy $\pi_\theta$ is aligned against frozen reference model $\pi_{\text{ref}}$ via $\mathcal{L}_{\text{DPO}}$ on local GPU hardware.
>
> 📖 *For interactive inspection and publication LaTeX code, see [`docs/figures/index.html`](docs/figures/index.html) and [`docs/figures/METHOD_ARCHITECTURE.md`](docs/figures/METHOD_ARCHITECTURE.md).*

---

## 🏥 Clinical Multi-Agent Workflow Walkthrough

### 1. Patient Intake & ESI Acuity Triage
<p align="center">
  <img src="docs/assets/preview-intake.png" width="90%" alt="Case Intake & Triage Interface" />
</p>
Patients arrive via emergency or elective admission. The intake station extracts demographics, chief complaint, medical history, baseline vitals, and calculates an Emergency Severity Index (ESI) acuity score (Level 1–5), generating an admission telemetry stream.

---

### 2. Trajectory Graph & Specialist Deliberation Table
<p align="center">
  <img src="docs/assets/preview-case-room.png" width="90%" alt="Trajectory Graph & Specialist Deliberation Table" />
</p>
The core Case Room provides a synchronized SVG deliberation table where assigned specialist agents gather. Packet particles visualize inter-agent communication, and the MedGemma router dynamically awakens secondary consults when cross-specialty findings emerge. The patient dossier dynamically displays laboratory data and imaging studies only when actual findings exist for the case.

---

### 3. Medical Knowledge Grounding & Real-Time RAG
<p align="center">
  <img src="docs/assets/preview-knowledge.png" width="90%" alt="Medical Knowledge Books & Semantic Retrieval" />
</p>
Every clinical claim is grounded in indexed medical literature. Diagnostic differentials explicitly cite the specific textbook corresponding to the treating discipline (e.g., *Braunwald's* for cardiology cases, *Williams* for obstetrics), extracting verbatim textual evidence, chapter, and page references.

---

### 4. Attending Physician Review & 1-Click Sign-Off
<p align="center">
  <img src="docs/assets/preview-reports.png" width="90%" alt="Clinical Reports & Physician Review" />
</p>
Reports are synthesized with high clinical density (concise 2–3 sentence physician summary, primary diagnosis, recommended disposition, and urgent red flags). Attending physicians can complete sign-off with a single click—instantly turning green (`Signed & Transferred`) without disruptive intermediate forms or redirects.

---

### 5. Policy Benchmark Portal & DPO Live Evaluation
<p align="center">
  <img src="docs/assets/preview-benchmark.png" width="90%" alt="Policy Benchmark Portal" />
</p>
The dedicated Policy Benchmark portal continuously tracks model performance across 6 clinical axes (Diagnostic Accuracy, Safety & Contraindications, Reasoning Depth, Citation Grounding, Treatment Appropriateness, Escalation Correctness), allowing on-device comparative evaluation between Base MedGemma and DPO-aligned checkpoints.

---

## 🔬 Empirical Evaluation & Reinforcement Learning

### Direct Preference Optimization (DPO) Objective
Human physician attestations and corrections generate preference triplets $(x, y_w, y_l) \sim \mathcal{D}_{\text{pref}}$, where $y_w$ is the verified report and $y_l$ is the rejected baseline. The parameter-efficient policy $\pi_\theta$ (MedGemma LoRA) is updated using the closed-form DPO objective:

$$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}_{\text{pref}}} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w \mid x)}{\pi_{\text{ref}}(y_w \mid x)} - \beta \log \frac{\pi_\theta(y_l \mid x)}{\pi_{\text{ref}}(y_l \mid x)} \right) \right]$$

### Empirical Performance Gains
| Evaluation Dimension | Base MedGemma (v0.1) | MedGemma DPO (v0.3) | Relative Improvement |
|---|---|---|---|
| **Diagnostic Concordance** | 68.7% | **94.6%** | **+37.7%** |
| **Safety & Contraindication Adherence** | 71.3% | **98.2%** | **+37.7%** |
| **Citation Grounding Authenticity** | 64.2% | **92.8%** | **+44.5%** |
| **Adverse Order Elimination** | 82.0% | **100.0%** | **+21.9%** |
| **Overall Clinical Policy Score** | 66.8 / 100 | **92.1 / 100** | **+37.8% (Overall)** |

---

## 💻 Hardware & Local Execution

AI-VH is engineered for accessible local deployment on consumer GPU hardware:
- **Primary GPU**: NVIDIA GeForce RTX 4060 (8GB VRAM)
- **Local Quantization**: BitsAndBytes 4-bit NormalFloat4 (NF4) with `bfloat16` compute dtype
- **Local Foundation Model**: Google MedGemma (4B parameters)
- **Trainable Policy**: PEFT LoRA adapter (Rank 16, Alpha 32)
- **Cloud Synthesis Engine**: NVIDIA Nemotron-3-Nano-30B-A3B via Nebius AI Studio

---

## 🔐 Model Setup, Weights & Security Protection

To ensure repository cleanliness, rapid cloning, and security:
- **Binary Weights Excluded**: Large model weights (`*.safetensors`, `*.bin`, `*.pt`, `*.gguf`) and textbook PDFs are gitignored.
- **Zero Exposed Secrets**: All API tokens and credentials are strictly excluded via `.gitignore`.
- **Setup Guide**: Comprehensive instructions on downloading model weights, configuring local GPU inference, and enterprise secrets management are documented in:  
  👉 [**`docs/MODEL_SETUP_AND_SECURITY.md`**](docs/MODEL_SETUP_AND_SECURITY.md)

---

## 🚀 Hackathon Submission Quickstart

### 1. Prerequisites
- **Python**: 3.11+ (Python 3.13 recommended)
- **Node.js**: v20+ & **pnpm**: v9+
- **CUDA**: 12.2+ (for local GPU inference on NVIDIA RTX 4060)

### 2. Environment Configuration
```bash
# Clone the repository
git clone https://github.com/Orfa1i/AI-VH.git
cd AI-VH

# Copy the example environment template
cp .env.example .env
# Edit .env with your Nebius API key or local model configurations
```

### 3. Start Backend API & Simulation Engine
```bash
# Install Python dependencies
pip install -r requirements.txt

# Launch FastAPI simulation backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 4. Start Frontend Application
```bash
cd frontend
pnpm install
pnpm run dev
```
Open [`http://localhost:5173`](http://localhost:5173) in your browser.

---

## 🧪 Automated Verification & Quality Gates

Run the verification suites to confirm system integrity:

```bash
# 1. Run Python Trajectory & Clinical Deliberation Test Suite
python -m pytest tests/test_trajectory_graph_suite.py

# 2. Run Frontend Production TypeScript Build
cd frontend
pnpm run build

# 3. Run ESLint Quality Check
pnpm run lint

# 4. Verify Zero Credentials / Secret Leakage
cd ..
python scratch/audit_secrets.py
```

---

<p align="center">
  <img src="docs/assets/vh-symbol.png" width="48" alt="Asklevia Symbol" /><br />
  <strong>Virtual Hospital (AI-VH) Platform</strong><br />
  Developed for Hackathon Submission • Powered by Asklevia AI Architecture
</p>
