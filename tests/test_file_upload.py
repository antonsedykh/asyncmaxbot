"""
Тесты для системы загрузки файлов
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO
from PIL import Image
from maxbot import Bot

# Загружаем токен из файла
def get_token():
    token_file = "token.txt"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return os.environ.get("MAXBOT_TOKEN", "YOUR_TOKEN_HERE")

TOKEN = get_token()

class TestFileUpload:
    """Тесты загрузки файлов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.bot = Bot(TOKEN)
    
    @pytest.mark.asyncio
    async def test_upload_image_from_path(self):
        """Тест загрузки изображения из файла"""
        # Создаем временный файл изображения
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(b'fake_jpeg_data')
            tmp_file_path = tmp_file.name
        
        try:
            async with self.bot:
                with patch.object(self.bot.session, 'post') as mock_post:
                    mock_response = AsyncMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.return_value = {
                        'file_id': 'test_file_id',
                        'url': 'https://example.com/test.jpg',
                        'type': 'image'
                    }
                    mock_post.return_value.__aenter__.return_value = mock_response
                    
                    result = await self.bot.upload_image(tmp_file_path)
                    
                    assert result['file_id'] == 'test_file_id'
                    assert result['url'] == 'https://example.com/test.jpg'
                    assert result['type'] == 'image'
                    
        finally:
            os.unlink(tmp_file_path)
    
    @pytest.mark.asyncio
    async def test_upload_video_from_bytes(self):
        """Тест загрузки видео из байтов"""
        video_data = b'fake_video_data'
        
        async with self.bot:
            with patch.object(self.bot.session, 'post') as mock_post:
                mock_response = AsyncMock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {
                    'file_id': 'video_id',
                    'url': 'https://example.com/test.mp4',
                    'type': 'video'
                }
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await self.bot.upload_video(
                    video_data, 
                    filename='test.mp4',
                    mime_type='video/mp4'
                )
                
                assert result['file_id'] == 'video_id'
                assert result['type'] == 'video'
    
    @pytest.mark.asyncio
    async def test_send_photo(self):
        """Тест отправки фото"""
        photo_data = b'fake_photo_data'
        
        async with self.bot:
            with patch.object(self.bot, 'upload_image') as mock_upload, \
                 patch.object(self.bot, '_make_request') as mock_request:
                
                mock_upload.return_value = {
                    'file_id': 'photo_id',
                    'url': 'https://example.com/photo.jpg',
                    'type': 'image'
                }
                
                mock_request.return_value = {
                    'message': {
                        'message_id': 'msg_id',
                        'text': 'Test caption'
                    }
                }
                
                result = await self.bot.send_photo(
                    photo_data,
                    user_id=123,
                    caption='Test caption'
                )
                
                mock_upload.assert_called_once_with(photo_data)
                mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_file_not_found_error(self):
        """Тест ошибки при отсутствии файла"""
        async with self.bot:
            with pytest.raises(FileNotFoundError):
                await self.bot.upload_image('/nonexistent/file.jpg')
    
    @pytest.mark.asyncio
    async def test_session_not_initialized_error(self):
        """Тест ошибки при неинициализированной сессии"""
        with pytest.raises(RuntimeError, match="Session not initialized"):
            await self.bot.upload_image(b'fake_data')
    
    @pytest.mark.asyncio
    async def test_send_without_user_or_chat_id(self):
        """Тест ошибки при отсутствии user_id или chat_id"""
        async with self.bot:
            with patch.object(self.bot, 'upload_image') as mock_upload:
                mock_upload.return_value = {'file_id': 'mock', 'url': 'mock', 'type': 'image'}
                with pytest.raises(ValueError, match="Either user_id or chat_id must be provided"):
                    await self.bot.send_photo(b'fake_data')

class TestFileUploadLive:
    """Живые тесты загрузки файлов (требуют реального API)"""
    def setup_method(self):
        self.bot = Bot(TOKEN)

    @pytest.mark.skipif(TOKEN == "YOUR_TOKEN_HERE", reason="Требуется реальный токен")
    @pytest.mark.asyncio
    async def test_upload_small_image_live(self):
        """Живой тест загрузки маленького изображения"""
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00'
            b'\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00'
            b'\x00\x04\x00\x01\xf5\xc7\xa3\xf0\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        async with self.bot:
            result = await self.bot.upload_image(png_data, filename='test.png')
            assert isinstance(result, dict)
            assert 'file_id' in result or 'url' in result
            print(f"[LIVE] Upload result: {result}")

    @pytest.mark.skipif(TOKEN == "YOUR_TOKEN_HERE", reason="Требуется реальный токен")
    @pytest.mark.skip(reason="API возвращает ошибку при отправке фото")
    @pytest.mark.asyncio
    async def test_send_photo_with_caption_live(self):
        """Живой тест отправки фото с подписью"""
        async with self.bot:
            chats_response = await self.bot.get_chats()
            if 'chats' in chats_response and chats_response['chats']:
                chat = chats_response['chats'][0]
                chat_id = chat['chat_id']
                png_data = (
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00'
                    b'\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00'
                    b'\x00\x04\x00\x01\xf5\xc7\xa3\xf0\x00\x00\x00\x00IEND\xaeB`\x82'
                )
                print("⚡️ Ожидай фото в чате:", chat_id)
                result = await self.bot.send_photo(
                    png_data,
                    chat_id=chat_id,
                    caption='Тестовое фото из live теста'
                )
                assert 'message' in result
                print(f"[LIVE] Photo sent: {result}")
            else:
                print("[LIVE] Нет доступных чатов для теста!")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"]) 