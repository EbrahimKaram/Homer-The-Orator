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
    Auto-detects language/voice if voice is not specified.
    speed: edge-tts rate string e.g. "+0%", "-25%", "+50%"
    progress_callback(current, total): called after each segment is processed.
    """
    if voice is None:
        voice, _ = await detect_voice(text)

    segments = _split_text(text)
    total = len(segments)

    with open(output_path, "wb") as f:
        for i, segment in enumerate(segments, 1):
            communicate = edge_tts.Communicate(segment, voice, rate=speed)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
            if progress_callback:
                await progress_callback(i, total)

    return output_path