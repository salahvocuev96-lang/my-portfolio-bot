import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Токен берется из переменных окружения
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие с кнопками"""
    keyboard = [
        [InlineKeyboardButton("💰 Прайс", callback_data="price")],
        [InlineKeyboardButton(" Адрес", callback_data="address")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! 👋 Я бот-помощник.\nВыберите пункт:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок"""
    query = update.callback_query
    await query.answer()

    if query.data == "price":
        text = "📋 Прайс:\n• Услуга 1 — 1000₽\n• Услуга 2 — 2000₽"
    elif query.data == "address":
        text = " Адрес: г. Москва, ул. Примерная, д. 1"
    elif query.data == "contacts":
        text = "📱 Телефон: +7 (999) 123-45-67"
    else:
        text = "Неизвестная команда"

    await query.edit_message_text(text=text)

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
