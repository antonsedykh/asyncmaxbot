"""
Middleware система для Max Bot API Client
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Any, Dict, Awaitable
from loguru import logger

from .max_types import Context

class BaseMiddleware(ABC):
    """Абстрактный базовый класс для всех middleware."""
    
    def __init__(self):
        self._next: Optional[Callable] = None
    
    def set_next(self, next_handler: Callable):
        """Устанавливает следующий обработчик в цепочке"""
        self._next = next_handler
    
    @abstractmethod
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context):
        """
        Основной метод middleware. Должен быть переопределен.
        Важно вызвать `await handler(ctx)` внутри, чтобы передать управление дальше.
        """
        pass

class MiddlewareManager:
    """
    Управляет выполнением цепочки middleware.

    Вызывает каждый middleware последовательно перед тем, как
    достичь основного обработчика.
    """
    
    def __init__(self):
        self.middlewares: List[BaseMiddleware] = []
    
    def add_middleware(self, middleware: BaseMiddleware):
        """Регистрирует новый middleware."""
        self.middlewares.append(middleware)
    
    async def process(self, ctx: Context, final_handler: Callable) -> Any:
        """
        Запускает цепочку middleware и вызывает конечный обработчик.
        """
        if not self.middlewares:
            return await final_handler(ctx)
        
        # Создаем цепочку в обратном порядке
        current = final_handler
        
        for middleware in reversed(self.middlewares):
            # Создаем обертку для каждого middleware
            def create_wrapper(mw, next_handler):
                async def wrapper(context):
                    return await mw(next_handler, context)
                return wrapper
            
            current = create_wrapper(middleware, current)
        
        return await current(ctx)

# Встроенные middleware

class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования входящих сообщений.

    Выводит в лог информацию о пользователе и тексте сообщения.
    """
    
    def __init__(self, log_level: str = "INFO"):
        super().__init__()
        self.log_level = log_level
    
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context):
        if ctx.payload:
            logger.info(f"Received callback from user_id={ctx.user_id}: payload='{ctx.payload}'")
        else:
            logger.info(f"Received message from user_id={ctx.user_id}: '{ctx.text}'")
        return await handler(ctx)

class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Middleware для отлова и логирования ошибок в обработчиках.

    Перехватывает исключения, чтобы бот не падал из-за ошибки
    в одном из хендлеров.
    """
    
    def __init__(self, error_handler: Optional[Callable] = None):
        super().__init__()
        self.error_handler = error_handler
    
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context):
        try:
            return await handler(ctx)
        except Exception as e:
            logger.error(f"Error in handler for update: {e}", exc_info=True)
            
            if self.error_handler:
                try:
                    await self.error_handler(ctx, e)
                except Exception as handler_error:
                    logger.error(f"Error in error handler: {handler_error}")
            
            # Можно отправить сообщение пользователю об ошибке
            try:
                await ctx.reply("Произошла ошибка, но я уже сообщил о ней разработчикам.")
            except Exception as reply_error:
                logger.error(f"Could not send error reply: {reply_error}")
            return None

class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, rate_limit: float = 1.0):  # секунды между запросами
        super().__init__()
        self.rate_limit = rate_limit
        self.user_timestamps = {}
    
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context) -> Any:
        user_id = ctx.user_id
        current_time = asyncio.get_event_loop().time()
        
        # Проверяем, не слишком ли часто пользователь отправляет сообщения
        if user_id in self.user_timestamps:
            time_diff = current_time - self.user_timestamps[user_id]
            if time_diff < self.rate_limit:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                await ctx.reply("Пожалуйста, не отправляйте сообщения так часто.")
                return
        
        # Обновляем временную метку
        self.user_timestamps[user_id] = current_time
        
        # Вызываем следующий обработчик
        return await handler(ctx)

class UserTrackingMiddleware(BaseMiddleware):
    """Middleware для отслеживания пользователей"""
    
    def __init__(self):
        super().__init__()
        self.active_users = set()
    
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context) -> Any:
        user_id = ctx.user_id
        
        # Добавляем пользователя в активные
        self.active_users.add(user_id)
        
        logger.info(f"Active users: {len(self.active_users)}")
        
        # Вызываем следующий обработчик
        result = await handler(ctx)
        
        return result
    
    def get_active_users_count(self) -> int:
        """Возвращает количество активных пользователей"""
        return len(self.active_users)
    
    def get_active_users(self) -> set:
        """Возвращает множество активных пользователей"""
        return self.active_users.copy()

class MetricsMiddleware(BaseMiddleware):
    """Middleware для сбора метрик"""
    
    def __init__(self):
        super().__init__()
        self.message_count = 0
        self.error_count = 0
        self.start_time = asyncio.get_event_loop().time()
    
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context) -> Any:
        self.message_count += 1
        
        try:
            result = await handler(ctx)
            return result
        except Exception as e:
            self.error_count += 1
            raise
    
    def get_metrics(self) -> dict:
        """Возвращает собранные метрики"""
        current_time = asyncio.get_event_loop().time()
        uptime = current_time - self.start_time
        
        return {
            "messages_processed": self.message_count,
            "errors": self.error_count,
            "uptime_seconds": uptime,
            "messages_per_second": self.message_count / uptime if uptime > 0 else 0,
            "error_rate": self.error_count / self.message_count if self.message_count > 0 else 0
        }

TrackingMiddleware = UserTrackingMiddleware 

class AntispamMiddleware(BaseMiddleware):
    """Middleware для антиспама: блокирует частые одинаковые сообщения от пользователя"""
    def __init__(self, interval=2.0):
        super().__init__()
        self.interval = interval
        self.last_messages = {}  # user_id: (text, timestamp)
    
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context) -> Any:
        user_id = ctx.user_id
        text = getattr(ctx, 'text', None)
        now = asyncio.get_event_loop().time()
        last = self.last_messages.get(user_id)
        if last and last[0] == text and now - last[1] < self.interval:
            await ctx.reply("Пожалуйста, не спамьте одинаковыми сообщениями.")
            return
        self.last_messages[user_id] = (text, now)
        return await handler(ctx)

class ValidationMiddleware(BaseMiddleware):
    """Middleware для кастомной валидации сообщений"""
    def __init__(self, validator):
        super().__init__()
        self.validator = validator  # async def validator(ctx) -> bool
    
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context) -> Any:
        if await self.validator(ctx):
            return await handler(ctx)
        else:
            await ctx.reply("Сообщение не прошло валидацию.")
            return

class ProfilingMiddleware(BaseMiddleware):
    """Middleware для профилирования времени обработки"""
    def __init__(self):
        super().__init__()
        self.times = []
    
    async def __call__(self, handler: Callable[[Context], Awaitable[Any]], ctx: Context) -> Any:
        start_time = asyncio.get_event_loop().time()
        result = await handler(ctx)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        self.times.append(processing_time)
        
        logger.info(f"Handler processing time: {processing_time:.3f}s")
        return result
    
    def get_avg_time(self):
        """Возвращает среднее время обработки"""
        return sum(self.times) / len(self.times) if self.times else 0 