import asyncio
from maxbot import Bot, Dispatcher, Context, F
from maxbot.max_types import InlineKeyboardMarkup, InlineKeyboardButton
import random

TOKEN = "YOUR_TOKEN_HERE"  # Замените на ваш токен

# Карты и значения
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUES = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}

# --- Игровое состояние ---
GAMES = {}

class GameState:
    def __init__(self):
        self.deck = self._create_deck()
        self.player = []
        self.dealer = []
        self.finished = False
        self.result = None
        self.deal()

    def _create_deck(self):
        deck = [(r, s) for r in RANKS for s in SUITS] * 4
        random.shuffle(deck)
        return deck

    def deal_card(self, hand):
        hand.append(self.deck.pop())

    def deal(self):
        self.deal_card(self.player)
        self.deal_card(self.dealer)
        self.deal_card(self.player)
        self.deal_card(self.dealer)

    def hand_value(self, hand):
        value = sum(VALUES[r] for r, _ in hand)
        # Корректировка для тузов
        aces = sum(1 for r, _ in hand if r == "A")
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def is_blackjack(self, hand):
        return len(hand) == 2 and self.hand_value(hand) == 21

    def is_bust(self, hand):
        return self.hand_value(hand) > 21

    def dealer_play(self):
        while self.hand_value(self.dealer) < 17:
            self.deal_card(self.dealer)

    def finish(self):
        self.finished = True
        self.dealer_play()
        p, d = self.hand_value(self.player), self.hand_value(self.dealer)
        if self.is_bust(self.player):
            self.result = "Вы проиграли! Перебор."
        elif self.is_bust(self.dealer):
            self.result = "Вы выиграли! У дилера перебор."
        elif p > d:
            self.result = "Вы выиграли!"
        elif p < d:
            self.result = "Вы проиграли!"
        else:
            self.result = "Ничья."

    def surrender(self):
        self.finished = True
        self.result = "Вы сдались. Половина ставки возвращена."

    def render_hand(self, hand):
        return " ".join(f"{r}{s}" for r, s in hand)

    def render_state(self, hide_dealer=False):
        msg = f"Ваши карты: {self.render_hand(self.player)} (сумма: {self.hand_value(self.player)})\n"
        if hide_dealer:
            msg += f"Карты дилера: {self.dealer[0][0]}{self.dealer[0][1]} ??"
        else:
            msg += f"Карты дилера: {self.render_hand(self.dealer)} (сумма: {self.hand_value(self.dealer)})"
        return msg

# --- Клавиатуры ---
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

# --- Бот ---
async def main():
    async with Bot(token=TOKEN) as bot:
        dp = Dispatcher(bot)

        @dp.message_handler(F.text == "/start")
        async def start(ctx: Context):
            GAMES[ctx.user_id] = GameState()
            game = GAMES[ctx.user_id]
            text = "🎲 Блэкджек!\n" + game.render_state(hide_dealer=True)
            await ctx.reply(text, reply_markup=get_keyboard())

        @dp.callback_query_handler(F.payload.in_(["hit", "stand", "surrender", "restart"]))
        async def handle_action(ctx: Context):
            user_id = ctx.user_id
            if ctx.payload == "restart":
                GAMES[user_id] = GameState()
                game = GAMES[user_id]
                text = "🔄 Новая игра!\n" + game.render_state(hide_dealer=True)
                await ctx.edit_message(text, reply_markup=get_keyboard())
                return
            game = GAMES.get(user_id)
            if not game or game.finished:
                await ctx.answer("Игра не найдена. Нажмите /start.")
                return
            if ctx.payload == "hit":
                game.deal_card(game.player)
                if game.is_bust(game.player):
                    game.finish()
                    text = game.render_state() + f"\n\n💥 {game.result}"
                    await ctx.edit_message(text, reply_markup=get_keyboard(finished=True))
                else:
                    await ctx.edit_message(game.render_state(hide_dealer=True), reply_markup=get_keyboard())
            elif ctx.payload == "stand":
                game.finish()
                text = game.render_state() + f"\n\n🏁 {game.result}"
                await ctx.edit_message(text, reply_markup=get_keyboard(finished=True))
            elif ctx.payload == "surrender":
                game.surrender()
                text = game.render_state() + f"\n\n🏳️ {game.result}"
                await ctx.edit_message(text, reply_markup=get_keyboard(finished=True))

        print("Бот Блэкджек с клавиатурой запущен!")
        await bot.polling(dispatcher=dp)

if __name__ == "__main__":
    asyncio.run(main()) 