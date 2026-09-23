import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# Состояния для диалога (сбор имени и телефона)
NAME, PHONE = range(2)

# Токен бота (берется из Render) и твой ID (зашит в код для простоты)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8688778044 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню с кнопками"""
    keyboard = [
        [InlineKeyboardButton("💰 Прайс", callback_data="price")],
        [InlineKeyboardButton("📍 Адрес", callback_data="address")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
        [InlineKeyboardButton(" Записаться", callback_data="signup")],
        [InlineKeyboardButton("📸 Наши работы", callback_data="gallery")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! 👋 Я бот-помощник.\nВыберите пункт:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data == "price":
        text = "📋 Прайс:\n• Услуга 1 — 1000₽\n• Услуга 2 — 2000₽"
        await query.edit_message_text(text=text)
    elif query.data == "address":
        await query.message.reply_text("📍 Мы находимся здесь! Ждем вас.")
        await context.bot.send_location(
            chat_id=query.message.chat_id,
            latitude=55.751244,
            longitude=37.618423
        )
    elif query.data == "contacts":
        text = "📞 Контакты: +7 (999) 123-45-67"
        await query.edit_message_text(text=text)
    elif query.data == "signup":
        await query.message.reply_text("Как вас зовут? Напишите ваше имя:")
        return NAME
    elif query.data == "gallery":
        photo_url = "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1000&q=80"
        await query.message.reply_photo(
            photo=photo_url,
            caption="📸 Посмотрите наши работы! Мы делаем лучший сервис в городе."
        )
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем имя и просим телефон"""
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Отлично! Теперь напишите ваш номер телефона:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем телефон и отправляем заявку тебе"""
    context.user_data['phone'] = update.message.text
    
    # Отправляем заявку тебе в личку
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔥 <b>Новая заявка!</b>\n👤 Имя: {context.user_data['name']}\n📱 Телефон: {context.user_data['phone']}",
        parse_mode="HTML"
    )
    await update.message.reply_text("Спасибо! Мы свяжемся с вами в ближайшее время.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена записи"""
    await update.message.reply_text("Запись отменена. Нажмите /start, чтобы начать заново.")
    return ConversationHandler.END

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        print("Ошибка: Токен бота не найден!")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик обычных кнопок (Прайс, Адрес, Контакты)
    application.add_handler(CallbackQueryHandler(button, pattern="^(price|address|contacts)$"))
    
    # Обработчик кнопки "Записаться" (собирает имя и телефон)
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="^signup$")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
