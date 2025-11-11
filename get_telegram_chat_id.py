#!/usr/bin/env python3
"""
Простой скрипт для получения Telegram Chat ID
Использование:
1. Создайте бота через @BotFather и получите токен
2. Запустите этот скрипт: python get_telegram_chat_id.py
3. Напишите вашему боту любое сообщение
4. Скрипт покажет ваш Chat ID
"""

import requests
import time
import sys

def get_chat_id(bot_token):
    """Получить Chat ID через Telegram Bot API"""
    
    if not bot_token:
        print("❌ Ошибка: Не указан токен бота")
        print("\n📝 Инструкция:")
        print("1. Создайте бота через @BotFather в Telegram")
        print("2. Получите токен бота")
        print("3. Запустите скрипт: python get_telegram_chat_id.py YOUR_BOT_TOKEN")
        return None
    
    print("🤖 Ожидание сообщения...")
    print("📱 Напишите вашему боту любое сообщение в Telegram")
    print("⏳ Ожидание 60 секунд...\n")
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    # Получаем последние обновления
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
        
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ Ошибка: {data.get('description', 'Unknown error')}")
            return None
        
        updates = data.get('result', [])
        
        if not updates:
            print("⚠️  Сообщений пока нет. Напишите боту сообщение и попробуйте снова.")
            return None
        
        # Берем последнее сообщение
        last_update = updates[-1]
        message = last_update.get('message', {})
        chat = message.get('chat', {})
        chat_id = chat.get('id')
        
        if chat_id:
            print("✅ Chat ID найден!")
            print(f"\n📋 Ваш Chat ID: {chat_id}")
            print(f"👤 Имя: {chat.get('first_name', 'N/A')} {chat.get('last_name', '')}")
            print(f"📱 Username: @{chat.get('username', 'N/A')}")
            print(f"\n💡 Добавьте в Railway Variables:")
            print(f"   TELEGRAM_CHAT_ID = {chat_id}")
            return chat_id
        else:
            print("❌ Не удалось найти Chat ID в сообщении")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("📝 Использование: python get_telegram_chat_id.py YOUR_BOT_TOKEN")
        print("\n💡 Альтернативные способы получения Chat ID:")
        print("1. Напишите @userinfobot в Telegram")
        print("2. Напишите @getidsbot в Telegram")
        print("3. Используйте этот скрипт с токеном бота")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    get_chat_id(bot_token)

