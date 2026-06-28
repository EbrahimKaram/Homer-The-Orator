import os

# Telegram Bot Token (get from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8989070141:AAEdKJHhTVQUR5t-yqirpkhSqP8bqyALx8o")

# List of allowed Telegram User IDs (integers). 
# Example: [123456789, 987654321]
ALLOWED_USERS = [
    # Replace with your Telegram User ID
     6822089746
]

# Edge-TTS Configuration
DEFAULT_VOICE = "en-US-AriaNeural"  # Fallback voice (used when language detection fails)

# Temporary directory for audio processing
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)


# From bot fatherDone! 
# Congratulations on your new bot. You will find it at t.me/HomerTheOrator_bot. You can now add a description, about section and profile picture for your bot, see /help for a list of commands. By the way, when you've finished creating your cool bot, ping our Bot Support if you want a better username for it. Just make sure the bot is fully operational before you do this.

# Use this token to access the HTTP API:
# 8989070141:AAEdKJHhTVQUR5t-yqirpkhSqP8bqyALx8o
# Keep your token secure and store it safely, it can be used by anyone to control your bot.

# For a description of the Bot API, see this page: https://core.telegram.org/bots/api


# Possible voices
# American Female (af_)

# af_alloy
# af_aoede
# af_bella
# af_heart (Your current default)
# af_jessica
# af_kore
# af_nicole
# af_nova
# af_river
# af_sarah
# af_sky


# American Male (am_)
# am_adam
# am_echo
# am_eric
# am_fenrir
# am_liam
# am_michael
# am_onyx
# am_puck
# am_santa
# British Female (bf_)

# bf_alice
# bf_emma
# bf_isabella
# bf_lily
# British Male (bm_)

# bm_daniel
# bm_fable
# bm_george
# bm_lewis