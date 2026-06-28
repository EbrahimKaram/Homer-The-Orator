import asyncio
import re
import edge_tts
from langdetect import detect, LangDetectException
import config


def _split_text(text: str, max_chars: int = 500) -> list[str]:
    """Split text into segments at paragraph then sentence boundaries."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    chunks = []
    for para in paragraphs:
        if len(para) <= max_chars:
            chunks.append(para)
        else:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) + 1 <= max_chars:
                    current = f"{current} {sent}".strip() if current else sent
                else:
                    if current:
                        chunks.append(current)
                    current = sent
            if current:
                chunks.append(current)
    return chunks if chunks else [text]


_voice_list_cache = None

async def _get_voice_list():
    """Fetch and cache the full edge-tts voice list."""
    global _voice_list_cache
    if _voice_list_cache is None:
        _voice_list_cache = await edge_tts.list_voices()
    return _voice_list_cache

async def detect_voice(text: str) -> tuple[str, str]:
    """Detect the language of the text. Returns (voice_name, language_code)."""
    try:
        lang = detect(text)
    except LangDetectException:
        return config.DEFAULT_VOICE, "unknown"

    if lang in config.VOICE_MAP:
        return config.VOICE_MAP[lang], lang

    # Language not in VOICE_MAP — find the first available voice for it
    voices = await _get_voice_list()
    for voice in voices:
        if voice["Locale"].lower().startswith(lang.lower() + "-"):
            print(f"Auto-selected voice '{voice['ShortName']}' for detected language '{lang}'")
            return voice["ShortName"], lang

    print(f"No voice found for language '{lang}', falling back to default")
    return config.DEFAULT_VOICE, lang


async def generate_wav(text: str, output_path: str, voice: str = None, speed: str = "+0%", progress_callback=None):
    """
    Generate audio from text and save as an MP3 file using edge-tts.
    Segments are processed in parallel (capped by config.TTS_CONCURRENCY).
    Results are written to the output file in original text order.
    """
    if voice is None:
        voice, _ = await detect_voice(text)

    segments = _split_text(text)
    total = len(segments)
    semaphore = asyncio.Semaphore(config.TTS_CONCURRENCY)
    completed = 0

    async def process_segment(segment: str) -> bytes:
        nonlocal completed
        async with semaphore:
            communicate = edge_tts.Communicate(segment, voice, rate=speed)
            audio = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio.extend(chunk["data"])
        completed += 1
        if progress_callback:
            await progress_callback(completed, total)
        return bytes(audio)

    results = await asyncio.gather(*[process_segment(seg) for seg in segments])

    with open(output_path, "wb") as f:
        for audio_data in results:
            f.write(audio_data)

    return output_path