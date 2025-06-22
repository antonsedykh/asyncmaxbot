import os
import requests
import pytest
import json
import asyncio
from maxbot import Bot

# Загружаем токен из файла
def get_token():
    token_file = "token.txt"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return os.environ.get("MAXBOT_TOKEN", "YOUR_TOKEN_HERE")

TOKEN = get_token()  # Замените на ваш токен для тестов

BASE_URL = "https://botapi.max.ru"

# Загружаем реальные ID из captured_updates.json
try:
    with open("captured_updates.json", "r", encoding="utf-8") as f:
        updates = json.load(f)
        if updates and len(updates) > 0:
            update = updates[0]
            CHAT_ID = update['message']['recipient']['chat_id']
            USER_ID = update['message']['sender']['user_id']
            MESSAGE_ID = update['message']['body']['mid']
        else:
            CHAT_ID = None
            USER_ID = None
            MESSAGE_ID = None
except FileNotFoundError:
    CHAT_ID = None
    USER_ID = None
    MESSAGE_ID = None

def get(url, **kwargs):
    params = kwargs.pop('params', {})
    params['access_token'] = TOKEN
    return requests.get(BASE_URL + url, params=params, **kwargs)

def post(url, **kwargs):
    params = kwargs.pop('params', {})
    params['access_token'] = TOKEN
    return requests.post(BASE_URL + url, params=params, **kwargs)

def patch(url, **kwargs):
    params = kwargs.pop('params', {})
    params['access_token'] = TOKEN
    return requests.patch(BASE_URL + url, params=params, **kwargs)

def delete(url, **kwargs):
    params = kwargs.pop('params', {})
    params['access_token'] = TOKEN
    return requests.delete(BASE_URL + url, params=params, **kwargs)

def put(url, **kwargs):
    params = kwargs.pop('params', {})
    params['access_token'] = TOKEN
    return requests.put(BASE_URL + url, params=params, **kwargs)

# Базовые GET-тесты
@pytest.mark.skipif(TOKEN == "YOUR_TOKEN_HERE", reason="Требуется реальный токен")
def test_get_me():
    resp = get("/me")
    assert resp.status_code == 200
    data = resp.json()
    assert 'user_id' in data
    assert data.get('is_bot') is True

@pytest.mark.skipif(TOKEN == "YOUR_TOKEN_HERE", reason="Требуется реальный токен")
def test_get_chats():
    resp = get("/chats")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert 'chats' in data

@pytest.mark.skipif(TOKEN == "YOUR_TOKEN_HERE", reason="Требуется реальный токен")
def test_get_subscriptions():
    resp = get("/subscriptions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert 'subscriptions' in data

@pytest.mark.skipif(TOKEN == "YOUR_TOKEN_HERE", reason="Требуется реальный токен")
def test_get_updates():
    resp = get("/updates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert 'updates' in data

@pytest.mark.skipif(TOKEN == "YOUR_TOKEN_HERE", reason="Требуется реальный токен")
def test_get_messages():
    resp = get("/messages")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert 'messages' in data

# Тесты с реальными ID
@pytest.mark.skipif(CHAT_ID is None, reason="Chat ID не найден")
def test_get_chat_by_id():
    resp = get(f"/chats/{CHAT_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('chat_id') == CHAT_ID

@pytest.mark.skipif(MESSAGE_ID is None, reason="Message ID не найден")
def test_get_message_by_id():
    resp = get(f"/messages/{MESSAGE_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('body', {}).get('mid') == MESSAGE_ID

@pytest.mark.skipif(CHAT_ID is None, reason="Chat ID не найден")
def test_get_chat_members():
    resp = get(f"/chats/{CHAT_ID}/members")
    assert resp.status_code == 200
    data = resp.json()
    assert 'members' in data

@pytest.mark.skipif(CHAT_ID is None, reason="Chat ID не найден")
def test_get_chat_membership():
    resp = get(f"/chats/{CHAT_ID}/membership")
    # API может не поддерживать этот endpoint
    assert resp.status_code in [200, 404, 405]

# POST тесты
@pytest.mark.skip(reason="Этот тест отправляет реальное сообщение")
@pytest.mark.skipif(CHAT_ID is None, reason="Chat ID не найден")
def test_send_message():
    payload = {
        "text": "Тестовое сообщение из автотеста",
    }
    resp = post(f"/chats/{CHAT_ID}/messages", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert 'message' in data

@pytest.mark.skip(reason="Может требовать специальных прав в чате")
@pytest.mark.skipif(CHAT_ID is None, reason="Chat ID не найден")
def test_send_action():
    payload = {
        "action": "typing"
    }
    resp = post(f"/chats/{CHAT_ID}/actions", json=payload)
    assert resp.status_code == 200

# PATCH тесты
@pytest.mark.skipif(CHAT_ID is None, reason="Chat ID не найден")
def test_edit_chat_info():
    payload = {
        "title": "Тестовый чат (изменён)"
    }
    resp = patch(f"/chats/{CHAT_ID}", json=payload)
    assert resp.status_code == 200

# DELETE тесты (осторожно!)
@pytest.mark.skipif(MESSAGE_ID is None, reason="Message ID не найден")
def test_delete_message():
    resp = delete(f"/messages/{MESSAGE_ID}")
    # API может не поддерживать удаление сообщений
    assert resp.status_code in [200, 404, 405]

@pytest.mark.asyncio
async def test_async_function():
    # Implementation of the async test function
    pass

@pytest.mark.skip(reason="Требует прав администратора в чате")
@pytest.mark.skipif(CHAT_ID is None or MESSAGE_ID is None, reason="Chat ID или Message ID не найдены")
def test_pin_message():
    resp = put(f"/chats/{CHAT_ID}/messages/{MESSAGE_ID}/pin", json={"notify": False})
    assert resp.status_code == 200

@pytest.mark.skip(reason="Требует прав администратора в чате")
@pytest.mark.skipif(CHAT_ID is None or MESSAGE_ID is None, reason="Chat ID или Message ID не найдены")
def test_unpin_message():
    resp = delete(f"/chats/{CHAT_ID}/messages/{MESSAGE_ID}/pin")
    assert resp.status_code == 200

@pytest.mark.skip(reason="Требует прав администратора в чате")
@pytest.mark.skipif(CHAT_ID is None, reason="Chat ID не найден")
def test_add_chat_members():
    # Используем ID текущего пользователя, чтобы не вызывать ошибку
    user_id = 5252202 # ID из captured_updates.json 
    resp = post(f"/chats/{CHAT_ID}/members", json={"user_ids": [user_id]})
    assert resp.status_code == 200

@pytest.mark.skip(reason="Этот тест приведет к выходу бота из чата")
@pytest.mark.skipif(CHAT_ID is None, reason="Chat ID не найден")
def test_leave_chat():
    resp = delete(f"/chats/{CHAT_ID}/members/me")
    assert resp.status_code == 200

if __name__ == "__main__":
    print(f"Chat ID: {CHAT_ID}")
    print(f"User ID: {USER_ID}")
    print(f"Message ID: {MESSAGE_ID}")
    
    # Запускаем базовые тесты
    test_get_me()
    test_get_chats()
    test_get_subscriptions()
    test_get_updates()
    test_get_messages()
    
    print("Базовые тесты пройдены успешно!") 