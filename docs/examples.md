# Примеры использования AsyncMaxBot SDK

В этом разделе собраны полноценные примеры ботов, демонстрирующие различные возможности **AsyncMaxBot SDK версии 1.4.1**. Все примеры основаны на реальных файлах из репозитория и показывают лучшие практики использования библиотеки.

---

## 1. Эхо-бот (Базовый пример)

Самый простой пример бота, который повторяет все сообщения пользователя.

```python
"""
Эхо-бот - исправленный рабочий пример
Демонстрирует базовые возможности библиотеки AsyncMaxBot SDK 1.4.0
"""

import asyncio
import os
from maxbot import Bot, Dispatcher, Context, F
from maxbot.filters import command, text
from maxbot.middleware import LoggingMiddleware, ErrorHandlingMiddleware

# Загружаем токен из файла
def get_token():
    token_file = "token.txt"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return os.environ.get("MAXBOT_TOKEN", "YOUR_TOKEN_HERE")

TOKEN = get_token()

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
- Использование inline клавиатур с кнопками
- Обработку callback-запросов
- MagicFilter систему (`F.command`, `F.payload`)
- Редактирование сообщений
- Управление состоянием игры
- Полноценную игровую логику

---

## 3. Router система (Модульная архитектура)

Пример использования Router системы для создания модульной архитектуры.

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
- Создание и использование роутеров
- Изоляцию логики по типам обработчиков
- Обработку расширенных событий (версия 1.4+)
- Модульную архитектуру проекта
- Навигацию по меню с callback

---

## 4. Бот-секретарь с Inline клавиатурами 👔

Полноценный бот-секретарь с inline-клавиатурами, управлением заявками, напоминаниями и статистикой.

```python
"""
Бот-секретарь - стандартная архитектура
Демонстрирует работу с состоянием и данными
"""

import asyncio
import os
from datetime import datetime
from maxbot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.filters import command, text, has_attachment, F
from maxbot.middleware import MiddlewareManager, LoggingMiddleware, ErrorHandlingMiddleware
from maxbot.max_types import Context, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "YOUR_TOKEN_HERE"  # Замените на ваш токен

class SecretaryBot:
    """Бот-секретарь с стандартной архитектурой"""
    
    def __init__(self):
        self.bot = Bot(TOKEN)
        self.dp = Dispatcher(self.bot)
        self.setup_middleware()
        self.setup_handlers()
        self.applications = []
        self.reminders = {}
    
    def setup_middleware(self):
        """Настройка базового middleware"""
        manager = MiddlewareManager()
        manager.add_middleware(LoggingMiddleware())
        manager.add_middleware(ErrorHandlingMiddleware())
        self.dp.middleware_manager = manager
    
    def get_main_keyboard(self):
        """Главная клавиатура"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📝 Новая заявка", payload="new_application"),
                    InlineKeyboardButton(text="📋 Мои заявки", payload="list_applications")
                ],
                [
                    InlineKeyboardButton(text="⏰ Напоминание", payload="set_reminder"),
                    InlineKeyboardButton(text="📊 Статистика", payload="statistics")
                ],
                [
                    InlineKeyboardButton(text="❓ Помощь", payload="help")
                ]
            ]
        )
    
    def get_application_keyboard(self):
        """Клавиатура для заявок"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📄 Общая", payload="category_general"),
                    InlineKeyboardButton(text="🔧 Техподдержка", payload="category_support")
                ],
                [
                    InlineKeyboardButton(text="💰 Финансы", payload="category_finance"),
                    InlineKeyboardButton(text="📈 Проект", payload="category_project")
                ],
                [
                    InlineKeyboardButton(text="🔙 Назад", payload="back_to_main")
                ]
            ]
        )
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        
        @self.dp.message_handler(command("start"))
        async def start_handler(ctx: Context):
            await ctx.reply(
                f"👋 Здравствуйте, {ctx.user.name}! Я ваш виртуальный секретарь.\n\n"
                "📋 Выберите действие:",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.message_handler(text(["привет", "здравствуйте", "добрый день", "доброе утро", "добрый вечер"]))
        async def greeting_handler(ctx: Context):
            await ctx.reply(
                f"👋 Здравствуйте, {ctx.user.name}! Я ваш виртуальный секретарь.\n\n"
                "📋 Выберите действие:",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.message_handler(text("помощь"))
        async def help_handler(ctx: Context):
            await ctx.reply(
                "❓ Помощь по командам:\n\n"
                "📝 заявка: [текст] — создать новую заявку\n"
                "📋 список заявок — показать ваши заявки\n"
                "⏰ напомни — установить напоминание\n"
                "📊 статистика — показать статистику\n"
                "❓ помощь — эта справка\n\n"
                "💡 Пример: заявка: Нужна консультация по проекту",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.message_handler(text("статистика"))
        async def stats_handler(ctx: Context):
            user_apps = [a for a in self.applications if a['user_id'] == ctx.user_id]
            total_apps = len(self.applications)
            
            await ctx.reply(
                f"📊 Статистика:\n\n"
                f"📋 Всего заявок в системе: {total_apps}\n"
                f"👤 Ваших заявок: {len(user_apps)}\n"
                f"📝 Новых заявок: {len([a for a in user_apps if a['status'] == '📝 Новая'])}\n"
                f"⏰ Активных напоминаний: {len(self.reminders)}",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.message_handler(text("напомни"))
        async def reminder_handler(ctx: Context):
            self.reminders[ctx.user_id] = datetime.now()
            await ctx.reply(
                "⏰ Напоминание установлено!\n"
                "🔔 Я напомню вам проверить заявки через час.",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.message_handler(text("список заявок"))
        async def list_applications_handler(ctx: Context):
            user_apps = [a for a in self.applications if a['user_id'] == ctx.user_id]
            
            if user_apps:
                apps_text = "📋 Ваши заявки:\n\n"
                for app in user_apps[-5:]:  # Последние 5
                    apps_text += f"🔸 #{app['id']} ({app['date']})\n"
                    apps_text += f"   {app['status']} {app['category']}\n"
                    apps_text += f"   📝 {app['text'][:50]}{'...' if len(app['text']) > 50 else ''}\n\n"
                await ctx.reply(apps_text, reply_markup=self.get_main_keyboard())
            else:
                await ctx.reply("📭 У вас пока нет заявок.", reply_markup=self.get_main_keyboard())
        
        @self.dp.message_handler(has_attachment(True))
        async def attachment_handler(ctx: Context):
            """
            Обрабатывает любое сообщение, содержащее вложения.
            Демонстрирует использование фильтра `has_attachment`.
            """
            attachment_types = [att.type for att in ctx.attachments]
            await ctx.reply(f"Вижу вложения! Типы: {', '.join(attachment_types)}. Сохраняю в архив.", reply_markup=self.get_main_keyboard())
            print(f"User {ctx.user_id} sent attachments: {attachment_types}")
        
        @self.dp.message_handler()
        async def no_attachment_handler(ctx: Context):
            """Обрабатывает сообщения без вложений."""
            await ctx.reply("Это сообщение без вложений, я его проигнорирую.", reply_markup=self.get_main_keyboard())
        
        @self.dp.message_handler()
        async def application_handler(ctx: Context):
            if ctx.text.startswith("заявка:"):
                application_text = ctx.text[7:].strip()
                if application_text:
                    app = {
                        "id": len(self.applications) + 1,
                        "user_id": ctx.user_id,
                        "user_name": ctx.user.name,
                        "text": application_text,
                        "status": "📝 Новая",
                        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "category": "📄 Общая"
                    }
                    self.applications.append(app)
                    await ctx.reply(
                        f"✅ Заявка #{app['id']} принята!\n"
                        f"📝 Текст: {application_text}\n"
                        f"📅 Дата: {app['date']}\n"
                        f"📊 Всего заявок: {len(self.applications)}",
                        reply_markup=self.get_main_keyboard()
                    )
                else:
                    await ctx.reply("❌ Пожалуйста, укажите текст заявки после двоеточия.", reply_markup=self.get_main_keyboard())
            else:
                await ctx.reply(
                    "🤔 Не понимаю команду. Напишите 'помощь' для справки.",
                    reply_markup=self.get_main_keyboard()
                )
        
        # Callback обработчики для кнопок
        @self.dp.callback_query_handler(F.payload == "new_application")
        async def new_application_callback(ctx: Context):
            await ctx.answer_callback("📝 Выберите категорию заявки:")
            await ctx.edit_message(
                "📝 Создание новой заявки\n\n"
                "Выберите категорию:",
                reply_markup=self.get_application_keyboard()
            )
        
        @self.dp.callback_query_handler(F.payload == "list_applications")
        async def list_applications_callback(ctx: Context):
            user_apps = [a for a in self.applications if a['user_id'] == ctx.user_id]
            
            if user_apps:
                apps_text = "📋 Ваши заявки:\n\n"
                for app in user_apps[-5:]:  # Последние 5
                    apps_text += f"🔸 #{app['id']} ({app['date']})\n"
                    apps_text += f"   {app['status']} {app['category']}\n"
                    apps_text += f"   📝 {app['text'][:50]}{'...' if len(app['text']) > 50 else ''}\n\n"
                await ctx.answer_callback("📋 Ваши заявки:")
                await ctx.edit_message(apps_text, reply_markup=self.get_main_keyboard())
            else:
                await ctx.answer_callback("📭 У вас пока нет заявок")
                await ctx.edit_message("📭 У вас пока нет заявок.", reply_markup=self.get_main_keyboard())
        
        @self.dp.callback_query_handler(F.payload == "set_reminder")
        async def set_reminder_callback(ctx: Context):
            self.reminders[ctx.user_id] = datetime.now()
            await ctx.answer_callback("⏰ Напоминание установлено!")
            await ctx.edit_message(
                "⏰ Напоминание установлено!\n"
                "🔔 Я напомню вам проверить заявки через час.",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.callback_query_handler(F.payload == "statistics")
        async def statistics_callback(ctx: Context):
            user_apps = [a for a in self.applications if a['user_id'] == ctx.user_id]
            total_apps = len(self.applications)
            
            await ctx.answer_callback("📊 Статистика загружена")
            await ctx.edit_message(
                f"📊 Статистика:\n\n"
                f"📋 Всего заявок в системе: {total_apps}\n"
                f"👤 Ваших заявок: {len(user_apps)}\n"
                f"📝 Новых заявок: {len([a for a in user_apps if a['status'] == '📝 Новая'])}\n"
                f"⏰ Активных напоминаний: {len(self.reminders)}",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.callback_query_handler(F.payload == "help")
        async def help_callback(ctx: Context):
            await ctx.answer_callback("❓ Справка")
            await ctx.edit_message(
                "❓ Помощь по командам:\n\n"
                "📝 заявка: [текст] — создать новую заявку\n"
                "📋 список заявок — показать ваши заявки\n"
                "⏰ напомни — установить напоминание\n"
                "📊 статистика — показать статистику\n"
                "❓ помощь — эта справка\n\n"
                "💡 Пример: заявка: Нужна консультация по проекту",
                reply_markup=self.get_main_keyboard()
            )
        
        @self.dp.callback_query_handler(F.payload == "back_to_main")
        async def back_to_main_callback(ctx: Context):
            await ctx.answer_callback("🔙 Возвращаемся в главное меню")
            await ctx.edit_message(
                f"👋 Здравствуйте, {ctx.user.name}! Я ваш виртуальный секретарь.\n\n"
                "📋 Выберите действие:",
                reply_markup=self.get_main_keyboard()
            )
        
        # Обработчики категорий заявок
        @self.dp.callback_query_handler(F.payload.startswith("category_"))
        async def category_callback(ctx: Context):
            category = ctx.payload.replace("category_", "")
            category_names = {
                "general": "📄 Общая",
                "support": "🔧 Техподдержка", 
                "finance": "💰 Финансы",
                "project": "📈 Проект"
            }
            
            await ctx.answer_callback(f"📝 Категория {category_names.get(category, 'Общая')} выбрана")
            await ctx.edit_message(
                f"📝 Создание заявки в категории: {category_names.get(category, 'Общая')}\n\n"
                "💬 Напишите текст заявки в формате:\n"
                "заявка: [ваш текст]",
                reply_markup=self.get_main_keyboard()
            )
    
    async def check_reminders(self):
        """Проверка напоминаний"""
        current_time = datetime.now()
        for user_id, reminder_time in list(self.reminders.items()):
            if (current_time - reminder_time).seconds > 3600:  # Через час
                await self.bot.send_message(
                    "🔔 Напоминание!\n"
                    "📋 Не забудьте проверить свои заявки.",
                    user_id=user_id
                )
                del self.reminders[user_id]
    
    async def run(self):
        """Запуск бота"""
        print("👔 Бот-секретарь запущен!")
        
        async with self.bot:
            me = await self.bot.get_me()
            print(f"🤖 Бот: {me['name']} (ID: {me['user_id']})")
            
            # Запускаем проверку напоминаний в фоне
            asyncio.create_task(self.reminder_loop())
            
            await self.bot.polling(
                dispatcher=self.dp,
                timeout=1,
                long_polling_timeout=30
            )
    
    async def reminder_loop(self):
        """Цикл проверки напоминаний"""
        while True:
            await self.check_reminders()
            await asyncio.sleep(60)  # Проверяем каждую минуту

async def main():
    bot = SecretaryBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
```

**Что демонстрирует:**
- Полноценную систему inline-клавиатур с навигацией
- Обработку callback-запросов с правильными фильтрами F.payload
- Управление состоянием приложения (заявки, напоминания)
- Обработку вложений с фильтром has_attachment
- Фоновые задачи (проверка напоминаний)
- Редактирование сообщений с клавиатурами
- Категоризацию заявок через callback
- Middleware систему для логирования и обработки ошибок

---

## Заключение

Эти примеры демонстрируют все основные возможности AsyncMaxBot SDK версии 1.4.1:

- ✅ **Базовая архитектура** с классами Bot, Dispatcher, Context
- ✅ **MagicFilter систему** для гибкой фильтрации (F.command, F.payload, F.text)
- ✅ **Inline клавиатуры и callback** обработку с навигацией
- ✅ **Router систему** для модульной архитектуры
- ✅ **Обработку вложений** всех типов с фильтром has_attachment
- ✅ **Расширенные события** (версия 1.4+)
- ✅ **Управление состоянием** приложения (заявки, игры, статистика)
- ✅ **Фоновые задачи** и напоминания
- ✅ **Редактирование сообщений** с клавиатурами
- ✅ **Middleware систему** для логирования и обработки ошибок
- ✅ **Полную типизацию** с Pydantic

**Включенные примеры:**
1. **Эхо-бот** — базовые возможности и обработка сообщений
2. **Блэкджек** — игры с inline-клавиатурами и callback
3. **Router система** — модульная архитектура и расширенные события  
4. **Бот-секретарь** — полноценное приложение с управлением состоянием

Все примеры полностью рабочие и готовы к использованию. Просто замените `YOUR_TOKEN_HERE` на реальный токен вашего бота и запускайте! 