# Примеры использования AsyncMaxBot SDK

В этом разделе собраны полноценные примеры ботов, демонстрирующие различные возможности **AsyncMaxBot SDK версии 1.4.2**. Все примеры основаны на реальных файлах из репозитория и показывают лучшие практики использования библиотеки.

---

## 1. Эхо-бот (Базовый пример)

Самый простой пример бота, который повторяет все сообщения пользователя.

```python
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
```

**Что демонстрирует:**
- Базовую структуру бота с классами
- Регистрацию обработчиков для команд (`F.command`)
- Регистрацию "catch-all" обработчика для любого текста
- Использование middleware для логирования и обработки ошибок
- Простое управление состоянием (статистика)

---

## 2. Блэкджек с Inline клавиатурами 🎰

Современный пример игры в блэкджек с использованием inline клавиатур, callback обработки и MagicFilter системы.

```python
"""
Блэкджек с Inline клавиатурами - исправленный рабочий пример
Демонстрирует inline клавиатуры, callback обработку и MagicFilter систему
"""

import asyncio
from maxbot import Bot, Dispatcher, Context, F
from maxbot.max_types import InlineKeyboardMarkup, InlineKeyboardButton
import random

TOKEN = "YOUR_TOKEN_HERE"

# Карты и значения
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUES = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}

# Игровое состояние
GAMES = {}

class GameState:
    def __init__(self):
        self.deck = self._create_deck()
        self.player = []
        self.dealer = []
        self.finished = False
        self.result = ""
    
    def _create_deck(self):
        deck = []
        for suit in SUITS:
            for rank in RANKS:
                deck.append(f"{rank}{suit}")
        random.shuffle(deck)
        return deck
    
    def deal_initial(self):
        self.player = [self.deck.pop(), self.deck.pop()]
        self.dealer = [self.deck.pop(), self.deck.pop()]
    
    def hit(self):
        if not self.finished:
            self.player.append(self.deck.pop())
            if self.get_hand_value(self.player) > 21:
                self.finished = True
                self.result = "💥 Перебор! Вы проиграли!"
    
    def stand(self):
        if not self.finished:
            self.finished = True
            while self.get_hand_value(self.dealer) < 17:
                self.dealer.append(self.deck.pop())
            
            player_value = self.get_hand_value(self.player)
            dealer_value = self.get_hand_value(self.dealer)
            
            if dealer_value > 21:
                self.result = "🎉 Дилер перебрал! Вы выиграли!"
            elif player_value > dealer_value:
                self.result = "🎉 Вы выиграли!"
            elif player_value < dealer_value:
                self.result = "😔 Дилер выиграл!"
            else:
                self.result = "🤝 Ничья!"
    
    def surrender(self):
        if not self.finished:
            self.finished = True
            self.result = "🏳️ Вы сдались!"
    
    def get_hand_value(self, hand):
        value = 0
        aces = 0
        
        for card in hand:
            rank = card[:-1]  # Убираем масть
            card_value = VALUES[rank]
            if card_value == 11:
                aces += 1
            else:
                value += card_value
        
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
        
        return value
    
    def get_display_text(self):
        player_value = self.get_hand_value(self.player)
        dealer_value = self.get_hand_value(self.dealer)
        
        text = f"🎲 **Блэкджек**\n\n"
        text += f"👤 **Ваши карты:** {' '.join(self.player)} = {player_value}\n"
        
        if self.finished:
            text += f"🤖 **Карты дилера:** {' '.join(self.dealer)} = {dealer_value}\n\n"
            text += f"**Результат:** {self.result}"
        else:
            text += f"🤖 **Карта дилера:** {self.dealer[0]} ?\n\n"
            text += "Выберите действие:"
        
        return text

def get_keyboard(finished=False):
    if finished:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔄 Сыграть ещё", payload="restart")]]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🃏 Взять", payload="hit"),
                InlineKeyboardButton(text="✋ Стоп", payload="stand"),
                InlineKeyboardButton(text="🏳️ Сдаться", payload="surrender"),
            ]
        ]
    )

async def main():
    async with Bot(token=TOKEN) as bot:
        dp = Dispatcher(bot)

        @dp.message_handler(F.command == "start")
        async def start(ctx: Context):
            GAMES[ctx.user_id] = GameState()
            game = GAMES[ctx.user_id]
            game.deal_initial()
            
            await ctx.reply(
                game.get_display_text(),
                reply_markup=get_keyboard()
            )

        @dp.callback_query_handler(F.payload == "hit")
        async def hit_handler(ctx: Context):
            if ctx.user_id not in GAMES:
                await ctx.answer_callback("❌ Игра не найдена. Начните новую игру!")
                return
            
            game = GAMES[ctx.user_id]
            game.hit()
            
            await ctx.answer_callback("🃏 Карта взята!")
            await ctx.edit_message(
                game.get_display_text(),
                reply_markup=get_keyboard(game.finished)
            )

        @dp.callback_query_handler(F.payload == "stand")
        async def stand_handler(ctx: Context):
            if ctx.user_id not in GAMES:
                await ctx.answer_callback("❌ Игра не найдена. Начните новую игру!")
                return
            
            game = GAMES[ctx.user_id]
            game.stand()
            
            await ctx.answer_callback("✋ Остановились!")
            await ctx.edit_message(
                game.get_display_text(),
                reply_markup=get_keyboard(game.finished)
            )

        @dp.callback_query_handler(F.payload == "surrender")
        async def surrender_handler(ctx: Context):
            if ctx.user_id not in GAMES:
                await ctx.answer_callback("❌ Игра не найдена. Начните новую игру!")
                return
            
            game = GAMES[ctx.user_id]
            game.surrender()
            
            await ctx.answer_callback("🏳️ Сдались!")
            await ctx.edit_message(
                game.get_display_text(),
                reply_markup=get_keyboard(game.finished)
            )

        @dp.callback_query_handler(F.payload == "restart")
        async def restart_handler(ctx: Context):
            GAMES[ctx.user_id] = GameState()
            game = GAMES[ctx.user_id]
            game.deal_initial()
            
            await ctx.answer_callback("🔄 Новая игра!")
            await ctx.edit_message(
                game.get_display_text(),
                reply_markup=get_keyboard()
            )

        print("🎰 Блэкджек бот запущен!")
        await bot.polling(dispatcher=dp)

if __name__ == "__main__":
    asyncio.run(main())
```

**Что демонстрирует:**
- Работу с `Inline` клавиатурами и `Callback` обработчиками
- Использование `MagicFilter` (`F.payload == "..."`) для фильтрации `callback`
- Управление состоянием игры для каждого пользователя (`GAMES` словарь)
- Редактирование сообщений (`ctx.edit_message`)

---

## 3. Router система (Модульная архитектура) 🏗️

Пример показывает, как использовать роутеры для разделения логики бота на независимые модули (команды, callbacks, события).

```python
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
```

**Что демонстрирует:**
- Разделение обработчиков на логические блоки с помощью `Router`
- Подключение роутеров к главному диспетчеру (`dp.include_router`)
- Обработку системных событий (`bot_started`, `user_added`, `chat_member_updated`)

---

## 4. Бот-секретарь с Inline клавиатурами  secretary

Бот для управления задачами с разными уровнями доступа.

```python
"""
Бот-секретарь - исправленный рабочий пример
Демонстрирует продвинутые возможности библиотеки AsyncMaxBot SDK 1.4.2:
- Inline клавиатуры
- Callback обработка
- MagicFilter система
- Router система
- Middleware
"""
import asyncio
from maxbot import Bot, Dispatcher, Router, F, Context
from maxbot.max_types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "YOUR_TOKEN_HERE"

# База данных задач (in-memory)
TASKS = {
    1: {"title": "Подготовить отчет", "status": "в процессе"},
    2: {"title": "Заказать пиццу", "status": "новая"},
    3: {"title": "Позвонить клиенту", "status": "выполнена"},
}

# --- Роутер для команд ---
commands_router = Router()

@commands_router.message_handler(F.command == "start")
async def start_command(ctx: Context):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список задач", payload="tasks_list")],
            [InlineKeyboardButton(text="➕ Новая задача", payload="new_task")]
        ]
    )
    await ctx.reply("👩‍💼 Бот-секретарь готов к работе. Выберите действие:", reply_markup=keyboard)


# --- Роутер для Callback ---
callback_router = Router()

@callback_router.callback_query_handler(F.payload == "tasks_list")
async def tasks_list_callback(ctx: Context):
    if not TASKS:
        await ctx.answer_callback("📭 Список задач пуст")
        return
    
    response = "📋 **Ваши задачи:**\n\n"
    for task_id, task in TASKS.items():
        icon = "✅" if task["status"] == "выполнена" else "📝"
        response += f"{icon} {task_id}: {task['title']} ({task['status']})\n"
        
    await ctx.answer_callback("📋 Задачи загружены")
    await ctx.edit_message(response)


@callback_router.callback_query_handler(F.payload == "new_task")
async def new_task_callback(ctx: Context):
    await ctx.answer_callback("➕ Создание задачи")
    await ctx.edit_message("📝 Введите название новой задачи:")
    # Здесь можно добавить логику для ожидания ответа пользователя

async def main():
    async with Bot(token=TOKEN) as bot:
        dp = Dispatcher(bot)
        dp.include_router(commands_router)
        dp.include_router(callback_router)
        
        print("👩‍💼 Бот-секретарь запущен!")
        await bot.polling(dispatcher=dp)

if __name__ == "__main__":
    asyncio.run(main())

```

**Что демонстрирует:**
- Создание простого CRUD-подобного интерфейса
- Динамическое формирование списка задач
- Более сложную логику взаимодействия через `callback`


---

### Заключение

Эти примеры демонстрируют все основные возможности AsyncMaxBot SDK версии 1.4.2:
- ✅ **Базовая архитектура** с классами Bot, Dispatcher, Context
- ✅ **Фильтры** через MagicFilter (`F.text`, `F.command`, `F.payload`)
- ✅ **Inline клавиатуры** для интерактивного взаимодействия
- ✅ **Callback обработка** для кнопок
- ✅ **Middleware** для логирования, троттлинга, обработки ошибок
- ✅ **Роутеры** для разделения логики
- ✅ **Обработка событий** (запуск бота, добавление пользователя и т.д.)

Все примеры можно найти в папке `examples` репозитория. 