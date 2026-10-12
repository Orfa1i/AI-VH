# Virtual Hospital (AI-VH) System Architecture: Publication Method Specification

**Target Venue:** CCF-A Conference (CVPR / ICLR / NeurIPS / AAAI)  
**Figure Reference:** Figure 1 (Full-Width Two-Column Method Diagram)  
**Figure Asset:** [`docs/figures/ai_vh_method_architecture.jpg`](./ai_vh_method_architecture.jpg)  
**Interactive Viewer:** [`docs/figures/index.html`](./index.html)

---

## 1. Architectural Reasoning & Panel Decomposition

```
+-------------------------------------------------------------------------------------------------------------------------------------+
|                                              AI-VH SYSTEM ARCHITECTURE & DPO FEEDBACK LOOP                                          |
+------------------------------------+------------------------------------+------------------------------------+----------------------+
| (a) Case Intake & Triage Router    | (b) Deliberation & RAG Grounding   | (c) Physician Attestation Gate     | (d) On-Device DPO    |
|                                    |                                    |                                    |                      |
|  [Patient EHR x]                   |  [Active Specialist]               |         [Attending MD]             |  [Loss Function]     |
|   - Vitals & Labs                  |         │                          |               │                    |   L_DPO(π_θ; π_ref)  |
|   - Imaging Studies                |  [Medical Books / APIs]            |      [4-Axis Evaluation]           |        ▲       ▲     |
|         │                          |   (Braunwald, Harrison, RxNorm)    |       - Diagnosis   - Workup       |        │       │     |
|         ▼                          |         │                          |       - Reasoning   - Safety       |     Frozen  Trainable|
|  [MedGemma Router]                 |         ▼                          |               │                    |      π_ref     π_θ   |
|   P(specialty | x)                 |  [NVIDIA Nemotron Engine]          |               ▼                    |    (Base)    (LoRA)  |
|         │                          |         │                          |  [Preference Pairs (yw, yl)]       |        ▲             |
|         ▼                          |         ▼                          |               │                    |        │             |
|  7 Specialist Stations             |  Clinical Assessment Report y      |               ▼                    |        │             |
|  (IM, CA, NE, SU, EM, OB, GY)      |                                    |  DPO Preference Dataset D_pref ───►┴────────┘             |
+------------------------------------+------------------------------------+------------------------------------+----------------------+
  ▲                                                                                                                      │
  └─────────────────────────────────── Closed-Loop Policy Feedback Loop ─────────────────────────────────────────────────┘
```

---

## 2. Formal Mathematical Formulation

### 2.1 Multi-Modal Case Intake & Router Dispatch
Given a patient admission record $x = (x_{\text{dem}}, x_{\text{cc}}, x_{\text{vit}}, x_{\text{labs}}, x_{\text{img}}) \in \mathcal{X}$, the MedGemma routing network $\mathcal{M}_{\text{router}}$ computes the categorical posterior distribution over $K = 7$ specialist departments:

$$P(k \mid x) = \text{Softmax}\left( \mathbf{W}_r \cdot \phi_{\text{MedGemma}}(x) \right), \quad k \in \{\text{IM}, \text{CA}, \text{NE}, \text{SU}, \text{EM}, \text{OB}, \text{GY}\}$$

Specialists with $P(k \mid x) \ge \tau_{\text{active}}$ are placed in active deliberation, while non-assigned specialists transition to standby, subject to dynamic referral wake-up transitions.

### 2.2 Grounded Evidence Retrieval (RAG) & Nemotron Synthesis
For each active specialist $k$, semantic search retrieves verified chunks $\mathcal{C}_k = \{c_1, \dots, c_m\}$ from indexed textbook passages $\mathcal{K}_{\text{books}}$ and open pharmacology databases:

$$\text{sim}(q_k, c_i) = \frac{\mathbf{e}(q_k)^\top \mathbf{e}(c_i)}{\|\mathbf{e}(q_k)\|_2 \|\mathbf{e}(c_i)\|_2}$$

The multi-agent discourse is synthesized via the NVIDIA Nemotron engine $\mathcal{S}_{\text{Nemotron}}$ into candidate clinical report $y$:

$$y \sim \mathcal{S}_{\text{Nemotron}}(\cdot \mid x, \{q_k, \mathcal{C}_k\}_{k \in \mathcal{A}})$$

### 2.3 Direct Preference Optimization (DPO) Closed Loop
Human physicians review candidate reports under single-click attestation or multi-dimensional scoring along four clinical axes $\mathbf{s} = (s_{\text{diag}}, s_{\text{reas}}, s_{\text{work}}, s_{\text{safe}})$. High-concordance reports and physician corrections generate preference pairs $(x, y_w, y_l) \sim \mathcal{D}_{\text{pref}}$.

The parameter-efficient policy $\pi_\theta$ (MedGemma + LoRA) is updated on local RTX GPU hardware with the closed-form DPO objective:

$$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}_{\text{pref}}} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w \mid x)}{\pi_{\text{ref}}(y_w \mid x)} - \beta \log \frac{\pi_\theta(y_l \mid x)}{\pi_{\text{ref}}(y_l \mid x)} \right) \right]$$

where $\pi_{\text{ref}}$ is the frozen base model, $\sigma$ is the sigmoid function, and $\beta$ controls the KL penalty regularization.

---

## 3. LaTeX Figure Snippet (Ready for Submission)

```latex
\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{figures/ai_vh_method_architecture.jpg}
\caption{\textbf{System architecture of the Virtual Hospital (AI-VH) multi-agent clinical reasoning and direct preference optimization framework.} 
\textbf{(a) Clinical Case Intake \& MedGemma Triage Router:} Patient EHR data $x$ is ingested and routed via $\mathcal{M}_{\text{router}}$ across 7 specialist clinical agents with dynamic standby/active management.
\textbf{(b) Multi-Agent Deliberation \& Evidence Grounding (RAG):} Active specialists ground clinical reasoning in authoritative medical textbooks and pharmacology APIs, synthesized by the NVIDIA Nemotron engine into structured clinical reports $y$.
\textbf{(c) Attending Physician Attestation \& Multi-Dimensional Grading:} Attending physicians evaluate candidate reports along four clinical axes, constructing verified DPO preference pairs $(y_w, y_l) \in \mathcal{D}_{\text{pref}}$.
\textbf{(d) On-Device DPO Alignment \& Closed-Loop Feedback:} Trainable LoRA policy $\pi_\theta$ is aligned against frozen reference model $\pi_{\text{ref}}$ via $\mathcal{L}_{\text{DPO}}$ on local GPU hardware, completing the clinical self-improvement loop.}
\label{fig:ai_vh_architecture}
\end{figure*}
```
