from typing import Dict, Any

ITEMS: Dict[str, Dict[str, Any]] = {
    'ice_cream': {
        'name': 'Ice Cream 🍦',
        'price': 1,
        'description': 'A delicious virtual ice cream',
        'secret': 'FROZEN2025'
    },
    'cookie': {
        'name': 'Cookie 🍪',
        'price': 3,
        'description': 'A sweet virtual cookie',
        'secret': 'SWEET2025'
    },
    'hamburger': {
        'name': 'Hamburger 🍔',
        'price': 5,
        'description': 'A tasty virtual hamburger',
        'secret': 'BURGER2025'
    }
}

MESSAGES = {
    'welcome': (
        "Welcome to the Digital Store! 🎉\n"
        "Select an item to purchase with Telegram Stars:"
    ),
    'help': (
        "🛍 *Digital Store Bot Help*\n\n"
        "Commands:\n"
        "/start - View available items\n"
        "/help - Show this help message\n"
        "/refund - Request a refund (requires transaction ID)\n\n"
        "How to use:\n"
        "1. Use /start to see available items\n"
        "2. Click on an item to purchase\n"
        "3. Pay with Stars\n"
        "4. Receive your secret code\n"
        "5. Use /refund to get a refund if needed"
    ),
    'refund_success': (
        "✅ Refund processed successfully!\n"
        "The Stars have been returned to your balance."
    ),
    'refund_failed': (
        "❌ Refund could not be processed.\n"
        "Please try again later or contact support."
    ),
    'refund_usage': (
        "Please provide the transaction ID after the /refund command.\n"
        "Example: `/refund YOUR_TRANSACTION_ID`"
    )
}
