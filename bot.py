from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import yt_dlp
import os
import asyncio

import logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /download <YouTube_URL> to select format.")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /download <YouTube_URL>")
        return

    url = context.args[0]
    context.user_data['yt_url'] = url

    keyboard = [
        [InlineKeyboardButton("🎞️ Video (MP4 720p)", callback_data='video')],
        [InlineKeyboardButton("🎧 Audio (MP3)", callback_data='audio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose format:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id not in ALLOWED_USERS:
        await query.edit_message_text("❌ Access denied.")
        return

    choice = query.data
    url = context.user_data.get('yt_url', '')
    filename = "yt_download"

    if choice == "cancel":
        await query.edit_message_text("❌ Cancelled.")
        return

    progress_message = await query.message.reply_text("⏳ Starting download...")

    download_progress = {"percent": 0}

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip()
            if percent:
                download_progress["percent"] = percent
                try:
                    context.application.create_task(progress_message.edit_text(f"📥 Downloading: {percent}"))
                except:
                    pass
        elif d['status'] == 'finished':
            try:
                context.application.create_task(progress_message.edit_text("✅ Download complete. Sending..."))
            except:
                pass

    try:
        if choice == 'video':
            ydl_opts = {
                'format': 'best[height<=720][ext=mp4]',
                'outtmpl': f'{filename}.mp4',
                'progress_hooks': [progress_hook],
            }
            ext = 'mp4'
        else:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{filename}.mp3',
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            ext = 'mp3'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_path = f"{filename}.{ext}"
        file_size = os.path.getsize(file_path) / (1024 * 1024)

        with open(file_path, 'rb') as f:
            if file_size < 49:
                if ext == 'mp4':
                    await query.message.reply_video(video=f)
                else:
                    await query.message.reply_audio(audio=f)
            else:
                await query.message.reply_document(document=f)

        # Show live countdown before deletion
        countdown_message = await query.message.reply_text("⚠️ File will be deleted from server in 1:00...")
        for i in range(59, -1, -1):
            await asyncio.sleep(1)
            minutes = i // 60
            seconds = i % 60
            await countdown_message.edit_text(f"⚠️ File will be deleted from server in {minutes}:{seconds:02d}...")

        # Final deletion
        try:
            os.remove(file_path)
            logging.info(f"✅ Auto-deleted {file_path}")
            await countdown_message.edit_text("✅ File deleted from server.")
        except Exception as e:
            logging.error(f"❌ Failed to delete file: {e}")
            await countdown_message.edit_text("⚠️ Failed to delete file from server.")

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")
        logging.error(f"Download failed: {e}")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("download", download))
app.add_handler(CallbackQueryHandler(button))
app.run_polling()
