"""
Router система - исправленный рабочий пример
Демонстрирует использование роутеров для изоляции логики
"""

import asyncio
from maxbot import Bot, Dispatcher, Router, F, Context
from maxbot.max_types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "YOUR_TOKEN_HERE"

# Создаем роутер для команд
def create_commands_router():
    router = Router()
    
    @router.message_handler(F.command == "start")
    async def start_command(ctx: Context):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Игры", payload="games")],
                [InlineKeyboardButton(text="📊 Статистика", payload="stats")],
                [InlineKeyboardButton(text="ℹ️ Помощь", payload="help")]
            ]
        )
        await ctx.reply(
            f"👋 Привет, {ctx.user.name}! Я модульный бот.\n"
            "Выберите раздел:",
            reply_markup=keyboard
        )
    
    @router.message_handler(F.command == "help")
    async def help_command(ctx: Context):
        await ctx.reply(
            "📚 Доступные команды:\n\n"
            "🎮 /games — игры\n"
            "📊 /stats — статистика\n"
            "ℹ️ /help — эта справка\n"
            "🔧 /settings — настройки"
        )
    
    @router.message_handler(F.command == "settings")
    async def settings_command(ctx: Context):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔔 Уведомления", payload="notifications")],
                [InlineKeyboardButton(text="🌍 Язык", payload="language")],
                [InlineKeyboardButton(text="🔙 Назад", payload="back_to_main")]
            ]
        )
        await ctx.reply("⚙️ Настройки:", reply_markup=keyboard)
    
    return router

# Создаем роутер для callback
def create_callback_router():
    router = Router()
    
    @router.callback_query_handler(F.payload == "games")
    async def games_callback(ctx: Context):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎰 Блэкджек", payload="blackjack")],
                [InlineKeyboardButton(text="🎲 Кости", payload="dice")],
                [InlineKeyboardButton(text="🔙 Назад", payload="back_to_main")]
            ]
        )
        await ctx.answer_callback("🎮 Выберите игру:")
        await ctx.edit_message("🎮 Доступные игры:", reply_markup=keyboard)
    
    @router.callback_query_handler(F.payload == "stats")
    async def stats_callback(ctx: Context):
        await ctx.answer_callback("📊 Статистика загружается...")
        await ctx.edit_message(
            "📊 Ваша статистика:\n"
            "🎮 Игр сыграно: 15\n"
            "🏆 Побед: 8\n"
            "📝 Сообщений: 127"
        )
    
    @router.callback_query_handler(F.payload == "help")
    async def help_callback(ctx: Context):
        await ctx.answer_callback("ℹ️ Справка")
        await ctx.edit_message(
            "ℹ️ Справка по боту:\n\n"
            "🎮 Игры — различные мини-игры\n"
            "📊 Статистика — ваши достижения\n"
            "⚙️ Настройки — персонализация"
        )
    
    @router.callback_query_handler(F.payload == "back_to_main")
    async def back_to_main_callback(ctx: Context):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Игры", payload="games")],
                [InlineKeyboardButton(text="📊 Статистика", payload="stats")],
                [InlineKeyboardButton(text="ℹ️ Помощь", payload="help")]
            ]
        )
        await ctx.answer_callback("🔙 Возвращаемся в главное меню")
        await ctx.edit_message(
            f"👋 Привет, {ctx.user.name}! Я модульный бот.\n"
            "Выберите раздел:",
            reply_markup=keyboard
        )
    
    return router

# Создаем роутер для событий
def create_events_router():
    router = Router()
    
    @router.bot_started_handler()
    async def on_bot_started(ctx: Context):
        await ctx.reply(
            f"🎉 Бот запущен пользователем {ctx.user.name}!\n"
            "Используйте /start для начала работы."
        )
    
    @router.user_added_handler()
    async def on_user_added(ctx: Context):
        await ctx.reply(
            f"👋 Добро пожаловать, {ctx.user.name}!\n"
            "Я модульный бот с различными возможностями.\n"
            "Используйте /start для начала работы."
        )
    
    @router.chat_member_updated_handler()
    async def on_member_updated(ctx: Context):
        await ctx.reply(
            f"👤 Статус пользователя {ctx.user.name} изменен:\n"
            f"📊 {ctx.old_status} → {ctx.new_status}"
        )
    
    return router

async def main():
    async with Bot(token=TOKEN) as bot:
        dp = Dispatcher(bot)
        
        # Подключаем роутеры
        commands_router = create_commands_router()
        callback_router = create_callback_router()
        events_router = create_events_router()
        
        dp.include_router(commands_router)
        dp.include_router(callback_router)
        dp.include_router(events_router)
        
        print("🔧 Модульный бот запущен!")
        await bot.polling(dispatcher=dp)

if __name__ == "__main__":
    asyncio.run(main()) 