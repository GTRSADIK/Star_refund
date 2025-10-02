from typing import Dict, Any

ITEMS: Dict[str, Dict[str, Any]] = {
    'ice_cream': {
        'name': 'Ice Cream 🍦',
        'price': 1,
        'description': 'Enjoy a virtual ice cream!',
        'secret': 'FROZEN2025'
    },
    'cookie': {
        'name': 'Cookie 🍪',
        'price': 3,
        'description': 'A sweet virtual cookie for you!',
        'secret': 'SWEET2025'
    },
    'hamburger': {
        'name': 'Hamburger 🍔',
        'price': 5,
        'description': 'Tasty virtual hamburger!',
        'secret': 'BURGER2025'
    }
}

MESSAGES = {
    'welcome': (
        "🎉 Welcome to the Digital Stars Store!\n\n"
        "Select an item below to purchase using Telegram Stars:"
    ),
    'help': (
        "🛒 *Digital Stars Bot Help*\n\n"
        "Commands:\n"
        "/start - View available items\n"
        "/help - Show this help message\n"
        "/refund - Request refund (admin only)\n\n"
        "How to use:\n"
        "1. Use /start to see items\n"
        "2. Click an item to buy with Stars\n"
        "3. Receive your secret code\n"
        "4. Admin can refund with /refund if needed"
    ),
    'refund_success': (
        "✅ Refund completed successfully! Stars returned to user."
    ),
    'refund_failed': (
        "❌ Refund failed. Try again later or contact support."
    ),
    'refund_usage': (
        "Please provide the transaction ID with /refund command.\n"
        "Example: `/refund YOUR_TRANSACTION_ID`"
    )
}

WELCOME_IMAGE = "https://example.com/welcome_image.png"
