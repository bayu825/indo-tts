import asyncio
import io
import tempfile
import os
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

# Daftar suara Bahasa Indonesia
INDONESIAN_VOICES = [
    {"id": "id-ID-ArdiNeural",   "name": "Ardi (Pria)",    "gender": "male"},
    {"id": "id-ID-GadisNeural",  "name": "Gadis (Wanita)", "gender": "female"},
]

# Suara tambahan yang bisa baca teks Indo dengan baik (English)
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


@app.get("/", response_class=HTMLResponse)
async def root():
    static_path = Path(__file__).parent / "index.html"
    return static_path.read_text(encoding="utf-8")


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

    # Pastikan voice valid
    all_voice_ids = [v["id"] for v in INDONESIAN_VOICES + EXTRA_VOICES]
    if voice not in all_voice_ids:
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="localhost", port=7860, reload=False)
