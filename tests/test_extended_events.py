import pytest
from unittest.mock import AsyncMock

from maxbot import Bot, Dispatcher, Context
from maxbot.max_types import Update, BotStarted, UserAdded, ChatMemberUpdated, User

@pytest.mark.asyncio
async def test_bot_started_event():
    """Тест обработки события 'bot_started'."""
    bot = Bot("test_token")
    dp = Dispatcher(bot)
    handler_was_called = False

    @dp.bot_started_handler()
    async def bot_started_handler(ctx: Context):
        nonlocal handler_was_called
        assert isinstance(ctx.bot_started, BotStarted)
        assert ctx.bot_started.chat_id == 123
        handler_was_called = True

    update_data = {
        "update_id": "1",
        "update_type": "bot_started",
        "timestamp": 1672531200,
        "bot_started": {
            "chat_id": 123,
            "user": {"user_id": 100, "is_bot": False, "name": "Test User"}
        }
    }
    
    await dp.process_update(update_data)
    assert handler_was_called is True

@pytest.mark.asyncio
async def test_user_added_event():
    """Тест обработки события 'user_added'."""
    bot = Bot("test_token")
    dp = Dispatcher(bot)
    handler_was_called = False

    @dp.user_added_handler()
    async def user_added_handler(ctx: Context):
        nonlocal handler_was_called
        assert isinstance(ctx.user_added, UserAdded)
        assert ctx.user_added.chat_id == 456
        assert ctx.user_added.user.user_id == 101
        assert ctx.user_added.inviter.user_id == 100
        handler_was_called = True

    update_data = {
        "update_id": "2",
        "update_type": "user_added",
        "timestamp": 1672531201,
        "user_added": {
            "chat_id": 456,
            "user": {"user_id": 101, "is_bot": False, "name": "New User"},
            "inviter": {"user_id": 100, "is_bot": False, "name": "Inviter"}
        }
    }
    
    await dp.process_update(update_data)
    assert handler_was_called is True

@pytest.mark.asyncio
async def test_chat_member_updated_event():
    """Тест обработки события 'chat_member_updated'."""
    bot = Bot("test_token")
    dp = Dispatcher(bot)
    handler_was_called = False

    @dp.chat_member_updated_handler()
    async def chat_member_updated_handler(ctx: Context):
        nonlocal handler_was_called
        assert isinstance(ctx.chat_member_updated, ChatMemberUpdated)
        assert ctx.chat_member_updated.chat_id == 789
        assert ctx.chat_member_updated.old_status == "member"
        assert ctx.chat_member_updated.new_status == "admin"
        handler_was_called = True

    update_data = {
        "update_id": "3",
        "update_type": "chat_member_updated",
        "timestamp": 1672531202,
        "chat_member_updated": {
            "chat_id": 789,
            "user": {"user_id": 102, "is_bot": False, "name": "Updated User"},
            "old_status": "member",
            "new_status": "admin"
        }
    }
    
    await dp.process_update(update_data)
    assert handler_was_called is True 