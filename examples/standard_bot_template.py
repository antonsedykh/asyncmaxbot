"""
Стандартный шаблон бота MaxBot
Минимальная архитектура для всех ботов
"""

import asyncio
import os
from maxbot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.filters import command, text
from maxbot.middleware import MiddlewareManager, LoggingMiddleware, ErrorHandlingMiddleware
from maxbot.max_types import Context

TOKEN = "YOUR_TOKEN_HERE"  # Замените на ваш токен

class StandardBot:
    """
    Базовый шаблон для создания бота.

    Этот бот отвечает на команды /start и /help, а также
    повторяет любое другое текстовое сообщение.
    Он демонстрирует основную структуру приложения:
    - Класс для инкапсуляции логики бота.
    - Инициализация Bot и Dispatcher.
    - Регистрация обработчиков (хендлеров) для команд и текста.
    - Метод для запуска polling.
    """
    
    def __init__(self, token: str):
        self.bot = Bot(token)
        self.dp = Dispatcher(self.bot)
        self.setup_middleware()
        self.setup_handlers()
    
    def setup_middleware(self):
        """Настройка базового middleware"""
        manager = MiddlewareManager()
        manager.add_middleware(LoggingMiddleware())
        manager.add_middleware(ErrorHandlingMiddleware())
        self.dp.middleware_manager = manager
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        
        @self.dp.message_handler(command("start"))
        async def start_handler(ctx: Context):
            """Обработчик команды /start."""
            await ctx.reply("Привет! Я стандартный бот.")
        
        @self.dp.message_handler(command("help"))
        async def help_handler(ctx: Context):
            """Обработчик команды /help."""
            await ctx.reply("Это справка. Я отвечаю на /start и /help, а также повторяю текст.")
        
        @self.dp.message_handler()
        async def echo_handler(ctx: Context):
            """Обработчик для всех остальных текстовых сообщений."""
            await ctx.reply(f"Получил текст: {ctx.text}")
    
    async def run(self):
        """Запуск бота"""
        print("🚀 Запуск стандартного бота...")
        
        async with self.bot:
            me = await self.bot.get_me()
            print(f"🤖 Бот: {me['name']} (ID: {me['user_id']})")
            
            await self.bot.polling(
                dispatcher=self.dp,
                timeout=1,
                long_polling_timeout=30
            )

async def main():
    bot = StandardBot(TOKEN)
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main()) 