# Telegram Text-To-Voice Bot 🎙️

A Telegram bot that converts text or article URLs into voice notes. Send it a block of text or a link and it replies with a native Telegram voice message.

- **Language auto-detection** — Arabic, French, English, and any other language supported by Microsoft Edge TTS are handled automatically.
- **No local models** — speech is generated via [edge-tts](https://github.com/rany2/edge-tts), which uses Microsoft's neural TTS voices over the internet.
- **Article extraction** — paste any URL and it strips out the readable content using `trafilatura`.
- **Adjustable speed** — use `/speed` to switch between Slow / Normal / Fast / Very Fast.

## Prerequisites

### Linux / Raspberry Pi
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### Windows
Install [ffmpeg](https://ffmpeg.org/download.html) and ensure it is on your `PATH` (or install via WinGet: `winget install ffmpeg`).

## Setup

1. **Create a virtual environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate      # Linux/macOS
    .venv\Scripts\Activate.ps1     # Windows PowerShell
    ```

2. **Install Python packages**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set your bot token**
    ```bash
    export BOT_TOKEN=your_token_here          # Linux/macOS
    $env:BOT_TOKEN = "your_token_here"        # Windows PowerShell
    ```
    Get your token from [@BotFather](https://t.me/BotFather).

## Configuration (`config.py`)

| Setting | Description |
|---|---|
| `BOT_TOKEN` | Read from the `BOT_TOKEN` environment variable |
| `ALLOWED_USERS` | List of Telegram user IDs allowed to use the bot. Set to `[]` to allow everyone |
| `DEFAULT_VOICE` | Fallback edge-tts voice when language detection fails |
| `DEFAULT_SPEED` | Default playback rate: `"-25%"` slow · `"+0%"` normal · `"+25%"` fast · `"+50%"` very fast |

To find your Telegram user ID, message [@userinfobot](https://t.me/userinfobot).

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Show the welcome message |
| `/speed` | Open the speed selector (inline keyboard) |

## Running the Bot

**Manual start:**
```bash
python bot.py
```

**Auto-start via systemd (Linux/Pi):**

1. Create a service file:
    ```bash
    sudo nano /etc/systemd/system/telegram-tts.service
    ```
2. Add the following (adjust paths for your setup):
    ```ini
    [Unit]
    Description=Telegram TTS Bot
    After=network.target

    [Service]
    User=pi
    WorkingDirectory=/home/pi/Text-To-Voice
    Environment=BOT_TOKEN=your_token_here
    ExecStart=/home/pi/Text-To-Voice/.venv/bin/python bot.py
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```
3. Enable and start:
    ```bash
    sudo systemctl enable telegram-tts.service
    sudo systemctl start telegram-tts.service
    ```