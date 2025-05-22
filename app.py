import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import uuid
import opennsfw2 as n2

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
    original_path = f"{unique_id}_original.jpg"

    await img_file.download_to_drive(original_path)

    # NSFW detection
    nsfw_score = n2.predict_image(original_path)
    print("NSFW Score:", nsfw_score)

    if nsfw_score > 0.8:
        try:
            await update.message.delete()
        except Exception as e:
            print("Could not delete user image:", e)

        # Send as native spoiler
        await update.message.chat.send_photo(
            photo=open(original_path, "rb"),
            caption="⚠️ This image may contain NSFW content.",
            has_spoiler=True
        )
    
    # Clean up
    os.remove(original_path)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("hello", hello))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

if __name__ == "__main__":
    print("Starting BlurBlur bot...")
    app.run_polling()