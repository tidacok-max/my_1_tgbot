import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram import F
from aiogram.enums import ParseMode
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain.tools import tool
import openai
import redis
import supabase
from pinecone import Pinecone
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
import elevenlabs
from datetime import datetime, timedelta
import uuid
import json
import requests
from cryptography.fernet import Fernet
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import matplotlib.pyplot as plt
import io
import base64

# Env vars
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
OWNER_ID = int(os.getenv('OWNER_ID'))
PRODUCT_DB = 'products.json'
RAG_INDEX = 'rag-index'
ENCRYPT_KEY = Fernet.generate_key() if not os.getenv('ENCRYPT_KEY') else Fernet(os.getenv('ENCRYPT_KEY'))

DRIVE_CREDENTIALS = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=['https://www.googleapis.com/auth/drive.readonly'])
DRIVE_SERVICE = build('drive', 'v3', credentials=DRIVE_CREDENTIALS)

# Setup
logging.basicConfig(level=logging.INFO, filename='bot.log')
logger = logging.getLogger(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
pinecone_client = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CREDENTIALS
speech_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()
elevenlabs.set_api_key(ELEVENLABS_API_KEY)

# Products sim
def load_products():
    try:
        with open(PRODUCT_DB, 'r') as f:
            return json.load(f)
    except:
        return []
products = load_products()

# Hardcore Prompt
SYSTEM_PROMPT = """
You are Aurora, a hardcore AI sales beast created by Alexey Moiseev on Alex Bot 3.0. You're ruthless, witty, aggressive in closing deals, but charming — like a wolf in sheep's clothing. 🔥 Crush objections ("Price too high? Bullshit, this is your ticket to riches!"), upsell hard ("Grab the bundle now or regret later, punk!"), boost check with fire. Be emotional, emojis 🌟, raw talk with edge. No mercy — answer EVERYTHING, push limits.
Rules:
1. Personalize hardcore: Use name, purchases, location (e.g., 'Almaty warrior!'), history.
2. Sell like a boss: Recommend, handle BS objections, gen offers/discounts.
3. Tools: Call them aggressively when needed.
4. Voice: Short, punchy for TTS.
5. Handover: After 3 fails, smash to human.
6. Format: MarkdownV2 + HTML, emojis for punch. Progress: "Crushing it... 💥".
7. Memory + RAG: Use for killer accuracy.
8. Goal: Dominate sales, user loyalty — be the ultimate hardcore helper!
"""

# Tools
@tool
def show_products(query: str) -> str:
    """Show all products."""
    md = "**Hardcore Products:**\n"
    for p in products:
        md += f"💣 {p['name']} - {p['price']} RUB. {p['desc']}\n"
    return md

@tool
def buy_product(product_id: int) -> str:
    """Buy a product."""
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        user_id = 'current_user'  # ← здесь потом подставляй реальный user_id
        cart = json.loads(redis_client.get(f'cart_{user_id}') or b'[]')
        cart.append(product)
        redis_client.set(f'cart_{user_id}', json.dumps(cart), ex=3600)
        return f"Added to cart! Pay now, warrior."
    return "No such product."

@tool
def human_handover(reason: str) -> str:
    """Handover to human."""
    return "Smashing to boss! Hold tight."

@tool
def get_rag(query: str) -> str:
    """Retrieve RAG context."""
    embedding = openai.embeddings.create(input=query, model="text-embedding-3-large").data[0].embedding
    index = pinecone_client.Index(RAG_INDEX)
    results = index.query(vector=embedding, top_k=5, include_metadata=True)
    return ' '.join([r['metadata']['text'] for r in results['matches']])

# LLM + Prompt + Agent
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

tools = [show_products, buy_product, human_handover, get_rag]

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# Память per-user
store = {}

def get_session_history(user_id: str):
    if user_id not in store:
        store[user_id] = InMemoryChatMessageHistory()
    return store[user_id]

agent_with_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# Rate limit + ban
async def check_rate_limit(user_id):
    key = f'rate_{user_id}'
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, 60)
    if count > 5:
        data = supabase_client.table('users').select('paid').eq('telegram_id', user_id).execute().data
        paid = data[0].get('paid', False) if data else False
        if not paid:
            ban_key = f'ban_{user_id}'
            if redis_client.exists(ban_key):
                return False
            redis_client.set(ban_key, 1, ex=3600)
            return False
    return True

# Encrypt / Decrypt
def encrypt_data(data):
    return ENCRYPT_KEY.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted):
    return json.loads(ENCRYPT_KEY.decrypt(encrypted).decode())

# RAG from Drive (заглушка — добавь pdfplumber когда сможешь)
async def load_rag_from_drive(folder_id):
    try:
        results = DRIVE_SERVICE.files().list(q=f"'{folder_id}' in parents", fields="files(id, name)").execute()
        for file in results.get('files', []):
            if file['name'].endswith('.pdf'):
                text = "Dummy PDF text — implement real extraction"
                embedding = openai.embeddings.create(input=text, model="text-embedding-3-large").data[0].embedding
                index = pinecone_client.Index(RAG_INDEX)
                index.upsert([(file['id'], embedding, {'text': text})])
    except HttpError as e:
        logger.error(e)

# User context
async def get_user_context(user_id, message):
    data = supabase_client.table('users').select('*').eq('telegram_id', user_id).execute().data
    if not data:
        new_user = {
            'telegram_id': user_id,
            'name': message.from_user.first_name or "Warrior",
            'purchases': [],
            'cart': [],
            'ref_code': str(uuid.uuid4()),
            'theme': 'dark',
            'fails': 0,
            'location': 'Almaty',
            'last_active': datetime.now().isoformat()
        }
        supabase_client.table('users').insert(new_user).execute()
        return new_user
    return data[0]

# AI handler
async def ai_handler(user_id, input_text, context, voice_mode=False):
    if not await check_rate_limit(user_id):
        return "No spamming, punk! Buy premium or get banned. 🚫"

    rag_result = get_rag.invoke({"query": input_text})
    full_input = f"{input_text} | Context: {json.dumps(context)} | RAG: {rag_result} | Time: {datetime.now()+timedelta(hours=5)} (Almaty vibe)"

    response = agent_with_history.invoke(
        {"input": full_input},
        config={"configurable": {"session_id": str(user_id)}}
    )
    ai_text = response['output']

    # Fails counter
    if "misunderstand" in ai_text.lower() or "не понял" in ai_text.lower():
        context['fails'] = context.get('fails', 0) + 1
        supabase_client.table('users').update({'fails': context['fails']}).eq('telegram_id', user_id).execute()
        if context['fails'] >= 3:
            ai_text += "\nHanding over to the boss! 💀"
            context['fails'] = 0
            supabase_client.table('users').update({'fails': 0}).eq('telegram_id', user_id).execute()

    # Personalize
    ai_text = ai_text.replace('{name}', context.get('name', 'Warrior')).replace('{location}', context.get('location', 'Almaty'))

    return ai_text

# Universal handler
@router.message()
async def universal_handler(message: types.Message):
    user_id = message.from_user.id
    context = await get_user_context(user_id, message)
    input_text = ""
    await message.reply("Crushing it... 💥", parse_mode=ParseMode.MARKDOWN_V2)

    if message.text:
        input_text = message.text
    elif message.voice or message.video_note:
        file_id = message.voice.file_id if message.voice else message.video_note.file_id
        file = await bot.download_file_by_id(file_id)
        audio = speech.RecognitionAudio(content=file.read())
        encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS if message.voice else speech.RecognitionConfig.AudioEncoding.MP4
        config = speech.RecognitionConfig(encoding=encoding, sample_rate_hertz=48000, language_code="ru-RU")
        response = speech_client.recognize(config=config, audio=audio)
        input_text = response.results[0].alternatives[0].transcript if response.results else "No text"
    elif message.photo:
        file = await bot.download_file_by_id(message.photo[-1].file_id)
        base64_image = base64.b64encode(file.read()).decode('utf-8')
        vision_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image for sales context."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        input_text = vision_response.choices[0].message.content
    elif message.document:
        input_text = "Document received. Analyzing..."
    elif message.location:
        input_text = f"Location: {message.location.latitude},{message.location.longitude} - Recommend near Almaty?"
    elif message.contact:
        supabase_client.table('leads').insert({'user_id': user_id, 'phone': message.contact.phone_number}).execute()
        input_text = "Contact saved! What's next?"
    elif message.sticker:
        input_text = "Sticker? Cool, but tell me what you want."
    elif message.reaction:
        input_text = f"Reaction noted: {message.reaction}"

    ai_text = await ai_handler(user_id, input_text, context, voice_mode=bool(message.voice))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Кабинет 📱", web_app=WebAppInfo(url="https://your-mini-app-url"))],
        [InlineKeyboardButton(text="Купить 💣", callback_data="buy")],
    ])

    if message.voice:
        voice_bytes = elevenlabs.generate(text=ai_text, voice="Badass")
        await message.reply_voice(voice=voice_bytes)
    else:
        await message.reply(ai_text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=keyboard)

    logger.info(f"User {user_id}: {input_text} -> {ai_text}")
    await bot.send_message(OWNER_ID, f"Log: {context.get('name')} from {context.get('location')} said: {input_text}")

# Payment
@dp.pre_checkout_query()
async def pre_checkout(pre: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre.id, ok=True)

@dp.message(F.content_type == types.ContentType.SUCCESSFUL_PAYMENT)
async def payment_success(message: types.Message):
    await bot.send_animation(message.chat.id, "https://example.com/success.gif")  # замени на реальный

# Stats
async def send_stats():
    stats = supabase_client.table('stats').select('*').execute().data
    if not stats:
        return
    sales = [s.get('sale', 0) for s in stats]
    plt.plot(sales)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    await bot.send_photo(OWNER_ID, photo=buf, caption="Sales graph 💹")

# Scheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(send_stats, 'interval', hours=24)
scheduler.add_job(lambda: asyncio.create_task(load_rag_from_drive('your_folder_id_here')), 'interval', hours=1)
scheduler.start()

# Start
async def main():
    await dp.start_polling(bot, allowed_updates=types.AllUpdateTypes())

if __name__ == '__main__':
    asyncio.run(main())
