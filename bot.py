"""
YouTube -> MP3 Telegram Bot
---------------------------
Send the bot a YouTube link, it downloads the audio, converts it to MP3,
and sends the file back to you in the chat.

Setup:
    1. pip install -r requirements.txt
    2. Install ffmpeg (required by yt-dlp for audio extraction):
         - Ubuntu/Debian: sudo apt install ffmpeg
         - macOS:         brew install ffmpeg
         - Windows:       https://ffmpeg.org/download.html
    3. Get a bot token from @BotFather on Telegram.
    4. Set the token as an environment variable:
         export TELEGRAM_BOT_TOKEN="123456:ABC-your-token"
    5. Run:
         python bot.py

Notes:
    - Telegram bots can only send files up to 50 MB via the Bot API.
      Very long videos may fail to send; the bot will tell the user if so.
    - Only use this to download content you have the rights to download
      (e.g. your own uploads, royalty-free audio, or otherwise permitted
      material). Respect YouTube's Terms of Service and copyright law in
      your jurisdiction.
"""

import logging
import os
import re
import tempfile
import uuid

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Matches most common YouTube URL formats (youtube.com/watch, youtu.be, shorts, etc.)
YOUTUBE_URL_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w\-]+"
)

MAX_TELEGRAM_FILE_BYTES = 50 * 1024 * 1024  # 50 MB Bot API limit


def extract_youtube_url(text: str) -> str | None:
    match = YOUTUBE_URL_RE.search(text)
    if not match:
        return None
    url = match.group(0)
    if not url.startswith("http"):
        url = "https://" + url
    return url


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Send me a YouTube link and I'll send you back the audio as an MP3."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Just paste a YouTube video link (youtube.com or youtu.be) and I'll reply "
        "with an MP3 of the audio."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    url = extract_youtube_url(text)

    if not url:
        await update.message.reply_text(
            "That doesn't look like a YouTube link. Send me a youtube.com or youtu.be URL."
        )
        return

    status_msg = await update.message.reply_text("Got it — downloading audio, one moment...")
    await update.effective_chat.send_action(ChatAction.RECORD_VOICE)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_template = os.path.join(tmpdir, f"{uuid.uuid4().hex}.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "audio")
        except yt_dlp.utils.DownloadError as e:
            logger.warning("Download failed for %s: %s", url, e)
            await status_msg.edit_text(
                "Sorry, I couldn't download that video. It may be private, "
                "age-restricted, region-locked, or otherwise unavailable."
            )
            return
        except Exception:
            logger.exception("Unexpected error while processing %s", url)
            await status_msg.edit_text("Something went wrong processing that link.")
            return

        # Find the resulting mp3 file (postprocessor renames extension to .mp3)
        mp3_path = None
        for fname in os.listdir(tmpdir):
            if fname.endswith(".mp3"):
                mp3_path = os.path.join(tmpdir, fname)
                break

        if not mp3_path or not os.path.exists(mp3_path):
            await status_msg.edit_text("Conversion failed — no MP3 was produced.")
            return

        file_size = os.path.getsize(mp3_path)
        if file_size > MAX_TELEGRAM_FILE_BYTES:
            await status_msg.edit_text(
                f"The resulting MP3 is {file_size / (1024*1024):.1f} MB, which is over "
                "Telegram's 50 MB bot upload limit, so I can't send it. Try a shorter video."
            )
            return

        await status_msg.edit_text("Uploading MP3...")
        await update.effective_chat.send_action(ChatAction.UPLOAD_VOICE)

        safe_title = re.sub(r"[^\w\-. ]", "_", title)[:60] or "audio"
        with open(mp3_path, "rb") as audio_file:
            await update.message.reply_audio(
                audio=audio_file,
                filename=f"{safe_title}.mp3",
                title=title,
            )

        await status_msg.delete()


def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN environment variable is not set. "
            "Get a token from @BotFather and export it before running the bot."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
