import os
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# --- Configuration (Yeh Render.com se values lega) ---
# Is code ko bilkul aise hi rehne dein. Token yahan nahi likhna hai.
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
# --- End of Configuration ---


# --- Functions ---
async def start(update, context):
    """/start command ke liye. User ko welcome message bhejta hai."""
    await update.message.reply_text("Namaste! Feedback ya koi post share karne ke liye, mujhe koi photo bhejein.")

async def forward_photo_to_channel(update, context):
    """User se photo receive karke channel par bhejta hai."""
    try:
        photo_id = update.message.photo[-1].file_id
        caption = update.message.caption
        
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id, caption=caption)
        
        await update.message.reply_text("Shukriya! Aapka photo channel par post kar diya gaya hai.")
        print("Feedback photo successfully forwarded.")
        
    except Exception as e:
        print(f"Failed to forward photo: {e}")
        await update.message.reply_text("Maaf kijiye, photo bhejte waqt koi problem aa gayi.")

def main():
    """Bot ko run karne ke liye main function."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers add karein
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, forward_photo_to_channel))

    # Bot ko run karein
    print("Bot is running and listening for photos...")
    application.run_polling()

if __name__ == '__main__':
    main()
