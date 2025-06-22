import asyncio
import logging

from maxbot import Bot, Dispatcher, Context
from maxbot.max_types import BotStarted, UserAdded, ChatMemberUpdated

# Замените на ваш токен
TOKEN = "YOUR_TOKEN_HERE" 

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

dp = Dispatcher(Bot(token=TOKEN))

@dp.bot_started_handler()
async def handle_bot_started(ctx: Context):
    event: BotStarted = ctx.bot_started
    logging.info(f"Бот запущен в чате {event.chat_id} пользователем {event.user.name} (ID: {event.user.user_id})")
    await ctx.reply(f"Привет, {event.user.name}! Спасибо, что начал диалог со мной.")

@dp.user_added_handler()
async def handle_user_added(ctx: Context):
    event: UserAdded = ctx.user_added
    logging.info(f"Пользователь {event.user.name} (ID: {event.user.user_id}) был добавлен в чат {event.chat_id} пользователем {event.inviter.name}")
    await ctx.reply(f"Добро пожаловать в чат, {event.user.name}!")

@dp.chat_member_updated_handler()
async def handle_chat_member_updated(ctx: Context):
    event: ChatMemberUpdated = ctx.chat_member_updated
    logging.info(f"Статус пользователя {event.user.name} в чате {event.chat_id} изменен с '{event.old_status}' на '{event.new_status}'")
    # Ответ в чат не отправляем, чтобы не спамить
    
@dp.message_handler()
async def handle_any_message(ctx: Context):
    logging.info(f"Получено сообщение от {ctx.user.name}: {ctx.text}")
    await ctx.reply("Я получил ваше сообщение. Я также отслеживаю события в чате.")


async def main():
    print("Бот для отслеживания событий запущен!")
    bot = dp.bot
    async with bot:
        await bot.polling(dispatcher=dp, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main()) 