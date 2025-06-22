"""
Пример использования MagicFilter (F) системы в asyncmaxbot

Демонстрирует гибкую фильтрацию сообщений с помощью MagicFilter.
"""

import asyncio
from maxbot import Bot, Dispatcher, F
from maxbot.filters import command, text

TOKEN = "YOUR_TOKEN_HERE"

async def main():
    async with Bot(token=TOKEN) as bot:
        dp = Dispatcher(bot)
        
        # Пример 1: Простые фильтры
        @dp.message_handler(F.command == "start")
        async def start_handler(ctx):
            await ctx.reply("👋 Привет! Это MagicFilter пример.")
        
        @dp.message_handler(F.text == "привет")
        async def hello_handler(ctx):
            await ctx.reply("😊 И тебе привет!")
        
        # Пример 2: Сложные условия
        @dp.message_handler(F.text.contains("заказ") & (F.user_id != 0))
        async def order_handler(ctx):
            await ctx.reply("📦 Вы интересуетесь заказом?")
        
        @dp.message_handler(F.text.startswith("!") | F.text.endswith("!"))
        async def exclamation_handler(ctx):
            await ctx.reply("❗ Восклицательное сообщение!")
        
        # Пример 3: Фильтры по пользователю
        @dp.message_handler(F.user_id == 123)
        async def admin_handler(ctx):
            await ctx.reply("🔒 Привет, админ!")
        
        @dp.message_handler(F.user_id.in_([1, 2, 3, 4, 5]))
        async def special_users_handler(ctx):
            await ctx.reply("⭐ Привет, особый пользователь!")
        
        # Пример 4: Фильтры по чату
        @dp.message_handler(F.chat_id < 0)
        async def group_handler(ctx):
            await ctx.reply("👥 Это групповой чат!")
        
        # Пример 5: Комбинированные фильтры
        @dp.message_handler(
            F.text.contains("помощь") & 
            ~F.text.contains("не нужна") & 
            (F.user_id > 0)
        )
        async def help_handler(ctx):
            await ctx.reply("🆘 Чем могу помочь?")
        
        # Пример 6: Фильтры по вложениям
        @dp.message_handler(F.attachment)
        async def attachment_handler(ctx):
            await ctx.reply("📎 Получено вложение!")
        
        # Пример 7: Смешанные фильтры (MagicFilter + обычные)
        @dp.message_handler(
            command("test") & 
            F.user_id.in_([1, 2, 3])
        )
        async def test_handler(ctx):
            await ctx.reply("🧪 Тест для особых пользователей!")
        
        # Пример 8: Сложная логика
        @dp.message_handler(
            (F.text.contains("важно") | F.text.contains("срочно")) &
            F.user_id > 100 &
            ~F.text.contains("шутка")
        )
        async def important_handler(ctx):
            await ctx.reply("🚨 Важное сообщение получено!")
        
        # Пример 9: Фильтры по времени (если реализованы)
        @dp.message_handler(F.text.contains("утро"))
        async def morning_handler(ctx):
            await ctx.reply("🌅 Доброе утро!")
        
        # Пример 10: Обработка ошибок в фильтрах
        @dp.message_handler(F.text.contains("ошибка"))
        async def error_test_handler(ctx):
            await ctx.reply("🔧 Тестируем обработку ошибок...")
            # Имитируем ошибку
            raise Exception("Тестовая ошибка")
        
        print("🤖 Бот с MagicFilter запущен...")
        print("📝 Примеры команд:")
        print("  /start - базовый фильтр")
        print("  привет - точное совпадение")
        print("  заказ - сложное условие")
        print("  !тест! - восклицание")
        print("  помощь - комбинированный фильтр")
        print("  важно срочно - сложная логика")
        
        await bot.polling(dispatcher=dp)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен.") 