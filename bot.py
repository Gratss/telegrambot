import asyncio
import os
import json
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, BotCommand, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from dotenv import load_dotenv
import base64

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LEAKCHECK_API_KEY = os.getenv("LEAKCHECK_API_KEY")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
IPQS_API_KEY = os.getenv("IPQS_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SUBSCRIBERS_FILE = "subscribers.json"
HISTORY_FILE = "history.json"
def load_subscribers():
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, "r") as file:
                return json.load(file)
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Ошибка загрузки подписчиков: {e}")
        return []

def save_subscribers(subscribers):
    try:
        with open(SUBSCRIBERS_FILE, "w") as file:
            json.dump(subscribers, file, indent=4)
    except Exception as e:
        logging.error(f"Ошибка сохранения подписчиков: {e}")

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as file:
                return json.load(file)
        return {}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Ошибка загрузки истории: {e}")
        return {}

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as file:
            json.dump(history, file, indent=4)
    except Exception as e:
        logging.error(f"Ошибка сохранения истории: {e}")

def add_to_history(user_id, data_type, value):
    history = load_history()
    user_id_str = str(user_id)
    
    if user_id_str not in history:
        history[user_id_str] = {"email": [], "ip": [], "phone": []}
    
    if value not in history[user_id_str][data_type]:
        history[user_id_str][data_type].append(value)
    
    save_history(history)

# Устанавливаем команды, доступные в боте
async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Начать работу с ботом"),
        BotCommand(command="/status", description="Показать статус подписки и историю")
    ]
    await bot.set_my_commands(commands)
    logging.info("Установлены команды /start и /status")

    # Логируем информацию в методе main
async def main():
    logging.info("Запуск бота...")
    await set_bot_commands()
    logging.info("Бот зарегистрировал команды.")
    await dp.start_polling(bot)

# Главная кнопка старт
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Подписаться на уведомления"), KeyboardButton(text="🚫 Отписаться от уведомлений")],
        [KeyboardButton(text="💡 Советы по безопасности")],
        [KeyboardButton(text="🔍 Проверка URL")],
        [KeyboardButton(text="📧 Проверка Email")],
        [KeyboardButton(text="📱 Проверка телефона")],
        [KeyboardButton(text="🌐 Проверка IP")],
        [KeyboardButton(text="🔐 2FA Info")]
    ],
    resize_keyboard=True
)

# /start
@dp.message(Command("start"))
async def start(message: Message):
    try:
        await message.answer(
            "🔐 Привет! Я бот для защиты персональных данных.\n"
            "Выберите одну из опций для проверки:\n",
            reply_markup=start_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике /start: {e}")
        await message.answer("Произошла ошибка, попробуйте позже.")

@dp.message(lambda message: message.text == "🔔 Подписаться на уведомления")
async def subscribe(message: Message):
    try:
        subscribers = load_subscribers()
        if message.from_user.id not in subscribers:
            subscribers.append(message.from_user.id)
            save_subscribers(subscribers)
            await message.answer("✅ Вы подписались на уведомления о новых утечках!")
        else:
            await message.answer("⚠️ Вы уже подписаны на уведомления.")
    except Exception as e:
        logging.error(f"Ошибка при подписке: {e}")
        await message.answer("❌ Произошла ошибка при подписке. Попробуйте позже.")

@dp.message(lambda message: message.text == "🚫 Отписаться от уведомлений")
async def unsubscribe(message: Message):
    try:
        subscribers = load_subscribers()
        if message.from_user.id in subscribers:
            subscribers.remove(message.from_user.id)
            save_subscribers(subscribers)
            await message.answer("✅ Вы отписались от уведомлений.")
        else:
            await message.answer("⚠️ Вы не были подписаны.")
    except Exception as e:
        logging.error(f"Ошибка при отписке: {e}")
        await message.answer("❌ Произошла ошибка при отписке. Попробуйте позже.")

@dp.message(Command("status"))
async def status(message: Message):
    logging.info("Команда /status получена")
    subscribers = load_subscribers()
    history = load_history()
    user_id_str = str(message.from_user.id)
    
    is_subscribed = "✅ Подписаны" if message.from_user.id in subscribers else "❌ Не подписаны"
    
    # Получаем историю для конкретного пользователя
    user_history = history.get(user_id_str, {"email": [], "ip": [], "phone": []})
    
    # Формируем списки для вывода
    email_list = "\n".join(user_history["email"]) if user_history["email"] else "Нет данных"
    ip_list = "\n".join(user_history["ip"]) if user_history["ip"] else "Нет данных"
    phone_list = "\n".join(user_history["phone"]) if user_history["phone"] else "Нет данных"
    
    response = f"📊 Ваш статус:\n🔔 Подписка: {is_subscribed}\n\n📧 История email:\n{email_list}\n\n🌐 История IP:\n{ip_list}\n\n📱 История телефонов:\n{phone_list}"
    
    await message.answer(response)


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer("Команды доступны: /start, /status")

async def send_notifications():
    while True:
        await asyncio.sleep(3600)
        subscribers = load_subscribers()
        if subscribers:
            for user_id in subscribers:
                try:
                    await bot.send_message(user_id, "⚠️ Внимание! Обнаружена новая утечка данных.")
                except Exception as e:
                    logging.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")


async def main():
    await set_bot_commands()
    asyncio.create_task(send_notifications())
    await dp.start_polling(bot)

# Обработчики кнопок
@dp.message(lambda message: message.text == "💡 Советы по безопасности")
async def send_tips(message: Message):
    tips = [
        "✅ Используй сложные пароли и менеджеры паролей.",
        "✅ Включи двухфакторную аутентификацию (2FA).",
        "✅ Никогда не переходи по подозрительным ссылкам.",
        "✅ Регулярно проверяй свои данные на утечки.",
        "✅ Не устанавливай сомнительные приложения."
    ]
    await message.answer("\n".join(tips))

@dp.message(lambda message: message.text == "🔍 Проверка URL")
async def check_url(message: Message):
    await message.answer("Введите URL для проверки:")

@dp.message(lambda message: message.text == "📧 Проверка Email")
async def check_email(message: Message):
    await message.answer("Введите email для проверки:")

@dp.message(lambda message: message.text == "📱 Проверка телефона")
async def check_phone(message: Message):
    await message.answer("Введите номер телефона для проверки:")

@dp.message(lambda message: message.text == "🌐 Проверка IP")
async def check_ip(message: Message):
    await message.answer("Введите IP-адрес для проверки:")

@dp.message(lambda message: message.text == "🔐 2FA Info")
async def send_2fa_info(message: Message):
    await message.answer(
        "🔐 Двухфакторная аутентификация (2FA) — это дополнительный уровень безопасности, "
        "который требует подтверждения личности пользователя при входе, помимо пароля.\n\n"
        "Рекомендуется включить 2FA на всех ваших аккаунтах, чтобы повысить их защиту.\n\n"
        "Для настройки двухфакторной аутентификации на популярных сервисах:\n"
        "- 📱 [Google](https://myaccount.google.com/security) - Инструкции для Google аккаунтов\n"
        "- 🔵 [Facebook](https://www.facebook.com/settings?tab=security) - Инструкции для Facebook\n"
        "- 🐦 [Twitter](https://twitter.com/settings/security) - Инструкции для Twitter\n"
        "- 📱 [Telegram](https://my.telegram.org/auth) - Инструкции для Telegram\n"
        "- 🎮 [Steam](https://steamcommunity.com/id/me/edit/settings) - Инструкции для Steam\n"
        "- 🦸‍♂️ [VKontakte](https://vk.com/settings) - Инструкции для ВКонтакте"
    )

# Проверка email на утечку данных через LeakCheck
async def check_data_breach(email):
    try:
        url = f"https://leakcheck.io/api?key={LEAKCHECK_API_KEY}&check={email}"
        logging.info(f"Запрос к LeakCheck для email: {email}")  # Логируем запрос
        response = requests.get(url)
        
        if response.status_code == 403:
            logging.error(f"Ошибка 403: Доступ к API LeakCheck запрещен. Проверь API-ключ.")
            return False
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Ответ от LeakCheck: {data}")  # Логируем ответ от сервера
            
            if data.get("success") and data.get("found"):
                add_to_history(user_id=email, data_type="email", value=email)
                return True  # Email найден в базе утечек
            else:
                return False  # Email не найден
        else:
            logging.error(f"Ошибка при запросе к LeakCheck: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Ошибка при проверке утечки данных: {e}")
        return False


# Проверка телефона на утечку данных
async def check_phone_breach(phone):
    try:
        url = f"https://leakcheck.io/api?key={LEAKCHECK_API_KEY}&check={phone}"
        response = requests.get(url)
        data = response.json()

        if data.get("success") and data.get("found"):
            add_to_history(user_id=phone, data_type="phone", value=phone)
            return True  # Телефон найден в базе утечек
        return False  # Телефон не найден
    except Exception as e:
        logging.error(f"Ошибка при проверке утечки данных: {e}")
        return False

# Проверка URL через VirusTotal API
async def check_url_virustotal(url):
    try:
        # Кодируем URL в base64
        encoded_url = base64.urlsafe_b64encode(url.encode()).decode().strip("=")

        headers = {
            "x-apikey": VIRUSTOTAL_API_KEY
        }
        vt_url = f"https://www.virustotal.com/api/v3/urls/{encoded_url}"
        response = requests.get(vt_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            malicious = data['data']['attributes']['last_analysis_stats']['malicious']
            if malicious > 0:
                return "❌ Ссылка опасна: найден вирус!"
            else:
                return "✅ Ссылка безопасна."
        else:
            return "❌ Ошибка при проверке ссылки. Попробуйте позже."
    except Exception as e:
        logging.error(f"Ошибка при проверке с VirusTotal: {e}")
        return "❌ Ошибка при проверке ссылки."

# Проверка репутации IP-адреса через IPQualityScore API
async def check_ip_reputation(ip_address):
    try:
        url = f"https://ipqualityscore.com/api/json/ip/{IPQS_API_KEY}/{ip_address}"
        response = requests.get(url)
        data = response.json()
        
        if data.get("success", False):
            risk = data.get("fraud_score", 0)
            if risk > 80:
                add_to_history(user_id=ip_address, data_type="ip", value=ip_address)
                return f"❌ IP-адрес {ip_address} имеет высокий риск: {risk}/100."
            elif risk > 50:
                add_to_history(user_id=ip_address, data_type="ip", value=ip_address)
                return f"⚠️ IP-адрес {ip_address} имеет средний риск: {risk}/100."
            else:
                add_to_history(user_id=ip_address, data_type="ip", value=ip_address)
                return f"✅ IP-адрес {ip_address} безопасен: {risk}/100."
        else:
            return "❌ Ошибка при проверке IP-адреса."
    except Exception as e:
        logging.error(f"Ошибка при проверке IP-адреса: {e}")
        return "❌ Ошибка при проверке IP-адреса."

# Обработчики сообщений для кнопок
@dp.message(lambda message: message.text == "🔍 Проверка URL")
async def handle_url_check(message: Message):
    await message.answer("Введите URL для проверки:")

@dp.message(lambda message: message.text == "📧 Проверка Email")
async def handle_email_check(message: Message):
    await message.answer("Введите email для проверки:")

@dp.message(lambda message: message.text == "📱 Проверка телефона")
async def handle_phone_check(message: Message):
    await message.answer("Введите номер телефона для проверки:")

@dp.message(lambda message: message.text == "🌐 Проверка IP")
async def handle_ip_check(message: Message):
    await message.answer("Введите IP-адрес для проверки:")

# Обработчик сообщений после ввода данных
@dp.message(lambda message: message.text)
async def handle_data_input(message: Message):
    text = message.text.strip()

    # Проверка email
    if "@" in text:
        is_breached = await check_data_breach(text)
        if is_breached:
            await message.answer(f"⚠️ Этот email найден в базе утечек! Срочно смените пароль.")
        else:
            await message.answer(f"✅ Email {text} не найден в утечках.")
    
    # Проверка телефона
    elif text.isdigit() and len(text) >= 10:
        is_breached = await check_phone_breach(text)
        if is_breached:
            await message.answer(f"⚠️ Этот телефон найден в базе утечек! Срочно примите меры.")
        else:
            await message.answer(f"✅ Телефон {text} не найден в утечках.")
    
    # Проверка URL
    elif text.startswith("http"):
        safety_message = await check_url_virustotal(text)
        await message.answer(safety_message)
    
    # Проверка IP
    elif text.count(".") == 3 and all(part.isdigit() for part in text.split(".")):
        result = await check_ip_reputation(text)
        await message.answer(result)
    else:
        await message.answer("❌ Пожалуйста, введите корректные данные для проверки.")

# Запуск бота
async def main():
    # Устанавливаем доступные команды
    await set_bot_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())