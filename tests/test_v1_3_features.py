"""
Тесты для новых возможностей v1.3
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
from maxbot import Bot
from maxbot.filters import (
    command, text, has_attachment, and_filter, or_filter, not_filter,
    time_filter, user_filter, custom_filter
)

@pytest.fixture
def bot():
    """Создает тестовый экземпляр бота."""
    return Bot("test_token")

@pytest.fixture
def temp_file():
    """Создает временный файл для тестов."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(b"test content")
        temp_path = f.name
    
    yield temp_path
    
    # Очистка
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestFileOperations:
    """Тесты для операций с файлами."""
    
    @pytest.mark.asyncio
    async def test_validate_file_size(self, bot, temp_file):
        """Тест валидации размера файла."""
        # Проверяем что файл проходит валидацию
        assert await bot.validate_file_size(temp_file, max_size_mb=1)
        
        # Проверяем что большой файл не проходит
        assert not await bot.validate_file_size(temp_file, max_size_mb=0.00001)
    
    @pytest.mark.asyncio
    async def test_validate_file_size_bytes(self, bot):
        """Тест валидации размера байтов."""
        test_bytes = b"test content"
        assert await bot.validate_file_size(test_bytes, max_size_mb=1)
        assert not await bot.validate_file_size(test_bytes, max_size_mb=0.00001)
    
    @pytest.mark.asyncio
    async def test_validate_file_size_file_not_found(self, bot):
        """Тест валидации несуществующего файла."""
        with pytest.raises(FileNotFoundError):
            await bot.validate_file_size("nonexistent_file.txt")
    
    @pytest.mark.asyncio
    async def test_get_supported_formats(self, bot):
        """Тест получения поддерживаемых форматов."""
        image_formats = await bot.get_supported_formats("image")
        assert ".jpg" in image_formats
        assert ".png" in image_formats
        
        video_formats = await bot.get_supported_formats("video")
        assert ".mp4" in video_formats
        
        audio_formats = await bot.get_supported_formats("audio")
        assert ".mp3" in audio_formats
        
        file_formats = await bot.get_supported_formats("file")
        assert ".pdf" in file_formats
        
        # Неизвестный тип
        unknown_formats = await bot.get_supported_formats("unknown")
        assert unknown_formats == []
    
    @pytest.mark.asyncio
    async def test_validate_file_format(self, bot, temp_file):
        """Тест валидации формата файла."""
        # Создаем файл с правильным расширением
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b"fake image")
            image_path = f.name
        
        try:
            assert await bot.validate_file_format(image_path, "image")
            assert not await bot.validate_file_format(image_path, "video")
        finally:
            if os.path.exists(image_path):
                os.unlink(image_path)
    
    @pytest.mark.asyncio
    async def test_validate_file_format_bytes(self, bot):
        """Тест валидации формата байтов."""
        # Для байтов True только если нет поддерживаемых форматов
        test_bytes = b"test content"
        assert not await bot.validate_file_format(test_bytes, "image")
        assert await bot.validate_file_format(test_bytes, "unknown")
    
    @pytest.mark.asyncio
    async def test_download_file(self, bot):
        """Тест скачивания файла."""
        with patch.object(bot, '_ensure_session'), \
             patch.object(bot, 'session') as mock_session:
            
            # Мокаем ответ
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.read.return_value = b"downloaded content"
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Тестируем скачивание в память
            result = await bot.download_file("test_file_id")
            assert result == b"downloaded content"
            
            # Тестируем скачивание в файл
            with tempfile.NamedTemporaryFile(delete=False) as f:
                save_path = f.name
            
            try:
                result = await bot.download_file("test_file_id", save_path)
                assert result == save_path
                assert os.path.exists(save_path)
                
                with open(save_path, 'rb') as f:
                    content = f.read()
                assert content == b"downloaded content"
            finally:
                if os.path.exists(save_path):
                    os.unlink(save_path)
    
    @pytest.mark.asyncio
    async def test_get_file(self, bot):
        """Тест получения информации о файле."""
        with patch.object(bot, '_make_request') as mock_request:
            mock_request.return_value = {"file_id": "test", "size": 1024}
            
            result = await bot.get_file("test_file_id")
            assert result == {"file_id": "test", "size": 1024}
            mock_request.assert_called_once_with('GET', 'files/test_file_id')

class TestCombinedFilters:
    """Тесты для комбинированных фильтров."""
    
    @pytest.fixture
    def mock_context(self):
        """Создает мок контекста."""
        context = MagicMock()
        context.text = "test message"
        context.user_id = 123
        context.chat_id = 456
        context.attachments = []
        return context
    
    @pytest.mark.asyncio
    async def test_and_filter(self, mock_context):
        """Тест AND фильтра."""
        # Оба фильтра проходят
        filter1 = text("test", exact=False)
        filter2 = text("message", exact=False)
        and_filter_obj = and_filter(filter1, filter2)
        
        assert await and_filter_obj.check(mock_context)
        
        # Один фильтр не проходит
        filter3 = text("nonexistent", exact=False)
        and_filter_obj2 = and_filter(filter1, filter3)
        
        assert not await and_filter_obj2.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_or_filter(self, mock_context):
        """Тест OR фильтра."""
        # Один фильтр проходит
        filter1 = text("test", exact=False)
        filter2 = text("nonexistent", exact=False)
        or_filter_obj = or_filter(filter1, filter2)
        
        assert await or_filter_obj.check(mock_context)
        
        # Ни один фильтр не проходит
        filter3 = text("another", exact=False)
        or_filter_obj2 = or_filter(filter2, filter3)
        
        assert not await or_filter_obj2.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_not_filter(self, mock_context):
        """Тест NOT фильтра."""
        # Фильтр не проходит, NOT должен вернуть True
        filter1 = text("nonexistent", exact=False)
        not_filter_obj = not_filter(filter1)
        
        assert await not_filter_obj.check(mock_context)
        
        # Фильтр проходит, NOT должен вернуть False
        filter2 = text("test", exact=False)
        not_filter_obj2 = not_filter(filter2)
        
        assert not await not_filter_obj2.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_time_filter(self, mock_context):
        """Тест фильтра по времени."""
        with patch('datetime.datetime') as mock_datetime:
            # Устанавливаем время 12:00
            mock_datetime.now.return_value.hour = 12
            
            # Фильтр с 10:00 до 14:00
            time_filter_obj = time_filter(10, 14)
            assert await time_filter_obj.check(mock_context)
            
            # Фильтр с 14:00 до 10:00 (ночное время)
            time_filter_obj2 = time_filter(14, 10)
            assert not await time_filter_obj2.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_user_filter(self, mock_context):
        """Тест фильтра по пользователю."""
        # Пользователь в списке
        user_filter_obj = user_filter([123, 456])
        assert await user_filter_obj.check(mock_context)
        
        # Пользователь не в списке
        user_filter_obj2 = user_filter([789, 999])
        assert not await user_filter_obj2.check(mock_context)
        
        # Один пользователь
        user_filter_obj3 = user_filter(123)
        assert await user_filter_obj3.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_custom_filter(self, mock_context):
        """Тест кастомного фильтра."""
        def is_long_message(ctx):
            return len(ctx.text) > 5
        
        custom_filter_obj = custom_filter(is_long_message)
        assert await custom_filter_obj.check(mock_context)
        
        def is_short_message(ctx):
            return len(ctx.text) < 5
        
        custom_filter_obj2 = custom_filter(is_short_message)
        assert not await custom_filter_obj2.check(mock_context)

class TestFilterOperators:
    """Тесты для операторов фильтров."""
    
    @pytest.fixture
    def mock_context(self):
        """Создает мок контекста."""
        context = MagicMock()
        context.text = "test message"
        context.user_id = 123
        return context
    
    @pytest.mark.asyncio
    async def test_and_operator(self, mock_context):
        """Тест оператора &."""
        filter1 = text("test", exact=False)
        filter2 = text("message", exact=False)
        
        combined = filter1 & filter2
        assert await combined.check(mock_context)
        
        filter3 = text("nonexistent", exact=False)
        combined2 = filter1 & filter3
        assert not await combined2.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_or_operator(self, mock_context):
        """Тест оператора |."""
        filter1 = text("test", exact=False)
        filter2 = text("nonexistent", exact=False)
        
        combined = filter1 | filter2
        assert await combined.check(mock_context)
        
        filter3 = text("another", exact=False)
        combined2 = filter2 | filter3
        assert not await combined2.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_invert_operator(self, mock_context):
        """Тест оператора ~."""
        filter1 = text("nonexistent", exact=False)
        
        inverted = ~filter1
        assert await inverted.check(mock_context)
        
        filter2 = text("test", exact=False)
        inverted2 = ~filter2
        assert not await inverted2.check(mock_context)

class TestComplexFilterScenarios:
    """Тесты сложных сценариев фильтров."""
    
    @pytest.fixture
    def mock_context(self):
        """Создает мок контекста."""
        context = MagicMock()
        context.text = "admin command"
        context.user_id = 123
        context.attachments = [MagicMock(type="image")]
        return context
    
    @pytest.mark.asyncio
    async def test_admin_with_attachment(self, mock_context):
        """Тест сложного фильтра: админ + вложение."""
        admin_filter = and_filter(
            text("admin", exact=False),
            user_filter([123]),
            has_attachment()
        )
        
        assert await admin_filter.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_command_or_attachment(self, mock_context):
        """Тест фильтра: команда ИЛИ вложение."""
        command_or_attachment = or_filter(
            command("start"),
            has_attachment()
        )
        
        assert await command_or_attachment.check(mock_context)
    
    @pytest.mark.asyncio
    async def test_not_admin(self, mock_context):
        """Тест фильтра: НЕ админ."""
        not_admin = not_filter(user_filter([123]))
        
        assert not await not_admin.check(mock_context)
        
        # Изменяем ID пользователя
        mock_context.user_id = 999
        assert await not_admin.check(mock_context)

if __name__ == "__main__":
    pytest.main([__file__]) 