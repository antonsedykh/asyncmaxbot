"""
Справочный бот с актуальной архитектурой AsyncMaxBot SDK.
Демонстрирует основные возможности библиотеки.
"""

import asyncio
import os
from maxbot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.filters import command, text, regex, attachment_type, has_attachment
from maxbot.middleware import LoggingMiddleware, ErrorHandlingMiddleware

# Получаем токен из переменной окружения или файла
def get_token():
    token_file = "token.txt"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return os.environ.get("MAXBOT_TOKEN", "YOUR_TOKEN_HERE")

async def main():
    bot = Bot(get_token())
    dispatcher = Dispatcher(bot)
    
    # Добавляем middleware
    dispatcher.add_middleware(LoggingMiddleware())
    dispatcher.add_middleware(ErrorHandlingMiddleware())
    
    @dispatcher.message_handler(command("start"))
    async def start_command(ctx):
        """Обработчик команды /start"""
        help_text = """
🤖 **Добро пожаловать в справочный бот!**

📚 **AsyncMaxBot SDK** — современная библиотека для создания ботов Max
Messenger с асинхронной архитектурой и удобным API.

🔧 **Доступные команды:**
• `/help` — показать эту справку
• `/info` — информация о библиотеке
• `/test` — тестовые функции
• `/upload` — загрузка файлов
• `/filters` — демонстрация фильтров

💡 **Отправьте любой файл** для демонстрации работы с вложениями!
        """
        await ctx.reply(help_text)
    
    @dispatcher.message_handler(command("info"))
    async def info_command(ctx):
        """Информация о библиотеке"""
        info_text = """
🏗️ **Архитектура AsyncMaxBot SDK:**

📦 **Основные компоненты:**
• `Bot` — основной класс для работы с API
• `Dispatcher` — диспетчер сообщений
• `Context` — контекст обработки
• `Filters` — система фильтрации
• `Middleware` — промежуточные обработчики

⚡ **Ключевые возможности:**
• Асинхронная архитектура
• Строгая типизация (Pydantic)
• Универсальная работа с вложениями
• Гибкая система фильтров
• Middleware для расширения
• Подробная документация

🔗 **GitHub:** https://github.com/maxbotdev/asyncmaxbot
        """
        await ctx.reply(info_text)
    
    @dispatcher.message_handler(command("test"))
    async def test_command(ctx):
        """Тестовые функции"""
        await ctx.reply("🧪 Запускаю тесты...")
        
        # Тест отправки действий
        await ctx.send_action("typing")
        await asyncio.sleep(1)
        
        # Тест редактирования
        msg = await ctx.reply("Это сообщение будет отредактировано...")
        await asyncio.sleep(2)
        await ctx.edit_message("✅ Сообщение отредактировано!")
        
        await ctx.reply("🎉 Все тесты пройдены!")
    
    @dispatcher.message_handler(command("upload"))
    async def upload_command(ctx):
        """Демонстрация загрузки файлов"""
        upload_text = """
📤 **Загрузка файлов:**

Для демонстрации загрузки отправьте:
• Изображение (PNG, JPG)
• Видео файл
• Аудио файл
• Документ

Бот покажет информацию о загруженном файле.
        """
        await ctx.reply(upload_text)
    
    @dispatcher.message_handler(command("filters"))
    async def filters_command(ctx):
        """Демонстрация фильтров"""
        filters_text = """
🔍 **Система фильтров:**

**Команды:**
• `/start` — срабатывает на команду "start"

**Текст:**
• Напишите "привет" — сработает текстовый фильтр
• Напишите число — сработает regex фильтр

**Вложения:**
• Отправьте фото — сработает фильтр изображений
• Отправьте файл — сработает фильтр файлов
• Отправьте что угодно — сработает общий фильтр

**Комбинированные:**
• Команда + вложение — сработает AND фильтр
        """
        await ctx.reply(filters_text)
    
    @dispatcher.message_handler(text("привет"))
    async def hello_handler(ctx):
        """Обработчик текстового фильтра"""
        await ctx.reply("👋 Привет! Текстовый фильтр сработал!")
    
    @dispatcher.message_handler(regex(r"^\d+$"))
    async def number_handler(ctx):
        """Обработчик regex фильтра для чисел"""
        number = int(ctx.text)
        await ctx.reply(f"🔢 Получил число: {number} (regex фильтр)")
    
    @dispatcher.message_handler(attachment_type("image"))
    async def image_handler(ctx):
        """Обработчик изображений"""
        for attachment in ctx.attachments:
            size = attachment.size or 0
            width = attachment.width or 0
            height = attachment.height or 0
            
            info = f"""
🖼️ **Изображение получено!**

📏 Размеры: {width}x{height}
💾 Размер файла: {size} байт
📄 Тип: {attachment.mime_type or 'Неизвестно'}
            """
            await ctx.reply(info)
    
    @dispatcher.message_handler(attachment_type("file"))
    async def file_handler(ctx):
        """Обработчик файлов"""
        for attachment in ctx.attachments:
            filename = attachment.filename or "Без названия"
            size = attachment.size or 0
            mime_type = attachment.mime_type or "Неизвестно"
            
            info = f"""
📄 **Файл получен!**

📁 Имя: {filename}
💾 Размер: {size} байт
📋 Тип: {mime_type}
            """
            await ctx.reply(info)
    
    @dispatcher.message_handler(has_attachment())
    async def any_attachment_handler(ctx):
        """Обработчик любых вложений"""
        if len(ctx.attachments) > 1:
            await ctx.reply(f"📎 Получил {len(ctx.attachments)} вложений!")
        else:
            attachment = ctx.attachments[0]
            await ctx.reply(f"📎 Вложение типа: {attachment.type}")
    
    @dispatcher.message_handler()
    async def echo_handler(ctx):
        """Эхо обработчик для всех остальных сообщений"""
        if ctx.text and not ctx.text.startswith('/'):
            await ctx.reply(f"💬 Вы сказали: {ctx.text}")
    
    # Запускаем бота
    print("🚀 Запускаю справочный бот...")
    print("📚 Отправьте /start для получения справки")
    
    async with bot:
        await bot.polling(dispatcher=dispatcher)

if __name__ == "__main__":
    asyncio.run(main()) 