import os
import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from PIL import Image, ImageDraw, ImageFont

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables from Render.com
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT")

# Define the professional caption
POST_CAPTION = "hack kharidne ke liye contact @TPKINGOWNER"

def add_watermark(photo_path):
    try:
        image = Image.open(photo_path).convert("RGBA")
        txt = Image.new("RGBA", image.size, (255, 255, 255, 0))
        try:
            font = ImageFont.truetype("arial.ttf", size=max(15, int(image.height / 30)))
        except IOError:
            font = ImageFont.load_default()
        d = ImageDraw.Draw(txt)
        text_width, text_height = d.textsize(WATERMARK_TEXT, font=font)
        x = (image.width - text_width) / 2
        y = image.height - text_height - (image.height * 0.05)
        d.rectangle([x-5, y-5, x + text_width + 5, y + text_height + 5], fill=(0, 0, 0, 128))
        d.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220))
        watermarked = Image.alpha_composite(image, txt).convert("RGB")
        watermarked_path = "watermarked.jpg"
        watermarked.save(watermarked_path)
        return watermarked_path
    except Exception as e:
        logger.error(f"Error adding watermark: {e}")
        return None

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! Please send me a photo to submit for review.')

def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    photo_file = update.message.photo[-1].get_file()
    
    # Create a short ID because file_id is too long for buttons
    short_id = uuid.uuid4().hex[:16]
    
    # Store the original file_id using the short_id as the key
    context.bot_data[short_id] = {
        'file_id': photo_file.file_id,
        'user_id': user_id
    }

    keyboard = [
        [
            # Use the short_id in the callback data
            InlineKeyboardButton("✅ Approve", callback_data=f'approve_{short_id}'),
            InlineKeyboardButton("❌ Reject", callback_data=f'reject_{short_id}'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=photo_file.file_id, 
        caption=f"New photo from user {user_id}. Approve to post in channel.",
        reply_markup=reply_markup
    )
    update.message.reply_text("Thanks! Your photo has been submitted for admin approval.")

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    # The second part is now the short_id
    action, short_id = query.data.split('_', 1)

    # Check if we have data for this short_id
    if short_id not in context.bot_data:
        query.edit_message_caption(caption="⚠️ Error: This approval request has expired or is invalid.")
        return

    # Retrieve the original file_id from bot_data
    file_id = context.bot_data[short_id]['file_id']

    if action == "approve":
        query.edit_message_caption(caption="✅ Approved. Posting to channel...")
        
        photo = context.bot.get_file(file_id)
        photo.download('temp_photo.jpg')

        watermarked_photo_path = add_watermark('temp_photo.jpg')

        if watermarked_photo_path:
            with open(watermarked_photo_path, 'rb') as photo_to_send:
                context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo_to_send, caption=POST_CAPTION)
            query.edit_message_caption(caption="✅ Photo posted successfully with watermark!")
            os.remove(watermarked_photo_path)
        else:
             query.edit_message_caption(caption="⚠️ Error: Could not apply watermark. Posting original.")
             context.bot.send_photo(chat_id=CHANNEL_ID, photo=file_id, caption=POST_CAPTION)

        os.remove('temp_photo.jpg')

    elif action == "reject":
        query.edit_message_caption(caption="❌ Rejected. The photo will not be posted.")
        
    # Clean up bot_data using the short_id
    del context.bot_data[short_id]

def main() -> None:
    if not all([BOT_TOKEN, CHANNEL_ID, ADMIN_ID, WATERMARK_TEXT]):
        logger.error("Missing one or more critical environment variables on Render.com!")
        return
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.photo & ~Filters.command, handle_photo))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))
    updater.start_polling()
    logger.info("Bot is running and listening...")
    updater.idle()

if __name__ == '__main__':
    main()
