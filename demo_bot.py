import os
import json
import threading
from datetime import datetime, timedelta

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# =========================================================
# FLASK KEEP-ALIVE
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!"


def run_flask():
    app.run(host="0.0.0.0", port=10000)


def keep_alive():
    thread = threading.Thread(target=run_flask)
    thread.daemon = True
    thread.start()


# =========================================================
# НАСТРОЙКИ
# =========================================================

NAME, PHONE, EDIT_PRICE, EDIT_ADDRESS, EDIT_CONTACTS, REVIEW, BROADCAST, EDIT_GALLERY = range(8)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8688778044
DATA_FILE = "bot_data.json"

scheduler = AsyncIOScheduler()


# =========================================================
# РАБОТА С ДАННЫМИ
# =========================================================

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")

    return {
        "price": "📋 Прайс:\n• Услуга 1 — 1000₽\n• Услуга 2 — 2000₽",
        "address": "📍 Адрес: г. Москва, ул. Примерная, д. 1",
        "contacts": "📞 Контакты: +7 (999) 123-45-67",
        "leads": [],
        "reviews": [],
        "stats": {
            "users": [],
            "price": 0,
            "address": 0,
            "contacts": 0,
            "signup": 0,
            "gallery": 0,
            "reviews": 0,
        },
        "gallery_photo_id": None,
    }


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

        print(f"✅ Данные сохранены в {DATA_FILE}")

    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")


bot_data = load_data()


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def register_user(user_id):
    stats = bot_data.setdefault("stats", {})
    users = stats.setdefault("users", [])

    if user_id not in users:
        users.append(user_id)
        save_data(bot_data)


def increment_stat(stat_name):
    stats = bot_data.setdefault("stats", {})
    stats[stat_name] = stats.get(stat_name, 0) + 1
    save_data(bot_data)


# =========================================================
# КЛИЕНТСКОЕ МЕНЮ
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    register_user(user_id)

    keyboard = [
        [InlineKeyboardButton("💰 Прайс", callback_data="price")],
        [InlineKeyboardButton("📍 Адрес", callback_data="address")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
        [InlineKeyboardButton("📝 Записаться", callback_data="signup")],
        [InlineKeyboardButton("📸 Наши работы", callback_data="gallery")],
        [InlineKeyboardButton("⭐ Отзывы", callback_data="reviews")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Я бот-помощник.\n"
        "Выберите нужный пункт:",
        reply_markup=reply_markup,
    )


# =========================================================
# АДМИН-ПАНЕЛЬ
# =========================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа.")
        return

    keyboard = [
        [InlineKeyboardButton("💰 Изменить прайс", callback_data="edit_price")],
        [InlineKeyboardButton("📍 Изменить адрес", callback_data="edit_address")],
        [InlineKeyboardButton("📞 Изменить контакты", callback_data="edit_contacts")],
        [InlineKeyboardButton("📸 Изменить фото", callback_data="edit_gallery")],
        [InlineKeyboardButton("⚙️ Помощь", callback_data="help_admin")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Что хотите изменить?",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


# =========================================================
# CALLBACK-КНОПКИ
# =========================================================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    callback_data = query.data

    print(
        f"🔘 Нажата кнопка: {callback_data} "
        f"от пользователя {user_id}"
    )

    register_user(user_id)

    # -----------------------------------------------------
    # ПРАЙС
    # -----------------------------------------------------

    if callback_data == "price":
        increment_stat("price")

        await query.message.reply_text(
            bot_data.get("price", "Прайс пока не установлен.")
        )

    # -----------------------------------------------------
    # АДРЕС
    # -----------------------------------------------------

    elif callback_data == "address":
        increment_stat("address")

        await query.message.reply_text(
            bot_data.get("address", "Адрес пока не установлен.")
        )

        # Текущая тестовая геолокация Москвы
        await context.bot.send_location(
            chat_id=query.message.chat_id,
            latitude=55.751244,
            longitude=37.618423,
        )

    # -----------------------------------------------------
    # КОНТАКТЫ
    # -----------------------------------------------------

    elif callback_data == "contacts":
        increment_stat("contacts")

        await query.message.reply_text(
            bot_data.get("contacts", "Контакты пока не установлены.")
        )

    # -----------------------------------------------------
    # ЗАПИСЬ
    # -----------------------------------------------------

    elif callback_data == "signup":
        increment_stat("signup")

        context.user_data.clear()

        await query.message.reply_text(
            "📝 <b>Запись</b>\n\n"
            "Как вас зовут?\n"
            "Напишите ваше имя:",
            parse_mode="HTML",
        )

        return NAME

    # -----------------------------------------------------
    # ГАЛЕРЕЯ
    # -----------------------------------------------------

    elif callback_data == "gallery":
        increment_stat("gallery")

        photo_id = bot_data.get("gallery_photo_id")

        if photo_id:
            await query.message.reply_photo(
                photo=photo_id,
                caption="📸 Наши работы",
            )
        else:
            await query.message.reply_text(
                "📸 Галерея пока пуста.\n"
                "Администратор скоро добавит фото."
            )

    # -----------------------------------------------------
    # ОТЗЫВЫ
    # -----------------------------------------------------

    elif callback_data == "reviews":
        increment_stat("reviews")

        reviews = bot_data.get("reviews", [])

        if not reviews:
            text = (
                "⭐ <b>Отзывы наших клиентов</b>\n\n"
                "📭 Пока никто не оставил отзыв.\n"
                "Будьте первым!"
            )
        else:
            last_reviews = reviews[-5:][::-1]

            text = "⭐ <b>Отзывы наших клиентов</b>\n\n"

            for index, review in enumerate(last_reviews, 1):
                text += f"{index}. {review}\n\n"

        keyboard = [
            [
                InlineKeyboardButton(
                    "✍️ Написать отзыв",
                    callback_data="leave_review",
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    # -----------------------------------------------------
    # ОСТАВИТЬ ОТЗЫВ
    # -----------------------------------------------------

    elif callback_data == "leave_review":
        await query.message.reply_text(
            "⭐ <b>Напишите ваш отзыв:</b>",
            parse_mode="HTML",
        )

        return REVIEW

    # -----------------------------------------------------
    # ИЗМЕНЕНИЕ ПРАЙСА
    # -----------------------------------------------------

    elif callback_data == "edit_price":
        if user_id != ADMIN_ID:
            await query.message.reply_text("⛔ Нет доступа.")
            return

        await query.message.reply_text(
            "💰 Введите новый текст для прайса:"
        )

        return EDIT_PRICE

    # -----------------------------------------------------
    # ИЗМЕНЕНИЕ АДРЕСА
    # -----------------------------------------------------

    elif callback_data == "edit_address":
        if user_id != ADMIN_ID:
            await query.message.reply_text("⛔ Нет доступа.")
            return

        await query.message.reply_text(
            "📍 Введите новый текст для адреса:"
        )

        return EDIT_ADDRESS

    # -----------------------------------------------------
    # ИЗМЕНЕНИЕ КОНТАКТОВ
    # -----------------------------------------------------

    elif callback_data == "edit_contacts":
        if user_id != ADMIN_ID:
            await query.message.reply_text("⛔ Нет доступа.")
            return

        await query.message.reply_text(
            "📞 Введите новые контакты:"
        )

        return EDIT_CONTACTS

    # -----------------------------------------------------
    # ИЗМЕНЕНИЕ ФОТО
    # -----------------------------------------------------

    elif callback_data == "edit_gallery":
        if user_id != ADMIN_ID:
            await query.message.reply_text("⛔ Нет доступа.")
            return

        await query.message.reply_text(
            "📸 Отправьте новое фото для галереи:"
        )

        return EDIT_GALLERY

    # -----------------------------------------------------
    # ПОМОЩЬ
    # -----------------------------------------------------

    elif callback_data == "help_admin":
        if user_id != ADMIN_ID:
            await query.message.reply_text("⛔ Нет доступа.")
            return

        help_text = """
📋 <b>Админ-команды:</b>

/admin — открыть админ-панель
/leads — посмотреть заявки
/reviews — посмотреть отзывы
/broadcast — сделать рассылку
/stats — статистика
/cancel — отменить действие

<b>В админ-панели:</b>

💰 Изменить прайс
📍 Изменить адрес
📞 Изменить контакты
📸 Изменить фото
⚙️ Помощь
"""

        await query.message.reply_text(
            help_text,
            parse_mode="HTML",
        )


# =========================================================
# ЗАПИСЬ КЛИЕНТА
# =========================================================

async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "Пожалуйста, напишите ваше имя."
        )
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        "Отлично! 👍\n\n"
        "Теперь напишите ваш номер телефона:"
    )

    return PHONE


async def get_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    phone = update.message.text.strip()

    if not phone:
        await update.message.reply_text(
            "Пожалуйста, укажите номер телефона."
        )
        return PHONE

    context.user_data["phone"] = phone

    name = context.user_data.get("name", "Не указано")

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    new_lead = {
        "name": name,
        "phone": phone,
        "date": now,
        "user_id": update.effective_user.id,
    }

    bot_data.setdefault("leads", []).append(new_lead)
    save_data(bot_data)

    # -----------------------------------------------------
    # НАПОМИНАНИЕ
    # -----------------------------------------------------

    scheduler.add_job(
        send_reminder,
        "date",
        run_date=datetime.now() + timedelta(seconds=30),
        args=[
            context,
            update.effective_user.id,
            name,
        ],
    )

    # -----------------------------------------------------
    # УВЕДОМЛЕНИЕ АДМИНУ
    # -----------------------------------------------------

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔥 <b>Новая заявка!</b>\n\n"
            f"👤 Имя: {name}\n"
            f"📱 Телефон: {phone}\n"
            f"🕒 Дата: {now}"
        ),
        parse_mode="HTML",
    )

    await update.message.reply_text(
        "✅ Спасибо! Заявка принята.\n\n"
        "Мы свяжемся с вами.\n"
        "🔔 Тестовое напоминание придёт через 30 секунд."
    )

    context.user_data.clear()

    return ConversationHandler.END


async def send_reminder(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    name: str,
):
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"🔔 Напоминаем, {name}!\n\n"
                "Вы оставляли заявку.\n"
                "Ждём вас! 😊"
            ),
        )

    except Exception as e:
        print(f"❌ Ошибка отправки напоминания: {e}")


# =========================================================
# ОТЗЫВЫ
# =========================================================

async def get_review(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    review_text = update.message.text.strip()

    if not review_text:
        await update.message.reply_text(
            "Пожалуйста, напишите текст отзыва."
        )
        return REVIEW

    user_name = update.effective_user.full_name or "Аноним"

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    new_review = {
        "name": user_name,
        "date": now,
        "text": review_text,
    }

    bot_data.setdefault("reviews", []).append(new_review)
    save_data(bot_data)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "⭐ <b>Новый отзыв!</b>\n\n"
            f"👤 {user_name}\n"
            f"🕒 {now}\n\n"
            f"💬 {review_text}"
        ),
        parse_mode="HTML",
    )

    await update.message.reply_text(
        "❤️ Спасибо за ваш отзыв!\n\n"
        "Он отправлен администратору."
    )

    return ConversationHandler.END


# =========================================================
# АДМИН: РЕДАКТИРОВАНИЕ
# =========================================================

async def edit_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    bot_data["price"] = update.message.text

    save_data(bot_data)

    await update.message.reply_text(
        "✅ Прайс успешно обновлён!"
    )

    return ConversationHandler.END


async def edit_address(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    bot_data["address"] = update.message.text

    save_data(bot_data)

    await update.message.reply_text(
        "✅ Адрес успешно обновлён!"
    )

    return ConversationHandler.END


async def edit_contacts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    bot_data["contacts"] = update.message.text

    save_data(bot_data)

    await update.message.reply_text(
        "✅ Контакты успешно обновлены!"
    )

    return ConversationHandler.END


async def edit_gallery_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    if not update.message.photo:
        await update.message.reply_text(
            "❌ Это не фотография.\n"
            "Пожалуйста, отправьте изображение."
        )
        return EDIT_GALLERY

    photo_file_id = update.message.photo[-1].file_id

    bot_data["gallery_photo_id"] = photo_file_id

    save_data(bot_data)

    await update.message.reply_text(
        "✅ Фото для галереи успешно обновлено!"
    )

    return ConversationHandler.END


# =========================================================
# АДМИН: ЗАЯВКИ
# =========================================================

async def show_leads(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта команда только для администратора."
        )
        return

    leads = bot_data.get("leads", [])

    if not leads:
        await update.message.reply_text(
            "📭 Пока нет ни одной заявки."
        )
        return

    text = "📋 <b>Все заявки:</b>\n\n"

    for index, lead in enumerate(leads, 1):
        if isinstance(lead, dict):
            text += (
                f"{index}. 👤 {lead.get('name', 'Не указано')}\n"
                f"   📱 {lead.get('phone', 'Не указано')}\n"
                f"   🕒 {lead.get('date', 'Не указано')}\n\n"
            )
        else:
            text += f"{index}. {lead}\n\n"

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================================================
# АДМИН: ОТЗЫВЫ
# =========================================================

async def show_reviews(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта команда только для администратора."
        )
        return

    reviews = bot_data.get("reviews", [])

    if not reviews:
        await update.message.reply_text(
            "📭 Пока нет ни одного отзыва."
        )
        return

    text = "⭐ <b>Все отзывы:</b>\n\n"

    for index, review in enumerate(reviews, 1):
        if isinstance(review, dict):
            text += (
                f"{index}. 👤 {review.get('name', 'Аноним')}\n"
                f"   🕒 {review.get('date', '')}\n"
                f"   💬 {review.get('text', '')}\n\n"
            )
        else:
            text += f"{index}. {review}\n\n"

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================================================
# РАССЫЛКА
# =========================================================

async def start_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта команда только для администратора."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "📢 Введите текст для рассылки всем пользователям:"
    )

    return BROADCAST


async def process_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    broadcast_text = update.message.text

    users = bot_data.get("stats", {}).get("users", [])

    success = 0
    failed = 0

    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=broadcast_text,
            )

            success += 1

        except Exception as e:
            print(
                f"❌ Не удалось отправить сообщение "
                f"{user_id}: {e}"
            )
            failed += 1

    await update.message.reply_text(
        "📢 <b>Рассылка завершена!</b>\n\n"
        f"✅ Успешно отправлено: {success}\n"
        f"❌ Ошибок: {failed}",
        parse_mode="HTML",
    )

    return ConversationHandler.END


# =========================================================
# СТАТИСТИКА
# =========================================================

async def show_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ Эта команда только для администратора."
        )
        return

    stats = bot_data.get("stats", {})

    total_users = len(stats.get("users", []))

    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Уникальных пользователей: {total_users}\n\n"
        f"💰 Прайс: {stats.get('price', 0)}\n"
        f"📍 Адрес: {stats.get('address', 0)}\n"
        f"📞 Контакты: {stats.get('contacts', 0)}\n"
        f"📝 Записаться: {stats.get('signup', 0)}\n"
        f"📸 Наши работы: {stats.get('gallery', 0)}\n"
        f"⭐ Отзывы: {stats.get('reviews', 0)}"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# =========================================================
# ОТМЕНА
# =========================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Действие отменено.\n\n"
        "Нажмите /start, чтобы открыть главное меню."
    )

    return ConversationHandler.END


# =========================================================
# STARTUP
# =========================================================

async def on_startup(application):
    try:
        scheduler.start()
        print("✅ Планировщик запущен.")
    except Exception as e:
        print(f"⚠️ Планировщик: {e}")

    try:
        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text="🟢 Бот успешно перезапустился и работает!"
        )
    except Exception as e:
        print(f"⚠️ Не удалось отправить сообщение админу: {e}")


# =========================================================
# MAIN
# =========================================================

def main():
    if not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения.")
        return

    print("🚀 Запуск бота...")

    keep_alive()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(on_startup)
        .build()
    )

    # -----------------------------------------------------
    # КОМАНДЫ
    # -----------------------------------------------------

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("admin", admin)
    )

    application.add_handler(
        CommandHandler("leads", show_leads)
    )

    application.add_handler(
        CommandHandler("reviews", show_reviews)
    )

    application.add_handler(
        CommandHandler("stats", show_stats)
    )

    # -----------------------------------------------------
    # CLIENT CONVERSATION
    # -----------------------------------------------------

    client_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                button,
                pattern="^(signup|leave_review)$"
            ),
            CommandHandler(
                "broadcast",
                start_broadcast
            ),
        ],

        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name
                )
            ],

            PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_phone
                )
            ],

            REVIEW: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_review
                )
            ],

            BROADCAST: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    process_broadcast
                )
            ],
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                cancel
            )
        ],
    )

    application.add_handler(client_conversation)

    # -----------------------------------------------------
    # ADMIN CONVERSATION
    # -----------------------------------------------------

    admin_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                button,
                pattern="^edit_(price|address|contacts|gallery)$"
            )
        ],

        states={
            EDIT_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_price
                )
            ],

            EDIT_ADDRESS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_address
                )
            ],

            EDIT_CONTACTS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_contacts
                )
            ],

            EDIT_GALLERY: [
                MessageHandler(
                    filters.PHOTO,
                    edit_gallery_photo
                )
            ],
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                cancel
            )
        ],
    )

    application.add_handler(admin_conversation)

    # -----------------------------------------------------
    # ОСТАЛЬНЫЕ CALLBACK-КНОПКИ
    # -----------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            button,
            pattern="^(price|address|contacts|gallery|reviews|help_admin)$"
        )
    )

    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    application.add_handler(
        CommandHandler("cancel", cancel)
    )

    # -----------------------------------------------------
    # ЗАПУСК
    # -----------------------------------------------------

    print("🟢 Бот запущен и ожидает сообщения...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
