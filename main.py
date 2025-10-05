import os
import logging
from collections import defaultdict
from typing import DefaultDict, Dict
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, CallbackContext
)
from config import ITEMS, MESSAGES, WELCOME_IMAGE

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# User stats
STATS: Dict[str, DefaultDict[str, int]] = {
    'purchases': defaultdict(int),
    'refunds': defaultdict(int)
}


async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    keyboard = [[InlineKeyboardButton("💫 Send Stars", callback_data="send_stars")]]
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=WELCOME_IMAGE,
            caption=MESSAGES['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"/start error: {e}")
        if update.message:
            await update.message.reply_text("⚠️ Something went wrong while sending the start menu.")


async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(MESSAGES['help'], parse_mode='Markdown')


async def refund_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Only admin can use this command.")
        return

    if not context.args:
        await update.message.reply_text(MESSAGES['refund_usage'])
        return

    charge_id = context.args[0]
    try:
        # Here you should implement your actual refund logic
        STATS['refunds'][charge_id] += 1
        await update.message.reply_text(MESSAGES['refund_success'])
    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"❌ Error processing refund: {str(e)}")


async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "send_stars":
        keyboard = []
        for item_id, item in ITEMS.items():
            keyboard.append([InlineKeyboardButton(f"{item['name']} - {item['value']} ⭐", callback_data=item_id)])
        await query.message.reply_text("Select Stars package to buy:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Item selected
    item_id = query.data
    if item_id not in ITEMS:
        return

    item = ITEMS[item_id]
    # For demo, we'll simulate purchase without real payment
    user_id = query.from_user.id
    if 'stars' not in context.user_data:
        context.user_data['stars'] = 0
    context.user_data['stars'] += item['value']
    STATS['purchases'][str(user_id)] += 1

    # Notify user
    await query.message.reply_text("✅ Your Stars purchase was successful! Admin received your request, waiting for payment.")

    # Notify admin
    if ADMIN_ID:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 User {query.from_user.full_name} ({user_id}) purchased {item['name']}."
        )


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("refund", refund_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🚀 Bot started successfully!")
    application.run_polling()


if __name__ == "__main__":
    main()
