"""
Основной класс Bot для работы с Max API
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, BinaryIO, Union, TYPE_CHECKING
from loguru import logger
import os
import mimetypes
import time
import urllib.parse
import base64
import json
from io import BytesIO

from .max_types import Update, User, Chat, Message, BaseAttachment, MessageBody

if TYPE_CHECKING:
    from .dispatcher import Dispatcher

class Bot:
    """
    Основной класс для взаимодействия с Max API.

    Этот класс предоставляет методы для отправки сообщений, загрузки файлов,
    получения информации о боте и управления long polling.

    Рекомендуется использовать его как асинхронный контекстный менеджер:
    `async with Bot(token) as bot:`
    """
    
    BASE_URL = "https://botapi.max.ru"
    
    def __init__(self, token: str):
        """
        Инициализирует объект Bot.

        :param token: API токен вашего бота.
        """
        self.token = token
        self.session = None
        self.last_marker = 0
    
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Корректно закрывает aiohttp сессию."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _ensure_session(self):
        """Убеждается что сессия создана"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def _make_request(self, method: str, path: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Внутренний метод для выполнения запросов к API.

        Автоматически добавляет `access_token` и обрабатывает ошибки.
        """
        if not self.session:
            raise RuntimeError("Session is not created. Use 'async with bot:' context manager.")

        # Добавляем токен во все запросы
        request_params = params.copy() if params else {}
        request_params['access_token'] = self.token
        
        try:
            url = f"{self.BASE_URL}/{path}"
            logger.debug(f"Making request: {method} {url} | params={request_params} | json={json}")
            
            async with self.session.request(method, url, params=request_params, json=json) as response:
                logger.debug(f"Response status: {response.status}")
                logger.debug(f"Response headers: {response.headers}")
                text = await response.text()
                logger.debug(f"Response text: {text}")
                response.raise_for_status()
                return await response.json()
        
        except aiohttp.ClientResponseError as e:
            logger.error(
                f"API request failed: {e.status} {e.message} "
                f"| method={method} path={path} params={params} response_text='{e.history[0].text if e.history else ''}'"
            )
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during request: {e}")
            raise
    
    async def get_me(self) -> Dict[str, Any]:
        """
        Получает информацию о текущем боте.

        :return: Словарь с информацией о боте.
        """
        return await self._make_request('GET', 'me')
    
    async def get_updates(self, offset: Optional[int] = None, limit: int = 100, timeout: int = 20) -> Dict:
        """
        Получает список обновлений от API.

        Этот метод используется внутри `polling`. В большинстве случаев вам не нужно вызывать его напрямую.

        :param offset: Маркер, с которого нужно начать получать обновления.
        :param limit: Максимальное количество обновлений за один запрос.
        :param timeout: Таймаут для long polling.
        :return: Словарь с сырыми данными обновлений.
        """
        await self._ensure_session()
        logger.debug(f"get_updates called with offset={offset}, limit={limit}, timeout={timeout}")
        
        params = {
            'limit': limit,
            'timeout': timeout,
            'access_token': self.token
        }
        if offset:
            params['marker'] = offset
            
        try:
            logger.debug(f"Making request to updates with params: {params}")
            async with self.session.get(f"{self.BASE_URL}/updates", params=params) as response:
                logger.debug(f"Response status: {response.status}")
                text = await response.text()
                logger.debug(f"Response text: {text}")
                response.raise_for_status()
                data = await response.json()
                logger.debug(f"Response data: {data}")
                return data
        except aiohttp.ClientResponseError as e:
            logger.error(f"API request failed: {e.status} {e.message}")
            return {}
        except Exception as e:
            logger.error(f"Exception in get_updates: {e}")
            return {}
    
    async def process_update(self, update_data):
        """Обработать обновление"""
        print(f"[DEBUG] process_update called with: {update_data}")
        
        if 'message' in update_data:
            message_data = update_data['message']
            print(f"[DEBUG] Processing message: {message_data}")
            
            # Здесь можно добавить обработку сообщений
            # Например, вызвать обработчики команд
            if 'text' in message_data:
                text = message_data['text']
                print(f"[DEBUG] Received text message: {text}")
                
                # Простая обработка команд
                if text.startswith('/'):
                    await self.handle_command(text, message_data)
    
    async def handle_command(self, command, message_data):
        """Обработать команду"""
        print(f"[DEBUG] Handling command: {command}")
        
        # Получаем данные пользователя и чата
        user_id = message_data.get('from', {}).get('id')
        chat_id = message_data.get('chat', {}).get('id')
        
        if command == '/start':
            await self.send_message("Привет! Я демо-бот Max API.", chat_id=chat_id)
        elif command == '/help':
            await self.send_message("Доступные команды: /start, /help, /info", chat_id=chat_id)
        elif command == '/info':
            await self.send_message("Я бот на Max API", chat_id=chat_id)
    
    async def send_message(self, text: str, user_id: Optional[int] = None, chat_id: Optional[int] = None, reply_markup: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Отправляет текстовое сообщение.
        """
        await self._ensure_session()
        
        params = {}
        if user_id:
            params['user_id'] = user_id
        if chat_id:
            params['chat_id'] = chat_id
        
        if not params:
            raise ValueError("Either user_id or chat_id must be provided.")

        payload = {'text': text, **kwargs}
        
        if reply_markup and hasattr(reply_markup, 'inline_keyboard'):
            attachments = [{
                'type': 'inline_keyboard',
                'payload': {
                    'buttons': [
                        [button.model_dump(exclude_none=True) for button in row] 
                        for row in reply_markup.inline_keyboard
                    ]
                }
            }]
            payload['attachments'] = attachments
            
        return await self._make_request('POST', 'messages', params=params, json=payload)

    async def edit_message(self, message_id: str, text: str, reply_markup: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Редактирует сообщение.
        """
        params = {'message_id': message_id}
        payload = {'text': text, **kwargs}
        
        if reply_markup and hasattr(reply_markup, 'inline_keyboard'):
            attachments = [{
                'type': 'inline_keyboard',
                'payload': {
                    'buttons': [
                        [button.model_dump(exclude_none=True) for button in row]
                        for row in reply_markup.inline_keyboard
                    ]
                }
            }]
            payload['attachments'] = attachments
            
        return await self._make_request('POST', 'messages/edit', params=params, json=payload)

    async def answer_callback_query(self, callback_id: str, **kwargs) -> Dict[str, Any]:
        """
        Отправляет callback-ответ.
        Это алиас для send_callback для совместимости.
        """
        return await self.send_callback(
            callback_query_id=callback_id,
            **kwargs
        )

    async def send_callback(self, callback_query_id: str, **kwargs) -> Dict[str, Any]:
        """
        Отправляет callback-ответ.
        """
        await self._ensure_session()

        params = {'callback_id': callback_query_id}
        
        return await self._make_request('POST', 'answers', params=params, json=kwargs)
    
    async def delete_message(self, message_id: str) -> Dict[str, Any]:
        """
        Удаляет сообщение.

        :param message_id: ID сообщения для удаления.
        :return: Словарь с ответом от API.
        """
        params = {'message_id': message_id}
        return await self._make_request('DELETE', 'messages', params=params)
    
    async def get_chat(self, chat_id: int) -> Dict[str, Any]:
        """
        Получает информацию о чате.

        :param chat_id: ID чата.
        :return: Словарь с информацией о чате.
        """
        return await self._make_request('GET', f'chats/{chat_id}')
    
    async def get_chats(self, **kwargs) -> Dict[str, Any]:
        """
        Получает список чатов, в которых состоит бот.

        :param kwargs: Дополнительные параметры для API.
        :return: Словарь со списком чатов.
        """
        return await self._make_request('GET', 'chats', params=kwargs)
    
    async def get_chat_members(self, chat_id: int, **kwargs) -> Dict[str, Any]:
        """
        Получает список участников чата.

        :param chat_id: ID чата.
        :param kwargs: Дополнительные параметры для API (например, limit, offset).
        :return: Словарь со списком участников.
        """
        return await self._make_request('GET', f'chats/{chat_id}/members', params=kwargs)
    
    async def send_action(self, chat_id: int, action: str) -> Dict[str, Any]:
        """
        Отправляет действие в чат (например, "печтатает...").

        :param chat_id: ID чата.
        :param action: Тип действия (например, 'typing').
        :return: Словарь с ответом от API.
        """
        payload = {'action': action}
        return await self._make_request('POST', f'chats/{chat_id}/actions', json=payload)
    
    async def pin_message(self, chat_id: int, message_id: str, **kwargs) -> Dict[str, Any]:
        """
        Закрепляет сообщение в чате.

        :param chat_id: ID чата.
        :param message_id: ID сообщения для закрепления.
        :param kwargs: Дополнительные параметры (например, notify=False).
        :return: Словарь с ответом от API.
        """
        return await self._make_request('PUT', f'chats/{chat_id}/messages/{message_id}/pin', json=kwargs)
    
    async def unpin_message(self, chat_id: int, message_id: str) -> Dict[str, Any]:
        """
        Открепляет сообщение в чате.

        :param chat_id: ID чата.
        :param message_id: ID сообщения для открепления.
        :return: Словарь с ответом от API.
        """
        return await self._make_request('DELETE', f'chats/{chat_id}/messages/{message_id}/pin')
    
    async def leave_chat(self, chat_id: int) -> Dict[str, Any]:
        """
        Покидает чат.

        :param chat_id: ID чата.
        :return: Словарь с ответом от API.
        """
        return await self._make_request('DELETE', f'chats/{chat_id}/members/me')
    
    async def add_chat_members(self, chat_id: int, user_ids: List[int]) -> Dict[str, Any]:
        """
        Добавляет участников в чат.

        :param chat_id: ID чата.
        :param user_ids: Список ID пользователей для добавления.
        :return: Словарь с ответом от API.
        """
        payload = {'user_ids': user_ids}
        return await self._make_request('POST', f'chats/{chat_id}/members', json=payload)
    
    # === МЕТОДЫ ЗАГРУЗКИ ФАЙЛОВ ===
    
    async def _upload_file(self, file: Union[str, BinaryIO, bytes], file_type: str, **kwargs) -> Dict[str, Any]:
        """Внутренний метод для загрузки файлов на сервер."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        # Определяем тип файла
        if isinstance(file, str):
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found: {file}")
            filename = os.path.basename(file)
            mime_type, _ = mimetypes.guess_type(file)
            with open(file, 'rb') as f:
                file_data = f.read()
        elif isinstance(file, bytes):
            file_data = file
            filename = kwargs.get('filename', 'file')
            mime_type = kwargs.get('mime_type')
        else:
            file_data = file.read()
            filename = kwargs.get('filename', 'file')
            mime_type = kwargs.get('mime_type')
        
        data = aiohttp.FormData()
        data.add_field('file', file_data, filename=filename, content_type=mime_type)
        # type только в params!
        params = {'access_token': self.token, 'type': file_type}
        
        # Добавляем дополнительные параметры (кроме type, filename, mime_type)
        for key, value in kwargs.items():
            if key not in ['filename', 'mime_type']:
                params[key] = str(value)
        
        url = f"{self.BASE_URL}/uploads"
        try:
            async with self.session.post(url, params=params, data=data) as response:
                response.raise_for_status()
                result = await response.json()
                logger.debug(f"Upload response: {result}")
                return result
        except aiohttp.ClientError as e:
            logger.error(f"File upload failed: {e}")
            raise
    
    async def upload_image(self, file: Union[str, BinaryIO, bytes], **kwargs) -> Dict[str, Any]:
        """
        Загружает изображение.

        :param file: Путь к файлу, байты или файловый объект.
        :param kwargs: Дополнительные параметры.
        :return: Словарь с URL и ID загруженного файла.
        """
        return await self._upload_file(file, 'image', **kwargs)
    
    async def upload_video(self, file: Union[str, BinaryIO, bytes], **kwargs) -> Dict[str, Any]:
        """
        Загружает видео.

        :param file: Путь к файлу, байты или файловый объект.
        :param kwargs: Дополнительные параметры.
        :return: Словарь с URL и ID загруженного файла.
        """
        return await self._upload_file(file, 'video', **kwargs)
    
    async def upload_audio(self, file: Union[str, BinaryIO, bytes], **kwargs) -> Dict[str, Any]:
        """
        Загружает аудио.

        :param file: Путь к файлу, байты или файловый объект.
        :param kwargs: Дополнительные параметры.
        :return: Словарь с URL и ID загруженного файла.
        """
        return await self._upload_file(file, 'audio', **kwargs)
    
    async def upload_file(self, file: Union[str, BinaryIO, bytes], **kwargs) -> Dict[str, Any]:
        """
        Загружает файл (документ).

        :param file: Путь к файлу, байты или файловый объект.
        :param kwargs: Дополнительные параметры.
        :return: Словарь с URL и ID загруженного файла.
        """
        return await self._upload_file(file, 'file', **kwargs)
    
    async def upload_sticker(self, file: Union[str, BinaryIO, bytes], **kwargs) -> Dict[str, Any]:
        """
        Загружает стикер.

        :param file: Путь к файлу, байты или файловый объект.
        :param kwargs: Дополнительные параметры.
        :return: Словарь с URL и ID загруженного файла.
        """
        return await self._upload_file(file, 'sticker', **kwargs)
    
    async def download_file(self, file_id: str, save_path: Optional[str] = None) -> Union[bytes, str]:
        """
        Скачивает файл по ID.

        :param file_id: ID файла для скачивания.
        :param save_path: Путь для сохранения файла (опционально).
        :return: Байты файла или путь к сохраненному файлу.
        """
        await self._ensure_session()
        
        params = {'access_token': self.token, 'file_id': file_id}
        url = f"{self.BASE_URL}/files/{file_id}"
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                file_data = await response.read()
                
                if save_path:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(file_data)
                    return save_path
                else:
                    return file_data
                    
        except aiohttp.ClientError as e:
            logger.error(f"File download failed: {e}")
            raise
    
    async def get_file(self, file_id: str) -> Dict[str, Any]:
        """
        Получает информацию о файле.

        :param file_id: ID файла.
        :return: Словарь с информацией о файле.
        """
        return await self._make_request('GET', f'files/{file_id}')
    
    async def validate_file_size(self, file: Union[str, BinaryIO, bytes], max_size_mb: int = 50) -> bool:
        """
        Проверяет размер файла.

        :param file: Файл для проверки.
        :param max_size_mb: Максимальный размер в МБ.
        :return: True если файл подходит по размеру.
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if isinstance(file, str):
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found: {file}")
            file_size = os.path.getsize(file)
        elif isinstance(file, bytes):
            file_size = len(file)
        else:
            # Для файловых объектов - читаем в память для проверки
            current_pos = file.tell()
            file.seek(0, 2)  # Перемещаемся в конец
            file_size = file.tell()
            file.seek(current_pos)  # Возвращаемся на исходную позицию
        
        return file_size <= max_size_bytes
    
    async def get_supported_formats(self, file_type: str) -> List[str]:
        """
        Получает список поддерживаемых форматов для типа файла.

        :param file_type: Тип файла (image, video, audio, file).
        :return: Список поддерживаемых расширений.
        """
        formats = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'],
            'file': ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z']
        }
        return formats.get(file_type, [])
    
    async def validate_file_format(self, file: Union[str, BinaryIO, bytes], file_type: str) -> bool:
        """
        Проверяет формат файла.

        :param file: Файл для проверки.
        :param file_type: Ожидаемый тип файла.
        :param kwargs: Дополнительные параметры.
        :return: True если формат поддерживается.
        """
        supported_formats = await self.get_supported_formats(file_type)
        if isinstance(file, str):
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found: {file}")
            filename = os.path.basename(file)
            file_ext = os.path.splitext(filename)[1].lower()
            return file_ext in supported_formats
        elif isinstance(file, bytes):
            return not supported_formats
        else:
            filename = getattr(file, 'name', 'file')
            file_ext = os.path.splitext(filename)[1].lower()
            return file_ext in supported_formats
    
    async def send_attachment(self, attachment_data: dict, 
                             user_id: Optional[int] = None, chat_id: Optional[int] = None,
                             caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Универсальный метод для отправки любого типа вложения.
        
        :param attachment_data: Словарь с данными вложения (как в incoming message)
        :param user_id: ID пользователя
        :param chat_id: ID чата
        :param caption: Подпись к сообщению
        :param kwargs: Дополнительные параметры
        :return: Ответ от API
        """
        from .max_types import BaseAttachment
        
        # Валидируем структуру вложения
        if not BaseAttachment.validate_attachment(attachment_data):
            raise ValueError(f"Invalid attachment structure: {attachment_data}")
        
        # Получаем payload для отправки
        payload = BaseAttachment.get_payload_for_sending(attachment_data)
        attachment_type = attachment_data['type']
        
        # Формируем данные для отправки
        data = {
            'attachments': [{
                'type': attachment_type,
                'payload': payload
            }]
        }
        
        # Добавляем дополнительные поля вложения (filename, size и т.д.)
        for key in ['filename', 'size', 'width', 'height', 'duration', 'performer', 'title', 'emoji']:
            if key in attachment_data:
                data['attachments'][0][key] = attachment_data[key]
        
        # Добавляем подпись
        if caption:
            data['text'] = caption
        
        # Добавляем дополнительные параметры
        data.update(kwargs)
        
        # Параметры запроса
        params = {'chat_id': chat_id} if chat_id is not None else {'user_id': user_id}
        if not params.get('chat_id') and not params.get('user_id'):
            raise ValueError("Either user_id or chat_id must be provided")
        
        return await self._make_request('POST', 'messages', params=params, json=data)

    async def send_photo(self, photo: Union[str, BinaryIO, bytes, Dict],
                        user_id: Optional[int] = None, chat_id: Optional[int] = None,
                        caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Отправляет фото. Можно передать как новый файл, так и ID уже загруженного."""
        if isinstance(photo, dict):
            # Если передали готовую структуру вложения - используем универсальный метод
            if 'type' in photo and photo['type'] == 'image':
                return await self.send_attachment(photo, user_id=user_id, chat_id=chat_id, caption=caption, **kwargs)
            # Иначе считаем что это payload
            attachment_payload = photo
        else:
            upload_result = await self.upload_image(photo, **kwargs)
            # Формируем payload как в реальном API: photo_id + token
            payload = {}
            if 'photo_id' in upload_result:
                payload['photo_id'] = upload_result['photo_id']
            elif 'url' in upload_result and 'photoIds=' in upload_result['url']:
                # Извлекаем photo_id из URL и декодируем
                photo_id_encoded = upload_result['url'].split('photoIds=')[1]
                try:
                    photo_id_decoded = base64.b64decode(photo_id_encoded + '==').decode('utf-8')
                    payload['photo_id'] = int(photo_id_decoded)
                except:
                    payload['photo_id'] = photo_id_encoded
            if 'token' in upload_result:
                payload['token'] = upload_result['token']
            if 'url' in upload_result:
                payload['url'] = upload_result['url']
            attachment_payload = payload
        
        params = {'chat_id': chat_id} if chat_id is not None else {'user_id': user_id}
        if not params.get('chat_id') and not params.get('user_id'):
            raise ValueError("Either user_id or chat_id must be provided")

        message_kwargs = {k: v for k, v in kwargs.items() if k not in ['filename', 'mime_type']}
        data = {'attachments': [{'type': 'image', 'payload': attachment_payload}], **message_kwargs}
        if caption:
            data['text'] = caption
        
        return await self._make_request('POST', 'messages', params=params, json=data)

    async def send_video(self, video: Union[str, BinaryIO, bytes, Dict],
                        user_id: Optional[int] = None, chat_id: Optional[int] = None,
                        caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Отправляет видео."""
        if isinstance(video, dict):
            attachment_payload = video
        else:
            attachment_payload = await self.upload_video(video, **kwargs)

        params = {'chat_id': chat_id} if chat_id is not None else {'user_id': user_id}
        if not params.get('chat_id') and not params.get('user_id'):
            raise ValueError("Either user_id or chat_id must be provided")

        message_kwargs = {k: v for k, v in kwargs.items() if k not in ['filename', 'mime_type']}
        data = {'attachments': [{'type': 'video', 'payload': attachment_payload}], **message_kwargs}
        if caption:
            data['text'] = caption
            
        return await self._make_request('POST', 'messages', params=params, json=data)

    async def send_audio(self, audio: Union[str, BinaryIO, bytes, Dict],
                        user_id: Optional[int] = None, chat_id: Optional[int] = None,
                        caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Отправляет аудио."""
        if isinstance(audio, dict):
            attachment_payload = audio
        else:
            attachment_payload = await self.upload_audio(audio, **kwargs)
            
        params = {'chat_id': chat_id} if chat_id is not None else {'user_id': user_id}
        if not params.get('chat_id') and not params.get('user_id'):
            raise ValueError("Either user_id or chat_id must be provided")

        message_kwargs = {k: v for k, v in kwargs.items() if k not in ['filename', 'mime_type']}
        data = {'attachments': [{'type': 'audio', 'payload': attachment_payload}], **message_kwargs}
        if caption:
            data['text'] = caption
            
        return await self._make_request('POST', 'messages', params=params, json=data)

    async def send_document(self, document: Union[str, BinaryIO, bytes, Dict],
                           user_id: Optional[int] = None, chat_id: Optional[int] = None,
                           caption: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Отправляет документ."""
        if isinstance(document, dict):
            attachment_payload = document
        else:
            attachment_payload = await self.upload_file(document, **kwargs)
            
        params = {'chat_id': chat_id} if chat_id is not None else {'user_id': user_id}
        if not params.get('chat_id') and not params.get('user_id'):
            raise ValueError("Either user_id or chat_id must be provided")

        message_kwargs = {k: v for k, v in kwargs.items() if k not in ['filename', 'mime_type']}
        data = {'attachments': [{'type': 'file', 'payload': attachment_payload}], **message_kwargs}
        if caption:
            data['text'] = caption
            
        return await self._make_request('POST', 'messages', params=params, json=data)
    
    async def polling(self, timeout: int = 1, long_polling_timeout: int = 20, dispatcher: 'Dispatcher' = None):
        """
        Запускает long polling для получения обновлений.

        Этот метод является точкой входа для запуска бота. Он будет бесконечно
        опрашивать API на наличие новых обновлений и передавать их в диспетчер.

        :param timeout: (не используется)
        :param long_polling_timeout: Таймаут для запроса обновлений.
        :param dispatcher: Экземпляр Dispatcher для обработки обновлений.
        """
        if not dispatcher:
            raise ValueError("Dispatcher is required for polling")

        logger.info(f"Polling started with long_polling_timeout={long_polling_timeout}")
        
        marker = None
        
        while True:
            try:
                logger.debug(f"Polling iteration, marker={marker}")
                response_data = await self.get_updates(offset=marker, timeout=long_polling_timeout)
                
                if not response_data:
                    logger.warning("get_updates returned empty response, sleeping for 1s")
                    await asyncio.sleep(1)
                    continue

                if isinstance(response_data, dict):
                    updates = response_data.get('updates', [])
                    marker = response_data.get('marker', marker)
                else:
                    updates = response_data
                    marker = None

                logger.debug(f"Got {len(updates)} updates, next marker: {marker}")
                
                for update_data in updates:
                    if isinstance(update_data, dict):
                        await dispatcher.process_update(update_data)
                    
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received, stopping polling")
                break
            except Exception as e:
                logger.error(f"Exception in polling loop: {e}", exc_info=True)
                await asyncio.sleep(5)
                continue

    async def start_webhook(self, host="0.0.0.0", port=8080, path="/webhook", handler=None, middleware_manager=None):
        """Запускает aiohttp веб-сервер для приёма обновлений через webhook"""
        from aiohttp import web
        print(f"[MaxBot] Webhook server started at http://{host}:{port}{path}")
        self.session = self.session or aiohttp.ClientSession()
        
        async def webhook_handler(request):
            try:
                data = await request.json()
                update = Update(**data)
                if middleware_manager:
                    await middleware_manager.process(update, handler)
                elif handler:
                    await handler(update)
                return web.Response(text="ok")
            except Exception as e:
                print(f"[MaxBot] Webhook error: {e}")
                return web.Response(status=500, text=str(e))
        
        app = web.Application()
        app.router.add_post(path, webhook_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        while True:
            await asyncio.sleep(3600) 