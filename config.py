import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token — set via environment variable: export BOT_TOKEN=your_token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# List of allowed Telegram User IDs (integers). Leave empty [] to allow everyone.
ALLOWED_USERS = [
    6822089746
]


# Preferred voices for common languages. Any language not listed here
# will automatically use the first available edge-tts voice for that locale.
VOICE_MAP = {
    "ar": "ar-AE-HamdanNeural",
    "fr": "fr-FR-DeniseNeural",
    "en": "en-US-AvaMultilingualNeural",
}


# Edge-TTS Configuration
DEFAULT_VOICE = "en-US-AriaNeural"  # Fallback voice (used when language detection fails)
DEFAULT_SPEED = "+0%"               # Playback rate: "-25%" slow, "+0%" normal, "+25%" fast, "+50%" very fast
# bf_isabella
# bf_lily
# British Male (bm_)

# bm_daniel
# bm_fable
# bm_george
# bm_lewis