#!/usr/bin/env python3
"""
Тесты для callback функциональности
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from maxbot import Bot, Dispatcher, F
from maxbot.max_types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    CallbackQuery,
    Message,
    User,
    Context
)

class TestCallbackQuery:
    """Тесты для CallbackQuery"""
    
    def test_callback_query_creation(self):
        """Тест создания CallbackQuery"""
        user = Mock(spec=User)
        user.user_id = 123
        user.first_name = "Test"
        
        message = Mock(spec=Message)
        message.body = Mock()
        message.body.mid = "456"
        message.body.text = "Test message"
        
        callback_query = CallbackQuery(
            callback_id="test_id",
            user=user,
            message=message,
            payload="test_data"
        )
        
        assert callback_query.callback_id == "test_id"
        assert callback_query.user == user
        assert callback_query.message == message
        assert callback_query.payload == "test_data"
    
    def test_callback_query_properties(self):
        """Тест свойств CallbackQuery"""
        user = Mock(spec=User)
        user.user_id = 123
        
        message = Mock(spec=Message)
        message.body = Mock()
        message.body.mid = "456"
        
        callback_query = CallbackQuery(
            callback_id="test_id",
            user=user,
            message=message,
            payload="test_data"
        )
        
        assert callback_query.payload == "test_data"
        assert callback_query.user == user

class TestInlineKeyboard:
    """Тесты для inline клавиатур"""
    
    def test_inline_keyboard_button_creation(self):
        """Тест создания InlineKeyboardButton"""
        button = InlineKeyboardButton(
            text="Test Button",
            payload="test_callback"
        )
        
        assert button.text == "Test Button"
        assert button.payload == "test_callback"
    
    def test_inline_keyboard_markup_creation(self):
        """Тест создания InlineKeyboardMarkup"""
        buttons = [
            [
                InlineKeyboardButton(text="Button 1", payload="btn1"),
                InlineKeyboardButton(text="Button 2", payload="btn2")
            ],
            [
                InlineKeyboardButton(text="Button 3", payload="btn3")
            ]
        ]
        
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        assert len(markup.inline_keyboard) == 2
        assert len(markup.inline_keyboard[0]) == 2
        assert len(markup.inline_keyboard[1]) == 1
        assert markup.inline_keyboard[0][0].text == "Button 1"
        assert markup.inline_keyboard[0][1].payload == "btn2"

class TestCallbackHandlers:
    """Тесты для callback обработчиков"""
    
    @pytest.fixture
    def bot(self):
        """Фикстура для бота"""
        return Bot("test_token")
    
    @pytest.fixture
    def dispatcher(self, bot):
        """Фикстура для диспетчера"""
        return Dispatcher(bot)
    
    @pytest.fixture
    def mock_callback_query(self):
        """Фикстура для mock callback_query"""
        user = Mock(spec=User)
        user.user_id = 123
        user.first_name = "Test"
        
        message = Mock(spec=Message)
        message.body = Mock()
        message.body.mid = "456"
        message.recipient = Mock()
        message.recipient.chat_id = 789
        message.edit_text = AsyncMock()
        
        callback_query = CallbackQuery(
            callback_id="test_id",
            user=user,
            message=message,
            payload="test_data"
        )
        
        return callback_query
    
    @pytest.mark.asyncio
    async def test_callback_handler_registration(self, dispatcher):
        """Тест регистрации callback обработчика"""
        handler_called = False
        
        @dispatcher.callback_query_handler(F.payload == "test")
        async def test_handler(callback_query):
            nonlocal handler_called
            handler_called = True
        
        # Проверяем, что обработчик зарегистрирован
        assert len(dispatcher.callback_query_handlers) == 1
    
    @pytest.mark.asyncio
    async def test_callback_handler_execution(self, dispatcher, mock_callback_query):
        """Тест выполнения callback обработчика"""
        handler_called = False
        callback_data = None
        
        @dispatcher.callback_query_handler(F.payload == "test_data")
        async def test_handler(callback_query):
            nonlocal handler_called, callback_data
            handler_called = True
            callback_data = callback_query.payload
        
        # Создаем контекст для callback
        bot = Mock(spec=Bot)
        update = Mock()
        update.update_type = 'message_callback'
        update.callback = mock_callback_query
        update.message = mock_callback_query.message
        ctx = Context(update, bot)
        
        # Проверяем фильтр
        handler = dispatcher.callback_query_handlers[0]
        result = await handler.check(ctx)
        
        assert result
        # Обработчик будет вызван при реальной обработке
    
    @pytest.mark.asyncio
    async def test_callback_filter_matching(self, dispatcher, mock_callback_query):
        """Тест фильтрации callback"""
        handler_called = False
        
        @dispatcher.callback_query_handler(F.payload.startswith("test"))
        async def test_handler(callback_query):
            nonlocal handler_called
            handler_called = True
        
        # Создаем контекст для callback
        bot = Mock(spec=Bot)
        update = Mock()
        update.update_type = 'message_callback'
        update.callback = mock_callback_query
        update.message = mock_callback_query.message
        ctx = Context(update, bot)
        
        # Проверяем фильтр
        handler = dispatcher.callback_query_handlers[0]
        result = await handler.check(ctx)
        
        assert result
    
    @pytest.mark.asyncio
    async def test_callback_filter_not_matching(self, dispatcher, mock_callback_query):
        """Тест несовпадения фильтра callback"""
        handler_called = False
        
        @dispatcher.callback_query_handler(F.payload == "different_data")
        async def test_handler(callback_query):
            nonlocal handler_called
            handler_called = True
        
        # Создаем контекст для callback
        bot = Mock(spec=Bot)
        update = Mock()
        update.update_type = 'message_callback'
        update.callback = mock_callback_query
        update.message = mock_callback_query.message
        ctx = Context(update, bot)
        
        # Проверяем фильтр
        handler = dispatcher.callback_query_handlers[0]
        result = await handler.check(ctx)
        
        assert not result

class TestContextCallback:
    """Тесты для Context с callback"""
    
    @pytest.fixture
    def mock_context(self):
        """Фикстура для mock контекста с callback"""
        user = Mock(spec=User)
        user.user_id = 123
        
        message = Mock(spec=Message)
        message.body = Mock()
        message.body.mid = "456"
        message.recipient = Mock()
        message.recipient.chat_id = 789
        message.edit_text = AsyncMock()
        
        callback_query = CallbackQuery(
            callback_id="test_id",
            user=user,
            message=message,
            payload="test_data"
        )
        
        bot = Mock(spec=Bot)
        update = Mock()
        update.update_type = 'message_callback'
        update.callback = callback_query
        update.message = message
        ctx = Context(update, bot)
        
        return ctx
    
    @pytest.mark.asyncio
    async def test_context_callback_properties(self, mock_context):
        """Тест свойств контекста для callback"""
        assert mock_context.is_callback is True
        assert mock_context.payload == "test_data"
        assert mock_context.callback_id == "test_id"
        assert mock_context.user_id == 123
    
    @pytest.mark.asyncio
    async def test_context_answer_callback(self, mock_context):
        """Тест answer_callback в контексте"""
        mock_context._bot.answer_callback_query = AsyncMock()
        
        await mock_context.answer_callback(text="Test answer")
        
        mock_context._bot.answer_callback_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_edit_message(self, mock_context):
        """Тест edit_message в контексте callback"""
        mock_context._bot.answer_callback_query = AsyncMock()
        
        await mock_context.edit_message(text="New text")
        
        mock_context._bot.answer_callback_query.assert_called_once()

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_callback_flow(self):
        """Тест полного цикла callback"""
        bot = Bot("test_token")
        dispatcher = Dispatcher(bot)
        
        # Создаем обработчики
        callback_received = False
        callback_data = None
        
        @dispatcher.callback_query_handler(F.payload == "test_callback")
        async def test_handler(callback_query):
            nonlocal callback_received, callback_data
            callback_received = True
            callback_data = callback_query.payload
        
        # Создаем mock callback_query
        user = Mock(spec=User)
        user.user_id = 123
        
        message = Mock(spec=Message)
        message.body = Mock()
        message.body.mid = "456"
        message.recipient = Mock()
        message.recipient.chat_id = 789
        
        callback_query = CallbackQuery(
            callback_id="test_id",
            user=user,
            message=message,
            payload="test_callback"
        )
        
        # Создаем полное фейковое обновление
        update_data = {
            "update_id": "1",
            "update_type": "message_callback",
            "timestamp": 1672531200,
            "callback": {
                "callback_id": "test_id",
                "user": {"user_id": 123, "is_bot": False},
                "payload": "test_callback",
                "message": {
                    "body": {"mid": "mid456", "seq": 2},
                    "author": {"user_id": 100, "is_bot": False},
                    "recipient": {"chat_id": 789, "chat_type": "private"},
                    "sender": {"user_id": 100, "is_bot": False},
                    "timestamp": 1672531100
                }
            },
            "message": {
                "body": {"mid": "mid456", "seq": 2},
                "author": {"user_id": 100, "is_bot": False},
                "recipient": {"chat_id": 789, "chat_type": "private"},
                "sender": {"user_id": 100, "is_bot": False},
                "timestamp": 1672531100
            }
        }
        
        # Мокируем методы API, которые могут быть вызваны
        bot.answer_callback_query = AsyncMock()

        # Запускаем полный цикл обработки
        await dispatcher.process_update(update_data)
        
        assert callback_received is True
        assert callback_data == "test_callback"

if __name__ == "__main__":
    pytest.main([__file__]) 