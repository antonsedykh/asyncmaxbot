"""
Тесты для MagicFilter системы
"""

import pytest
from unittest.mock import Mock, AsyncMock
from maxbot.filters import F, MagicFilter, MagicCondition
from maxbot.max_types import Update, Context
from maxbot.bot import Bot

@pytest.fixture
def mock_context():
    """Создает мок контекста для тестов"""
    context = Mock()
    context.text = "Hello world!"
    context.user_id = 123
    context.chat_id = 456
    context.message_id = "789"
    context.date = 1234567890
    context.attachments = []
    context.forward_from = None
    context.reply_to_message = None
    
    # Мок пользователя
    user = Mock()
    user.id = 123
    user.name = "Test User"
    user.username = "testuser"
    context.user = user
    context.from_user = user
    
    # Мок чата
    chat = Mock()
    chat.id = 456
    chat.title = "Test Chat"
    chat.type = "group"
    context.chat = chat
    
    return context

class TestMagicFilter:
    """Тесты для MagicFilter"""
    
    def test_magic_filter_creation(self):
        """Тест создания MagicFilter"""
        assert isinstance(F, MagicFilter)
    
    def test_magic_filter_attribute_access(self):
        """Тест доступа к атрибутам MagicFilter"""
        text_attr = F.text
        assert hasattr(text_attr, 'name')
        assert text_attr.name == 'text'
    
    def test_magic_filter_index_access(self):
        """Тест индексации MagicFilter"""
        text_attr = F['text']
        assert hasattr(text_attr, 'name')
        assert text_attr.name == 'text'

class TestMagicCondition:
    """Тесты для MagicCondition"""
    
    @pytest.mark.asyncio
    async def test_text_equals(self, mock_context):
        """Тест F.text == 'value'"""
        condition = F.text == "Hello world!"
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_text_not_equals(self, mock_context):
        """Тест F.text != 'value'"""
        condition = F.text != "Wrong text"
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_text_contains(self, mock_context):
        """Тест F.text.contains('value')"""
        condition = F.text.contains("world")
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_text_startswith(self, mock_context):
        """Тест F.text.startswith('value')"""
        condition = F.text.startswith("Hello")
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_text_endswith(self, mock_context):
        """Тест F.text.endswith('value')"""
        condition = F.text.endswith("!")
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_user_id_equals(self, mock_context):
        """Тест F.user_id == value"""
        condition = F.user_id == 123
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_user_id_comparison(self, mock_context):
        """Тест F.user_id > value"""
        condition = F.user_id > 100
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_user_id_in_list(self, mock_context):
        """Тест F.user_id.in_([1, 2, 3])"""
        condition = F.user_id.in_([1, 2, 123, 4, 5])
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_chat_id_negative(self, mock_context):
        """Тест F.chat_id < 0"""
        condition = F.chat_id < 0
        result = await condition.check(mock_context)
        assert result is False  # chat_id = 456 > 0
    
    @pytest.mark.asyncio
    async def test_command_filter(self, mock_context):
        """Тест F.command == 'start'"""
        mock_context.text = "/start help"
        condition = F.command == "start"
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_attachment_filter(self, mock_context):
        """Тест F.has_attachments"""
        condition = F.has_attachments == True
        result = await condition.check(mock_context)
        assert result is False  # нет вложений
    
    @pytest.mark.asyncio
    async def test_attachment_with_attachments(self):
        """Тест F.has_attachments с вложениями"""
        # Создаем более реалистичный контекст с вложениями
        update_data = {
            "update_id": "1",
            "update_type": "message_created",
            "timestamp": 1672531200,
            "message": {
                "body": {
                    "mid": "mid123", "seq": 1, "text": "Message with attachment",
                    "attachments": [{
                        "type": "image",
                        "payload": {"url": "http://example.com/img.png"}
                    }]
                },
                "author": {"user_id": 100, "is_bot": False},
                "recipient": {"chat_id": 200, "chat_type": "private"},
                "sender": {"user_id": 100, "is_bot": False},
                "timestamp": 1672531200
            }
        }
        bot = Mock(spec=Bot)
        update = Update.model_validate(update_data)
        ctx = Context(update, bot)

        condition = F.has_attachments == True
        result = await condition.check(ctx)
        assert result is True

class TestCombinedFilters:
    """Тесты для комбинированных фильтров"""
    
    @pytest.mark.asyncio
    async def test_and_filter(self, mock_context):
        """Тест F.text & F.user_id"""
        condition = F.text.contains("Hello") & (F.user_id == 123)
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_or_filter(self, mock_context):
        """Тест F.text | F.user_id"""
        condition = F.text.contains("Wrong") | (F.user_id == 123)
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_not_filter(self, mock_context):
        """Тест ~F.text"""
        condition = ~F.text.contains("Wrong")
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_complex_filter(self, mock_context):
        """Тест сложного фильтра"""
        condition = (
            F.text.contains("Hello") & 
            (F.user_id > 100) & 
            ~F.text.contains("Wrong")
        )
        result = await condition.check(mock_context)
        assert result is True

class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    @pytest.mark.asyncio
    async def test_none_value_handling(self, mock_context):
        """Тест обработки None значений"""
        mock_context.text = None
        condition = F.text.contains("Hello")
        result = await condition.check(mock_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_missing_attribute(self, mock_context):
        """Тест отсутствующего атрибута"""
        condition = F.nonexistent_attribute == "value"
        result = await condition.check(mock_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_invalid_operator(self, mock_context):
        """Тест неверного оператора"""
        condition = MagicCondition(F.text, "invalid", "value")
        result = await condition.check(mock_context)
        assert result is False

class TestCaseInsensitive:
    """Тесты регистронезависимости"""
    
    @pytest.mark.asyncio
    async def test_contains_case_insensitive(self, mock_context):
        """Тест F.text.contains() без учета регистра"""
        condition = F.text.contains("WORLD")
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_startswith_case_insensitive(self, mock_context):
        """Тест F.text.startswith() без учета регистра"""
        condition = F.text.startswith("HELLO")
        result = await condition.check(mock_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_endswith_case_insensitive(self, mock_context):
        """Тест F.text.endswith() без учета регистра"""
        condition = F.text.endswith("!")
        result = await condition.check(mock_context)
        assert result is True

if __name__ == "__main__":
    pytest.main([__file__]) 