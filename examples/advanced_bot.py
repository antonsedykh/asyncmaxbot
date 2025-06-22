import asyncio
import os
from maxbot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.filters import command, text, regex, attachment_type, has_attachment, attachment_type as Attachment, has_attachment as HasAttachment
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

from maxbot.middleware import (
    MiddlewareManager, LoggingMiddleware, ThrottlingMiddleware, 
    ErrorHandlingMiddleware, MetricsMiddleware, AntispamMiddleware
)
from maxbot.max_types import Context

TOKEN = "YOUR_TOKEN_HERE"  # Замените на ваш токен

class AdvancedBot:
    """
    Продвинутый бот для демонстрации сложных возможностей SDK.

    Демонстрирует:
    - Добавление Middleware (Logging, Error Handling).
    - Комбинацию нескольких фильтров для одного обработчика.
    - Использование фильтров по регулярному выражению (`Regex`) и
      типу вложения (`Attachment`).
    """
    
    def __init__(self):
        self.bot = Bot(TOKEN)
        self.dp = Dispatcher(self.bot)
        self.setup_middleware()
        self.setup_handlers()
        self.stats = {"messages": 0, "users": set()}
    
    def setup_middleware(self):
        """Настройка middleware системы"""
        manager = MiddlewareManager()
        
        # Логирование всех сообщений
        manager.add_middleware(LoggingMiddleware(log_level="INFO"))
        
        # Ограничение частоты (1 сообщение в секунду)
        manager.add_middleware(ThrottlingMiddleware(rate_limit=1.0))
        
        # Обработка ошибок
        manager.add_middleware(ErrorHandlingMiddleware())
        
        # Антиспам
        manager.add_middleware(AntispamMiddleware(interval=2.0))
        
        # Сбор метрик
        self.metrics = MetricsMiddleware()
        manager.add_middleware(self.metrics)
        
        self.dp.middleware_manager = manager
    
    def setup_handlers(self):
        """Настройка обработчиков с фильтрами"""
        
        # Команды с декораторами
        @self.dp.message_handler(command("start"))
        async def start_handler(ctx: Context):
            """Обработчик команды /start."""
            await ctx.reply(
                "🚀 Добро пожаловать в продвинутый бот!\n\n"
                "📋 Доступные команды:\n"
                "🔧 /help - справка\n"
                "📊 /stats - статистика\n"
                "🖼️ /photo - отправить фото\n"
                "📁 /file - отправить файл\n"
                "🎵 /audio - отправить аудио\n"
                "📹 /video - отправить видео\n"
                "📍 /location - отправить геолокацию\n"
                "🔗 /share - отправить ссылку\n"
                "📎 /test_attachments - тест вложений\n"
                "⚙️ /metrics - метрики бота"
            )
        
        @self.dp.message_handler(command("help"))
        async def help_handler(ctx: Context):
            help_text = """
🔧 **Возможности этого бота:**

📝 **Команды:**
• /start - приветствие
• /help - эта справка
• /stats - статистика
• /metrics - метрики

📎 **Работа с файлами:**
• /photo - отправить фото
• /file - отправить файл
• /audio - отправить аудио
• /video - отправить видео

📍 **Геолокация и ссылки:**
• /location - отправить координаты
• /share - отправить ссылку

🧪 **Тестирование:**
• /test_attachments - тест обработки вложений

💡 **Просто отправьте:**
• Фото, видео, аудио, файлы - бот их обработает
• "привет" - получите приветствие
• Любой текст с "тест" - получите ответ
            """
            await ctx.reply(help_text)
        
        @self.dp.message_handler(command("stats"))
        async def stats_handler(ctx: Context):
            self.stats["messages"] += 1
            self.stats["users"].add(ctx.user_id)
            
            metrics = self.metrics.get_metrics()
            stats_text = f"""
📊 **Статистика бота:**

💬 Сообщений обработано: {self.stats['messages']}
👥 Уникальных пользователей: {len(self.stats['users'])}

⚙️ **Системные метрики:**
📈 Сообщений в секунду: {metrics['messages_per_second']:.2f}
⏱️ Время работы: {metrics['uptime_seconds']:.0f} сек
❌ Ошибок: {metrics['errors']}
📊 Процент ошибок: {metrics['error_rate']*100:.1f}%
            """
            await ctx.reply(stats_text)
        
        @self.dp.message_handler(command("metrics"))
        async def metrics_handler(ctx: Context):
            metrics = self.metrics.get_metrics()
            await ctx.reply(f"📈 Метрики: {metrics}")
        
        # Обработка файлов
        @self.dp.message_handler(command("photo"))
        async def photo_handler(ctx: Context):
            # Создаем тестовое изображение
            img = Image.new('RGB', (400, 300), color='lightblue')
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "Тестовое фото", fill='black')
            draw.text((20, 60), f"Отправлено: {datetime.now()}", fill='black')
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            await self.bot.send_photo(
                img_bytes, 
                user_id=ctx.user_id, 
                caption="🖼️ Тестовое изображение от продвинутого бота!"
            )
        
        @self.dp.message_handler(command("file"))
        async def file_handler(ctx: Context):
            file_content = f"""
📄 Тестовый файл от продвинутого бота

📅 Создан: {datetime.now()}
👤 Пользователь: {ctx.user.name}
💬 Сообщений: {self.stats['messages']}

🔧 Этот файл демонстрирует возможности
   отправки документов через Max API.
            """
            
            file_bytes = io.BytesIO(file_content.encode('utf-8'))
            await self.bot.send_document(
                file_bytes,
                user_id=ctx.user_id,
                caption="📁 Тестовый документ",
                filename="test_document.txt"
            )
        
        @self.dp.message_handler(command("audio"))
        async def audio_handler(ctx: Context):
            # Создаем простой аудиофайл (заглушка)
            audio_content = b"RIFF" + b"\x00" * 100  # Простой WAV заголовок
            audio_bytes = io.BytesIO(audio_content)
            
            await self.bot.send_audio(
                audio_bytes,
                user_id=ctx.user_id,
                caption="🎵 Тестовое аудио",
                filename="test_audio.wav"
            )
        
        @self.dp.message_handler(command("video"))
        async def video_handler(ctx: Context):
            # Создаем простое видео (заглушка)
            video_content = b"test video content"
            video_bytes = io.BytesIO(video_content)
            
            await self.bot.send_video(
                video_bytes,
                user_id=ctx.user_id,
                caption="📹 Тестовое видео",
                filename="test_video.mp4"
            )
        
        @self.dp.message_handler(command("location"))
        async def location_handler(ctx: Context):
            await self.bot.send_location(
                latitude=55.7558,
                longitude=37.6176,
                user_id=ctx.user_id,
                caption="📍 Москва, Красная площадь"
            )
        
        @self.dp.message_handler(command("share"))
        async def share_handler(ctx: Context):
            await self.bot.send_share(
                url="https://github.com/sdkinfotech/asyncmaxbot",
                title="AsyncMaxBot SDK",
                description="Python SDK для Max API",
                user_id=ctx.user_id
            )
        
        # Обработка вложений
        @self.dp.message_handler(attachment_type("image"))
        async def image_attachment_handler(ctx: Context):
            await ctx.reply("🖼️ Получил изображение! Обрабатываю...")
            
            if ctx.attachments:
                for att in ctx.attachments:
                    if att.type == "image":
                        await ctx.reply(
                            f"📸 Детали изображения:\n"
                            f"🔗 URL: {att.url}\n"
                            f"📏 Размер: {att.width}x{att.height}\n"
                            f"🆔 ID: {att.file_id}"
                        )
        
        @self.dp.message_handler(attachment_type("video"))
        async def video_attachment_handler(ctx: Context):
            await ctx.reply("📹 Получил видео! Обрабатываю...")
            
            if ctx.attachments:
                for att in ctx.attachments:
                    if att.type == "video":
                        await ctx.reply(
                            f"🎬 Детали видео:\n"
                            f"🔗 URL: {att.url}\n"
                            f"📏 Размер: {att.width}x{att.height}\n"
                            f"⏱️ Длительность: {att.duration} сек\n"
                            f"🆔 ID: {att.file_id}"
                        )
        
        @self.dp.message_handler(attachment_type("file"))
        async def file_attachment_handler(ctx: Context):
            await ctx.reply("📁 Получил файл! Обрабатываю...")
            
            if ctx.attachments:
                for att in ctx.attachments:
                    if att.type == "file":
                        await ctx.reply(
                            f"📄 Детали файла:\n"
                            f"📝 Имя: {att.filename}\n"
                            f"📏 Размер: {att.size} байт\n"
                            f"🔗 URL: {att.url}\n"
                            f"🆔 ID: {att.file_id}"
                        )
        
        @self.dp.message_handler(has_attachment())
        async def any_attachment_handler(ctx: Context):
            await ctx.reply("📎 Получил вложение! Тип: " + 
                          ", ".join([att.type for att in ctx.attachments]))
        
        # Текстовые фильтры
        @self.dp.message_handler(text("привет", exact=False))
        async def hello_handler(ctx: Context):
            await ctx.reply(f"👋 Привет, {ctx.user.name}!")
        
        @self.dp.message_handler(text(["спасибо", "благодарю"], exact=False))
        async def thanks_handler(ctx: Context):
            await ctx.reply("🙏 Пожалуйста! Рад помочь!")
        
        @self.dp.message_handler(regex(r"тест.*"))
        async def test_handler(ctx: Context):
            await ctx.reply("🧪 Тест пройден! Бот работает корректно.")
        
        @self.dp.message_handler(regex(r"\d+"))
        async def number_handler(ctx: Context):
            await ctx.reply(f"🔢 Получил число: {ctx.text}")
        
        # Обработчик всех остальных сообщений
        @self.dp.message_handler()
        async def default_handler(ctx: Context):
            await ctx.reply(
                f"💬 Получил: {ctx.text}\n\n"
                f"💡 Напишите /help для списка команд"
            )
    
    async def run(self):
        """Запуск бота с polling"""
        print("🚀 Запуск продвинутого бота...")
        
        async with self.bot:
            # Получаем информацию о боте
            me = await self.bot.get_me()
            print(f"🤖 Бот: {me['name']} (ID: {me['user_id']})")
            
            # Запускаем polling с диспетчером
            await self.bot.polling(
                dispatcher=self.dp,
                timeout=1,
                long_polling_timeout=30
            )

async def main():
    bot = AdvancedBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main()) 