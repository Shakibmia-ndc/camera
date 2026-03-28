import sys
import types

# --- পাইথন ৩.১৩ এর imghdr এরর ফিক্স (সবার আগে থাকতে হবে) ---
mock_imghdr = types.ModuleType('imghdr')
mock_imghdr.what = lambda file, h=None: None
sys.modules['imghdr'] = mock_imghdr
# ---------------------------------------------------

import os
import subprocess
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# লগিং সেটআপ (বটের ভেতরে কি হচ্ছে তা দেখার জন্য)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# আপনার বটের টোকেন
TOKEN = '8675593212:AAFIp7L9x730NK9-HHPXW87XAhMhP39YVEY'

# স্টার্ট কমান্ড এবং মেনু বাটন সেটআপ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("ভিডিও কম্প্রেস করুন 🎬")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "আসসালামু আলাইকুম মিজানুর রহমান ভাই!\n\n"
        "আপনার 'Bachelor Point Season 5' প্রজেক্টের জন্য এই বটটি রেডি।\n"
        "নিচের বাটনটি চাপুন অথবা সরাসরি ভিডিও ফাইলটি এখানে পাঠান।",
        reply_markup=reply_markup
    )

# ভিডিও প্রসেস করার মেইন ফাংশন
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    if not video:
        await update.message.reply_text("ভাই, দয়া করে একটি ভিডিও ফাইল পাঠান।")
        return

    # ইউজারের জন্য স্ট্যাটাস মেসেজ
    status_msg = await update.message.reply_text("📥 ভিডিও ডাউনলোড হচ্ছে... একটু সবুর করুন।")
    
    # ফাইল পাথ সেট করা
    file = await video.get_file()
    input_path = f"in_{update.message.message_id}.mp4"
    output_path = f"out_{update.message.message_id}.mp4"
    
    # ডাউনলোড শুরু
    await file.download_to_drive(input_path)
    await status_msg.edit_text("⚙️ সাইজ কমানো শুরু হয়েছে (টার্গেট: ২০০ MB এর নিচে)...")

    try:
        # ১. ভিডিওর ডিউরেশন (সময়) বের করা
        probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {input_path}"
        duration = float(subprocess.check_output(probe_cmd, shell=True).decode().strip())

        # ২. বিটরেট ক্যালকুলেশন (টার্গেট ১৯৫ এমবি যাতে ২০০ পার না হয়)
        # সূত্র: (সাইজ ইন বিটস / সময়) - অডিও বিটরেট
        target_size_bits = 195 * 8 * 1024 * 1024
        video_bitrate = int(target_size_bits / duration) - 128000 

        # ৩. FFmpeg কমান্ড চালানো (মোবাইলের জন্য 'fast' প্রিসেট সেরা)
        ffmpeg_cmd = (
            f'ffmpeg -y -i "{input_path}" -b:v {video_bitrate} -vcodec libx264 '
            f'-preset fast -crf 28 -acodec aac -b:a 128k "{output_path}"'
        )
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        # ৪. সফল হলে ভিডিও পাঠানো
        await status_msg.edit_text("📤 কাজ শেষ! এখন ভিডিও পাঠানো হচ্ছে...")
        await update.message.reply_video(
            video=open(output_path, 'rb'),
            caption="✅ মিজানুর ভাই, আপনার ভিডিও ২০০ এমবি-র নিচে করা হয়েছে।\nএখন Catbox-এ আপলোড করতে পারবেন।"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ ভুল হয়েছে ভাই: {str(e)}\n\nটিপস: আপনার ফোনে FFmpeg ইনস্টল করা আছে তো?")
    
    finally:
        # ৫. টেম্পোরারি ফাইলগুলো ডিলিট করে ফোন বা সার্ভার পরিষ্কার রাখা
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        await status_msg.delete()

# মেনু বাটনের টেক্সট হ্যান্ডলার
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "ভিডিও কম্প্রেস করুন 🎬":
        await update.message.reply_text("ঠিক আছে ভাই, আপনার বড় ভিডিও ফাইলটি পাঠান। আমি ২০০ এমবি-র নিচে করে দিচ্ছি।")

if __name__ == '__main__':
    # বট অ্যাপ্লিকেশন তৈরি
    app = ApplicationBuilder().token(TOKEN).build()
    
    # কমান্ড এবং মেসেজ হ্যান্ডলার যোগ করা
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), button_handler))

    print("--- বট এখন অনলাইনে আছে, মিজানুর ভাই! ---")
    app.run_polling()
      
