import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_ID
from claude_client import chat
from voice import download_and_transcribe
from scheduler import create_scheduler, set_sender
from budget import get_budget_status_message

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# In-memory conversation history per user (last 20 messages = 10 turns)
_history: dict[int, list] = {}

MODEL_EMOJI = {
    "claude-haiku-4-5-20251001": "⚡",
    "claude-sonnet-4-6": "🔵",
    "claude-fable-5": "🌟",
}


def _guard(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id == TELEGRAM_ALLOWED_USER_ID


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    await update.message.reply_text(
        "👋 *Alex's Universal Agent — online*\n\n"
        "Γράψε οτιδήποτε. Στείλε voice note για φωνητική εντολή.\n\n"
        "⚡ Haiku — quick tasks\n"
        "🔵 Sonnet — standard (default)\n"
        "🌟 Fable 5 — /deep /plan /research /analyze\n\n"
        "/budget — τρέχον spend\n"
        "/clear — καθαρισμός ιστορικού",
        parse_mode="Markdown"
    )


async def cmd_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    await update.message.reply_text(get_budget_status_message())


async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    _history.pop(update.effective_user.id, None)
    await update.message.reply_text("✅ Ιστορικό καθαρίστηκε.")


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    await _process(update, update.effective_user.id, update.message.text.strip())


async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _guard(update):
        return
    user_id = update.effective_user.id
    await update.message.reply_text("🎙️ Transcribing...")
    try:
        text = await download_and_transcribe(update.message.voice, ctx.bot)
        await update.message.reply_text(f"📝 _{text}_", parse_mode="Markdown")
        await _process(update, user_id, text)
    except Exception as e:
        logger.error("Voice failed: %s", e)
        await update.message.reply_text(f"❌ {e}")


async def _process(update: Update, user_id: int, text: str):
    history = _history.get(user_id, [])
    try:
        response, model_used, budget_alert = chat(text, history)
        _history[user_id] = (history + [
            {"role": "user", "content": text},
            {"role": "assistant", "content": response},
        ])[-20:]

        emoji = MODEL_EMOJI.get(model_used, "🤖")
        await update.message.reply_text(f"{emoji} {response}")
        if budget_alert:
            await update.message.reply_text(budget_alert)
    except Exception as e:
        logger.error("Chat failed: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("budget", cmd_budget))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    scheduler = create_scheduler()

    async def send_to_alex(text: str):
        await app.bot.send_message(
            chat_id=TELEGRAM_ALLOWED_USER_ID, text=text, parse_mode="Markdown"
        )

    set_sender(send_to_alex)

    async def on_startup(app):
        scheduler.start()
        logger.info("Scheduler started. Bot online.")

    async def on_shutdown(app):
        scheduler.shutdown()

    app.post_init = on_startup
    app.post_shutdown = on_shutdown

    logger.info("Starting bot...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
