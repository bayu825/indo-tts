import os
import tempfile
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
from pathlib import Path

app = FastAPI(title="Indo TTS - Text to Speech Bahasa Indonesia")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INDONESIAN_VOICES = [
    {"id": "id-ID-ArdiNeural",  "name": "Ardi (Pria)",    "gender": "male"},
    {"id": "id-ID-GadisNeural", "name": "Gadis (Wanita)", "gender": "female"},
]

EXTRA_VOICES = [
    {"id": "jv-ID-DimasNeural",   "name": "Dimas (Jawa - Pria)",   "gender": "male"},
    {"id": "jv-ID-SitiNeural",    "name": "Siti (Jawa - Wanita)",  "gender": "female"},
    {"id": "su-ID-JajangNeural",  "name": "Jajang (Sunda - Pria)", "gender": "male"},
    {"id": "su-ID-TutiNeural",    "name": "Tuti (Sunda - Wanita)", "gender": "female"},
    {"id": "en-US-AvaMultilingualNeural",   "name": "Ava (Multilingual - Wanita)",   "gender": "female"},
    {"id": "en-US-AndrewMultilingualNeural", "name": "Andrew (Multilingual - Pria)", "gender": "male"},
    {"id": "en-US-EmmaMultilingualNeural",  "name": "Emma (Multilingual - Wanita)",  "gender": "female"},
    {"id": "en-US-BrianMultilingualNeural", "name": "Brian (Multilingual - Pria)",   "gender": "male"},
]

ALL_VOICE_IDS = [v["id"] for v in INDONESIAN_VOICES + EXTRA_VOICES]


@app.get("/", response_class=HTMLResponse)
async def root():
    # Vercel structure: this file is in api/, index.html is in root
    static_path = Path(__file__).parent.parent / "index.html"
    return static_path.read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/voices")
async def get_voices():
    return JSONResponse({"indonesian": INDONESIAN_VOICES, "extra": EXTRA_VOICES})


@app.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    voice: str = Form("id-ID-ArdiNeural"),
    rate: str = Form("+0%"),
    pitch: str = Form("+0Hz"),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Teks tidak boleh kosong!")
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="Teks maksimal 5000 karakter!")
    if voice not in ALL_VOICE_IDS:
        voice = "id-ID-ArdiNeural"

    async def generate():
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    return StreamingResponse(
        generate(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=output.mp3"},
    )
