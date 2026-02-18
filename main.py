# bot.py — Кодекс | Алекс бот 3.0 | Создано Моисеевым Алексеем для Авроры 😈
# Запуск: python bot.py

import logging
import sqlite3
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# ────────────────────────────────────────────────
# Настройки и логи
# ────────────────────────────────────────────────

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = '8396553639:AAEvYPcODVlXxWVSaSwPnkvnXMGzBgjpjFA'  # ← ВСТАВЬ СВОЙ ТОКЕН ОТ BOTFATHER

# Состояния
(
    MAIN_MENU,
    NEURO_MENU,
    CHEATS_MENU,
    PROFILE_MENU,
    BUY_NEURO,
    TEST_NEURO,
    SUPPORT_NEURO,
    SUPPORT_CHEATS,
    REGISTER_EMAIL,
    REGISTER_NAME,
    LOGIN_EMAIL,
    LOGIN_NAME
) = range(12)

# ────────────────────────────────────────────────
# База данных (SQLite)
# ────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                 )''')
    conn.commit()
    conn.close()

init_db()

# ────────────────────────────────────────────────
# Главное меню
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ['Нейросеть', 'Читы на Роблокс'],
        ['Профиль']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text(
        '🔥 Добро пожаловать в **Кодекс** 🔥\n'
        'Выбери, куда ныряем:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MAIN_MENU


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Выбери кнопку из меню, братан 😏")


# ────────────────────────────────────────────────
# Нейросеть → подменю
# ────────────────────────────────────────────────

async def neuro_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Купить нейросеть", callback_data='buy_neuro')],
        [InlineKeyboardButton("Протестировать бесплатно", callback_data='test_neuro')],
        [InlineKeyboardButton("Поддержка по нейросети", callback_data='support_neuro')],
        [InlineKeyboardButton("← Назад", callback_data='back_main')]
    ])
    await update.message.reply_text('🧠 **Нейросеть**', reply_markup=keyboard, parse_mode='Markdown')
    return NEURO_MENU


async def buy_neuro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Леша бот", callback_data='lesha_bot')],
        [InlineKeyboardButton("Аврора", callback_data='avrora')],
        [InlineKeyboardButton("← Назад", callback_data='back_neuro')]
    ])
    await query.edit_message_text('Выбери нейросеть для покупки:', reply_markup=keyboard)
    return BUY_NEURO


async def lesha_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Конечно, держи ссылку на **Леша бот**:\n'
        'https://drive.google.com/file/d/1gjKK4thPSTklaIb2AttHvSuC9tfCS6yz/view?usp=sharing'
    )
    return await neuro_menu(update, context)


async def avrora(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("← Назад", callback_data='back_neuro')]
    ])
    await query.edit_message_text(
        'Аврора появится **30 февраля в 3:00 ночи** 🌙\n(шучу, но кто знает 👀)',
        reply_markup=keyboard
    )
    return BUY_NEURO


async def test_neuro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Тестовый режим активирован! Пиши любой вопрос:')
    return TEST_NEURO


async def test_neuro_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    await update.message.reply_text(
        f'Тестовый ответ от Авроры:\n\n“{text}” → звучит как план по захвату мира 😈\n'
        '(в будущем тут будет нормальная нейронка)'
    )
    return await neuro_menu(update, context)


async def support_neuro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Напиши свой вопрос по нейросети — передадим Алексею 🔥')
    return SUPPORT_NEURO


async def support_neuro_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    await update.message.reply_text(
        f'Вопрос принят:\n“{text}”\n\nСкоро ответим, не скучай 😘'
    )
    return await neuro_menu(update, context)


# ────────────────────────────────────────────────
# Читы на Роблокс
# ────────────────────────────────────────────────

async def cheats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Codex", callback_data='codex')],
        [InlineKeyboardButton("Delta Alex", callback_data='delta')],
        [InlineKeyboardButton("Поддержка по читам", callback_data='support_cheats')],
        [InlineKeyboardButton("← Назад", callback_data='back_main')]
    ])
    await update.message.reply_text('🎮 **Читы на Роблокс**', reply_markup=keyboard, parse_mode='Markdown')
    return CHEATS_MENU


async def codex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Скачать **Codex** → https://www.codex.lol/')
    return await cheats_menu(update, context)


async def delta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("← Назад", callback_data='back_cheats')]
    ])
    await query.edit_message_text('**Delta Alex** давно мёртв 😢', reply_markup=keyboard)
    return CHEATS_MENU


async def support_cheats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Кидай вопрос по читам — разберёмся 💀')
    return SUPPORT_CHEATS


async def support_cheats_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    await update.message.reply_text(f'Вопрос по читам:\n“{text}”\n\nСкоро отпишемся, не спались 😉')
    return await cheats_menu(update, context)


# ────────────────────────────────────────────────
# Профиль / Регистрация / Вход
# ────────────────────────────────────────────────

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Зарегистрироваться", callback_data='register')],
        [InlineKeyboardButton("Войти", callback_data='login')],
        [InlineKeyboardButton("← Назад", callback_data='back_main')]
    ])
    await update.message.reply_text('👤 **Профиль**', reply_markup=keyboard, parse_mode='Markdown')
    return PROFILE_MENU


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Введи свою почту для регистрации:')
    return REGISTER_EMAIL


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    context.user_data['reg_email'] = email

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    exists = c.fetchone()
    conn.close()

    if exists:
        await update.message.reply_text('Эта почта уже занята. Попробуй другую.')
        return REGISTER_EMAIL

    await update.message.reply_text('Круто! Теперь введи своё имя (или ник):')
    return REGISTER_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    email = context.user_data.get('reg_email')

    if not email:
        await update.message.reply_text('Что-то пошло не так... Начни заново /start')
        return await start(update, context)

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, name) VALUES (?, ?)", (email, name))
        conn.commit()
        await update.message.reply_text(f'Добро пожаловать в семью, **{name}**! 🔥')
    except sqlite3.IntegrityError:
        await update.message.reply_text('Почта уже зарегистрирована.')
    finally:
        conn.close()

    return await start(update, context)


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Введи почту, по которой регистрировался:')
    return LOGIN_EMAIL


async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    context.user_data['login_email'] = email

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()

    if not result:
        await update.message.reply_text('Такая почта не найдена. Может зарегистрироваться?')
        return await profile_menu(update, context)

    context.user_data['expected_name'] = result[0]
    await update.message.reply_text('Теперь введи имя/ник, который указывал при регистрации:')
    return LOGIN_NAME


async def login_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    expected = context.user_data.get('expected_name')

    if name == expected:
        await update.message.reply_text(f'Заходи, **{name}**! Всё под контролем 😈')
        return await start(update, context)
    else:
        await update.message.reply_text('Имя не совпадает. Попробуй ещё раз.')
        return LOGIN_NAME


# ────────────────────────────────────────────────
# Кнопки Назад
# ────────────────────────────────────────────────

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await start(update, context)


async def back_neuro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await neuro_menu(update, context)


async def back_cheats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return await cheats_menu(update, context)


# ────────────────────────────────────────────────
# Основной хэндлер
# ────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex('^Нейросеть$'), neuro_menu),
                MessageHandler(filters.Regex('^Читы на Роблокс$'), cheats_menu),
                MessageHandler(filters.Regex('^Профиль$'), profile_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown),
            ],
            NEURO_MENU: [
                CallbackQueryHandler(buy_neuro, pattern='^buy_neuro$'),
                CallbackQueryHandler(test_neuro, pattern='^test_neuro$'),
                CallbackQueryHandler(support_neuro, pattern='^support_neuro$'),
                CallbackQueryHandler(back_main, pattern='^back_main$'),
            ],
            BUY_NEURO: [
                CallbackQueryHandler(lesha_bot, pattern='^lesha_bot$'),
                CallbackQueryHandler(avrora, pattern='^avrora$'),
                CallbackQueryHandler(back_neuro, pattern='^back_neuro$'),
            ],
            TEST_NEURO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, test_neuro_response),
            ],
            SUPPORT_NEURO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, support_neuro_response),
            ],
            CHEATS_MENU: [
                CallbackQueryHandler(codex, pattern='^codex$'),
                CallbackQueryHandler(delta, pattern='^delta$'),
                CallbackQueryHandler(support_cheats, pattern='^support_cheats$'),
                CallbackQueryHandler(back_main, pattern='^back_main$'),
            ],
            SUPPORT_CHEATS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, support_cheats_response),
            ],
            PROFILE_MENU: [
                CallbackQueryHandler(register, pattern='^register$'),
                CallbackQueryHandler(login, pattern='^login$'),
                CallbackQueryHandler(back_main, pattern='^back_main$'),
            ],
            REGISTER_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_email),
            ],
            REGISTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),
            ],
            LOGIN_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_email),
            ],
            LOGIN_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_name),
            ],
        },
        fallbacks=[CallbackQueryHandler(back_main)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(back_neuro, pattern='^back_neuro$'))
    app.add_handler(CallbackQueryHandler(back_cheats, pattern='^back_cheats$'))

    print("🚀 Кодекс запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
