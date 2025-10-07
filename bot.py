import os
import logging
import asyncio
import torch
import whisper
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.error import BadRequest

# ============ НАСТРОЙКИ ============
BOT_TOKEN = "8220500069:AAFPOBIgyElxreQMDpkxhLUJIrf06kwf1jQ"  # <-- замени на свой токен
CHANNEL_USERNAME = "@Maskonhak"  # канал, на который нужно быть подписанным

# ===================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Загрузка модели Whisper...")
model = whisper.load_model("base")  # можно "small", "medium" или "large" для точности
logger.info("Модель готова к работе.")

# ---------- Проверка подписки ----------
async def check_subscription(update, context):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except BadRequest:
        return False


# ---------- Команда /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_subscribed = await check_subscription(update, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("✅ Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Чтобы пользоваться ботом, подпишись на наш канал:\n👉 https://t.me/Maskonhak",
            reply_markup=reply_markup
        )
        return

    await update.message.reply_text(
        "🎧 Привет! Отправь мне голосовое сообщение, и я переведу его в текст."
    )


# ---------- Проверка кнопки ----------
async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    is_subscribed = await check_subscription(update, context)
    if is_subscribed:
        await query.edit_message_text("✅ Отлично! Ты подписан. Отправь голосовое 🎤")
    else:
        await query.edit_message_text(
            "❌ Ты всё ещё не подписан. Подпишись на канал и попробуй снова.\n👉 https://t.me/Maskonhak"
        )


# ---------- Расшифровка голосовых ----------
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_subscribed = await check_subscription(update, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("✅ Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Чтобы пользоваться ботом, подпишись на наш канал:",
            reply_markup=reply_markup
        )
        return

    voice = await update.message.voice.get_file()
    file_path = "voice.ogg"
    await voice.download_to_drive(file_path)
    logger.info("🎤 Голосовое получено, начинаю обработку...")

    # Конвертация и распознавание
    result = model.transcribe(file_path, fp16=torch.cuda.is_available())
    text = result["text"].strip()

    await update.message.reply_text(f"📝 Расшифровка:\n\n{text}")
    os.remove(file_path)


# ---------- Запуск ----------
async def main():
    logger.info("✅ Бот запущен и ждёт голосовые сообщения.")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))

    await app.run_polling()


if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
