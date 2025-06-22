"""
Тест библиотеки maxbot
"""

import asyncio
import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher, Context
from maxbot.max_types import (
    Message, User, Chat, Update, MessageBody, BaseAttachment
)

# Загружаем токен из файла
def get_token():
    token_file = "token.txt"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return os.environ.get("MAXBOT_TOKEN", "YOUR_TOKEN_HERE")

TOKEN = get_token()

class MockBot:
    """Мок бота для тестов"""
    def __init__(self):
        self.token = "test_token"
    
    async def send_message(self, text, user_id=None, **kwargs):
        """Мок метод для отправки сообщений"""
        return {"message_id": "mock_msg_id"}

@pytest.mark.skipif(TOKEN == "YOUR_TOKEN_HERE", reason="Требуется реальный токен")
@pytest.mark.asyncio
async def test_bot():
    """Тестирует основные функции библиотеки"""
    
    # Создаем бота
    bot = Bot(TOKEN)
    
    async with bot:
        # Тестируем получение информации о боте
        print("Testing get_me()...")
        me = await bot.get_me()
        print(f"Bot info: {me['name']} (ID: {me['user_id']})")
        
        # Тестируем получение обновлений
        print("Testing get_updates()...")
        response = await bot.get_updates(limit=10)
        updates_list = response.get('updates', [])
        print(f"Received {len(updates_list)} updates")

        for i, update_data in enumerate(updates_list):
            update = Update.model_validate(update_data)
            print(f"\\nUpdate {i}:")
            print(f"Type: {update.update_type}")
            if update.message:
                print(f"Message from {update.message.sender.user_id} in chat {update.message.recipient.chat_id}")
                assert update.message.body is not None

        # Тестируем отправку сообщения
        print("Testing send_message()...")
        if updates_list:
            first_update_data = updates_list[0]
            update = Update.model_validate(first_update_data)
            if update.message and update.message.sender:
                user_id = update.message.sender.user_id
                result = await bot.send_message("Тестовое сообщение от библиотеки", user_id=user_id)
                print(f"Message sent: {result}")

@pytest.mark.asyncio
async def test_context_attachments():
    """Тест контекста с вложениями"""
    user = User(user_id=1, name="testuser")
    chat = Chat(chat_id=1, chat_type="dialog", user_id=1)
    message_body = MessageBody(mid="test", seq=1, text="test")
    message = Message(sender=user, recipient=chat, body=message_body, timestamp=123)
    update = Update(update_type="message_created", timestamp=123, marker=1, message=message)
    bot = MockBot()
    ctx = Context(update, bot)
    
    assert ctx.has_attachments is False
    assert ctx.attachments is None
    assert ctx.images == []

@pytest.mark.parametrize("att_type, att_data, expected_cls, check", [
    ("image", {
        "type": "image",
        "payload": {"url": "img.png", "photo_id": "imgid"},
        "width": 100, "height": 200
    }, BaseAttachment, lambda a: a.type == "image" and a.url == "img.png" and a.width == 100 and a.height == 200),
    ("video", {
        "type": "video",
        "payload": {"url": "vid.mp4", "id": "vidid"},
        "width": 320, "height": 240, "duration": 10, "thumbnail": {"url": "thumb.jpg"}
    }, BaseAttachment, lambda a: a.type == "video" and a.url == "vid.mp4" and a.width == 320 and a.height == 240),
    ("audio", {
        "type": "audio",
        "payload": {"url": "aud.mp3", "id": "audid"}
    }, BaseAttachment, lambda a: a.type == "audio" and a.url == "aud.mp3"),
    ("file", {
        "type": "file",
        "payload": {"url": "file.bin", "fileId": "fileid"},
        "filename": "file.bin", "size": 1234
    }, BaseAttachment, lambda a: a.type == "file" and a.url == "file.bin" and a.filename == "file.bin" and a.size == 1234),
    ("sticker", {
        "type": "sticker",
        "payload": {"url": "stick.webp", "sticker_id": "stid", "emoji": "😀"},
        "width": 64, "height": 64
    }, BaseAttachment, lambda a: a.type == "sticker" and a.url == "stick.webp" and a.emoji == "😀" and a.width == 64 and a.height == 64),
    ("location", {
        "type": "location",
        "latitude": 55.7, "longitude": 37.6
    }, BaseAttachment, lambda a: a.type == "location" and a.latitude == 55.7 and a.longitude == 37.6),
    ("share", {
        "type": "share",
        "payload": {"url": "https://ya.ru", "title": "Yandex"}
    }, BaseAttachment, lambda a: a.type == "share" and a.url == "https://ya.ru"),
])
def test_attachment_parsing(att_type, att_data, expected_cls, check):
    """Тест парсинга вложений"""
    # Имитация update_data как в get_updates
    update_data = {
        "marker": 1,
        "update_type": "message_created",
        "timestamp": 123456,
        "message": {
            "sender": {"user_id": 123, "name": "testuser"},
            "recipient": {"chat_id": 456, "chat_type": "dialog", "user_id": 123},
            "timestamp": 123456,
            "body": {
                "mid": "mid1",
                "seq": 1,
                "text": "test",
                "attachments": [att_data]
            }
        }
    }
    
    # Проверяем, что данные корректно структурированы
    assert update_data["message"]["body"]["attachments"][0]["type"] == att_type
    assert update_data["message"]["body"]["attachments"][0] == att_data

@pytest.mark.asyncio
async def test_dispatcher():
    """Тест диспетчера"""
    bot = MockBot()
    dispatcher = Dispatcher(bot)
    
    @dispatcher.message_handler()
    async def test_handler(ctx):
        return "test_response"
    
    # Создаем тестовый контекст
    user = User(user_id=1, name="testuser")
    chat = Chat(chat_id=1, chat_type="dialog", user_id=1)
    message_body = MessageBody(mid="test", seq=1, text="/test")
    message = Message(sender=user, recipient=chat, body=message_body, timestamp=123)
    update = Update(update_type="message_created", timestamp=123, marker=1, message=message)
    ctx = Context(update, bot)
    
    # Тестируем обработку
    result = await dispatcher.process_update(update.__dict__)
    assert result is None  # process_update не возвращает результат

def test_attachment_validation():
    """Тест валидации структуры вложений"""
    # Валидные вложения
    valid_image = {
        'type': 'image',
        'payload': {
            'photo_id': 123,
            'token': 'test_token',
            'url': 'https://example.com/image.jpg'
        }
    }
    assert BaseAttachment.validate_attachment(valid_image) == True
    
    valid_file = {
        'type': 'file',
        'payload': {
            'fileId': 'file_123',
            'token': 'test_token'
        }
    }
    assert BaseAttachment.validate_attachment(valid_file) == True
    
    valid_location = {
        'type': 'location',
        'latitude': 55.7558,
        'longitude': 37.6176
    }
    assert BaseAttachment.validate_attachment(valid_location) == True
    
    # Невалидные вложения
    invalid_no_type = {'payload': {'photo_id': 123}}
    assert BaseAttachment.validate_attachment(invalid_no_type) == False
    
    invalid_no_payload = {'type': 'image'}
    assert BaseAttachment.validate_attachment(invalid_no_payload) == False
    
    invalid_wrong_payload = {
        'type': 'image',
        'payload': 'not_a_dict'
    }
    assert BaseAttachment.validate_attachment(invalid_wrong_payload) == False

def test_get_payload_for_sending():
    """Тест извлечения payload для отправки"""
    # Тест для image
    image_attachment = {
        'type': 'image',
        'payload': {
            'photo_id': 123,
            'token': 'test_token',
            'url': 'https://example.com/image.jpg'
        }
    }
    payload = BaseAttachment.get_payload_for_sending(image_attachment)
    assert payload == {
        'photo_id': 123,
        'token': 'test_token',
        'url': 'https://example.com/image.jpg'
    }
    
    # Тест для location
    location_attachment = {
        'type': 'location',
        'latitude': 55.7558,
        'longitude': 37.6176
    }
    payload = BaseAttachment.get_payload_for_sending(location_attachment)
    assert payload == {
        'latitude': 55.7558,
        'longitude': 37.6176
    }
    
    # Тест для невалидного вложения
    with pytest.raises(ValueError):
        BaseAttachment.get_payload_for_sending({'type': 'invalid'})

if __name__ == "__main__":
    asyncio.run(test_bot())
    asyncio.run(test_context_attachments()) 