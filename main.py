import os
import logging
import traceback
import uuid
from collections import defaultdict
from typing import DefaultDict, Dict
from dotenv import load_dotenv
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, PreCheckoutQueryHandler, CallbackContext
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

# Stats and transactions
STATS: Dict[str, DefaultDict[str, int]] = {
    'purchases': defaultdict(int),
    'refunds': defaultdict(int)
}
TRANSACTIONS: Dict[str, Dict] = {}  # transaction_id -> data

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
    if transaction_id not in TRANSACTIONS:
        await update.message.reply_text(f"❌ Invalid transaction ID: {transaction_id}")
        return

    data = TRANSACTIONS.pop(transaction_id)
    user_id_refund = data['user_id']
    item_price = data['price']
    STATS['refunds'][str(user_id_refund)] += item_price

    await update.message.reply_text(f"✅ Refund successful: {item_price} XTR refunded from transaction {transaction_id}")

    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 Admin processed refund:\nUser ID: {user_id_refund}\nAmount: {item_price} XTR\nTransaction: {transaction_id}"
        )
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

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
        provider_token="",  # XTR stars payment
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
    username = f"@{user.username}" if user.username else f"ID: {user_id}"

    # Generate transaction ID
    transaction_id = str(uuid.uuid4())
    TRANSACTIONS[transaction_id] = {
        'user_id': user_id,
        'item_id': item_id,
        'price': int(item['price'])
    }

    STATS['purchases'][str(user_id)] += int(item['price'])

    # Notify user
    await update.message.reply_text(
        f"✅ {item['price']} ⭐ successfully sent!\n💰 Transaction ID: `{transaction_id}`\n💡 Refund possible only by admin.",
        parse_mode='Markdown'
    )

    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 User {username} purchased {item['price']} ⭐\nItem: {item['name']}\nTransaction ID: {transaction_id}",
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
