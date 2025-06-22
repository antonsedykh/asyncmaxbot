import pytest
from unittest.mock import Mock, AsyncMock
from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.router import Router
from maxbot.max_types import Context
from maxbot.filters import F

@pytest.fixture
def bot():
    """Фикстура для создания мок-объекта Bot."""
    return Mock(spec=Bot)

@pytest.fixture
def dispatcher(bot):
    """Фикстура для создания Dispatcher с мок-ботом."""
    return Dispatcher(bot)

@pytest.fixture
def router():
    """Фикстура для создания экземпляра Router."""
    return Router()

class TestRouter:
    """Тесты для класса Router."""

    def test_message_handler_registration(self, router: Router):
        """Проверяет, что обработчик сообщений правильно регистрируется в роутере."""
        @router.message_handler(F.text == "/test")
        async def my_handler(ctx: Context):
            pass

        assert len(router.message_handlers) == 1
        handler_info = router.message_handlers[0]
        assert handler_info["handler"] == my_handler
        assert len(handler_info["filters"]) == 1

    def test_callback_query_handler_registration(self, router: Router):
        """Проверяет, что обработчик callback'ов правильно регистрируется в роутере."""
        @router.callback_query_handler(F.payload == "test_payload")
        async def my_handler(ctx: Context):
            pass

        assert len(router.callback_query_handlers) == 1
        handler_info = router.callback_query_handlers[0]
        assert handler_info["handler"] == my_handler
        assert len(handler_info["filters"]) == 1

class TestIncludeRouter:
    """Тесты для метода Dispatcher.include_router()."""

    def test_include_router_message_handlers(self, dispatcher: Dispatcher, router: Router):
        """Проверяет, что обработчики сообщений из роутера добавляются в диспетчер."""
        @router.message_handler(F.text == "/test1")
        async def handler1(ctx: Context): pass

        @router.message_handler(F.text == "/test2")
        async def handler2(ctx: Context): pass

        dispatcher.include_router(router)
        assert len(dispatcher.handlers) == 2
        # Простая проверка, что обработчики на месте. Более детально их работу проверит интеграционный тест
        assert dispatcher.handlers[0].callback == handler1
        assert dispatcher.handlers[1].callback == handler2
    
    def test_include_router_callback_query_handlers(self, dispatcher: Dispatcher, router: Router):
        """Проверяет, что обработчики callback'ов из роутера добавляются в диспетчер."""
        @router.callback_query_handler(F.payload == "payload1")
        async def handler1(ctx: Context): pass

        @router.callback_query_handler(F.payload == "payload2")
        async def handler2(ctx: Context): pass

        dispatcher.include_router(router)
        assert len(dispatcher.callback_query_handlers) == 2
        assert dispatcher.callback_query_handlers[0].callback == handler1
        assert dispatcher.callback_query_handlers[1].callback == handler2

@pytest.mark.asyncio
async def test_router_integration_flow(bot, dispatcher: Dispatcher, router: Router):
    """
    Интеграционный тест: проверяет полный цикл от получения обновления 
    до вызова правильного обработчика в роутере.
    """
    handler_was_called = False
    
    @router.message_handler(F.text == "/hello")
    async def hello_handler(ctx: Context):
        nonlocal handler_was_called
        handler_was_called = True
        await ctx.reply("Success!")
        
    dispatcher.include_router(router)

    # Создаем фейковое обновление
    update_data = {
        "update_id": "1",
        "update_type": "message_created",
        "timestamp": 1672531200,
        "message": {
            "body": {"mid": "mid123", "text": "/hello", "seq": 1},
            "author": {"user_id": 100, "is_bot": False},
            "recipient": {"chat_id": 200, "chat_type": "private"},
            "sender": {"user_id": 100, "is_bot": False},
            "timestamp": 1672531200
        }
    }
    
    # Мокируем ответ от reply, чтобы избежать ошибок
    bot.reply = AsyncMock()

    await dispatcher.process_update(update_data)
    
    assert handler_was_called is True 