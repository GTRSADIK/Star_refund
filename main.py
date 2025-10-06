import os
import json
import logging
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv
from config import ITEMS, MESSAGES, WELCOME_IMAGE

# Load .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data store
STATS = {'purchases': defaultdict(int), 'refunds': defaultdict(int)}
TRANSACTION_FILE = "transactions.json"
if not os.path.exists(TRANSACTION_FILE):
    with open(TRANSACTION_FILE, "w") as f:
        json.dump({}, f)
with open(TRANSACTION_FILE, "r") as f:
    TRANSACTIONS = json.load(f)

def save_transactions():
    with open(TRANSACTION_FILE, "w") as f:
        json.dump(TRANSACTIONS, f, indent=4)

# Global temp storage for broadcast
ADMIN_STATE = {}

# Start
async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("💫 Send Stars", callback_data="send_stars")]]
    await update.message.reply_photo(
        photo=WELCOME_IMAGE,
        caption=MESSAGES['welcome'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Help
async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(MESSAGES['help'])

# Refund (admin only)
async def refund_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Only admin can use this command.")
        return

    if not context.args:
        await update.message.reply_text(MESSAGES['refund_usage'])
        return

    transaction_id = context.args[0]
    if transaction_id not in TRANSACTIONS:
        await update.message.reply_text("❌ Invalid transaction ID.")
        return

    transaction = TRANSACTIONS.pop(transaction_id)
    save_transactions()
    STATS['refunds'][str(ADMIN_ID)] += transaction['stars']

    await update.message.reply_text(f"✅ Refund successful! {transaction['stars']}⭐ refunded from transaction {transaction_id}.")

# Broadcast (Admin only)
async def broadcast_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not authorized.")
        return
    ADMIN_STATE[user_id] = {"step": "ask_user_id"}
    await update.message.reply_text("📨 Please send the user ID you want to message:")

# Handle admin responses
async def handle_admin_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    # Step 1: ask user ID
    if user_id in ADMIN_STATE and ADMIN_STATE[user_id]["step"] == "ask_user_id":
        try:
            target_id = int(update.message.text.strip())
            ADMIN_STATE[user_id] = {"step": "ask_message", "target_id": target_id}
            await update.message.reply_text(f"✅ Target user set: `{target_id}`\nNow send the message you want to deliver:", parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ Invalid ID. Please send numeric Telegram user ID.")
        return

    # Step 2: send message
    if user_id in ADMIN_STATE and ADMIN_STATE[user_id]["step"] == "ask_message":
        target_id = ADMIN_STATE[user_id]["target_id"]
        text_to_send = update.message.text

        try:
            await context.bot.send_message(chat_id=target_id, text=text_to_send)
            await update.message.reply_text(f"✅ Message delivered successfully to `{target_id}`", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send: {e}")
        ADMIN_STATE.pop(user_id, None)
        return

# Inline buttons
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "send_stars":
        keyboard = [[InlineKeyboardButton(f"{item['name']} - {item['price']}⭐", callback_data=item_id)] for item_id, item in ITEMS.items()]
        await query.message.reply_text("Select item to buy:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    item_id = query.data
    if item_id not in ITEMS:
        return

    item = ITEMS[item_id]
    await context.bot.send_invoice(
        chat_id=query.message.chat.id,
        title=item['name'],
        description=item['description'],
        payload=item_id,
        provider_token="",  # For test mode
        currency="XTR",
        prices=[LabeledPrice(item['name'], int(item['price']))],
        start_parameter="test-payment"
    )

# Pre-checkout
async def precheckout_callback(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    if query.invoice_payload in ITEMS:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Invalid item payload.")

# Payment success
async def successful_payment_callback(update: Update, context: CallbackContext):
    payment = update.message.successful_payment
    item_id = payment.invoice_payload
    item = ITEMS[item_id]
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else f"ID:{user_id}"
    stars = int(item['price'])
    transaction_id = payment.telegram_payment_charge_id

    TRANSACTIONS[transaction_id] = {
        "user_id": user_id,
        "username": username,
        "stars": stars,
        "item": item['name']
    }
    save_transactions()

    STATS['purchases'][str(user_id)] += stars
    await update.message.reply_text(f"✅ {stars}⭐ successfully sent!\nWaiting for admin confirmation.")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 New Purchase:\nUser: {username}\nStars: {stars}\nItem: {item['name']}\nTransaction ID: `{transaction_id}`",
        parse_mode="Markdown"
    )

# Run bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("refund", refund_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_admin_message))

    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
