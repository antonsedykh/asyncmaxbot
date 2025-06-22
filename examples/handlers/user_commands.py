# examples/handlers/user_commands.py
from maxbot import Router, Context, F

router = Router()

@router.message_handler(F.text == "/start")
async def handle_start(ctx: Context):
    await ctx.reply("Привет! Это бот с использованием роутеров.")

@router.message_handler(F.text == "/help")
async def handle_help(ctx: Context):
    await ctx.reply("Это просто демонстрация модульности. Доступные команды: /start, /help, /image") 