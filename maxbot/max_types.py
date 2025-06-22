"""
Типы данных для MaxBot
Совместимы с Max API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Union, Any, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass

if TYPE_CHECKING:
    from .bot import Bot

# ===============================================================
#  Модели данных API (Pydantic)
# ===============================================================

class AttachmentPayload(BaseModel):
    """Внутренняя полезная нагрузка вложения."""
    url: Optional[str] = None
    photo_id: Optional[Union[str, int]] = None
    id: Optional[Union[str, int]] = None
    fileId: Optional[Union[str, int]] = None
    sticker_id: Optional[str] = None
    title: Optional[str] = None
    emoji: Optional[str] = None
    token: Optional[str] = None
    model_config = {"extra": "allow"}

class AttachmentThumbnail(BaseModel):
    """Превью для вложения (например, у видео)."""
    url: Optional[str] = None

class BaseAttachment(BaseModel):
    """Базовая модель для любого типа вложения."""
    type: str
    payload: Optional[AttachmentPayload] = None
    url: Optional[str] = None
    file_id: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    performer: Optional[str] = None
    title: Optional[str] = None
    thumbnail: Optional[AttachmentThumbnail] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    emoji: Optional[str] = None

    def __getattr__(self, name):
        if self.payload and hasattr(self.payload, name):
            return getattr(self.payload, name)
        return self.model_extra.get(name)
    
    @classmethod
    def validate_attachment(cls, attachment_data: dict) -> bool:
        """
        Валидирует структуру вложения на основе реальных данных MaxBot API.
        
        :param attachment_data: Словарь с данными вложения
        :return: True если структура валидна
        """
        if not isinstance(attachment_data, dict):
            return False
        
        if 'type' not in attachment_data:
            return False
        
        attachment_type = attachment_data['type']
        
        # Вложения с payload (image, file, audio, video, sticker)
        if attachment_type in ['image', 'file', 'audio', 'video', 'sticker']:
            if 'payload' not in attachment_data:
                return False
            payload = attachment_data['payload']
            if not isinstance(payload, dict):
                return False
            
            # Валидация по типу
            if attachment_type == 'image':
                return 'photo_id' in payload and 'token' in payload
            elif attachment_type == 'file':
                return 'fileId' in payload and 'token' in payload
            elif attachment_type in ['audio', 'video']:
                return 'token' in payload
            elif attachment_type == 'sticker':
                return 'token' in payload
        
        # Вложения без payload (location, share)
        elif attachment_type == 'location':
            return 'latitude' in attachment_data and 'longitude' in attachment_data
        elif attachment_type == 'share':
            return 'url' in attachment_data
        
        return False
    
    @classmethod
    def get_payload_for_sending(cls, attachment_data: dict) -> dict:
        """
        Извлекает payload для отправки вложения.
        
        :param attachment_data: Словарь с данными вложения
        :return: Словарь payload для отправки
        """
        if not cls.validate_attachment(attachment_data):
            raise ValueError(f"Invalid attachment structure: {attachment_data}")
        
        attachment_type = attachment_data['type']
        
        # Для вложений с payload
        if attachment_type in ['image', 'file', 'audio', 'video', 'sticker']:
            return attachment_data['payload']
        
        # Для вложений без payload (location, share)
        elif attachment_type == 'location':
            return {
                'latitude': attachment_data['latitude'],
                'longitude': attachment_data['longitude']
            }
        elif attachment_type == 'share':
            return {
                'url': attachment_data['url'],
                'title': attachment_data.get('title')
            }
        
        raise ValueError(f"Unsupported attachment type: {attachment_type}")

class User(BaseModel):
    """Представление пользователя Max API."""
    user_id: int
    name: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_bot: bool = False
    last_activity_time: Optional[int] = 0

class Chat(BaseModel):
    """Представление чата Max API."""
    chat_id: int
    chat_type: str
    user_id: Optional[int] = None

class MessageBody(BaseModel):
    """Тело сообщения, содержащее текст и вложения."""
    mid: str
    seq: int
    text: Optional[str] = None
    attachments: Optional[List[BaseAttachment]] = None

class Message(BaseModel):
    """Представление сообщения Max API."""
    recipient: Chat
    sender: User
    timestamp: int
    body: MessageBody
    
    async def edit_text(self, text: str, reply_markup: Optional[Any] = None, **kwargs):
        """
        Редактирует текст сообщения.
        
        :param text: Новый текст сообщения.
        :param reply_markup: Клавиатура (InlineKeyboardMarkup/ReplyKeyboardMarkup).
        :param kwargs: Дополнительные параметры.
        """
        # Нужен доступ к bot для редактирования
        # Это будет обработано в Context
        raise NotImplementedError("Use context.edit_message() instead")

class CallbackQuery(BaseModel):
    """Представление callback-запроса."""
    callback_id: str
    user: User
    payload: Optional[str] = None
    message: Optional[Message] = None
    model_config = {"extra": "allow"}

class BotStarted(BaseModel):
    """Событие: бот запущен (начал диалог с пользователем)."""
    chat_id: int
    user: User

class UserAdded(BaseModel):
    """Событие: пользователь добавлен в чат."""
    chat_id: int
    user: User
    inviter: User
    
class ChatMemberUpdated(BaseModel):
    """Событие: обновлен статус участника чата."""
    chat_id: int
    user: User
    old_status: str
    new_status: str

class Update(BaseModel):
    """
    Представление входящего обновления от API.
    Это корневой объект, который получает Dispatcher.
    """
    message: Optional[Message] = None
    callback: Optional[CallbackQuery] = None
    bot_started: Optional[BotStarted] = Field(None, alias="bot_started")
    user_added: Optional[UserAdded] = Field(None, alias="user_added")
    chat_member_updated: Optional[ChatMemberUpdated] = Field(None, alias="chat_member_updated")
    update_type: str
    timestamp: int
    marker: Optional[int] = None
    user_locale: Optional[str] = None
    model_config = {"extra": "allow"}

# ===============================================================
#  Старые и вспомогательные классы (могут быть неактуальны)
# ===============================================================

class UpdateType(Enum):
    """Типы обновлений в Max API"""
    MESSAGE = "message"
    CALLBACK_QUERY = "callback_query"
    CHAT_MEMBER = "chat_member"
    MESSAGE_CREATED = "message_created"

# ===============================================================
#  Класс Context
# ===============================================================

class Context:
    """
    Класс Контекста. Главный инструмент для работы внутри обработчиков.
    Предоставляет удобный доступ ко всем данным обновления и методы для ответа.
    """
    
    def __init__(self, update: Update, bot: 'Bot'):
        self._update = update
        self._bot = bot
        
        # Определяем ключевые сущности сразу в конструкторе
        self.callback_query: Optional[CallbackQuery] = None
        self.message_in_update: Optional[Message] = None

        if update.update_type == 'message_callback' and update.callback:
            self.callback_query = update.callback
            # Сообщение, к которому привязан колбэк, лежит на том же уровне
            self.message_in_update = update.message
        elif update.message:
            self.message_in_update = update.message

    @property
    def bot_started(self) -> Optional[BotStarted]:
        """Возвращает объект BotStarted, если он есть в обновлении."""
        return self._update.bot_started

    @property
    def user_added(self) -> Optional[UserAdded]:
        """Возвращает объект UserAdded, если он есть в обновлении."""
        return self._update.user_added

    @property
    def chat_member_updated(self) -> Optional[ChatMemberUpdated]:
        """Возвращает объект ChatMemberUpdated, если он есть в обновлении."""
        return self._update.chat_member_updated

    @property
    def is_callback(self) -> bool:
        """Проверяет, является ли обновление callback-запросом."""
        return self.callback_query is not None
    
    @property
    def message(self) -> Optional[Message]:
        """
        Объект `Message` из обновления. Для callback - это сообщение с кнопками.
        """
        return self.message_in_update

    @property
    def user(self) -> Optional[User]:
        """
        Объект `User`, инициировавший обновление.
        Для callback - это пользователь, нажавший кнопку.
        """
        if self.callback_query:
            return self.callback_query.user
        if self.message_in_update:
            return self.message_in_update.sender
        return None

    @property
    def chat(self) -> Optional[Chat]:
        """Объект `Chat`, в котором произошло обновление."""
        if self.message_in_update:
            return self.message_in_update.recipient
        return None

    @property
    def date(self) -> int:
        """Timestamp обновления."""
        return self._update.timestamp

    @property
    def text(self) -> Optional[str]:
        """Текст сообщения (даже в callback)."""
        if self.message_in_update and self.message_in_update.body:
            return self.message_in_update.body.text
        return None
    
    @property
    def chat_id(self) -> Optional[int]:
        """ID чата, в котором произошло обновление."""
        c = self.chat
        return c.chat_id if c else None
    
    @property
    def user_id(self) -> Optional[int]:
        """ID пользователя, инициировавшего обновление."""
        u = self.user
        return u.user_id if u else None
    
    @property
    def payload(self) -> Optional[str]:
        """Payload из callback-запроса."""
        return self.callback_query.payload if self.callback_query else None
    
    @property
    def callback_id(self) -> Optional[str]:
        """ID callback-запроса."""
        return self.callback_query.callback_id if self.callback_query else None

    @property
    def message_id(self) -> Optional[str]:
        """ID сообщения, с которым связано обновление."""
        if self.message_in_update and self.message_in_update.body:
            return self.message_in_update.body.mid
        return None
    
    async def reply(self, text: str, reply_markup: Optional[Any] = None, **kwargs):
        """
        Удобный метод для ответа в тот же чат, откуда пришло сообщение.

        :param text: Текст ответного сообщения.
        :param reply_markup: Клавиатура (InlineKeyboardMarkup/ReplyKeyboardMarkup).
        :param kwargs: Дополнительные параметры для `bot.send_message`.
        """
        if not self.chat_id:
            raise ValueError("No chat_id to reply to")
        return await self._bot.send_message(text, chat_id=self.chat_id, reply_markup=reply_markup, **kwargs)
    
    async def answer(self, text: str, reply_markup: Optional[Any] = None, **kwargs):
        """Алиас для `reply`."""
        return await self.reply(text, reply_markup=reply_markup, **kwargs)

    async def edit_message(self, text: str, reply_markup: Optional[Any] = None, **kwargs):
        """
        Редактирует текущее сообщение (то, которое вызвало этот хендлер).

        :param text: Новый текст сообщения.
        :param reply_markup: Клавиатура (InlineKeyboardMarkup/ReplyKeyboardMarkup).
        :param kwargs: Дополнительные параметры для `bot.edit_message`.
        """
        # Определяем ID сообщения для редактирования
        message_id_to_edit = self.message_id
            
        if not message_id_to_edit:
            raise ValueError("Cannot edit message: message ID not found in context.")
        
        # Если мы находимся в callback-контексте, используем answer_callback для редактирования
        if self.is_callback:
            return await self.answer_callback(message={'text': text, 'reply_markup': reply_markup})

        # Для обычных сообщений используем стандартный edit_message
        return await self._bot.edit_message(message_id=message_id_to_edit, text=text, reply_markup=reply_markup, **kwargs)

    async def delete_message(self, **kwargs):
        """
        Удаляет текущее сообщение (то, которое вызвало этот хендлер).
        
        :param kwargs: Дополнительные параметры для `bot.delete_message`.
        """
        if not self.message or not self.message.body or not self.message.body.mid:
            raise ValueError("Cannot delete message: message ID not found in context.")
        # `delete_message` в bot.py не принимает kwargs
        return await self._bot.delete_message(message_id=self.message.body.mid)

    async def get_members(self, **kwargs):
        """
        Получает список участников текущего чата.

        :param kwargs: Дополнительные параметры для `bot.get_chat_members`.
        """
        if not self.chat_id:
            raise ValueError("No chat_id to get members from")
        return await self._bot.get_chat_members(self.chat_id, **kwargs)

    async def send_action(self, action: str):
        """
        Отправляет действие в текущий чат.

        :param action: Тип действия (например, 'typing').
        """
        if not self.chat_id:
            raise ValueError("No chat_id to send action to")
        return await self._bot.send_action(self.chat_id, action)

    async def pin_message(self, message_id: Optional[str] = None, **kwargs):
        """
        Закрепляет сообщение в текущем чате.
        Если message_id не указан, закрепляет текущее сообщение.

        :param message_id: ID сообщения для закрепления.
        :param kwargs: Дополнительные параметры для `bot.pin_message`.
        """
        if not self.chat_id:
            raise ValueError("No chat_id to pin message in")
        
        msg_id_to_pin = message_id or (self.message.body.mid if self.message and self.message.body else None)
        if not msg_id_to_pin:
            raise ValueError("No message_id to pin")
            
        return await self._bot.pin_message(self.chat_id, msg_id_to_pin, **kwargs)

    async def unpin_message(self, message_id: str):
        """
        Открепляет сообщение в текущем чате.

        :param message_id: ID сообщения для открепления.
        """
        if not self.chat_id:
            raise ValueError("No chat_id to unpin message in")
        return await self._bot.unpin_message(self.chat_id, message_id)

    async def leave_chat(self):
        """
        Бот покидает текущий чат.
        """
        if not self.chat_id:
            raise ValueError("No chat_id to leave")
        return await self._bot.leave_chat(self.chat_id)

    async def add_members(self, user_ids: List[int]):
        """
        Добавляет участников в текущий чат.

        :param user_ids: Список ID пользователей.
        """
        if not self.chat_id:
            raise ValueError("No chat_id to add members to")
        return await self._bot.add_chat_members(self.chat_id, user_ids)

    @property
    def has_attachments(self) -> bool:
        """True, если в сообщении есть хотя бы одно вложение."""
        return bool(self.attachments)

    @property
    def attachments(self) -> Optional[List[BaseAttachment]]:
        """Список вложений в сообщении."""
        return self.message.body.attachments if self.message and self.message.body else None

    @property
    def images(self) -> List[BaseAttachment]:
        """Возвращает список вложений-изображений."""
        if not self.has_attachments:
            return []
        return [att for att in self.attachments if att.type == "image"]

    async def answer_callback(self, 
                            text: Optional[str] = None, 
                            message: Optional[dict] = None,
                            show_alert: bool = False, 
                            **kwargs):
        """
        Отвечает на callback-запрос.
        Можно отправить либо уведомление (notification), либо отредактировать сообщение (message).

        :param text: Текст уведомления.
        :param message: Словарь для редактирования сообщения (например, {'text': 'new text'}).
        :param show_alert: Показывать ли alert (только для notification).
        :param kwargs: Дополнительные параметры.
        """
        if not self.callback_id:
            raise ValueError("No callback_id in context to answer")

        payload = {}
        if text:
            # `notification` должен быть строкой
            payload['notification'] = text
            if show_alert:
                payload['show_alert'] = True
        elif message:
            # Конвертируем reply_markup в словарь, если это объект
            if 'reply_markup' in message and message.get('reply_markup') and hasattr(message['reply_markup'], 'model_dump'):
                 message['reply_markup'] = message['reply_markup'].model_dump(exclude_none=True)
            payload['message'] = message
        
        if not payload:
            # По умолчанию отправляем пустой ответ, чтобы убрать "часики" с кнопки
            return await self._bot.answer_callback_query(callback_id=self.callback_id)

        return await self._bot.answer_callback_query(
            callback_id=self.callback_id,
            **payload,
            **kwargs
        )

# ===============================================================
#  Клавиатуры и кнопки
# ===============================================================

class InlineKeyboardButton(BaseModel):
    """Представляет одну кнопку в inline-клавиатуре."""
    type: str = 'callback'  # Добавляем тип кнопки по умолчанию
    text: str
    payload: Optional[str] = None
    url: Optional[str] = None
    # Можно добавить другие параметры по необходимости

class InlineKeyboardMarkup(BaseModel):
    """Представляет inline-клавиатуру."""
    inline_keyboard: List[List[InlineKeyboardButton]]

class KeyboardButton(BaseModel):
    text: str
    request_contact: Optional[bool] = False
    request_location: Optional[bool] = False

class ReplyKeyboardMarkup(BaseModel):
    keyboard: List[List[KeyboardButton]]
    resize_keyboard: Optional[bool] = True
    one_time_keyboard: Optional[bool] = False
    selective: Optional[bool] = False 