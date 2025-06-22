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