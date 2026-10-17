# Medical Triage Assistant (non-diagnostic) — Sarvam AI

Patient speaks, uploads audio, or types symptoms in an Indian language -> structured English note for the doctor
(symptoms, duration, severity, red flags, summary) + spoken read-back to the patient.

Uses Sarvam Saaras (STT), Sarvam-105B (structured note), Bulbul (TTS). Not a diagnostic tool.

## Run locally
    python -m venv .venv && .venv/bin/pip install -r requirements.txt
    echo "SARVAM_API_KEY=your_key" > .env
    .venv/bin/uvicorn app:app --reload

## Deploy
Render: New -> Web Service -> connect this repo (render.yaml is picked up), set `SARVAM_API_KEY`.
