from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import yt_dlp
import os

BOT_TOKEN = '8077362820:AAEfjXLGxEd9UUv2hG4mDpbAp1D1I6GQ-iA'

# START command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /download <YouTube_URL> to select format.")

# /download command with format options
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

# Handle button press
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('yt_url', '')
    if not url:
        await query.edit_message_text("URL missing.")
        return

    format_choice = query.data
    filename = "yt_download"

    try:
        if format_choice == 'video':
            ydl_opts = {
                'format': 'best[height<=720][ext=mp4]',
                'outtmpl': f'{filename}.mp4',
            }
            ext = 'mp4'

        elif format_choice == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{filename}.mp3',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            ext = 'mp3'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(f'{filename}.{ext}', 'rb') as f:
            if ext == 'mp4':
                await query.message.reply_video(video=f)
            else:
                await query.message.reply_audio(audio=f)

        os.remove(f'{filename}.{ext}')
        await query.edit_message_text("✅ Done!")

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")

# MAIN
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("download", download))
app.add_handler(CallbackQueryHandler(button))
app.run_polling()
