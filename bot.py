import asyncio
import logging
import os
import re
import tempfile
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import yt_dlp

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("media-downloader-bot")

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
MAX_UPLOAD_SIZE = 49 * 1024 * 1024


WELCOME_TEXT = (
    "👋 Привет!\n\n"
    "🕵️ Я помогаю скачивать видео и фото из Instagram, TikTok, YouTube и Pinterest — "
    "без водяных знаков и в лучшем качестве!\n\n"
    "🔗 Просто отправь ссылку — и получи файл за пару секунд.\n\n"
    "❕ Бот работает без рекламы.\n\n"
    "💬 Бот также работает в группах и чатах."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_username = context.bot.username or ""
    add_to_group_url = f"https://t.me/{bot_username}?startgroup=true" if bot_username else "https://t.me"

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("➕ Добавить в группу", url=add_to_group_url)]]
    )

    await update.message.reply_text(WELCOME_TEXT, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Отправь ссылку на пост/ролик/видео, и я попробую скачать файл.")


def _download_media(url: str, workdir: str) -> Path:
    output_template = str(Path(workdir) / "%(title).80s_%(id)s.%(ext)s")
    ydl_opts = {
        "quiet": True,
        "noprogress": True,
        "outtmpl": output_template,
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "restrictfilenames": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if "entries" in info and info["entries"]:
            info = info["entries"][0]
        file_path = Path(ydl.prepare_filename(info))

    if not file_path.exists():
        possible_files = sorted(Path(workdir).glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not possible_files:
            raise FileNotFoundError("Не удалось найти скачанный файл")
        file_path = possible_files[0]

    return file_path


async def _safe_reply(update: Update, text: str) -> None:
    if update.message:
        await update.message.reply_text(text)


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    match = URL_RE.search(update.message.text)
    if not match:
        return

    url = match.group(0)
    await update.message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    processing_msg = await update.message.reply_text("⏳ Загружаю, подожди пару секунд...")

    try:
        with tempfile.TemporaryDirectory() as tmp:
            loop = asyncio.get_running_loop()
            media_path = await loop.run_in_executor(None, _download_media, url, tmp)

            file_size = media_path.stat().st_size
            if file_size > MAX_UPLOAD_SIZE:
                mb = file_size / (1024 * 1024)
                await _safe_reply(
                    update,
                    f"⚠️ Файл слишком большой для отправки ботом ({mb:.1f} МБ). Попробуй другую ссылку.",
                )
                return

            suffix = media_path.suffix.lower()
            with media_path.open("rb") as media_file:
                caption = "Скачано ✅"
                if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
                    await update.message.reply_photo(photo=media_file, caption=caption)
                else:
                    await update.message.reply_video(video=media_file, caption=caption)

    except Exception as exc:
        logger.exception("Download failed: %s", exc)
        await _safe_reply(
            update,
            "❌ Не получилось скачать файл. Проверь ссылку или попробуй позже.",
        )
    finally:
        await processing_msg.delete()


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _safe_reply(update, "Отправь ссылку на видео/пост, и я скачаю файл.")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.add_handler(MessageHandler(filters.ALL, unknown))

    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
