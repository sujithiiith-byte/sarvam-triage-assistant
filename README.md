# Medical Triage Assistant (Non-Diagnostic)

> Patients often can't explain their symptoms in English. This app lets them **speak, upload audio, or type in their own language**, and gives the doctor a **structured English note**.

Built with [Sarvam AI](https://docs.sarvam.ai) for a hackathon.

**🔗 Live demo: https://sarvam-triage-assistant.onrender.com/** (free tier: the first load may take ~30 seconds to wake up)

> ⚠️ **Not a medical device and not a diagnostic tool.** It only records and translates what the patient says. It never diagnoses or recommends treatment. In an emergency, call your local emergency number.

## How it works

```
 Patient (Telugu, Hindi, Tamil, ...)
        │  voice / audio file / typed text
        ▼
 Sarvam Saaras (speech-to-text)      → transcript + detected language
        ▼
 Sarvam-105B (chat completion)       → structured JSON note
        ▼
 Doctor sees English note            Patient hears a read-back in their language
                                     (Sarvam Bulbul text-to-speech)
```

**Example:** Telugu *"నాకు మూడు రోజులుగా జ్వరం మరియు తీవ్రమైన తలనొప్పి ఉంది. ఛాతీలో కొద్దిగా నొప్పి కూడా ఉంది."* becomes:

| Field | Value |
|---|---|
| Symptoms | fever, severe headache, slight chest pain |
| Duration | 3 days |
| Severity | Severe |
| Red flags | chest pain |
| Summary | The patient reports three days of fever and severe headache, along with slight chest pain. |

## Features

- Three input modes: live microphone, audio file upload, or typed text
- Auto language detection for speech; language picker for typed text
- Structured note: symptoms, duration, severity, other details, red flags, summary
- The patient can edit the transcript before the note is generated
- Spoken read-back in the patient's language, to confirm the note is correct
- Copy-to-clipboard for the doctor's note
- Emergency red flags are highlighted

Supported languages: Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, English.

## Sarvam APIs used

| Step | Endpoint | Model |
|---|---|---|
| Speech to text | `POST /speech-to-text` | `saaras:v4` |
| Structured note | `POST /v1/chat/completions` | `sarvam-105b` |
| Read-back | `POST /text-to-speech` | `bulbul:v4-flash` |

## Run locally

You need Python 3.10+ and a Sarvam API key from the [Sarvam dashboard](https://dashboard.sarvam.ai).

```bash
git clone https://github.com/sujithiiith-byte/sarvam-triage-assistant.git
cd sarvam-triage-assistant
python -m venv .venv
.venv/bin/pip install -r requirements.txt     # Windows: .venv\Scripts\pip
echo "SARVAM_API_KEY=your_key_here" > .env
.venv/bin/uvicorn app:app --reload
```

Open http://localhost:8000.

The microphone only works on `localhost` or over HTTPS. Audio upload and typed text work anywhere.

## Deploy (Render)

1. Fork or clone this repo to your GitHub account.
2. On [render.com](https://render.com): **New → Blueprint** and pick the repo. `render.yaml` sets the build and start commands.
3. Add the environment variable `SARVAM_API_KEY`, then deploy.

Start command, if you set it by hand: `uvicorn app:app --host 0.0.0.0 --port $PORT`

The API key stays on the server and is never sent to the browser.

## Project layout

```
app.py              FastAPI backend (transcribe, report, speak endpoints)
static/index.html   Single-page frontend
render.yaml         Render deploy config
requirements.txt    Python dependencies
```

## Limitations

- Speech-to-text on the REST API accepts up to 30 seconds of audio per request.
- Severity is taken from what the patient says. The app does not assess it.
- The model can make mistakes, so a clinician must always verify the note with the patient.
- No data is stored. Nothing is saved on the server, but audio and text are sent to Sarvam's API for processing. Don't use real patient data without proper consent and compliance review.

## Ideas for next steps

- PDF export of the note
- Show the follow-up questions the model already generates
- Longer audio via Sarvam's batch speech API
- Streaming, real-time transcription

## License

[MIT](LICENSE)
