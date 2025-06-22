#!/usr/bin/env python3
"""
Пример бота с callback кнопками
Демонстрирует использование inline клавиатур и обработку callback_query
"""

import asyncio
from maxbot import Bot, Dispatcher, F
from maxbot.max_types import InlineKeyboardMarkup, InlineKeyboardButton

# Инициализация бота и диспетчера
bot = Bot("YOUR_TOKEN_HERE")
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_command(message):
    """Обработчик команды /start с inline клавиатурой"""
    # Создаем inline клавиатуру согласно maxapi реализации
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Кнопка 1", payload="btn1"),
                InlineKeyboardButton(text="Кнопка 2", payload="btn2"),
            ],
            [
                InlineKeyboardButton(text="Информация", payload="info"),
                InlineKeyboardButton(text="Помощь", payload="help"),
            ]
        ]
    )
    
    await message.reply(
        "Привет! Выберите действие:",
        reply_markup=keyboard
    )

@dp.message_handler(commands=["menu"])
async def menu_command(message):
    """Обработчик команды /menu с динамической клавиатурой"""
    # Создаем клавиатуру динамически
    buttons = []
    for i in range(1, 4):
        buttons.append([
            InlineKeyboardButton(
                text=f"Опция {i}", 
                payload=f"option_{i}"
            )
        ])
    
    # Добавляем кнопку отмены
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", payload="cancel")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.reply(
        "Выберите опцию:",
        reply_markup=keyboard
    )

@dp.callback_query_handler()
async def handle_all_callbacks(ctx: Context):
    """
    Обрабатывает все колбэки, для которых нет явных обработчиков.
    """
    if ctx.payload == 'btn1':
        await ctx.answer_callback("Вы нажали на Кнопку 1")
    elif ctx.payload == 'btn2':
        await ctx.answer_callback("Вы нажали на Кнопку 2")
    elif ctx.payload == 'info':
        await ctx.edit_message("Это информационное сообщение.", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="← Назад", payload="back_to_start")]]
        ))
    elif ctx.payload == 'help':
        await ctx.edit_message("Это сообщение помощи.", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="← Назад", payload="back_to_start")]]
        ))
    elif ctx.payload.startswith("option_"):
        option_num = ctx.payload.split("_")[1]
        await ctx.answer_callback(f"Выбрана опция {option_num}")
    elif ctx.payload == "cancel":
        await ctx.edit_message("❌ Действие отменено")
    elif ctx.payload == "back_to_start":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Кнопка 1", payload="btn1"),
                    InlineKeyboardButton(text="Кнопка 2", payload="btn2"),
                ],
                [
                    InlineKeyboardButton(text="Информация", payload="info"),
                    InlineKeyboardButton(text="Помощь", payload="help"),
                ]
            ]
        )
        await ctx.edit_message("Главное меню:", reply_markup=keyboard)
    elif ctx.payload == "back_to_menu":
        # Логика возврата к меню опций
        pass # Можно реализовать по аналогии
    else:
        await ctx.answer_callback(f"Неизвестный колбэк: {ctx.payload}")

if __name__ == "__main__":
    print("Запуск callback бота...")
    print("Используйте /start для главного меню")
    print("Используйте /menu для дополнительных опций")
    
    # Запуск бота
    async def main():
        async with bot:
            me = await bot.get_me()
            print(f"🤖 Бот: {me['name']} (ID: {me['user_id']})")
            
            await bot.polling(
                dispatcher=dp,
                timeout=1,
                long_polling_timeout=30
            )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Бот остановлен") 