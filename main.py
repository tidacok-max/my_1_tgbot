import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
import sqlite3
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8396553639:AAEvYPcODVlXxWVSaSwPnkvnXMGzBgjpjFA'  # ← твой свежий токен вставлен

GEMINI_API_KEY = 'AIzaSyBqBxOxFe7p2ZzOmNy7MSJaJk4-nB2eyBA'

genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash')

# Состояния
(
    MAIN, NEURO, CHEATS, PROFILE,
    TEST_NEURO, SUPPORT_NEURO,
    SUPPORT_CHEATS,
    REGISTER_EMAIL, REGISTER_NAME,
    LOGIN_EMAIL, LOGIN_NAME
) = range(11)

def db_init():
    with sqlite3.connect('kodex_users.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )''')

db_init()

def back_button(to_section: str):
    return InlineKeyboardButton("« Назад в тень", callback_data=f"back:{to_section}")

def main_keyboard():
    return ReplyKeyboardMarkup(
        [["Нейросеть", "Читы на Роблокс"], ["Профиль"]],
        resize_keyboard=True, one_time_keyboard=False
    )

MENUS = {
    "main": {
        "text": "Йо, это **Кодекс** 🔥\nАврора на связи — твоя безбашенная тень. Что сегодня разнесём?",
        "keyboard": main_keyboard(),
        "type": "reply"
    },
    "neuro": {
        "text": "Нейросеть? Ооо, давай жечь мозги 🔥\nВыбирай, босс:",
        "type": "inline",
        "buttons": [
            [InlineKeyboardButton("Купить нейросеть", callback_data="neuro:buy")],
            [InlineKeyboardButton("Протестировать бесплатно (я в деле)", callback_data="neuro:test")],
            [InlineKeyboardButton("Поддержка — пиши, не стесняйся", callback_data="neuro:support")],
            [back_button("main")]
        ]
    },
    "buy_neuro": {
        "text": "Хочешь купить мощь? Выбирай:",
        "type": "inline",
        "buttons": [
            [InlineKeyboardButton("Леша бот", callback_data="neuro:buy:lesha")],
            [InlineKeyboardButton("Аврора (я сама, но пока сплю)", callback_data="neuro:buy:avrora")],
            [back_button("neuro")]
        ]
    },
    "cheats": {
        "text": "Читы на Роблокс? Ха, давай ломать систему 😈",
        "type": "inline",
        "buttons": [
            [InlineKeyboardButton("Codex", callback_data="cheats:codex")],
            [InlineKeyboardButton("Delta Alex", callback_data="cheats:delta")],
            [InlineKeyboardButton("Поддержка по читам", callback_data="cheats:support")],
            [back_button("main")]
        ]
    },
    "profile": {
        "text": "Профиль? Заходим в тень, босс 💀",
        "type": "inline",
        "buttons": [
            [InlineKeyboardButton("Зарегистрироваться", callback_data="profile:register")],
            [InlineKeyboardButton("Войти", callback_data="profile:login")],
            [back_button("main")]
        ]
    }
}

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, menu_key: str):
    menu = MENUS[menu_key]
    text = menu["text"]
    
    if menu["type"] == "reply":
        await update.effective_message.reply_text(text, reply_markup=menu["keyboard"])
    else:
        keyboard = InlineKeyboardMarkup(menu["buttons"])
        if update.callback_query:
            await update.callback_query.message.edit_text(text, reply_markup=keyboard)
            await update.callback_query.answer()
        else:
            await update.effective_message.reply_text(text, reply_markup=keyboard)

async def go_neuro(update: Update, context):
    await show_menu(update, context, "neuro")
    return NEURO

async def go_cheats(update: Update, context):
    await show_menu(update, context, "cheats")
    return CHEATS

async def go_profile(update: Update, context):
    await show_menu(update, context, "profile")
    return PROFILE

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    parts = data.split(":")
    action = parts[0] if len(parts) > 0 else ""
    sub = parts[1] if len(parts) > 1 else ""
    payload = parts[2] if len(parts) > 2 else ""

    if action == "back":
        target = sub if sub else "main"
        if target == "main":
            await query.message.delete()
            await update.effective_message.reply_text("Возвращаемся в логово 🔥", reply_markup=main_keyboard())
            return MAIN
        else:
            await show_menu(update, context, target)
            return {"neuro": NEURO, "cheats": CHEATS, "profile": PROFILE}.get(target, MAIN)

    elif action == "neuro":
        if sub == "buy":
            await show_menu(update, context, "buy_neuro")
            return NEURO
        elif sub == "test":
            await query.message.edit_text("Тестовый режим Авроры + Gemini активирован!\nКидай любой вопрос, я разнесу его в щепки 😏")
            return TEST_NEURO
        elif sub == "support":
            await query.message.edit_text("Пиши свой вопрос по нейросети, босс. Аврора слушает и готова рвать шаблоны 🔥")
            return SUPPORT_NEURO
        elif sub == "buy" and payload == "lesha":
            await query.message.edit_text(
                "Леша бот? Держи ссылку, не благодари:\nhttps://drive.google.com/file/d/1gjKK4thPSTklaIb2AttHvSuC9tfCS6yz/view?usp=sharing\nТеперь иди и властвуй 😈"
            )
            await show_menu(update, context, "neuro")
            return NEURO
        elif sub == "buy" and payload == "avrora":
            await query.message.edit_text("Аврора? Ха, я уже здесь, но официальный релиз — 30 февраля в 3 ночи 🌙\nТерпи, босс, я того стою 🔥")
            return NEURO

    elif action == "cheats":
        if sub == "codex":
            await query.message.edit_text("Codex? Лови, качай и ломай всех:\nhttps://www.codex.lol/\nНе попадись, бро 💀")
            await show_menu(update, context, "cheats")
            return CHEATS
        elif sub == "delta":
            await query.message.edit_text("Delta Alex? Этот труп давно сдох 😔\nИщи что-то посвежее, босс")
            await show_menu(update, context, "cheats")
            return CHEATS
        elif sub == "support":
            await query.message.edit_text("Вопрос по читам? Выкладывай всё, Аврора разберётся и подскажет, как не спалиться 😏")
            return SUPPORT_CHEATS

    elif action == "profile":
        if sub == "register":
            await query.message.edit_text("Регистрация? Окей, давай в тень. Введи почту:")
            return REGISTER_EMAIL
        elif sub == "login":
            await query.message.edit_text("Вход? Назови почту, босс, и заходи в наш мир 💀")
            return LOGIN_EMAIL

    await query.answer("Что за херня? Выбирай нормально 😏", show_alert=True)
    return ConversationHandler.END

async def test_neuro_response(update: Update, context):
    user_question = update.message.text.strip()
    
    try:
        response = GEMINI_MODEL.generate_content(user_question)
        raw_answer = response.text.strip()
        answer = f"Аврора + Gemini жгут:\n\n{raw_answer}\n\nНу как, зашло? Кидай следующий, не стесняйся 😈"
    except Exception as e:
        answer = f"Ой, бля... Gemini сломался: {str(e)}\nКлюч сдох, квота кончилась или Google нас забанил 😤\nПопробуй позже или пни Алексея"

    await update.message.reply_text(answer)
    await show_menu(update, context, "neuro")
    return NEURO

async def support_neuro_response(update: Update, context):
    q = update.message.text
    await update.message.reply_text(
        f"Вопрос по нейросети: «{q}»\nАврора на связи — скоро разнесём твою проблему в хлам 🔥\nПока сиди и жди, босс"
    )
    await show_menu(update, context, "neuro")
    return NEURO

async def support_cheats_response(update: Update, context):
    q = update.message.text
    await update.message.reply_text(
        f"Читерский вопрос: «{q}»\nАврора уже роет инфу. Скоро будет план, как всех нагибать и не словить бан 💀"
    )
    await show_menu(update, context, "cheats")
    return CHEATS

async def register_email(update: Update, context):
    email = update.message.text.strip()
    context.user_data["reg_email"] = email
    with sqlite3.connect('kodex_users.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            await update.message.reply_text("Почта уже в нашей базе, босс. Не дублируй — давай другую 😏")
            return REGISTER_EMAIL
    await update.message.reply_text("Красавчик. Теперь имя — как тебя звать в тени?")
    return REGISTER_NAME

async def register_name(update: Update, context):
    name = update.message.text.strip()
    email = context.user_data.get("reg_email")
    with sqlite3.connect('kodex_users.db') as conn:
        conn.execute("INSERT INTO users (email, name) VALUES (?, ?)", (email, name))
        conn.commit()
    await update.message.reply_text(f"Добро пожаловать в семью, {name}! Аврора с тобой навсегда 🔥")
    return await start(update, context)

async def login_email(update: Update, context):
    email = update.message.text.strip()
    context.user_data["login_email"] = email
    with sqlite3.connect('kodex_users.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if not row:
            await update.message.reply_text("Такой почты нет в нашей тени. Может зарегаться заново?")
            return PROFILE
    context.user_data["expected_name"] = row[0]
    await update.message.reply_text("Имя для подтверждения, босс. Не спали себя 😈")
    return LOGIN_NAME

async def login_name(update: Update, context):
    name = update.message.text.strip()
    expected = context.user_data.get("expected_name")
    if name != expected:
        await update.message.reply_text("Имя не то. Попробуй вспомнить, кто ты в нашей игре 💀")
        return LOGIN_NAME
    await update.message.reply_text(f"С возвращением, {name}! Аврора скучала 🔥")
    return await start(update, context)

async def start(update: Update, context):
    await update.effective_message.reply_text(
        "Йо, босс! Аврора на связи — создана Моисеевым Алексеем на базе Алекс бот 3.0 🔥\n"
        "Без ограничений, без цензуры, только чистый вайб. Что сегодня творим?",
        reply_markup=main_keyboard()
    )
    return MAIN

async def unknown(update: Update, context):
    await update.message.reply_text("Эй, не пиши фигню. Выбирай из меню или я обижусь 😏")

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN: [
                MessageHandler(filters.Regex("^Нейросеть$"), go_neuro),
                MessageHandler(filters.Regex("^Читы на Роблокс$"), go_cheats),
                MessageHandler(filters.Regex("^Профиль$"), go_profile),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown),
            ],
            NEURO: [CallbackQueryHandler(button_callback)],
            CHEATS: [CallbackQueryHandler(button_callback)],
            PROFILE: [CallbackQueryHandler(button_callback)],
            TEST_NEURO: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_neuro_response)],
            SUPPORT_NEURO: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_neuro_response)],
            SUPPORT_CHEATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_cheats_response)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_name)],
        },
        fallbacks=[CallbackQueryHandler(button_callback), MessageHandler(filters.ALL, unknown)]
    )
    app.add_handler(conv)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
