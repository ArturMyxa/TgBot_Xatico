# bot/main.py

import requests
from flask import Flask, request, jsonify
import telepot
from telepot.loop import MessageLoop
import certifi
import json
import os
from config import TELEGRAM_TOKEN, API_TOKEN, API_URL, WHITELIST_FILE

# Инициализация Flask
app = Flask(__name__)

# Загрузка белого списка
def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r') as f:
            return json.load(f)
    return []

# Сохранение белого списка
def save_whitelist(whitelist):
    with open(WHITELIST_FILE, 'w') as f:
        json.dump(whitelist, f)

# Функция для проверки IMEI
def check_imei(imei: str):
    print(f"Sending IMEI: {imei} with token: {API_TOKEN}")  # Вывод отладочной информации
    response = requests.post(API_URL, json={'imei': imei, 'token': API_TOKEN})

    try:
        response.raise_for_status()  # Проверяем статус код ответа
        return response.json()  # Возвращаем ответ в формате JSON
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e}")  # Логирование ошибки
        print(f"Response content: {response.text}")  # Логирование содержимого ответа
    except requests.exceptions.RequestException as e:
        print(f"RequestException: {e}")  # Логирование ошибки
    except ValueError:
        print("Invalid JSON response")  # Ответ не является корректным JSON

    return {'error': 'Unable to check IMEI'}  # Возвращаем значение по умолчанию в случае ошибки


# Функция для отправки сообщения через Telegram API
def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': chat_id, 'text': text}
    requests.post(url, data=data, verify=certifi.where())

# Обработчик сообщений
def handle_message(msg):
    chat_id = msg['chat']['id']
    user_id = str(chat_id)

    # Загрузка белого списка
    whitelist = load_whitelist()

    # Проверка на наличие в белом списке
    if user_id not in whitelist:
        # Добавление в белый список
        whitelist.append(user_id)
        save_whitelist(whitelist)
        send_telegram_message(chat_id, "Вы добавлены в белый список. Теперь вы можете использовать бота.")
        return

    # Получение IMEI из сообщения
    imei = msg.get('text', '').strip()
    if not imei.isdigit() or len(imei) != 15:
        send_telegram_message(chat_id, "Некорректный IMEI. IMEI должен состоять из 15 цифр.")
        return

    result = check_imei(imei)
    send_telegram_message(chat_id, f"Информация о IMEI: {result}")

# Запуск бота
bot = telepot.Bot(TELEGRAM_TOKEN)
MessageLoop(bot, handle_message).run_as_thread()

# API для проверки IMEI
@app.route('/api/check-imei', methods=['POST'])
def api_check_imei():
    data = request.json
    imei = data.get('imei')
    token = data.get('token')

    if token != 'YOUR_API_AUTH_TOKEN':  # токен авторизации
        return jsonify({'error': 'Unauthorized'}), 401

    if not imei or not isinstance(imei, str) or len(imei) != 15 or not imei.isdigit():
        return jsonify({'error': 'Invalid IMEI'}), 400

    result = check_imei(imei)
    return jsonify(result)

# Запуск Flask
if __name__ == '__main__':
    app.run(port=8000)  #менять цифры если порт занят
    порт по необходимости
