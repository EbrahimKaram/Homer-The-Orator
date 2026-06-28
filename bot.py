import os
import tempfile
import time
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import config
import extractor
import tts
import converter

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if config.ALLOWED_USERS and update.effective_user.id not in config.ALLOWED_USERS:
        return  # Ignore unauthorized users

    await update.message.reply_text(
        "👋 Hi! Send me some text or a link to an article, and I will read it to you as a voice note!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming messages, extract text, generate TTS, and send voice note."""
    user_id = update.effective_user.id

    # Access Control Check
    if config.ALLOWED_USERS and user_id not in config.ALLOWED_USERS:
        print(f"Unauthorized access attempt from user {user_id}")
        return  # Silently ignore

    input_text = update.message.text
    if not input_text:
        return

    # FIX 1 & 2: Define temp paths here (before try) so the finally block
    # can always reference them, even if an exception fires before they'd
    # otherwise have been assigned.
    unique_id = uuid.uuid4()
    tmp_dir = tempfile.gettempdir()
    mp3_path = os.path.join(tmp_dir, f"homer_{unique_id}.mp3")
    ogg_path = os.path.join(tmp_dir, f"homer_{unique_id}.ogg")

    status_message = await update.message.reply_text("⏳ Generating... (This might take a while for long text)")

    try:
        # 1. Extraction
        if extractor.is_url(input_text):
            text_to_read = extractor.extract_text(input_text)
            if text_to_read.startswith("Error"):
                await status_message.edit_text(text_to_read)
                return
        else:
            text_to_read = input_text

        if len(text_to_read) < 2:
            await status_message.edit_text("Could not find enough text to read.")
            return

        last_edit_time = time.time()

        async def progress_callback(chunk_id):
            nonlocal last_edit_time
            # Update Telegram at most once every 3 seconds to avoid rate limiting
            if time.time() - last_edit_time > 3:
                try:
                    await status_message.edit_text(f"⏳ Generating audio... (Processed {chunk_id} paragraphs/chunks)")
                    last_edit_time = time.time()
                except Exception:
                    pass

        # 2. TTS Generation
        await tts.generate_wav(text_to_read, mp3_path, progress_callback=progress_callback)

        # 3. Convert to OGG
        success = await converter.convert_wav_to_ogg(mp3_path, ogg_path)

        if success and os.path.exists(ogg_path):
            # 4. Send Voice Note
            with open(ogg_path, "rb") as voice_file:
                await update.message.reply_voice(voice=voice_file)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Failed to convert audio format.")

    except Exception as e:
        print(f"Error handling message: {e}")
        await status_message.edit_text("❌ An unexpected error occurred while generating speech.")

    finally:
        # Cleanup Temporary Files
        for f_path in [mp3_path, ogg_path]:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except Exception as e:
                    print(f"Failed to delete temp file {f_path}: {e}")

if __name__ == "__main__":
    if config.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not config.BOT_TOKEN:
        print("Please set your BOT_TOKEN in config.py")
        exit(1)

    print("🚀 Starting Bot...")
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()