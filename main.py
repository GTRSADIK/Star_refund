import os
import logging
import traceback
from collections import defaultdict
from typing import DefaultDict, Dict
from dotenv import load_dotenv
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    PreCheckoutQueryHandler,
    CallbackContext
)
from config import ITEMS, MESSAGES, WELCOME_IMAGE

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '123456789'))

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stats
STATS: Dict[str, DefaultDict[str, int]] = {
    'purchases': defaultdict(int),
    'refunds': defaultdict(int)
}

# Conversation state for amount input
AMOUNT_INPUT = range(1)

async def start(update: Update, context: CallbackContext) -> None:
    """Send welcome image + inline buy button"""
    keyboard = [[InlineKeyboardButton("Buy with ⭐", callback_data="buy_star")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=MESSAGES['welcome'],
            reply_markup=reply_markup
        )

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(MESSAGES['help'], parse_mode='Markdown')

async def refund_command(update: Update, context: CallbackContext) -> None:
    """Admin-only refund"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can issue refunds.")
        return
    if not context.args:
        await update.message.reply_text(MESSAGES['refund_usage'])
        return
    try:
        charge_id = context.args[0]
        success = await context.bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=charge_id)
        if success:
            STATS['refunds'][str(user_id)] += 1
            await update.message.reply_text(MESSAGES['refund_success'])
        else:
            await update.message.reply_text(MESSAGES['refund_failed'])
    except Exception as e:
        logger.error(traceback.format_exc())
        await update.message.reply_text(f"❌ Error processing refund:\n{type(e).__name__} - {str(e)}")

# -------------------
# Buy with Stars flow
# -------------------
async def button_handler(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()
    if query.data == "buy_star":
        await query.message.reply_text("Enter the amount of Stars you want to pay (max 10000):")
        return AMOUNT_INPUT
    return ConversationHandler.END

async def amount_input(update: Update, context: CallbackContext) -> int:
    try:
        amount = int(update.message.text)
        if amount < 1 or amount > 10000:
            await update.message.reply_text("❌ Invalid amount. Please enter a value between 1 and 10000.")
            return AMOUNT_INPUT

        context.user_data['star_amount'] = amount

        # Example: use a dummy item for payment (can replace with real logic)
        item = ITEMS['ice_cream']
        await context.bot.send_invoice(
            chat_id=update.message.chat_id,
            title=f"Payment of {amount} Stars",
            description=f"Pay {amount} Stars for {item['name']}",
            payload=f"star_{amount}",
            provider_token="",  # Telegram Stars token
            currency="XTR",
            prices=[LabeledPrice(f"{item['name']} ({amount} ⭐)", amount)],
            start_parameter="start_parameter"
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return AMOUNT_INPUT

async def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    STATS['purchases'][str(user_id)] += 1
    await update.message.reply_text(f"✅ Payment successful! You paid {payment.total_amount} Stars.")

async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={AMOUNT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_input)]},
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("refund", refund_command))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
