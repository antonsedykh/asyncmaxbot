[![PyPI - Version](https://img.shields.io/pypi/v/asyncmaxbot.svg)](https://pypi.org/project/asyncmaxbot/)
[![PyPI - License](https://img.shields.io/pypi/l/asyncmaxbot.svg)](https://github.com/sdkinfotech/asyncmaxbot/blob/main/LICENSE)

# Добро пожаловать в AsyncMaxBot SDK!

Это официальная документация по **AsyncMaxBot**, асинхронной Python-библиотеке для создания ботов в Max Messenger.

Здесь вы найдете всё необходимое для разработки ботов любой сложности: от простых эхо-ботов до продвинутых систем с комплексной логикой, inline клавиатурами и callback обработкой.

## 🚀 Быстрый старт

Вот минимальный пример бота, который отвечает на команду `/start` и повторяет любое текстовое сообщение. Этот код полностью рабочий.

```python
import asyncio
from maxbot import Bot, Dispatcher, Context, F
from maxbot.max_types import InlineKeyboardMarkup, InlineKeyboardButton

# Рекомендуется хранить токен в переменной окружения или в файле
TOKEN = "YOUR_TOKEN_HERE"

async def main():
    # Используем 'async with' для корректного управления сессией
    async with Bot(token=TOKEN) as bot:
        dp = Dispatcher(bot)

        # Обработчик команды /start с inline клавиатурой
        @dp.message_handler(F.command == "start")
        async def handle_start(ctx: Context):
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎮 Играть", payload="play")],
                    [InlineKeyboardButton(text="ℹ️ Помощь", payload="help")]
                ]
            )
            await ctx.reply(f"Привет, {ctx.user.name}! Выберите действие:", reply_markup=keyboard)

        # Обработчик callback кнопок
        @dp.callback_query_handler(F.payload == "play")
        async def handle_play_callback(ctx: Context):
            await ctx.answer_callback("🎮 Начинаем игру!")
            await ctx.edit_message("Игра началась! 🎲")

        @dp.callback_query_handler(F.payload == "help")
        async def handle_help_callback(ctx: Context):
            await ctx.answer_callback("ℹ️ Справка")
            await ctx.edit_message("Это простой бот с inline клавиатурой!")

        # Обработчик для всех остальных текстовых сообщений
        @dp.message_handler()
        async def handle_echo(ctx: Context):
            if ctx.text:
                await ctx.reply(f"Вы написали: {ctx.text}")

        # Запускаем получение обновлений
        print("Бот запущен...")
        await bot.polling(dispatcher=dp)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
```

### Как запустить:
1.  Установите библиотеку: `pip install asyncmaxbot`
2.  Сохраните код в файл, например, `my_bot.py`.
3.  Замените `"YOUR_TOKEN_HERE"` на реальный токен вашего бота.
4.  Запустите его: `python my_bot.py`

## ✨ Ключевые возможности

### 🎯 **MagicFilter система (F)**
Гибкая система фильтрации для создания сложных условий:
```python
@dp.message_handler(F.text.contains("привет") & F.user_id == 123)
@dp.message_handler(F.command == "start" | F.text.startswith("help"))
@dp.message_handler(F.has_attachments == True)
```

### 🎮 **Inline клавиатуры и callback**
Создание интерактивных кнопок и обработка нажатий:
```python
keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Кнопка", payload="action")]
    ]
)

@dp.callback_query_handler(F.payload == "action")
async def handle_callback(ctx: Context):
    await ctx.answer_callback("Обработано!")
```

### 📎 **Работа с вложениями**
Поддержка всех типов файлов: изображения, видео, аудио, документы:
```python
@dp.message_handler(F.attachment.type == "image")
async def handle_photo(ctx: Context):
    for attachment in ctx.attachments:
        await ctx.reply(f"Получено изображение: {attachment.filename}")
```

### 🔧 **Middleware система**
Сквозная логика для всех обновлений:
```python
from maxbot.middleware import LoggingMiddleware, ThrottlingMiddleware

dp.include_middleware(LoggingMiddleware())
dp.include_middleware(ThrottlingMiddleware(rate_limit=1.0))
```

### 🎲 **Игровые возможности**
Встроенные примеры игр (блэкджек, секретарь) с управлением состоянием.

## 📚 Куда двигаться дальше?

*   **[Руководство по API](./api.md):** Перейдите сюда для подробного изучения всех компонентов, классов и методов SDK.
*   **[Примеры кода](./examples.md):** Изучите новую страницу с "живыми" примерами кода, включая игры и продвинутые сценарии.
*   **[Страница проекта на PyPI](https://pypi.org/project/asyncmaxbot/):** Посетите страницу проекта для получения информации об установке и версиях.

## 🔄 Версия 1.4.2

Текущая версия включает: 
- ✅ **Router-система**: для модульной архитектуры.
- ✅ **Расширенные события**: обработка добавления пользователя, старта бота и др.
- ✅ MagicFilter систему для гибкой фильтрации
- ✅ Inline клавиатуры и callback обработку
- ✅ Расширенную систему вложений
- ✅ Middleware архитектуру
- ✅ Полную типизацию с Pydantic
- ✅ Комплексные примеры и тесты