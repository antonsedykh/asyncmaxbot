# examples/handlers/image_sender.py
from maxbot import Router, Context, F

router = Router()

@router.message_handler(F.text == "/image")
async def handle_image(ctx: Context):
    # В реальном боте здесь была бы логика отправки картинки
    await ctx.reply("🖼️ Представьте, что здесь красивая картинка.") 