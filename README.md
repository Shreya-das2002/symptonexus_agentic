# SymptoNexus Agentic AI Backend

A Python FastAPI backend for your **doctor–patient booking platform** with an **offline symptom-check chatbot**.

## What this backend does

1. Connects to a PostgreSQL database through `DATABASE_URL`
2. Reads doctor specialization from `domain_lookups`
3. Reads doctor profile data from:
   - `doctors`
   - `doctor_details`
   - `doctor_specializations`
4. Calls the configured **Qwen chat API**
5. Uses an **agent loop with tools** so the model can:
   - infer symptom intent
   - map symptoms to specialization
   - search matching doctors from DB
   - respond politely and safely

## Model

Default model: `qwen3.6:27b`. You can change the endpoint, API key, model, and timeout in `.env`.

## Install

```bash
cd symptonexus_agentic_backend
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Configure env

```bash
cp .env.example .env
```

Set `QWEN_API_KEY` in `.env` to the bearer token provided by your Qwen API service. Do not commit this token.

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
