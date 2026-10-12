# AI Virtual Hospital (AI-VH) — Model Setup, Security & Secrets Guide

This document provides instructions for acquiring, provisioning, protecting, and executing the AI models and clinical knowledge vectors utilized by the **AI Virtual Hospital (AI-VH)** platform.

---

## 1. Architectural Model Overview

AI-VH operates a hybrid on-device / cloud-deliberation multi-agent architecture:

| Component | Architecture | Default Location | Primary Function |
|---|---|---|---|
| **MedGemma 4B** | Google MedGemma (4B, NF4 4-bit) | `./MedGemma Model/model/` | Local clinical reasoning, differential diagnosis, intake triage |
| **MedGemma DPO LoRA** | LoRA Adapter (Rank 16, Alpha 32) | `./models/medgemma-dpo-lora/` | Aligned policy trained on physician attestation feedback |
| **NVIDIA Nemotron** | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | Nebius AI Studio API | Multi-agent deliberation synthesis & clinical report drafting |
| **Medical RAG Vector Index** | Dense embeddings (Chroma / NumPy) | `./data/knowledge/` | Semantic retrieval across 47,000+ indexed textbook passages |

---

## 2. Why Model Weights Are Excluded from Git

In accordance with standard ML engineering best practices and hackathon submission guidelines:
- Large binary weights (`.safetensors`, `.bin`, `.pt`, `.gguf`) range from **2.5 GB to 8.0+ GB** in size.
- GitHub enforces a strict **100 MB per-file limit** and recommends keeping repositories under **1 GB total**.
- Committing binary weights inflates clone times and bloats repository history.
- The repository tracks **all architecture configurations, tokenizer settings, LoRA adapter configs (`adapter_config.json`), inference pipelines, and evaluation harnesses**. Weights are provisioned separately as described below.

---

## 3. Model Setup Instructions

### 3.1 Local MedGemma 4B Setup

To run MedGemma locally on GPU hardware (e.g., NVIDIA RTX 4060 with 8GB VRAM):

1. **Request Access / Download Weights**:
   - MedGemma weights can be obtained from the official Hugging Face repository:
     ```bash
     # Install HuggingFace CLI
     pip install huggingface_hub
     
     # Download model weights into project structure
     huggingface-cli download google/medgemma-4b --local-dir "./MedGemma Model/model"
     ```
   - Alternatively, place pre-quantized 4-bit NF4 weights or GGUF files directly into:
     ```
     AI-VH/
     └── MedGemma Model/
         └── model/
             ├── config.json
             ├── model.safetensors (or model-*.safetensors shards)
             ├── tokenizer.json
             └── tokenizer_config.json
     ```

2. **Verify Local Inference**:
   Execute the included on-device verification harness:
   ```bash
   python "MedGemma Model/test_inference.py"
   ```

### 3.2 DPO LoRA Policy Adapter (`models/medgemma-dpo-lora`)

The repository includes the full training hyperparameters, adapter config, and evaluation report:
- `adapter_config.json`: PEFT LoRA target modules (`q_proj`, `v_proj`, `k_proj`, `o_proj`), rank `16`, alpha `32`.
- `training_summary.json`: DPO loss convergence and KL divergence metrics.

To attach the binary LoRA weights:
1. Place the trained `adapter_model.safetensors` file into `./models/medgemma-dpo-lora/`.
2. When the backend starts, `backend/rl/evaluator.py` automatically detects and mounts the adapter onto the base model using Hugging Face `peft.PeftModel`.

### 3.3 NVIDIA Nemotron & Cloud Synthesis Setup

For real-time multi-agent deliberation and clinical report synthesis:
1. Register for an API key on **Nebius AI Studio** (or an OpenAI-compatible NVIDIA NIM endpoint).
2. Create your local `.env` configuration file from the template:
   ```bash
   cp .env.example .env
   ```
3. Set your API credentials in `.env`:
   ```ini
   NEBIUS_API_KEY=your_actual_nebius_api_key_here
   NEBIUS_BASE_URL=https://api.studio.nebius.ai/v1/
   NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
   ```

---

## 4. Security, Secrets & Privacy Protection

### 4.1 Strict Secrets Isolation

- **Never Commit `.env` Files**: The root `.gitignore` explicitly excludes all `.env`, `.env.*`, and `.env.local` files. Only the sanitized `.env.example` template is tracked.
- **Automated Secrets Pre-Flight Audit**: Run our pre-commit secret audit to verify no keys or credentials exist in tracked files:
  ```bash
  python scratch/audit_secrets.py
  ```
- **Environment Variable Fallback**: In production, pass credentials directly via operating system environment variables or container secrets:
  ```bash
  export NEBIUS_API_KEY="your-api-key"
  export SECRET_KEY="your-django-or-fastapi-jwt-secret"
  ```

### 4.2 Protecting Proprietary Weights & Clinical Knowledge

If deploying in a clinical hospital network or institutional cloud:
1. **Private Storage Buckets**: Store proprietary weights in private AWS S3, Google Cloud Storage, or Azure Blob containers with SSE-KMS encryption and IAM role-based access.
2. **Signed Download URLs**: Distribute weights to compute clusters via short-lived pre-signed URLs (e.g., 15-minute validity).
3. **SHA256 Integrity Verification**: Always verify checksums prior to loading weights into execution memory:
   ```bash
   sha256sum "./MedGemma Model/model/model.safetensors"
   ```
4. **VPC & Air-Gapped Operation**: For clinical patient privacy (HIPAA / GDPR compliance), the MedGemma 4B model runs entirely on-device without outbound internet access.

---

## 5. Quickstart Verification Checklist

Before running clinical evaluations, confirm:
- [x] `.env` is created from `.env.example` with valid credentials.
- [x] Python dependencies are installed (`pip install -r requirements.txt`).
- [x] Frontend dependencies are installed (`pnpm install` in `frontend/`).
- [x] Verify backend health: `python -m pytest tests/test_trajectory_graph_suite.py` passes 100%.
- [x] Verify frontend build: `pnpm run build` and `pnpm run lint` report 0 errors.
