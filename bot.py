import asyncio
import os
import tempfile
import time
import traceback
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

# Tracks the active generation task per user_id so /cancel can stop it
_active_tasks: dict[int, asyncio.Task] = {}


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
        "Commands:\n"
        "/speed — change reading speed\n"
        "/cancel — cancel current audio generation\n"
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


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if config.ALLOWED_USERS and update.effective_user.id not in config.ALLOWED_USERS:
        return
    user_id = update.effective_user.id
    task = _active_tasks.get(user_id)
    if task and not task.done():
        task.cancel()
    else:
        await update.message.reply_text("Nothing is currently being generated.")


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


async def _generate_and_send(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs the full extraction → TTS → send pipeline. Cancellable via asyncio task."""
    input_text = update.message.text

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

        async def progress_callback(current, total):
            nonlocal last_edit_time
            if time.time() - last_edit_time > 3:
                try:
                    pct = int(current / total * 100)
                    await status_message.edit_text(
                        f"🗣 Language: {lang}  |  Voice: {voice}\n⏳ Generating audio... {current}/{total} segments ({pct}%)"
                    )
                    last_edit_time = time.time()
                except Exception:
                    pass

        # 3. TTS Generation
        await tts.generate_wav(text_to_read, mp3_path, voice=voice, speed=speed, progress_callback=progress_callback)

        # 4. Convert to OGG
        success = await converter.convert_wav_to_ogg(mp3_path, ogg_path)

        if success and os.path.exists(ogg_path):
            size_mb = os.path.getsize(ogg_path) / (1024 * 1024)
            if size_mb > 49:
                await status_message.edit_text(
                    f"❌ Audio file is too large to send ({size_mb:.1f} MB). "
                    f"Telegram's limit is 50 MB. Try a shorter text."
                )
                return
            with open(ogg_path, "rb") as voice_file:
                await update.message.reply_voice(voice=voice_file, reply_to_message_id=update.message.message_id)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Failed to convert audio format.")

    except asyncio.CancelledError:
        await status_message.edit_text("⏹ Generation cancelled.")

    except Exception as e:
        traceback.print_exc()
        await status_message.edit_text(f"❌ Error: {e}")

    finally:
        for f_path in [mp3_path, ogg_path]:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except Exception as e:
                    print(f"Failed to delete temp file {f_path}: {e}")
        _active_tasks.pop(user_id, None)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if config.ALLOWED_USERS and user_id not in config.ALLOWED_USERS:
        print(f"Unauthorized access attempt from user {user_id}")
        return

    if not update.message.text:
        return

    # Cancel any in-progress generation for this user before starting a new one
    existing = _active_tasks.get(user_id)
    if existing and not existing.done():
        existing.cancel()

    task = asyncio.create_task(_generate_and_send(user_id, update, context))
    _active_tasks[user_id] = task


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start", "Show welcome message and instructions"),
        BotCommand("speed", "Change reading speed — Slow / Normal / Fast / Very Fast"),
        BotCommand("cancel", "Cancel the current audio generation"),
        BotCommand("myid", "Get your Telegram user ID"),
    ])


if __name__ == "__main__":
    if not config.BOT_TOKEN:
        print("Please set the BOT_TOKEN environment variable.")
        exit(1)

    print("🚀 Starting Bot...")
    # Increase the write timeout for sending large audio files (default is usually 10-30s)
    app = ApplicationBuilder().token(config.BOT_TOKEN).write_timeout(300).read_timeout(300).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("speed", speed_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CallbackQueryHandler(speed_callback, pattern=r"^speed:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()