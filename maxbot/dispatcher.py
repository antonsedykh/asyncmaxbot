"""
Диспетчер для обработки обновлений MaxBot
"""

import asyncio
from typing import Callable, List, Optional, Union, TYPE_CHECKING, Coroutine, Any, Dict
from loguru import logger
from logging import getLogger

if TYPE_CHECKING:
    from .bot import Bot

from .max_types import Context, Update, CallbackQuery, Message, User, BaseAttachment
from .filters import BaseFilter, Command, Filter, command, text, and_filter
from .middleware import MiddlewareManager
from .router import Router

class Handler:
    """
    Контейнер для хранения обработчика (callback) и связанных с ним фильтров.
    """
    
    def __init__(self, callback: Callable[[Context], Coroutine[Any, Any, None]], filter: Filter):
        """
        :param callback: Функция-обработчик, которая будет вызвана.
        :param filter: Фильтр, который должен быть пройден.
        """
        self.callback = callback
        self.filter = filter
    
    async def check(self, ctx: Context) -> bool:
        """
        Проверяет, соответствует ли контекст фильтру этого обработчика.

        :param ctx: Объект Context для проверки.
        :return: True, если фильтр пройден, иначе False.
        """
        return await self.filter.check(ctx)

class Dispatcher:
    """
    Диспетчер обрабатывает входящие обновления, пропускает их через Middleware,
    находит подходящий обработчик на основе фильтров и вызывает его.
    """
    
    def __init__(self, bot: 'Bot'):
        """
        :param bot: Экземпляр класса Bot.
        """
        self.bot = bot
        self.handlers: List[Handler] = []
        self.callback_query_handlers: List[Handler] = []
        self.bot_started_handlers: List[Handler] = []
        self.user_added_handlers: List[Handler] = []
        self.chat_member_updated_handlers: List[Handler] = []
        self.middleware_manager = MiddlewareManager()
        self.logger = getLogger(__name__)
    
    def include_router(self, router: Router):
        """
        Подключает роутер к диспетчеру.
        Все обработчики из роутера будут добавлены в диспетчер.

        :param router: Экземпляр класса Router.
        """
        for handler_info in router.message_handlers:
            filter_instance = self._combine_filters(handler_info["filters"])
            self.handlers.append(Handler(handler_info["handler"], filter_instance))
        
        for handler_info in router.callback_query_handlers:
            filter_instance = self._combine_filters(handler_info["filters"])
            self.callback_query_handlers.append(Handler(handler_info["handler"], filter_instance))

        for handler_info in router.bot_started_handlers:
            filter_instance = self._combine_filters(handler_info["filters"])
            self.bot_started_handlers.append(Handler(handler_info["handler"], filter_instance))

        for handler_info in router.user_added_handlers:
            filter_instance = self._combine_filters(handler_info["filters"])
            self.user_added_handlers.append(Handler(handler_info["handler"], filter_instance))
        
        for handler_info in router.chat_member_updated_handlers:
            filter_instance = self._combine_filters(handler_info["filters"])
            self.chat_member_updated_handlers.append(Handler(handler_info["handler"], filter_instance))

    def message_handler(self, *filters: Filter):
        """
        Декоратор для регистрации обработчика сообщений.

        Пример:
        @dp.message_handler(commands=["start"])
        async def start_command(ctx: Context):
            await ctx.reply("Привет!")

        :param filters: Последовательность фильтров. Обработчик сработает,
                        если все фильтры вернут True.
        """
        def decorator(callback: Callable[[Context], Coroutine[Any, Any, None]]):
            filter_instance = self._combine_filters(filters)
            self.handlers.append(Handler(callback, filter_instance))
            return callback
        return decorator
    
    def callback_query_handler(self, *filters: Filter):
        """
        Декоратор для регистрации обработчика callback-запросов.
        Пример:
        @dp.callback_query_handler(F.data == "info")
        async def callback_handler(ctx): ...
        """
        def decorator(callback: Callable[[Context], Coroutine[Any, Any, None]]):
            filter_instance = self._combine_filters(filters)
            self.callback_query_handlers.append(Handler(callback, filter_instance))
            return callback
        return decorator
    
    def bot_started_handler(self, *filters: Filter):
        """Декоратор для регистрации обработчика события 'bot_started'."""
        def decorator(callback: Callable[[Context], Coroutine[Any, Any, None]]):
            filter_instance = self._combine_filters(filters)
            self.bot_started_handlers.append(Handler(callback, filter_instance))
            return callback
        return decorator

    def user_added_handler(self, *filters: Filter):
        """Декоратор для регистрации обработчика события 'user_added'."""
        def decorator(callback: Callable[[Context], Coroutine[Any, Any, None]]):
            filter_instance = self._combine_filters(filters)
            self.user_added_handlers.append(Handler(callback, filter_instance))
            return callback
        return decorator
    
    def chat_member_updated_handler(self, *filters: Filter):
        """Декоратор для регистрации обработчика события 'chat_member_updated'."""
        def decorator(callback: Callable[[Context], Coroutine[Any, Any, None]]):
            filter_instance = self._combine_filters(filters)
            self.chat_member_updated_handlers.append(Handler(callback, filter_instance))
            return callback
        return decorator
    
    def _combine_filters(self, filters: tuple[Filter, ...]) -> Filter:
        if len(filters) == 1:
            return filters[0]
        
        return and_filter(*filters)
    
    def include_middleware(self, middleware):
        """
        Добавляет Middleware для обработки всех входящих обновлений.

        :param middleware: Объект Middleware.
        """
        self.middleware_manager.add_middleware(middleware)
    
    async def process_update(self, update_data: Dict[str, Any]):
        """
        Основной метод обработки входящего обновления.
        Определяет тип обновления и вызывает нужный обработчик.
        """
        self.logger.info(f"=== DISPATCHER: Processing update ===")
        self.logger.debug(f"Processing update data: {update_data}")
        try:
            update = Update.model_validate(update_data)
            
            update_type = update.update_type
            self.logger.info(f"Update type: {update_type}")
            
            if update_type == 'message_callback':
                self.logger.info("Processing as callback query")
                if update.callback:
                    await self._process_event(update, self.callback_query_handlers)
                else:
                    self.logger.warning("Received message_callback update without callback data.")

            elif update_type == 'message_created':
                self.logger.info("Processing as message")
                if update.message:
                    await self._process_event(update, self.handlers)
                else:
                    self.logger.warning(f"Update without message: {update}")
            
            elif update_type == 'bot_started':
                self.logger.info("Processing as bot_started")
                if update.bot_started:
                     await self._process_event(update, self.bot_started_handlers)
                else:
                    self.logger.warning(f"Update without bot_started data: {update}")

            elif update_type == 'user_added':
                self.logger.info("Processing as user_added")
                if update.user_added:
                    await self._process_event(update, self.user_added_handlers)
                else:
                    self.logger.warning(f"Update without user_added data: {update}")

            elif update_type == 'chat_member_updated':
                self.logger.info("Processing as chat_member_updated")
                if update.chat_member_updated:
                    await self._process_event(update, self.chat_member_updated_handlers)
                else:
                    self.logger.warning(f"Update without chat_member_updated data: {update}")

        except Exception as e:
            self.logger.error(f"Error processing update: {e}", exc_info=True)
            self.logger.debug(f"Update data that caused error: {update_data}")

    async def _process_event(self, update: Update, handlers: List[Handler]):
        """
        Универсальный метод для обработки любого события.
        Создает контекст и ищет подходящий обработчик.
        """
        ctx = Context(update, self.bot)
        for handler in handlers:
            try:
                filter_check_result = await handler.check(ctx)
                self.logger.debug(f"Checking handler '{getattr(handler.callback, '__name__', 'unknown')}' -> Filter check: {filter_check_result}")
                if filter_check_result:
                    self.logger.info(f"Found handler '{getattr(handler.callback, '__name__', 'unknown')}'. Processing...")
                    await self.middleware_manager.process(ctx, handler.callback)
                    return
            except Exception as e:
                self.logger.error(f"Error in handler '{getattr(handler.callback, '__name__', 'unknown')}': {e}", exc_info=True)
        self.logger.warning(f"No matching handler for update: {update.update_type}")

    async def _process_message(self, ctx: Context):
        self.logger.debug("Created context. Text: '%s', Attachments: %s", ctx.text, ctx.attachments)
        
        for handler in self.handlers:
            try:
                filter_check_result = await handler.check(ctx)
                self.logger.debug(f"Checking handler '{getattr(handler.callback, '__name__', 'unknown')}' -> Filter check: {filter_check_result}")
                if filter_check_result:
                    self.logger.info(f"Found handler '{getattr(handler.callback, '__name__', 'unknown')}'. Processing...")
                    await self.middleware_manager.process(ctx, handler.callback)
                    return
            except Exception as e:
                self.logger.error(f"Error in handler '{getattr(handler.callback, '__name__', 'unknown')}': {e}", exc_info=True)
        self.logger.warning(f"No matching handler for text: '{ctx.text}'")

    async def _process_callback_query(self, ctx: Context):
        for handler in self.callback_query_handlers:
            try:
                if await handler.check(ctx):
                    self.logger.info(f"Found callback handler '{getattr(handler.callback, '__name__', 'unknown')}'. Processing...")
                    await self.middleware_manager.process(ctx, handler.callback)
                    return
            except Exception as e:
                self.logger.error(f"Error in callback handler '{getattr(handler.callback, '__name__', 'unknown')}': {e}", exc_info=True)
        self.logger.warning(f"No matching callback handler for payload: '{ctx.payload}'")

    async def start_polling(self, skip_updates: bool = False):
        """
        Starts the polling process to receive updates from the bot API.
        """
        if skip_updates:
            await self.bot.get_updates(offset=-1)

        self.logger.info("Bot started polling...")
        while True:
            try:
                self.logger.info("Calling bot.get_updates()...")
                updates_response = await self.bot.get_updates()
                self.logger.info(f"Received updates response: {len(updates_response.get('updates', []))} updates")
                if 'updates' in updates_response:
                    for i, update in enumerate(updates_response['updates']):
                        self.logger.info(f"Processing update {i+1}/{len(updates_response['updates'])}: {update.get('update_type', 'unknown')}")
                        await self.process_update(update)
                else:
                    self.logger.info("No updates in response")
            except Exception as e:
                self.logger.error(f"Error during polling: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait between polling attempts 