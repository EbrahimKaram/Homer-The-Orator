import edge_tts
from langdetect import detect, LangDetectException
import config

# Preferred voices for common languages. Any language not listed here
# will automatically use the first available edge-tts voice for that locale.
VOICE_MAP = {
    "ar": "ar-AE-HamdanNeural",
    "fr": "fr-FR-DeniseNeural",
    "en": "en-US-AvaMultilingualNeural",
}
_voice_list_cache = None

async def _get_voice_list():
    """Fetch and cache the full edge-tts voice list."""
    global _voice_list_cache
    if _voice_list_cache is None:
        _voice_list_cache = await edge_tts.list_voices()
    return _voice_list_cache

async def detect_voice(text: str) -> str:
    """Detect the language of the text and return the appropriate edge-tts voice."""
    try:
        lang = detect(text)
    except LangDetectException:
        return config.DEFAULT_VOICE

    if lang in VOICE_MAP:
        return VOICE_MAP[lang]

    # Language not in VOICE_MAP — find the first available voice for it
    voices = await _get_voice_list()
    for voice in voices:
        if voice["Locale"].lower().startswith(lang.lower() + "-"):
            print(f"Auto-selected voice '{voice['ShortName']}' for detected language '{lang}'")
            return voice["ShortName"]

    print(f"No voice found for language '{lang}', falling back to default")
    return config.DEFAULT_VOICE

async def generate_wav(text: str, output_path: str, voice: str = None, progress_callback=None):
    """
    Generate audio from text and save as an MP3 file using edge-tts.
    Auto-detects language if no voice is specified.
    """
    if voice is None:
        voice = await detect_voice(text)

    communicate = edge_tts.Communicate(text, voice)
    chunk_count = 0

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
                chunk_count += 1
                if progress_callback and chunk_count % 10 == 0:
                    await progress_callback(chunk_count)

    return output_path