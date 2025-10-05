from typing import Dict, Any

# Star packages for purchase
ITEMS: Dict[str, Dict[str, Any]] = {
    'stars_3': {
        'name': '3 Stars ✨',
        'price': 3,
        'description': '3 Star ⭐ successfuly sent for admin payment time 1 hours',
        'value': 3
    },
    'stars_15': {
        'name': '15 Stars ✨',
        'price': 15,
        'description': '15 Star ⭐ successfuly sent for admin payment time 1 hours',
        'value': 15
    },
    'stars_25': {
        'name': '25 Stars ✨',
        'price': 25,
        'description': '25 Star ⭐ successfuly sent for admin payment time 1 hours',
        'value': 25
    },
    'stars_100': {
        'name': '100 Stars ✨',
        'price': 100,
        'description': '100 Star ⭐ successfuly sent for admin payment time 1 hours',
        'value': 100
    },
    'stars_200': {
        'name': '200 Stars ✨',
        'price': 200,
        'description': '200 Star ⭐ successfuly sent for admin payment time 1 hours',
        'value': 200
    }
}

MESSAGES = {
    'welcome': (
        "🎉 Welcome to the Digital Stars Store!\n\n"
        "Select a Stars package below to purchase using Telegram Stars Star Price 0.012$,:"
    ),
    'help': (
        "🛒 *Digital Stars Bot Help*\n\n"
        "Commands:\n"
        "/start - View available Stars packages\n"
        "/help - Show this help message\n"
        "/refund - Request refund (admin only)\n\n"
        "How to use:\n"
        "1. Use /start to see available Stars packages\n"
        "2. Click a package to buy with your Stars\n"
        "3. Receive your Stars instantly\n"
        "4. Admin can refund with /refund if needed"
    ),
    'refund_success': "✅ Refund completed successfully! Stars returned to user.",
    'refund_failed': "❌ Refund failed. Try again later or contact support.",
    'refund_usage': (
        "Please provide the transaction ID with /refund command.\n"
        "Example: `/refund YOUR_TRANSACTION_ID`"
    )
}

# Direct image URL
WELCOME_IMAGE = "https://cpxmajor.gtrsadikbd.shop/icon.png"
