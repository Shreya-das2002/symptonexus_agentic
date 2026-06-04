# SymptoNexus Agentic AI Backend

A Python FastAPI backend for your **doctor–patient booking platform** with an **offline symptom-check chatbot**.

## What this backend does

1. Connects to your local MySQL database:
   - host: `localhost`
   - user: `root`
   - password: `root`
   - db: `symptonexus`
2. Reads doctor specialization from `domain_lookups`
3. Reads doctor profile data from:
   - `doctors`
   - `doctor_details`
   - `doctor_specializations`
4. Runs a **local LLM via Ollama**
5. Uses an **agent loop with tools** so the model can:
   - infer symptom intent
   - map symptoms to specialization
   - search matching doctors from DB
   - respond politely and safely

## Recommended offline model

Default model in this project: `qwen2.5:3b`

You can change this in `.env`.

## Install

```bash
cd symptonexus_agentic_backend
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Start Ollama

Install and run Ollama locally, then pull a model:

```bash
ollama pull qwen2.5:3b
ollama serve
```

## Configure env

```bash
cp .env.example .env
```

## Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Main APIs

### Health
```bash
GET /health
```

### Get specializations
```bash
GET /api/specializations
```

### Search doctors
```bash
GET /api/doctors/search?specialization=Cardiologist
GET /api/doctors/search?category=skin
GET /api/doctors/search?query=diabetes
```

### Symptom chatbot
```bash
POST /api/chat/symptom-check
Content-Type: application/json

{
  "message": "I have itchy red skin rashes for three days",
  "conversation": []
}
```

## How the chatbot behaves

- polite and patient-friendly
- does **not** claim to be a real doctor
- suggests the **most relevant specialization**
- fetches doctors from DB
- encourages emergency care when symptoms sound severe
- keeps answers short, structured, and useful

## Important note

This is a **triage assistant**, not a diagnosis engine.
It helps route the patient toward the right doctor category and available doctor list.
