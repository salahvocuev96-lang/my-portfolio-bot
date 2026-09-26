import os
import json
from datetime import datetime, timedelta
import threading
from flask import Flask, send_file
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- FLASK KEEP-ALIVE ---
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

# --- НАСТРОЙКИ ---
(
    NAME, PHONE, DATE, TIME, 
    EDIT_PRICE, EDIT_ADDRESS, EDIT_CONTACTS, 
    REVIEW, BROADCAST, EDIT_GALLERY, EDIT_FAQ, EDIT_PROMO,
    CHAT_WITH_ADMIN
) = range(13)

BOT_TOKEN = os.environ.get("8823273688:AAHHkuNlI_qKOVGVQYAfJEXWlx3fkfqZLNQ")
ADMIN_ID = 8688778044
DATA_FILE = "bot_data.json"

scheduler = AsyncIOScheduler()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "price": "📋 Прайс:\n• Услуга 1 — 1000₽\n• Услуга 2 — 2000₽",
        "address": "📍 Адрес: г. Москва, ул. Примерная, д. 1",
        "contacts": "📞 Контакты: +7 (999) 123-45-67",
        "leads": [],
        "reviews": [],
        "faq": [
            {"q": "Как записаться?", "a": "Нажмите кнопку 'Записаться' в главном меню."},
            {"q": "Есть ли парковка?", "a": "Да, бесплатная парковка во дворе."},
            {"q": "Какой график работы?", "a": "Пн-Вс с 9:00 до 21:00"}
        ],
        "promo": {"text": " Скидка 20% на первое посещение!", "photo_id": None},
        "gallery": [],
        "stats": {"users": [], "buttons": {}},
        "reminders": []
    }

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Данные сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

bot_data = load_data()

# --- ОБРАБОТЧИКИ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    
    # Сохраняем пользователя
    stats = bot_data.setdefault("stats", {})
    if user_id not in stats.get("users", []):
        stats.setdefault("users", []).append(user_id)
        save_data(bot_data)
        
        # Уведомление админу о новом пользователе
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👤 <b>Новый пользователь!</b>\nID: {user_id}\nИмя: {user_name}",
            parse_mode="HTML"
        )
    
    keyboard = [
        [InlineKeyboardButton("💰 Прайс", callback_data="price")],
        [InlineKeyboardButton("📍 Адрес", callback_data="address")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
        [InlineKeyboardButton("📝 Записаться", callback_data="signup")],
        [InlineKeyboardButton("📸 Галерея", callback_data="gallery_0")],
        [InlineKeyboardButton("⭐ Отзывы", callback_data="reviews_menu")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("🔥 Акции", callback_data="promo")],
        [InlineKeyboardButton("💬 Чат с админом", callback_data="chat_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Привет, {user_name}! 👋\nЯ бот-помощник. Выберите раздел:",
        reply_markup=reply_markup
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("✏️ Прайс", callback_data="edit_price")],
        [InlineKeyboardButton("📍 Адрес", callback_data="edit_address")],
        [InlineKeyboardButton("📞 Контакты", callback_data="edit_contacts")],
        [InlineKeyboardButton(" Галерея", callback_data="edit_gallery")],
        [InlineKeyboardButton("❓ FAQ", callback_data="edit_faq")],
        [InlineKeyboardButton("🔥 Акции", callback_data="edit_promo")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(" Экспорт заявок", callback_data="export")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton("⚙️ Помощь", callback_data="help_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Админ-панель:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    # Статистика
    stats = bot_data.setdefault("stats", {})
    button_stats = stats.setdefault("buttons", {})
    button_stats[query.data] = button_stats.get(query.data, 0) + 1
    save_data(bot_data)
    
    # Обработка кнопок
    if query.data == "price":
        await query.message.reply_text(bot_data["price"])
    
    elif query.data == "address":
        await query.message.reply_text(bot_data["address"])
        await context.bot.send_location(
            chat_id=query.message.chat_id,
            latitude=55.751244,
            longitude=37.618423
        )
    
    elif query.data == "contacts":
        await query.message.reply_text(bot_data["contacts"])
    
    elif query.data == "signup":
        await query.message.reply_text("Как вас зовут?")
        return NAME
    
    elif query.data.startswith("gallery_"):
        page = int(query.data.split("_")[1])
        gallery = bot_data.get("gallery", [])
        if not gallery:
            await query.message.reply_text("📸 Галерея пуста")
            return
        
        total_pages = len(gallery)
        photo_id = gallery[page]
        
        keyboard = []
        if page > 0:
            keyboard.append(InlineKeyboardButton("◀️", callback_data=f"gallery_{page-1}"))
        keyboard.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            keyboard.append(InlineKeyboardButton("▶️", callback_data=f"gallery_{page+1}"))
        
        reply_markup = InlineKeyboardMarkup([keyboard])
        await query.message.reply_photo(photo=photo_id, reply_markup=reply_markup)
    
    elif query.data == "reviews_menu":
        reviews = bot_data.get("reviews", [])
        if not reviews:
            text = "📭 Пока нет отзывов. Будьте первым!"
        else:
            last_reviews = reviews[-5:][::-1]
            text = "💬 <b>Отзывы клиентов:</b>\n\n"
            for i, review in enumerate(last_reviews, 1):
                text += f"{i}. {review}\n\n"
        
        keyboard = [[InlineKeyboardButton("✍️ Написать отзыв", callback_data="leave_review")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    
    elif query.data == "faq":
        faq_list = bot_data.get("faq", [])
        keyboard = [[InlineKeyboardButton(item["q"], callback_data=f"faq_{i}")] for i, item in enumerate(faq_list)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("❓ Частые вопросы:", reply_markup=reply_markup)
    
    elif query.data.startswith("faq_"):
        idx = int(query.data.split("_")[1])
        faq_list = bot_data.get("faq", [])
        if idx < len(faq_list):
            await query.message.reply_text(f"<b>{faq_list[idx]['q']}</b>\n\n{faq_list[idx]['a']}", parse_mode="HTML")
    
    elif query.data == "promo":
        promo = bot_data.get("promo", {})
        if promo.get("photo_id"):
            await query.message.reply_photo(photo=promo["photo_id"], caption=promo.get("text", ""))
        else:
            await query.message.reply_text(promo.get("text", "🔥 Акции скоро появятся!"))
    
    elif query.data == "chat_admin":
        await query.message.reply_text("Напишите ваше сообщение, и администратор ответит вам.")
        return CHAT_WITH_ADMIN
    
    # Админские кнопки
    elif query.data == "edit_price" and user_id == ADMIN_ID:
        await query.message.reply_text("Введите новый прайс:")
        return EDIT_PRICE
    
    elif query.data == "edit_address" and user_id == ADMIN_ID:
        await query.message.reply_text("Введите новый адрес:")
        return EDIT_ADDRESS
    
    elif query.data == "edit_contacts" and user_id == ADMIN_ID:
        await query.message.reply_text("Введите новые контакты:")
        return EDIT_CONTACTS
    
    elif query.data == "edit_gallery" and user_id == ADMIN_ID:
        await query.message.reply_text("Отправьте фото для галереи (можно несколько):")
        return EDIT_GALLERY
    
    elif query.data == "edit_faq" and user_id == ADMIN_ID:
        await query.message.reply_text("Введите вопрос и ответ в формате:\nВопрос\nОтвет")
        return EDIT_FAQ
    
    elif query.data == "edit_promo" and user_id == ADMIN_ID:
        await query.message.reply_text("Отправьте фото акции с подписью (текст акции):")
        return EDIT_PROMO
    
    elif query.data == "stats" and user_id == ADMIN_ID:
        await show_stats(update, context)
    
    elif query.data == "export" and user_id == ADMIN_ID:
        await export_leads(update, context)
    
    elif query.data == "broadcast" and user_id == ADMIN_ID:
        await query.message.reply_text("Введите текст для рассылки:")
        return BROADCAST
    
    elif query.data == "help_admin" and user_id == ADMIN_ID:
        help_text = """📋 <b>Админ-команды:</b>

/admin - Админ-панель
/leads - Все заявки
/reviews - Все отзывы
/broadcast - Рассылка
/stats - Статистика
/export - Экспорт заявок
/cancel - Отменить действие

<b>Кнопки:</b>
• Редактирование прайса, адреса, контактов
• Управление галереей и FAQ
• Акции и спецпредложения
• Удаление заявок"""
        await query.message.reply_text(help_text, parse_mode="HTML")
    
    elif query.data.startswith("delete_lead_") and user_id == ADMIN_ID:
        idx = int(query.data.split("_")[2])
        leads = bot_data.get("leads", [])
        if idx < len(leads):
            deleted = leads.pop(idx)
            save_data(bot_data)
            await query.message.reply_text(f"🗑 Заявка удалена:\n{deleted}")
    
    elif query.data == "leave_review":
        await query.message.reply_text("Напишите ваш отзыв:")
        return REVIEW
    
    elif query.data == "noop":
        pass

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Ваш номер телефона?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Дата записи (ДД.ММ.ГГГГ)?")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("Время записи (ЧЧ:ММ)?")
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    new_lead = {
        "name": context.user_data['name'],
        "phone": context.user_data['phone'],
        "date": context.user_data['date'],
        "time": context.user_data['time'],
        "created": now
    }
    bot_data.setdefault("leads", []).append(new_lead)
    save_data(bot_data)
    
    # Напоминание за час до записи
    try:
        reminder_time = datetime.strptime(f"{new_lead['date']} {new_lead['time']}", "%d.%m.%Y %H:%M") - timedelta(hours=1)
        if reminder_time > datetime.now():
            scheduler.add_job(
                send_reminder,
                'date',
                run_date=reminder_time,
                args=[context, update.effective_user.id, new_lead['name'], new_lead['date'], new_lead['time']]
            )
    except:
        pass
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔥 <b>Новая заявка!</b>\n👤 {new_lead['name']}\n📱 {new_lead['phone']}\n📅 {new_lead['date']} в {new_lead['time']}",
        parse_mode="HTML"
    )
    await update.message.reply_text("✅ Вы записаны! Напоминание придет за час до визита.")
    return ConversationHandler.END

async def send_reminder(context: ContextTypes.DEFAULT_TYPE, user_id: int, name: str, date: str, time: str):
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔔 Напоминание: {name}, вы записаны {date} в {time}. Ждем вас!"
        )
    except Exception as e:
        print(f"Ошибка напоминания: {e}")

async def edit_gallery_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        bot_data.setdefault("gallery", []).append(photo_file_id)
        save_data(bot_data)
        await update.message.reply_text("✅ Фото добавлено в галерею!")
    else:
        await update.message.reply_text("❌ Это не фото")
    return ConversationHandler.END

async def edit_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_data["price"] = update.message.text
    save_data(bot_data)
    await update.message.reply_text("✅ Прайс обновлен!")
    return ConversationHandler.END

async def edit_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_data["address"] = update.message.text
    save_data(bot_data)
    await update.message.reply_text("✅ Адрес обновлен!")
    return ConversationHandler.END

async def edit_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_data["contacts"] = update.message.text
    save_data(bot_data)
    await update.message.reply_text("✅ Контакты обновлены!")
    return ConversationHandler.END

async def edit_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = update.message.text.split("\n", 1)
    if len(lines) == 2:
        bot_data.setdefault("faq", []).append({"q": lines[0], "a": lines[1]})
        save_data(bot_data)
        await update.message.reply_text("✅ Вопрос добавлен в FAQ!")
    else:
        await update.message.reply_text("❌ Формат: Вопрос\\nОтвет")
    return ConversationHandler.END

async def edit_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        caption = update.message.caption or "🔥 Акция!"
        bot_data["promo"] = {"text": caption, "photo_id": photo_file_id}
        save_data(bot_data)
        await update.message.reply_text("✅ Акция обновлена!")
    else:
        await update.message.reply_text("❌ Отправьте фото с подписью")
    return ConversationHandler.END

async def get_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    review_text = update.message.text
    user_name = context.user_data.get('name', 'Аноним')
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    new_review = f" {user_name} | 🕒 {now}\n💬 {review_text}"
    
    bot_data.setdefault("reviews", []).append(new_review)
    save_data(bot_data)
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"⭐ <b>Новый отзыв!</b>\n{new_review}",
        parse_mode="HTML"
    )
    await update.message.reply_text("✅ Спасибо за отзыв!")
    return ConversationHandler.END

async def chat_with_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💬 <b>Сообщение от клиента:</b>\n👤 {user_name} (ID: {user_id})\n\n{message_text}",
        parse_mode="HTML"
    )
    await update.message.reply_text("✅ Сообщение отправлено администратору. Ожидайте ответа.")
    return ConversationHandler.END

async def show_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    leads = bot_data.get("leads", [])
    if not leads:
        await update.message.reply_text("📭 Нет заявок")
        return
    
    for i, lead in enumerate(leads):
        text = f"📋 <b>Заявка #{i+1}</b>\n👤 {lead['name']}\n📱 {lead['phone']}\n📅 {lead['date']} в {lead['time']}"
        keyboard = [[InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_lead_{i}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)

async def show_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    reviews = bot_data.get("reviews", [])
    if not reviews:
        await update.message.reply_text("📭 Нет отзывов")
        return
    
    text = "⭐ <b>Все отзывы:</b>\n\n"
    for i, review in enumerate(reviews, 1):
        text += f"{i}. {review}\n\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    stats = bot_data.get("stats", {})
    total_users = len(stats.get("users", []))
    button_stats = stats.get("buttons", {})
    
    text = f"📊 <b>Статистика:</b>\n\n👥 Пользователей: {total_users}\n\n"
    text += "<b>Нажатия кнопок:</b>\n"
    for btn, count in sorted(button_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        text += f"• {btn}: {count}\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def export_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    leads = bot_data.get("leads", [])
    if not leads:
        await update.message.reply_text("📭 Нет заявок для экспорта")
        return
    
    filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for i, lead in enumerate(leads, 1):
            f.write(f"{i}. {lead['name']} | {lead['phone']} | {lead['date']} {lead['time']}\n")
    
    with open(filename, "rb") as f:
        await update.message.reply_document(document=f, filename=filename)
    
    os.remove(filename)
    await update.message.reply_text("✅ Файл отправлен!")

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Введите текст для рассылки:")
    return BROADCAST

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    users = bot_data.get("stats", {}).get("users", [])
    
    success = 0
    failed = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
            success += 1
        except:
            failed += 1
    
    await update.message.reply_text(f"✅ Рассылка завершена!\nОтправлено: {success}\nОшибок: {failed}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(" Действие отменено")
    return ConversationHandler.END

# --- ЗАПУСК ---
async def on_startup(application):
    scheduler.start()
    await application.bot.send_message(chat_id=ADMIN_ID, text="🟢 Бот запущен!")

def main():
    if not BOT_TOKEN:
        print("Ошибка: Токен не найден!")
        return
    
    keep_alive()
    
    application = Application.builder().token(BOT_TOKEN).post_init(on_startup).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("leads", show_leads))
    application.add_handler(CommandHandler("reviews", show_reviews))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button, pattern="^(price|address|contacts|gallery_|reviews_menu|faq|faq_|promo|chat_admin|edit_|stats|export|broadcast|help_admin|delete_lead_|leave_review|noop)$"))
    
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button, pattern="^(signup|leave_review|chat_admin)$"),
            CommandHandler("broadcast", start_broadcast)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            REVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_review)],
            BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_broadcast)],
            CHAT_WITH_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_admin)],
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
            EDIT_GALLERY: [MessageHandler(filters.PHOTO, edit_gallery_photo)],
            EDIT_FAQ: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_faq)],
            EDIT_PROMO: [MessageHandler(filters.PHOTO, edit_promo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(admin_handler)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
