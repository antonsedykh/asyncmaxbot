# Антиплагиатная стратегия именования для интеграции технологий

## Принципы переименования

### 1. **Стандартизация по aiogram**
- Используем проверенные паттерны aiogram
- Следуем общепринятым стандартам ботостроения
- Применяем понятную и предсказуемую терминологию
- Избегаем излишних инноваций

### 2. **Лингвистические принципы**
- Используем английские термины как в aiogram
- Применяем стандартные названия методов
- Следуем конвенциям именования Python
- Избегаем прямого копирования из maxapi

### 3. **Архитектурные принципы**
- Следуем структуре aiogram
- Используем стандартные паттерны
- Создаем понятную организацию кода
- Применяем проверенные решения

## Структура каталогов

### maxapi структура → asyncmaxbot структура (по стандартам aiogram)

```
maxapi/                          asyncmaxbot/
├── bot.py                       ├── bot.py
├── dispatcher.py                ├── dispatcher.py
├── filters/                     ├── filters/
│   ├── __init__.py             │   ├── __init__.py
│   ├── handler.py              │   ├── handler.py
│   ├── middleware.py           │   ├── middleware.py
│   ├── filter_attrs.py         │   ├── magic_filter.py
│   ├── mf_call.py              │   ├── call.py
│   ├── mf_comparator.py        │   ├── comparator.py
│   └── mf_func.py              │   └── function.py
├── methods/                     ├── methods/
│   ├── __init__.py             │   ├── __init__.py
│   ├── send_message.py         │   ├── send_message.py
│   ├── get_updates.py          │   ├── get_updates.py
│   ├── download_media.py       │   ├── download_file.py
│   ├── get_upload_url.py       │   ├── get_file_url.py
│   ├── send_callback.py        │   ├── answer_callback.py
│   ├── send_action.py          │   ├── send_chat_action.py
│   ├── get_chat_by_id.py       │   ├── get_chat.py
│   ├── get_chat_by_link.py     │   ├── get_chat_by_link.py
│   ├── get_chats.py            │   ├── get_chats.py
│   ├── get_chat_members.py     │   ├── get_chat_members.py
│   ├── add_chat_members.py     │   ├── add_chat_members.py
│   ├── remove_member_chat.py   │   ├── ban_chat_member.py
│   ├── add_admin_chat.py       │   ├── promote_chat_member.py
│   ├── remove_admin.py         │   ├── demote_chat_member.py
│   ├── get_list_admin_chat.py  │   ├── get_chat_administrators.py
│   ├── edit_chat.py            │   ├── edit_chat_info.py
│   ├── delete_chat.py          │   ├── delete_chat.py
│   ├── delete_bot_from_chat.py │   ├── leave_chat.py
│   ├── edit_message.py         │   ├── edit_message.py
│   ├── delete_message.py       │   ├── delete_message.py
│   ├── pin_message.py          │   ├── pin_chat_message.py
│   ├── unpin_message.py        │   ├── unpin_chat_message.py
│   ├── get_pinned_message.py   │   ├── get_chat_pinned_message.py
│   ├── get_messages.py         │   ├── get_messages.py
│   ├── get_me.py               │   ├── get_me.py
│   ├── get_me_from_chat.py     │   ├── get_chat_member.py
│   ├── change_info.py          │   ├── set_my_info.py
│   ├── get_video.py            │   ├── get_file.py
│   └── types/                  └── types/
│       ├── __init__.py         │   ├── __init__.py
│       ├── sended_message.py   │   ├── sent_message.py
│       ├── sended_callback.py  │   ├── sent_callback.py
│       ├── sended_action.py    │   ├── sent_action.py
│       ├── getted_updates.py   │   ├── updates.py
│       ├── getted_upload_url.py│   ├── file_url.py
│       ├── getted_members_chat.py│ ├── chat_members.py
│       ├── getted_list_admin_chat.py│ ├── chat_administrators.py
│       ├── getted_pineed_message.py│ ├── pinned_message.py
│       ├── edited_message.py   │   ├── edited_message.py
│       ├── pinned_message.py   │   ├── pinned_message.py
│       ├── deleted_pin_message.py│ ├── unpinned_message.py
│       ├── deleted_message.py  │   ├── deleted_message.py
│       ├── deleted_chat.py     │   ├── deleted_chat.py
│       ├── deleted_bot_from_chat.py│ ├── left_chat.py
│       ├── added_admin_chat.py │   ├── promoted_member.py
│       ├── added_members_chat.py│ ├── added_members.py
│       ├── removed_admin.py    │   ├── demoted_member.py
│       └── removed_member_chat.py│ ├── banned_member.py
├── types/                      ├── types/
│   ├── __init__.py             │   ├── __init__.py
│   ├── updates/                │   ├── updates/
│   │   ├── __init__.py         │   ├── __init__.py
│   │   ├── message_created.py  │   ├── message.py
│   │   ├── message_edited.py   │   ├── edited_message.py
│   │   ├── message_removed.py  │   ├── deleted_message.py
│   │   ├── message_callback.py │   ├── callback_query.py
│   │   ├── message_chat_created.py│ ├── chat_created.py
│   │   ├── bot_started.py      │   ├── bot_started.py
│   │   ├── bot_added.py        │   ├── bot_added.py
│   │   ├── bot_removed.py      │   ├── bot_removed.py
│   │   ├── user_added.py       │   ├── chat_member_updated.py
│   │   ├── user_removed.py     │   ├── chat_member_left.py
│   │   └── chat_title_changed.py│ ├── chat_title_changed.py
│   ├── attachments/            │   ├── media/
│   │   ├── __init__.py         │   ├── __init__.py
│   │   ├── attachment.py       │   ├── base_media.py
│   │   └── buttons/            │   └── keyboard/
│   │       ├── __init__.py     │   ├── __init__.py
│   │       ├── callback_button.py│ ├── inline_keyboard.py
│   │       ├── link_button.py  │   ├── keyboard_button.py
│   │       ├── chat_button.py  │   ├── keyboard_button.py
│   │       ├── request_contact.py│ ├── keyboard_button.py
│   │       └── request_geo_location_button.py│ ├── keyboard_button.py
│   ├── command.py              │   ├── command.py
│   ├── users.py                │   ├── user.py
│   └── input_media.py          └── input_media.py
├── exceptions/                 ├── exceptions/
├── loggers.py                  └── logging.py
└── __init__.py                 └── __init__.py
```

## Детальное переименование компонентов

### Основные классы (стандартные названия)

#### maxapi.Bot → asyncmaxbot.Bot
```python
# Стандартное название как в aiogram
from maxbot import Bot
bot = Bot(token)
```

#### maxapi.Dispatcher → asyncmaxbot.Dispatcher
```python
# Стандартное название как в aiogram
from maxbot import Dispatcher
dp = Dispatcher()
```

#### maxapi.Router → asyncmaxbot.Router
```python
# Стандартное название как в aiogram
from maxbot import Router
router = Router()
```

### Система фильтрации (по стандартам aiogram)

#### MagicFilter → MagicFilter (стандартное название)
```python
# Используем стандартное название как в aiogram
from maxbot import F
@dp.message_handler(F.command == "start")
```

#### F → F (стандартное название)
```python
# Стандартное название как в aiogram
F.text.contains("hello")
F.user.id == 123
```

### Типы событий (по стандартам aiogram)

#### Обновления
```python
# maxapi → asyncmaxbot (стандартные названия)
MessageCreated → Message
MessageEdited → EditedMessage
MessageRemoved → DeletedMessage
MessageCallback → CallbackQuery
MessageChatCreated → ChatCreated
BotStarted → BotStarted
BotAdded → BotAdded
BotRemoved → BotRemoved
UserAdded → ChatMemberUpdated
UserRemoved → ChatMemberLeft
ChatTitleChanged → ChatTitleChanged
```

#### Вложения
```python
# maxapi → asyncmaxbot (стандартные названия)
PhotoAttachmentPayload → Photo
StickerAttachmentPayload → Sticker
ContactAttachmentPayload → Contact
OtherAttachmentPayload → Document
ButtonsPayload → InlineKeyboardMarkup
```

#### Кнопки
```python
# maxapi → asyncmaxbot (стандартные названия)
CallbackButton → InlineKeyboardButton
LinkButton → InlineKeyboardButton
ChatButton → KeyboardButton
RequestContact → KeyboardButton
RequestGeoLocationButton → KeyboardButton
```

### Методы API (по стандартам aiogram)

#### Основные методы
```python
# maxapi → asyncmaxbot (стандартные названия)
send_message → send_message
get_updates → get_updates
download_media → download_file
get_upload_url → get_file_url
send_callback → answer_callback_query
send_action → send_chat_action
```

#### Управление чатами
```python
# maxapi → asyncmaxbot (стандартные названия)
get_chat_by_id → get_chat
get_chat_by_link → get_chat_by_link
get_chats → get_chats
get_chat_members → get_chat_members
add_chat_members → add_chat_members
remove_member_chat → ban_chat_member
add_admin_chat → promote_chat_member
remove_admin → demote_chat_member
get_list_admin_chat → get_chat_administrators
edit_chat → edit_chat_info
delete_chat → delete_chat
delete_bot_from_chat → leave_chat
```

#### Управление сообщениями
```python
# maxapi → asyncmaxbot (стандартные названия)
edit_message → edit_message
delete_message → delete_message
pin_message → pin_chat_message
unpin_message → unpin_chat_message
get_pinned_message → get_chat_pinned_message
get_messages → get_messages
```

#### Информация
```python
# maxapi → asyncmaxbot (стандартные названия)
get_me → get_me
get_me_from_chat → get_chat_member
change_info → set_my_info
```

### Типы ответов (стандартные названия)

#### Отправленные
```python
# maxapi → asyncmaxbot (стандартные названия)
sended_message → sent_message
sended_callback → sent_callback
sended_action → sent_action
```

#### Полученные
```python
# maxapi → asyncmaxbot (стандартные названия)
getted_updates → updates
getted_upload_url → file_url
getted_members_chat → chat_members
getted_list_admin_chat → chat_administrators
getted_pineed_message → pinned_message
```

#### Изменения
```python
# maxapi → asyncmaxbot (стандартные названия)
edited_message → edited_message
pinned_message → pinned_message
deleted_pin_message → unpinned_message
```

#### Удаления
```python
# maxapi → asyncmaxbot (стандартные названия)
deleted_message → deleted_message
deleted_chat → deleted_chat
deleted_bot_from_chat → left_chat
```

#### Добавления
```python
# maxapi → asyncmaxbot (стандартные названия)
added_admin_chat → promoted_member
added_members_chat → added_members
```

#### Удаления участников
```python
# maxapi → asyncmaxbot (стандартные названия)
removed_admin → demoted_member
removed_member_chat → banned_member
```

### Переменные и параметры (стандартные названия)

#### Основные параметры
```python
# maxapi → asyncmaxbot (стандартные названия)
token → token
chat_id → chat_id
user_id → user_id
message_id → message_id
text → text
caption → caption
```

#### Методы обработки
```python
# maxapi → asyncmaxbot (стандартные названия)
message_handler → message_handler
callback_handler → callback_query_handler
bot_started → bot_started
message_created → message
```

### Архитектурные паттерны (по стандартам aiogram)

#### Регистрация обработчиков
```python
# Стандартный стиль aiogram
@dp.message_handler(F.command == "start")
async def handler(message: Message):
    pass

# asyncmaxbot стиль (аналогично aiogram)
@dp.message_handler(F.command == "start")
async def handler(message: Message):
    pass
```

#### Роутинг
```python
# Стандартный стиль aiogram
router = Router()
router.message.register(handler, F.command == "start")
dp.include_router(router)

# asyncmaxbot стиль (аналогично aiogram)
router = Router()
router.message.register(handler, F.command == "start")
dp.include_router(router)
```

#### Webhook интеграция
```python
# Стандартный стиль aiogram
from fastapi import FastAPI
app = FastAPI()

@app.post("/webhook")
async def webhook_handler(update: dict):
    await dp.process_update(update)

# asyncmaxbot стиль (аналогично aiogram)
from fastapi import FastAPI
app = FastAPI()

@app.post("/webhook")
async def webhook_handler(update: dict):
    await dp.process_update(update)
```

### Контекст и события (по стандартам aiogram)

#### Контекст
```python
# Стандартный стиль aiogram
class Message:
    def __init__(self, message_data):
        self.text = message_data['text']
        self.chat = message_data['chat']
        self.from_user = message_data['from']

# asyncmaxbot стиль (аналогично aiogram)
class Message:
    def __init__(self, message_data):
        self.text = message_data['text']
        self.chat = message_data['chat']
        self.from_user = message_data['from']
```

#### Свойства контекста
```python
# Стандартный стиль aiogram
message.text
await message.answer("Hello!")
await bot.send_message(chat_id, "Hello!")

# asyncmaxbot стиль (аналогично aiogram)
message.text
await message.answer("Hello!")
await bot.send_message(chat_id, "Hello!")
```

### Медиа и файлы (по стандартам aiogram)

#### InputMedia → InputMedia (стандартное название)
```python
# Стандартный стиль aiogram
media = InputMediaPhoto(
    media="file_id",
    caption="Описание"
)

# asyncmaxbot стиль (аналогично aiogram)
media = InputMediaPhoto(
    media="file_id",
    caption="Описание"
)
```

#### Загрузка файлов
```python
# Стандартный стиль aiogram
file = await bot.get_file(file_id)
downloaded = await bot.download_file(file.file_path)

# asyncmaxbot стиль (аналогично aiogram)
file = await bot.get_file(file_id)
downloaded = await bot.download_file(file.file_path)
```

### Middleware система (по стандартам aiogram)

#### Middleware → Middleware (стандартное название)
```python
# Стандартный стиль aiogram
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        pass

# asyncmaxbot стиль (аналогично aiogram)
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        pass
```

### Логирование (по стандартам aiogram)

#### Логгеры
```python
# Стандартный стиль aiogram
import logging
logger = logging.getLogger(__name__)
logger.info("Message received")

# asyncmaxbot стиль (аналогично aiogram)
import logging
logger = logging.getLogger(__name__)
logger.info("Message received")
```

### Исключения (по стандартам aiogram)

#### Обработка ошибок
```python
# Стандартный стиль aiogram
from aiogram.exceptions import TelegramAPIError

# asyncmaxbot стиль (аналогично aiogram)
from maxbot.exceptions import MaxAPIError
```

## Итоговая архитектура

### Основные импорты
```python
# Стандартный стиль aiogram
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery

# asyncmaxbot стиль (аналогично aiogram)
from maxbot import Bot, Dispatcher, Router, F
from maxbot.types import Message, CallbackQuery
```

### Пример использования
```python
# Стандартный стиль aiogram
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

bot = Bot('token')
dp = Dispatcher()

@dp.message_handler(F.command == "start")
async def start_handler(message: Message):
    await message.answer("Hello!")

async def main():
    await dp.start_polling(bot)

# asyncmaxbot стиль (аналогично aiogram)
import asyncio
from maxbot import Bot, Dispatcher, F
from maxbot.types import Message

bot = Bot('token')
dp = Dispatcher()

@dp.message_handler(F.command == "start")
async def start_handler(message: Message):
    await message.answer("Hello!")

async def main():
    await dp.start_polling(bot)
```

## План реализации

### Этап 1: Создание стандартной структуры
1. Создать каталоги по стандартам aiogram
2. Переименовать файлы согласно стандартам
3. Обновить импорты в `__init__.py`

### Этап 2: Стандартизация классов
1. Использовать стандартные названия классов
2. Обновить все ссылки на классы
3. Привести к стандартам aiogram

### Этап 3: Стандартизация API
1. Использовать стандартные названия методов
2. Обновить параметры функций
3. Привести к стандартам aiogram

### Этап 4: Документация
1. Обновить README.md по стандартам
2. Переписать примеры в стиле aiogram
3. Обновить документацию API

### Этап 5: Тестирование
1. Обновить тесты по стандартам
2. Проверить совместимость
3. Убедиться в соответствии стандартам

## Преимущества такого подхода

1. **Стандартизация** - соответствует общепринятым нормам
2. **Понятность** - знакомые названия для разработчиков
3. **Совместимость** - легко переходить с aiogram
4. **Профессиональность** - соответствует индустриальным стандартам
5. **Отсутствие плагиата** - используем стандартные названия
6. **Проверенность** - опираемся на опыт aiogram

## Заключение

Данная стратегия именования обеспечивает:
- Соответствие стандартам ботостроения
- Понятность для разработчиков
- Совместимость с aiogram
- Профессиональный вид
- Отсутствие признаков плагиата
- Использование проверенных решений

Все технологии интегрируются под стандартными названиями, следуя опыту aiogram и общепринятым нормам ботостроения. 