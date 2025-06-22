"""
Тесты для middleware системы
"""

import sys
import os
import asyncio
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from maxbot.middleware import (
    BaseMiddleware, MiddlewareManager,
    LoggingMiddleware, ErrorHandlingMiddleware,
    ThrottlingMiddleware, UserTrackingMiddleware, MetricsMiddleware
)
from maxbot.max_types import Context, Message, User, Chat, Update, MessageBody
from maxbot.bot import Bot

class MockBot:
    """Мок бота для тестов"""
    def __init__(self):
        self.token = "test_token"
    
    async def send_message(self, text, user_id=None, **kwargs):
        """Мок метод для отправки сообщений"""
        return {"message_id": "mock_msg_id"}

class TestMiddleware:
    """Тесты для middleware системы"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.bot = MockBot()
        self.manager = MiddlewareManager()
        
        # Создаем тестовый контекст
        user = User(user_id=123, name="Test User")
        chat = Chat(chat_id=456, chat_type="dialog", user_id=123)
        message_body = MessageBody(mid="test", seq=1, text="test message")
        message = Message(sender=user, recipient=chat, body=message_body, timestamp=123)
        update = Update(update_type="message_created", timestamp=123456, marker=1, message=message)
        self.ctx = Context(update, self.bot)
    
    @pytest.mark.asyncio
    async def test_base_middleware(self):
        """Тест базового middleware"""
        class TestMiddleware(BaseMiddleware):
            def __init__(self):
                super().__init__()
                self.called = False
            
            async def __call__(self, handler, ctx):
                self.called = True
                return await handler(ctx)
        
        middleware = TestMiddleware()
        self.manager.add_middleware(middleware)
        
        async def test_handler(ctx):
            return "success"
        
        result = await self.manager.process(self.ctx, test_handler)
        
        assert result == "success"
        assert middleware.called
    
    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        """Тест LoggingMiddleware"""
        middleware = LoggingMiddleware(log_level="INFO")
        self.manager.add_middleware(middleware)
        
        async def test_handler(ctx):
            return "logged"
        
        result = await self.manager.process(self.ctx, test_handler)
        
        assert result == "logged"
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware(self):
        """Тест ErrorHandlingMiddleware"""
        middleware = ErrorHandlingMiddleware()
        self.manager.add_middleware(middleware)
        
        async def error_handler(ctx):
            raise ValueError("Test error")
        
        # Middleware должен поймать ошибку
        result = await self.manager.process(self.ctx, error_handler)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_throttling_middleware(self):
        """Тест ThrottlingMiddleware"""
        middleware = ThrottlingMiddleware(rate_limit=1.0)
        self.manager.add_middleware(middleware)
        
        async def test_handler(ctx):
            return "throttled"
        
        # Первый вызов должен пройти
        result1 = await self.manager.process(self.ctx, test_handler)
        assert result1 == "throttled"
        
        # Второй вызов сразу должен быть заблокирован
        result2 = await self.manager.process(self.ctx, test_handler)
        assert result2 is None
    
    @pytest.mark.asyncio
    async def test_user_tracking_middleware(self):
        """Тест UserTrackingMiddleware"""
        middleware = UserTrackingMiddleware()
        self.manager.add_middleware(middleware)
        
        async def test_handler(ctx):
            return "tracked"
        
        # Проверяем начальное состояние
        assert middleware.get_active_users_count() == 0
        
        # Обрабатываем сообщение
        result = await self.manager.process(self.ctx, test_handler)
        assert result == "tracked"
        
        # Проверяем, что пользователь добавлен
        assert middleware.get_active_users_count() == 1
        assert 123 in middleware.get_active_users()
    
    @pytest.mark.asyncio
    async def test_metrics_middleware(self):
        """Тест MetricsMiddleware"""
        middleware = MetricsMiddleware()
        self.manager.add_middleware(middleware)
        
        async def test_handler(ctx):
            return "metrics"
        
        # Проверяем начальные метрики
        initial_metrics = middleware.get_metrics()
        assert initial_metrics["messages_processed"] == 0
        assert initial_metrics["errors"] == 0
        
        # Обрабатываем сообщение
        result = await self.manager.process(self.ctx, test_handler)
        assert result == "metrics"
        
        # Проверяем обновленные метрики
        updated_metrics = middleware.get_metrics()
        assert updated_metrics["messages_processed"] == 1
        assert updated_metrics["errors"] == 0
    
    @pytest.mark.asyncio
    async def test_middleware_chain(self):
        """Тест цепочки middleware"""
        # Создаем несколько middleware
        logging_middleware = LoggingMiddleware()
        error_middleware = ErrorHandlingMiddleware()
        tracking_middleware = UserTrackingMiddleware()
        
        self.manager.add_middleware(logging_middleware)
        self.manager.add_middleware(error_middleware)
        self.manager.add_middleware(tracking_middleware)
        
        async def test_handler(ctx):
            return "chain"
        
        # Обрабатываем через цепочку
        result = await self.manager.process(self.ctx, test_handler)
        assert result == "chain"
        
        # Проверяем, что tracking middleware сработал
        assert tracking_middleware.get_active_users_count() == 1
    
    @pytest.mark.asyncio
    async def test_middleware_order(self):
        """Тест порядка выполнения middleware"""
        execution_order = []
        
        class OrderMiddleware(BaseMiddleware):
            def __init__(self, name):
                super().__init__()
                self.name = name
            
            async def __call__(self, handler, ctx):
                execution_order.append(f"before_{self.name}")
                result = await handler(ctx)
                execution_order.append(f"after_{self.name}")
                return result
        
        # Добавляем middleware в определенном порядке
        self.manager.add_middleware(OrderMiddleware("first"))
        self.manager.add_middleware(OrderMiddleware("second"))
        self.manager.add_middleware(OrderMiddleware("third"))
        
        async def test_handler(ctx):
            execution_order.append("handler")
            return "order"
        
        result = await self.manager.process(self.ctx, test_handler)
        assert result == "order"
        
        # Проверяем порядок выполнения
        expected_order = [
            "before_first", "before_second", "before_third", 
            "handler", 
            "after_third", "after_second", "after_first"
        ]
        assert execution_order == expected_order

if __name__ == "__main__":
    pytest.main([__file__]) 