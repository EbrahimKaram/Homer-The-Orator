import os
import tempfile
import time
import uuid
from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes, Application
)

import config
import extractor
import tts
import converter

SPEED_OPTIONS = [
    ("🐢 Slow",      "-25%"),
    ("🚶 Normal",    "+0%"),
    ("🏃 Fast",      "+25%"),
    ("⚡ Very Fast", "+50%"),
]


def _speed_keyboard(current: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{'✅ ' if rate == current else ''}{label}",
            callback_data=f"speed:{rate}"
        )]
        for label, rate in SPEED_OPTIONS
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config.ALLOWED_USERS and update.effective_user.id not in config.ALLOWED_USERS:
        return
    await update.message.reply_text(
        "👋 Hi! Send me some text or an article link and I'll read it to you as a voice note!\n\n"
        "/speed — change reading speed\n"
        "/myid — get your Telegram user ID\n"
        "/start — show this message"
    )


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if config.ALLOWED_USERS:
        status = "✅ You are in the allowed users list." if user.id in config.ALLOWED_USERS else "❌ You are not in the allowed users list."
    else:
        status = "✅ Access is open to everyone."
    await update.message.reply_text(
        f"🔑 Your Telegram User ID is:\n\n<code>{user.id}</code>\n\n{status}",
        parse_mode="HTML"
    )


async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config.ALLOWED_USERS and update.effective_user.id not in config.ALLOWED_USERS:
        return
    current = context.user_data.get("speed", config.DEFAULT_SPEED)
    await update.message.reply_text(
        "🎚 Select reading speed:",
        reply_markup=_speed_keyboard(current)
    )


async def speed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rate = query.data.split(":", 1)[1]
    context.user_data["speed"] = rate
    label = next((lbl for lbl, r in SPEED_OPTIONS if r == rate), rate)
    await query.edit_message_text(
        f"🎚 Select reading speed:\n\nNow set to: {label}",
        reply_markup=_speed_keyboard(rate)
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if config.ALLOWED_USERS and user_id not in config.ALLOWED_USERS:
        print(f"Unauthorized access attempt from user {user_id}")
        return

    input_text = update.message.text
    if not input_text:
        return

    unique_id = uuid.uuid4()
    tmp_dir = tempfile.gettempdir()
    mp3_path = os.path.join(tmp_dir, f"homer_{unique_id}.mp3")
    ogg_path = os.path.join(tmp_dir, f"homer_{unique_id}.ogg")
    speed = context.user_data.get("speed", config.DEFAULT_SPEED)

    status_message = await update.message.reply_text("⏳ Processing...")

    try:
        # 1. Extraction
        if extractor.is_url(input_text):
            await status_message.edit_text("🔗 Article link detected — fetching text...")
            text_to_read = extractor.extract_text(input_text)
            if text_to_read.startswith("Error"):
                await status_message.edit_text(text_to_read)
                return
        else:
            await status_message.edit_text("📝 Text detected — detecting language...")
            text_to_read = input_text

        if len(text_to_read) < 2:
            await status_message.edit_text("Could not find enough text to read.")
            return

        # 2. Detect language & voice
        voice, lang = await tts.detect_voice(text_to_read)
        await status_message.edit_text(
            f"🗣 Language: {lang}  |  Voice: {voice}\n⏳ Generating audio..."
        )

        last_edit_time = time.time()

        async def progress_callback(chunk_id):
            nonlocal last_edit_time
            if time.time() - last_edit_time > 3:
                try:
                    await status_message.edit_text(
                        f"🗣 Language: {lang}  |  Voice: {voice}\n⏳ Generating audio... ({chunk_id} chunks)"
                    )
                    last_edit_time = time.time()
                except Exception:
                    pass

        # 3. TTS Generation
        await tts.generate_wav(text_to_read, mp3_path, voice=voice, speed=speed, progress_callback=progress_callback)

        # 4. Convert to OGG
        success = await converter.convert_wav_to_ogg(mp3_path, ogg_path)

        if success and os.path.exists(ogg_path):
            with open(ogg_path, "rb") as voice_file:
                await update.message.reply_voice(voice=voice_file)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Failed to convert audio format.")

    except Exception as e:
        print(f"Error handling message: {e}")
        await status_message.edit_text("❌ An unexpected error occurred while generating speech.")

    finally:
        for f_path in [mp3_path, ogg_path]:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except Exception as e:
                    print(f"Failed to delete temp file {f_path}: {e}")


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start", "Show welcome message and instructions"),
        BotCommand("speed", "Change reading speed — Slow / Normal / Fast / Very Fast"),
        BotCommand("myid", "Get your Telegram user ID"),
    ])


if __name__ == "__main__":
    if not config.BOT_TOKEN:
        print("Please set the BOT_TOKEN environment variable.")
        exit(1)

    print("🚀 Starting Bot...")
    app = ApplicationBuilder().token(config.BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("speed", speed_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CallbackQueryHandler(speed_callback, pattern=r"^speed:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()