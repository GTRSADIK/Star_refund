import os
import logging
import traceback
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
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Stats & balances
STATS: Dict[str, DefaultDict] = {
    'purchases': defaultdict(list),   # user_id -> list of payments
    'refunds': defaultdict(list)      # user_id -> list of refunded payments
}

ADMIN_BALANCE = 0

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

# Refund command (user can refund, stars go to admin)
async def refund_command(update: Update, context: CallbackContext) -> None:
    global ADMIN_BALANCE
    if not context.args:
        await update.message.reply_text("Usage: /refund <transaction_id>")
        return

    refund_id = context.args[0]
    found = False
    user_id = update.effective_user.id
    username = f"@{update.effective_user.username}" if update.effective_user.username else f"ID: {user_id}"

    # Search in purchases
    for uid, tx_list in STATS['purchases'].items():
        for tx in tx_list:
            if tx['id'] == refund_id:
                # Remove from user
                tx_list.remove(tx)
                STATS['refunds'][uid].append(tx)

                # Add stars to admin balance
                ADMIN_BALANCE += tx['stars']

                found = True

                # Notify admin
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"📩 Refund processed!\nUser: {username}\nStars refunded: {tx['stars']}\nTransaction ID: {refund_id}\nAdmin balance: {ADMIN_BALANCE}"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin: {e}")

                await update.message.reply_text(f"✅ Refund successful. Stars sent to admin.")
                break
        if found:
            break

    if not found:
        await update.message.reply_text(f"❌ Transaction ID {refund_id} not found")

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
        provider_token="",  # leave empty for Stars
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

    # Save transaction
    STATS['purchases'][str(user_id)].append({
        "id": payment.telegram_payment_charge_id,
        "stars": item['price'],
        "item": item['name']
    })

    # Notify user
    await update.message.reply_text(
        f"✅ {item['price']} Star(s) successfully sent!\n💰 Waiting for admin payment within 1 hour.",
        parse_mode='Markdown'
    )

    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 User {username} just sent {item['price']}⭐ for *{item['name']}*.\nTransaction ID: {payment.telegram_payment_charge_id}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

# Main
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
