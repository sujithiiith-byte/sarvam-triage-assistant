"""Medical Triage Assistant (non-diagnostic) built on Sarvam AI.

Flow: native-language speech -> Saaras STT -> Sarvam-105B structured English note
      -> (optional) Bulbul TTS read-back to the patient in their own language.
"""
import base64
import json
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()
API = "https://api.sarvam.ai"
app = FastAPI(title="Sarvam Medical Triage Assistant")

LANGS = {
    "te-IN": "Telugu", "hi-IN": "Hindi", "ta-IN": "Tamil", "kn-IN": "Kannada",
    "ml-IN": "Malayalam", "bn-IN": "Bengali", "mr-IN": "Marathi",
    "gu-IN": "Gujarati", "pa-IN": "Punjabi", "od-IN": "Odia", "en-IN": "English",
}

SYSTEM_PROMPT = """You are a medical intake scribe, NOT a doctor. You never diagnose, never suggest \
medication or treatment. You convert a patient's own words into a structured note for a clinician.
The patient spoke {lang}. Output ONLY a JSON object with exactly these keys:
- "symptoms": list of short English strings, one per symptom
- "duration": English string (e.g. "3 days"), or "Not stated"
- "severity": one of "Mild", "Moderate", "Severe", "Not stated" - based only on what the patient said
- "other_details": English string with relevant context (triggers, medications mentioned, allergies, \
history), or "None"
- "red_flags": list of English strings for emergency warning signs the patient mentioned (e.g. chest pain, \
trouble breathing, fainting, heavy bleeding, stroke signs); empty list if none
- "summary_en": 2-3 sentence English summary for the doctor
- "followup_questions": up to 3 short questions in {lang} the clinician might ask next (patient-readable)
- "confirmation_native": one short sentence in {lang} reading back what you understood, \
ending by asking the patient if that is correct
Do not invent facts. If something is not stated, say "Not stated"."""


def headers() -> dict:
    key = os.getenv("SARVAM_API_KEY")
    if not key:
        raise HTTPException(500, "SARVAM_API_KEY is not set. Add it to .env")
    return {"api-subscription-key": key}


def check(r: httpx.Response, step: str):
    if r.status_code >= 400:
        raise HTTPException(502, f"{step} failed ({r.status_code}): {r.text[:300]}")


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), mode: str = Form("transcribe")):
    """Native speech -> text. Auto-detects language. REST limit: 30s of audio."""
    data = await audio.read()
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            f"{API}/speech-to-text",
            headers=headers(),
            data={"model": "saaras:v4", "mode": mode},
            files={"file": (audio.filename or "audio.webm", data, audio.content_type or "audio/webm")},
        )
    check(r, "Speech-to-text")
    j = r.json()
    return {"transcript": j.get("transcript", ""), "language_code": j.get("language_code")}


class ReportReq(BaseModel):
    transcript: str
    language_code: str | None = None


@app.post("/api/report")
async def report(req: ReportReq):
    """Native transcript -> structured English medical intake note (JSON)."""
    if not req.transcript.strip():
        raise HTTPException(400, "Empty transcript")
    lang = LANGS.get(req.language_code or "", "the patient's language")
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(
            f"{API}/v1/chat/completions",
            headers={**headers(), "Content-Type": "application/json"},
            json={
                "model": "sarvam-105b",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT.format(lang=lang)},
                    {"role": "user", "content": req.transcript},
                ],
                "temperature": 0.2,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"},
            },
        )
    check(r, "Report generation")
    content = r.json()["choices"][0]["message"].get("content") or ""
    m = re.search(r"\{.*\}", content, re.S)  # tolerate stray text around the JSON
    if not m:
        raise HTTPException(502, "Model returned no JSON; try again")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        raise HTTPException(502, "Model returned invalid JSON; try again")


class TTSReq(BaseModel):
    text: str
    language_code: str = "hi-IN"


@app.post("/api/speak")
async def speak(req: TTSReq):
    """Read the confirmation back to the patient in their language."""
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            f"{API}/text-to-speech",
            headers={**headers(), "Content-Type": "application/json"},
            json={
                "text": req.text[:2500],
                "language_code": req.language_code,
                "model": "bulbul:v4-flash",
                "speaker": "simran_en_customer",
            },
        )
    check(r, "Text-to-speech")
    return {"audio_b64": "".join(r.json()["audios"])}


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")
