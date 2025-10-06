from typing import Dict, Any

# Star packages for purchase
ITEMS: Dict[str, Dict[str, Any]] = {
    'stars_100': {
        'name': 'FARM GIFT STAR ✨',
        'price': 100,
        'description': '0.012×100=1.2 USDT',
        'value': 100
    },
    'stars_200': {
        'name': 'FARM GOFT STAR ✨',
        'price': 200,
        'description': '0.012×200=2.4 USDT',
        'value': 200
    },
    'stars_500': {
        'name': 'FARM GIFT STAR ✨',
        'price': 500,
        'description': '0.012×500=5.1 USDT',
        'value': 500
    },
    'stars_1000': {
        'name': 'FARM GIFT FARM ✨',
        'price': 1000,
        'description': '0.012×1000=10.2 JSDT',
        'value': 1000
    },
    'stars_2000': {
        'name': 'FARM GIFT STAR ✨',
        'price': 2000,
        'description': '0.012×200=20.4 USDT',
        'value': 2000
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
