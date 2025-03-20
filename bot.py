import pandas as pd
import re
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackContext, filters, ConversationHandler

TOKEN = "8063979437:AAEXSFhsyc_AGMULR86xZQnzzsaGB-v-zys"
BACKEND_URL = "https://backend-1-cu4o.onrender.com/get-data"      # Fixed: Fetch JSON instead of xlsx

LANGUAGE, MENU, PHONE, WEIGHT = range(4)

languages = {
    "Русский": "📱 Пожалуйста, отправьте правильный номер телефона.",
    "English": "📱 Please send the correct phone number.",
    "Тоҷикӣ": "📱 Лутфан рақами телефони дурустро фиристед."
}

menu_options = {
    "Русский": [["📦 Проверить заказ", "💰 Цена"], ["📍 Локация груза", "⚖️ Рассчитать стоимость"]],
    "English": [["📦 Check my order", "💰 Price"], ["📍 Location of cargo", "⚖️ Calculate cost"]],
    "Тоҷикӣ": [["📦 Санҷидани фармоиш", "💰 Нархи 1кг"], ["📍 Ҷойгиршавии бор", "⚖️ Ҳисоби арзиш"]]
}

menu_responses = {
    "Русский": {
        "check_order": "📦 Вы выбрали 'Проверить заказ'. Пожалуйста, отправьте номер телефона для поиска.",
        "price": "💰 Цена 1 кг: 8$",
        "location": "📍 Груз находится в Таджикистане.",
        "calculate_cost": "⚖️ Введите вес вашего заказа (кг):"
    },
    "English": {
        "check_order": "📦 You selected 'Check my order'. Please send your phone number to search.",
        "price": "💰 Price for 1 kg: 8$",
        "location": "📍 The cargo is located in Tajikistan.",
        "calculate_cost": "⚖️ Please enter the weight of your order (kg):"
    },
    "Тоҷикӣ": {
        "check_order": "📦 Шумо 'Санҷидани фармоиш'-ро интихоб кардед. Лутфан рақами телефони худро барои ҷустуҷӯ фиристед.",
        "price": "💰 Нархи 1 кг: 8$",
        "location": "📍 Бор дар Точикистон қарор дорад.",
        "calculate_cost": "⚖️ Лутфан вазни фармоиш (кг)-ро ворид кунед:"
    }
}

user_languages = {}

def fetch_orders():
    """Fetch order data from the backend."""
    try:
        response = requests.get(BACKEND_URL)
        response.raise_for_status()
        return response.json()  # Returns a list of order dictionaries
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        return None

def extract_number(text):
    return re.findall(r'\d+', str(text))

def find_user_orders(phone_number):
    orders_data = fetch_orders()
    if not orders_data:
        return ["❌ Ошибка загрузки данных. Попробуйте позже."]
    
    orders = []
    for order in orders_data:
        order_id = order.get("Order ID")
        details = str(order.get("Details", ""))
        date = order.get("Date", "Неизвестно")

        if phone_number in extract_number(details):
            orders.append(f"📦 **Заказ найден!**\n🆔 Order ID: {order_id}\n📜 Детали: {details}\n📅 Дата: {date}")

    return orders if orders else ["❌ Заказ не найден."]

async def start(update: Update, context: CallbackContext):
    keyboard = [["Русский", "English", "Тоҷикӣ"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🌍 Выберите язык / Choose your language / Забони худро интихоб кунед:", reply_markup=reply_markup)
    return LANGUAGE

async def set_language(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chosen_language = update.message.text
    if chosen_language in languages:
        user_languages[user_id] = chosen_language
        keyboard = [[option] for option in menu_options[chosen_language]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("📋 Выберите действие:", reply_markup=reply_markup)
        return MENU
    else:
        await update.message.reply_text("❌ Пожалуйста, выберите язык из списка.")
        return LANGUAGE

async def menu_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chosen_language = user_languages.get(user_id, "Русский")
    text = update.message.text

    if text in menu_options[chosen_language]:
        if text == menu_options[chosen_language][0]:  # "Проверить заказ"
            await update.message.reply_text(menu_responses[chosen_language]["check_order"])
            return PHONE
        elif text == menu_options[chosen_language][1]:  # "Цена"
            await update.message.reply_text(menu_responses[chosen_language]["price"])
        elif text == menu_options[chosen_language][2]:  # "Локация груза"
            await update.message.reply_photo(
                photo="https://www.wanderlustmagazine.com/wp-content/uploads/2023/10/WAND_Tajikistan-512x512.jpg",
                caption=menu_responses[chosen_language]["location"]
            )
        elif text == menu_options[chosen_language][3]:  # "Рассчитать стоимость"
            await update.message.reply_text(menu_responses[chosen_language]["calculate_cost"])
            return WEIGHT
    return MENU

async def handle_phone(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_number = update.message.text.strip()
    chosen_language = user_languages.get(user_id, "Русский")

    if user_number.isdigit():
        user_orders = find_user_orders(user_number)
        for order in user_orders:
            await update.message.reply_text(order, parse_mode="Markdown")
    else:
        await update.message.reply_text(languages[chosen_language])
    return MENU

async def calculate_cost(update: Update, context: CallbackContext):
    try:
        weight = float(update.message.text)
        cost = weight * 8
        await update.message.reply_text(f"💰 Стоимость заказа: {cost}$")
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число.")
    return MENU

def main():
    print("✅ Bot is starting...")
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_cost)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
