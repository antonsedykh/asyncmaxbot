"""
Эхо-бот - исправленный рабочий пример
Демонстрирует базовые возможности библиотеки AsyncMaxBot SDK 1.4.2
"""

import asyncio
from maxbot import Bot, Dispatcher, Context, F
from maxbot.filters import command, text
from maxbot.middleware import LoggingMiddleware, ErrorHandlingMiddleware

# ⚠️ Вставьте ваш токен сюда
TOKEN = "YOUR_TOKEN_HERE"

class EchoBot:
    """Эхо-бот с стандартной архитектурой"""
    
    def __init__(self):
        self.bot = Bot(TOKEN)
        self.dp = Dispatcher(self.bot)
        self.setup_middleware()
        self.setup_handlers()
        self.stats = {"messages": 0, "users": set()}
    
    def setup_middleware(self):
        """Настройка базового middleware"""
        self.dp.include_middleware(LoggingMiddleware())
        self.dp.include_middleware(ErrorHandlingMiddleware())
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        
        @self.dp.message_handler(F.command == "start")
        async def start_handler(ctx: Context):
            await ctx.reply(
                f"👋 Привет, {ctx.user.name}! Я эхо-бот.\n"
                "📝 Просто напиши что-нибудь, и я повторю это.\n"
                "📊 /stats — статистика\n"
                "🔄 /echo — режим эхо\n"
                "❓ /help — эта справка"
            )
        
        @self.dp.message_handler(F.command == "help")
        async def help_handler(ctx: Context):
            await ctx.reply(
                "📚 Справка по эхо-боту:\n\n"
                "💬 Просто напишите любое сообщение, и я его повторю\n"
                "📊 /stats — показать статистику\n"
                "🔄 /echo — включить режим эхо\n"
                "❓ /help — эта справка"
            )
        
        @self.dp.message_handler(F.command == "stats")
        async def stats_handler(ctx: Context):
            self.stats["messages"] += 1
            self.stats["users"].add(ctx.user_id)
            
            await ctx.reply(
                f"📊 Статистика:\n"
                f"💬 Сообщений: {self.stats['messages']}\n"
                f"👥 Уникальных пользователей: {len(self.stats['users'])}"
            )
        
        @self.dp.message_handler(F.command == "echo")
        async def echo_mode_handler(ctx: Context):
            await ctx.reply("🔄 Режим эхо включен! Напиши что-нибудь.")
        
        @self.dp.message_handler(F.text.contains("привет"))
        async def hello_handler(ctx: Context):
            emoji = "🦜" if "привет" in ctx.text.lower() else "📢"
            await ctx.reply(f"{emoji} {ctx.text}")
        
        @self.dp.message_handler()
        async def echo_handler(ctx: Context):
            """
            Этот обработчик ловит любое сообщение и отвечает тем же текстом.
            Демонстрирует:
            - Регистрацию обработчика без фильтров (срабатывает на все).
            - Использование `ctx.text` для получения текста.
            - Использование `ctx.reply` для ответа.
            """
            self.stats["messages"] += 1
            self.stats["users"].add(ctx.user_id)
            
            if ctx.text and ctx.text.startswith("/"):
                await ctx.reply("❓ Неизвестная команда. Напиши /help")
            elif ctx.text:
                emoji = "🦜" if "привет" in ctx.text.lower() else "📢"
                await ctx.reply(f"{emoji} {ctx.text}")
    
    async def run(self):
        """Запуск бота"""
        print("🤖 Эхо-бот запущен!")
        
        async with self.bot:
            me = await self.bot.get_me()
            print(f"🤖 Бот: {me['name']} (ID: {me['user_id']})")
            
            await self.bot.polling(dispatcher=self.dp)

async def main():
    """Основная функция для запуска бота."""
    bot = EchoBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main()) 