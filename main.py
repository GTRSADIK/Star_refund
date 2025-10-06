import os
import logging
import traceback
from collections import defaultdict
from typing import DefaultDict, Dict
from dotenv import load_dotenv
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, CallbackContext, filters
)
from config import ITEMS, MESSAGES, WELCOME_IMAGE

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stats: admin balance and transactions
STATS: Dict[str, DefaultDict] = {
    'admin_balance': defaultdict(int),   # Admin star balance
    'transactions': {}                   # Stores transaction_id -> {'user_id': x, 'username': y, 'item': z, 'stars': n}
}

# Start command
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

# Help command
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(MESSAGES['help'], parse_mode='Markdown')

# Refund command (admin only)
async def refund_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Only admin can use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /refund <transaction_id>")
        return

    transaction_id = context.args[0]
    if transaction_id not in STATS['transactions']:
        await update.message.reply_text("❌ Invalid transaction ID.")
        return

    txn = STATS['transactions'].pop(transaction_id)
    STATS['admin_balance'][ADMIN_ID] += txn['stars']

    await update.message.reply_text(
        f"✅ Refund completed. {txn['stars']}⭐ added to admin balance."
    )

# Button handler for items
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "send_stars":
        keyboard = []
        for item_id, item in ITEMS.items():
            keyboard.append([InlineKeyboardButton(f"{item['name']} - {item['price']} ⭐", callback_data=item_id)])
        await query.message.reply_text("Select item to buy:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Item selected
    item_id = query.data
    if item_id not in ITEMS:
        return

    item = ITEMS[item_id]
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=item['name'],
        description=item['description'],
        payload=item_id,
        provider_token="",  # Leave empty for Stars
        currency="XTR",
        prices=[LabeledPrice(item['name'], int(item['price']))],
        start_parameter="test-payment"
    )

# Precheckout
async def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    if query.invoice_payload in ITEMS:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Invalid item.")

# Successful payment
async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    payment = update.message.successful_payment
    item_id = payment.invoice_payload
    item = ITEMS[item_id]
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else f"ID:{user_id}"
    transaction_id = payment.telegram_payment_charge_id

    # Save transaction for admin
    STATS['transactions'][transaction_id] = {
        'user_id': user_id,
        'username': username,
        'item': item_id,
        'stars': item['price']
    }

    # Notify user
    await update.message.reply_text(
        f"✅ {item['price']}⭐ successfully sent!\n"
        f"💰 Admin will confirm within 1 hour.",
        parse_mode='Markdown'
    )

    # Notify Admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 Transaction ID: {transaction_id}\nUser {username} sent {item['price']}⭐ for *{item['name']}*.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("refund", refund_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    logger.info("🚀 Bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()
