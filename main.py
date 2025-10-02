import os
import logging
import traceback
from collections import defaultdict
from typing import DefaultDict, Dict
from dotenv import load_dotenv
from telegram import (
    Update, LabeledPrice, InlineKeyboardButton,
    InlineKeyboardMarkup
)
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

STATS: Dict[str, DefaultDict[str, int]] = {
    'purchases': defaultdict(int),
    'refunds': defaultdict(int)
}


async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("💫 Send Stars", callback_data="send_stars")]
    ]

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
        success = await context.bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)
        if success:
            STATS['refunds'][str(user_id)] += 1
            await update.message.reply_text(MESSAGES['refund_success'])
        else:
            await update.message.reply_text(MESSAGES['refund_failed'])
    except Exception as e:
        error_text = ''.join(traceback.format_tb(e.__traceback__))
        logger.error(error_text)
        await update.message.reply_text(f"❌ Error processing refund: {str(e)}")


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


async def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    if query.invoice_payload in ITEMS:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Invalid item.")


async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    payment = update.message.successful_payment
    item_id = payment.invoice_payload
    item = ITEMS[item_id]
    user_id = update.effective_user.id

    STATS['purchases'][str(user_id)] += 1

    await update.message.reply_text(
        f"🎉 Thank you for your purchase!\n\n"
        f"🔐 Secret code for *{item['name']}*:\n`{item['secret']}`\n\n"
        f"💡 To refund, admin can use:\n`/refund {payment.telegram_payment_charge_id}`",
        parse_mode='Markdown'
    )


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
