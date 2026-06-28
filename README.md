# Telegram Text-To-Voice Bot 🎙️

A Telegram bot built to run on a Raspberry Pi. It takes text or URLs, extracts the readable article using `trafilatura`, generates speech using the locally running `kokoro-onnx` TTS engine, and sends it back to you natively as a Telegram OGG Opus voice note via `ffmpeg`.

## Prerequisites (Raspberry Pi Setup)

1. **Update and Install Dependencies**
    You need `ffmpeg` for audio conversion and `espeak-ng` which Kokoro uses under the hood:
    ```bash
    sudo apt-get update
    sudo apt-get install -y ffmpeg libespeak-ng1
    ```

2. **Create a Virtual Environment**
    It's recommended to run this in an isolated Python environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. **Install Python Packages**
    ```bash
    pip install -r requirements.txt
    ```

4. **Download TTS Models**
    Run the included script to download the Kokoro ONNX model and the voice configurations:
    ```bash
    python download_models.py
    ```

## Configuration

Edit `config.py` to set up your bot:

- `BOT_TOKEN`: Get this from [@BotFather](https://t.me/BotFather) on Telegram.
- `ALLOWED_USERS`: A list of your Telegram User IDs. **Leave empty (`[]`) to allow anyone**, but since Kokoro is CPU heavy, adding your ID is highly recommended to prevent abuse. (You can find your ID using a bot like `@userinfobot`).
- `VOICE_NAME`: The default voice is `af_heart` (American Female). Other voices are available in Kokoro.

## Running the Bot

**Manual start:**
```bash
python bot.py
```

**Auto-Start via Systemd (Recommended for Pi):**
If you want the bot to run automatically on boot:

1. Create a service file: `sudo nano /etc/systemd/system/telegram-tts.service`
2. Add the following (adjust paths to match your setup):
    ```ini
    [Unit]
    Description=Telegram TTS Bot
    After=network.target

    [Service]
    User=pi
    WorkingDirectory=/home/pi/Text-To-Voice
    ExecStart=/home/pi/Text-To-Voice/.venv/bin/python bot.py
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```
3. Enable and start the service:
    ```bash
    sudo systemctl enable telegram-tts.service
    sudo systemctl start telegram-tts.service
    ```