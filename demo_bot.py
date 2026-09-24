import os
import json
from datetime import datetime
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# --- FLASK KEEP-ALIVE (Чтобы Render не засыпал) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- НАСТРОЙКИ БОТА ---
NAME, PHONE, EDIT_PRICE, EDIT_ADDRESS, EDIT_CONTACTS = range(5)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8688778044 
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "price": "📋 Прайс:\n• Услуга 1 — 1000₽\n• Услуга 2 — 2000₽",
        "address": "📍 Адрес: г. Москва, ул. Примерная, д. 1",
        "contacts": "📞 Контакты: +7 (999) 123-45-67",
        "leads": []
    }

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Данные успешно сохранены в {DATA_FILE}")
    except Exception as e:
        print(f"❌ ОШИБКА СОХРАНЕНИЯ: {e}")

bot_data = load_data()

# --- ОБРАБОТЧИКИ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Прайс", callback_data="price")],
        [InlineKeyboardButton("📍 Адрес", callback_data="address")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
        [InlineKeyboardButton("📝 Записаться", callback_data="signup")],
        [InlineKeyboardButton("📸 Наши работы", callback_data="gallery")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! 👋 Я бот-помощник.\nВыберите пункт:", reply_markup=reply_markup)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("Изменить Прайс", callback_data="edit_price")],
        [InlineKeyboardButton("Изменить Адрес", callback_data="edit_address")],
        [InlineKeyboardButton("Изменить Контакты", callback_data="edit_contacts")],
        [InlineKeyboardButton("️ Помощь", callback_data="help_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("️ Админ-панель. Что меняем?", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    print(f"🔘 Получено нажатие кнопки: {query.data} от пользователя {user_id}")

    # Считаем статистику
    stats = bot_data.setdefault("stats", {})
    if query.data in stats:
        stats[query.data] += 1
    if user_id not in stats.get("users", []):
        stats.setdefault("users", []).append(user_id)
    save_data(bot_data)

    if query.data == "price":
        print("➡️ Отправляем прайс")
        await query.message.reply_text(bot_data["price"])
    elif query.data == "address":
        print("➡️ Отправляем адрес")
        await query.message.reply_text("Мы находимся здесь!")
        await context.bot.send_location(chat_id=query.message.chat_id, latitude=55.751244, longitude=37.618423)
    elif query.data == "contacts":
        print("➡️ Отправляем контакты")
        await query.message.reply_text(bot_data["contacts"])
    elif query.data == "signup":
        print("➡️ Начинаем запись клиента")
        await query.message.reply_text("Как вас зовут? Напишите ваше имя:")
        return NAME
    elif query.data == "gallery":
        print("➡️ Отправляем галерею")
        photo_url = "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1000&q=80"
        await query.message.reply_photo(photo=photo_url, caption="📸 Посмотрите наши работы!")
    elif query.data == "edit_price" and user_id == ADMIN_ID:
        print(f"➡️ Админ хочет изменить прайс (ID: {user_id})")
        await query.message.reply_text("Введите новый текст для Прайса:")
        return EDIT_PRICE
    elif query.data == "edit_address" and user_id == ADMIN_ID:
        print(f"➡️ Админ хочет изменить адрес (ID: {user_id})")
        await query.message.reply_text("Введите новый текст для Адреса:")
        return EDIT_ADDRESS
    elif query.data == "edit_contacts" and user_id == ADMIN_ID:
        print(f"➡️ Админ хочет изменить контакты (ID: {user_id})")
        await query.message.reply_text("Введите новый текст для Контактов:")
        return EDIT_CONTACTS
    elif query.data == "help_admin" and user_id == ADMIN_ID:
        print(f"➡️ Админ запросил помощь (ID: {user_id})")
        help_text = """📋 <b>Админ-команды:</b>

/admin - Открыть панель управления
/leads - Посмотреть все заявки
/stats - Статистика использования
/cancel - Отменить текущее действие

<b>Кнопки в админ-панели:</b>
• Изменить Прайс
• Изменить Адрес
• Изменить Контакты
• Помощь (эта кнопка)"""
        await query.message.reply_text(help_text, parse_mode="HTML")
        
    elif query.data == "edit_price" and user_id == ADMIN_ID:
        print(f"➡️ Админ хочет изменить прайс (ID: {user_id})")
        await query.message.reply_text("Введите новый текст для Прайса:")
        return EDIT_PRICE
    elif query.data == "edit_address" and user_id == ADMIN_ID:
        print(f"️ Админ хочет изменить адрес (ID: {user_id})")
        await query.message.reply_text("Введите новый текст для Адреса:")
        return EDIT_ADDRESS
    elif query.data == "edit_contacts" and user_id == ADMIN_ID:
        print(f"➡️ Админ хочет изменить контакты (ID: {user_id})")
        await query.message.reply_text("Введите новый текст для Контактов:")
        return EDIT_CONTACTS
    elif query.data == "help_admin" and user_id == ADMIN_ID:
        print(f"️ Админ запросил помощь (ID: {user_id})")
        help_text = """📋 <b>Админ-команды:</b>

/admin - Открыть панель управления
/leads - Посмотреть все заявки
/stats - Статистика использования
/cancel - Отменить текущее действие

<b>Кнопки в админ-панели:</b>
• Изменить Прайс
• Изменить Адрес
• Изменить Контакты
• Помощь (эта кнопка)"""
        await query.message.reply_text(help_text, parse_mode="HTML")


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Отлично! Теперь напишите ваш номер телефона:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    
    # Сохраняем заявку в файл
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    new_lead = f"👤 {context.user_data['name']} | 📱 {context.user_data['phone']} | 🕒 {now}"
    bot_data.setdefault("leads", []).append(new_lead)
    save_data(bot_data)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔥 <b>Новая заявка!</b>\n👤 Имя: {context.user_data['name']}\n Телефон: {context.user_data['phone']}",
        parse_mode="HTML"
    )
    await update.message.reply_text("Спасибо! Мы свяжемся с вами.")
    return ConversationHandler.END
async def edit_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_data["price"] = update.message.text
    save_data(bot_data)
    await update.message.reply_text("✅ Прайс успешно обновлен!")
    return ConversationHandler.END

async def edit_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_data["address"] = update.message.text
    save_data(bot_data)
    await update.message.reply_text("✅ Адрес успешно обновлен!")
    return ConversationHandler.END

async def edit_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    print(f"📩 Бот получил новый текст: '{new_text}'")
    
    bot_data["contacts"] = new_text
    save_data(bot_data)
    
    await update.message.reply_text("✅ Контакты успешно обновлены!")
    return ConversationHandler.END

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Эта команда только для админа.")
        return
    
    stats = bot_data.get("stats", {})
    total_users = len(stats.get("users", []))
    
    text = "📊 <b>Статистика бота:</b>\n\n"
    text += f"👥 Уникальных пользователей: {total_users}\n\n"
    text += f"💰 Прайс: {stats.get('price', 0)} нажатий\n"
    text += f"📍 Адрес: {stats.get('address', 0)} нажатий\n"
    text += f"📞 Контакты: {stats.get('contacts', 0)} нажатий\n"
    text += f"📝 Записаться: {stats.get('signup', 0)} нажатий\n"
    text += f"📸 Наши работы: {stats.get('gallery', 0)} нажатий"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено. Нажмите /start.")
    return ConversationHandler.END

# --- ЗАПУСК ---
async def on_startup(application):
    await application.bot.send_message(chat_id=ADMIN_ID, text="🟢 Бот успешно перезапустился и работает!")

def main():
    if not BOT_TOKEN:
        print("Ошибка: Токен бота не найден!")
        return

    keep_alive()

    application = Application.builder().token(BOT_TOKEN).post_init(on_startup).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("leads", show_leads))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button, pattern="^(price|address|contacts|gallery|help_admin)$"))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="^signup$")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    admin_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="^edit_")],
        states={
            EDIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_price)],
            EDIT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_address)],
            EDIT_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_contacts)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(admin_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
