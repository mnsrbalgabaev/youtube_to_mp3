# YouTube → MP3 Telegram Bot

A simple Telegram bot: send it a YouTube link, it replies with the audio as an MP3.

## 1. Prerequisites

- Python 3.10+
- **ffmpeg** installed and on your PATH (required for audio conversion)
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: download from https://ffmpeg.org/download.html and add to PATH
- A Telegram bot token from [@BotFather](https://t.me/BotFather):
  1. Open a chat with @BotFather
  2. Send `/newbot` and follow the prompts
  3. Copy the token it gives you (looks like `123456789:AAExampleTokenString`)

## 2. Install

```bash
cd ytmp3bot
pip install -r requirements.txt
```

## 3. Configure

Set your bot token as an environment variable:

```bash
export TELEGRAM_BOT_TOKEN="123456789:AAExampleTokenString"
```

(On Windows PowerShell: `$env:TELEGRAM_BOT_TOKEN="123456789:AAExampleTokenString"`)

## 4. Run

```bash
python bot.py
```

Now open Telegram, find your bot, and send it a YouTube link (e.g.
`https://www.youtube.com/watch?v=...` or `https://youtu.be/...`). It will
download the audio, convert it to MP3, and send it back in the chat.

## How it works

- **python-telegram-bot** handles the Telegram side (receiving messages, sending files).
- **yt-dlp** downloads the best available audio stream from the YouTube link and
  uses its built-in FFmpeg post-processor to convert it to MP3 (192 kbps).
- Files are downloaded to a temporary directory and deleted automatically after
  being sent.

## Limitations & notes

- Telegram bots can only upload files up to **50 MB**. Very long videos may
  produce an MP3 larger than that; the bot will tell the user instead of
  failing silently.
- Age-restricted, private, or region-locked videos may fail to download —
  yt-dlp will raise an error and the bot reports this back to the user.
- **Use responsibly.** Only download audio you have the right to download
  (your own content, royalty-free/Creative Commons material, or anything
  else you're permitted to use). Downloading copyrighted content without
  permission may violate YouTube's Terms of Service and copyright law where
  you live — that responsibility is on whoever operates and uses this bot.
- For production use (many users, need for reliability), consider:
  - Running this behind a process manager (systemd, supervisor, Docker) so it
    restarts on failure.
  - Adding a job queue if you expect concurrent requests, since downloads are
    somewhat slow and block that update's handler.
  - Rate-limiting per user to avoid abuse.

## Deploying it long-term

Any machine that can stay online works: a small VPS (DigitalOcean, Hetzner,
AWS EC2, etc.), a Raspberry Pi at home, or a container platform (Railway,
Render, Fly.io). Just make sure ffmpeg is installed in that environment, set
the `TELEGRAM_BOT_TOKEN` env var, and run `python bot.py` with a process
supervisor so it stays running.
