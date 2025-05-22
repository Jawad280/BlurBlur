import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import uuid
import opennsfw2 as n2
from PIL import Image
from util.image_utils import process_image
from util.video_utils import process_video

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Hello command
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

# Handle incoming Images
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]
    file_id = photo.file_id
    img_file = await context.bot.get_file(file_id)

    unique_id = str(uuid.uuid4())
    local_path = f"{unique_id}_original.jpg"

    # Download image
    await img_file.download_to_drive(local_path)

    # NSFW detection
    try:
        score = process_image(local_path)
        print(f"Photo NSFW Score: {score}")

        if score > 0.8:
            try:
                await update.message.delete()
            except Exception as e:
                print("Could not delete user image:", e)

            await update.message.chat.send_photo(
                photo=open(local_path, "rb"),
                caption=f"⚠️ This image may contain NSFW content.\nProbability: {score * 100:.2f}%",
                has_spoiler=True
            )
    finally:
        os.remove(local_path)

# Handle incoming Video -> Not enabled for now to save memory
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    video = update.message.video

    if video.file_size > 20 * 1024 * 1024:
        await update.message.reply_text("⚠️ Video too large to scan. Max 20 MB.")
        return

    file = await context.bot.get_file(video.file_id)
    unique_id = str(uuid.uuid4())
    video_path = f"{unique_id}.mp4"

    await file.download_to_drive(video_path)

    try:
        score = process_video(video_path)
        print("Video NSFW Score:", score)

        if score > 0.8:
            try:
                await update.message.delete()
            except Exception as e:
                print("Could not delete NSFW video:", e)

            await update.message.chat.send_message(
                text=f"⚠️ This video may contain NSFW content.\nHighest detected probability: {score * 100:.2f}%"
            )        
    finally:
        os.remove(video_path)

# Handle incoming Sticker
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sticker = update.message.sticker
    file = await context.bot.get_file(sticker.file_id)

    unique_id = str(uuid.uuid4())
    if sticker.is_animated:
        await update.message.reply_text("⚠️ Animated stickers (.tgs) are currently not supported.")
        return
    
    # Determine extension and local path
    ext = ".webm" if sticker.is_video else ".webp"
    local_path = f"{unique_id}{ext}"
    await file.download_to_drive(local_path)

    try:
        if sticker.is_video:
            score = await process_video(local_path)
        else:
            jpg_path = local_path.replace(".webp", ".jpg")
            with Image.open(local_path) as im:
                im.convert("RGB").save(jpg_path, "JPEG")

            score = await process_image(jpg_path)
            os.remove(jpg_path)
        
        print(f"Sticker NSFW Score: {score}")

        if score > 0.8:
            try:
                await update.message.delete()
            except Exception as e:
                print("Could not delete NSFW sticker:", e)

            if sticker.is_video:
                await update.message.chat.send_message(
                    text=f"⚠️ This sticker may contain NSFW content.\nProbability: {score * 100:.2f}%"
                )
            else:
                with open(local_path, "rb") as photo:
                    await update.message.chat.send_photo(
                        photo=photo,
                        caption=f"⚠️ This sticker may contain NSFW content.\nProbability: {score * 100:.2f}%",
                        has_spoiler=True
                    )
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)        

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))
# app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))

if __name__ == "__main__":
    print("Starting BlurBlur bot...")
    app.run_polling()