#!/usr/bin/env python3
"""
Пример бота для тестирования универсального метода send_attachment
"""

import asyncio
import json
import os
from maxbot import Bot
from maxbot.dispatcher import Dispatcher
from maxbot.filters import command

# Загружаем токен
def get_token():
    token_file = "token.txt"
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return os.environ.get("MAXBOT_TOKEN", "YOUR_TOKEN_HERE")

TOKEN = get_token()

# Загружаем реальные данные вложений
def load_attachments():
    if os.path.exists("captured_updates.json"):
        with open("captured_updates.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            attachments = []
            
            # Если файл содержит словарь с ключом 'updates', извлекаем список
            if isinstance(data, dict) and 'updates' in data:
                updates = data['updates']
            # Если файл содержит список, используем его как есть
            elif isinstance(data, list):
                updates = data
            else:
                return []
            
            for update in updates:
                if 'message' in update and 'body' in update['message']:
                    body = update['message']['body']
                    if 'attachments' in body and isinstance(body['attachments'], list):
                        attachments.extend(body['attachments'])
            return attachments
    return []

async def main():
    bot = Bot(TOKEN)
    dispatcher = Dispatcher(bot)
    
    @dispatcher.message_handler(command('test_attachment'))
    async def test_attachment(ctx):
        """Тестирует отправку вложения через универсальный метод"""
        attachments = load_attachments()
        
        if not attachments:
            await ctx.reply("Нет сохраненных вложений для тестирования. Отправьте сначала фото/файл/геолокацию.")
            return
        
        # Берем первое вложение для теста
        attachment = attachments[0]
        attachment_type = attachment.get('type', 'unknown')
        
        try:
            # Отправляем вложение обратно через универсальный метод
            result = await bot.send_attachment(
                attachment, 
                chat_id=ctx.message.recipient.chat_id,
                caption=f"Тест отправки {attachment_type} через send_attachment"
            )
            
            await ctx.reply(f"✅ Успешно отправлен {attachment_type}!\nРезультат: {result.get('message_id', 'N/A')}")
            
        except Exception as e:
            await ctx.reply(f"❌ Ошибка отправки {attachment_type}: {str(e)}")
    
    @dispatcher.message_handler(command('test_all_attachments'))
    async def test_all_attachments(ctx):
        """Тестирует все сохраненные вложения"""
        attachments = load_attachments()
        
        if not attachments:
            await ctx.reply("Нет сохраненных вложений для тестирования.")
            return
        
        await ctx.reply(f"Найдено {len(attachments)} вложений. Тестируем...")
        
        success_count = 0
        for i, attachment in enumerate(attachments):
            attachment_type = attachment.get('type', 'unknown')
            
            try:
                result = await bot.send_attachment(
                    attachment,
                    chat_id=ctx.message.recipient.chat_id,
                    caption=f"Тест {i+1}: {attachment_type}"
                )
                success_count += 1
                await asyncio.sleep(1)  # Небольшая пауза между отправками
                
            except Exception as e:
                await ctx.reply(f"❌ Ошибка {attachment_type}: {str(e)}")
        
        await ctx.reply(f"✅ Тестирование завершено! Успешно: {success_count}/{len(attachments)}")
    
    @dispatcher.message_handler(command('show_attachments'))
    async def show_attachments(ctx):
        """Показывает информацию о сохраненных вложениях"""
        attachments = load_attachments()
        
        if not attachments:
            await ctx.reply("Нет сохраненных вложений.")
            return
        
        info = f"Найдено {len(attachments)} вложений:\n\n"
        
        for i, attachment in enumerate(attachments):
            attachment_type = attachment.get('type', 'unknown')
            info += f"{i+1}. Тип: {attachment_type}\n"
            
            if attachment_type in ['image', 'file', 'audio', 'video', 'sticker']:
                payload = attachment.get('payload', {})
                if 'photo_id' in payload:
                    info += f"   photo_id: {payload['photo_id']}\n"
                if 'fileId' in payload:
                    info += f"   fileId: {payload['fileId']}\n"
                if 'token' in payload:
                    info += f"   token: {payload['token'][:10]}...\n"
            
            elif attachment_type == 'location':
                info += f"   lat: {attachment.get('latitude')}, lon: {attachment.get('longitude')}\n"
            
            elif attachment_type == 'share':
                info += f"   url: {attachment.get('url', 'N/A')}\n"
            
            info += "\n"
        
        await ctx.reply(info)
    
    @dispatcher.message_handler(command('help'))
    async def help_command(ctx):
        """Показывает справку"""
        help_text = """
🤖 Attachment Test Bot

Команды:
/test_attachment - Тестирует отправку первого сохраненного вложения
/test_all_attachments - Тестирует все сохраненные вложения
/show_attachments - Показывает информацию о сохраненных вложениях
/help - Показывает эту справку

Отправьте фото/файл/геолокацию чтобы сохранить вложение для тестирования.
        """
        await ctx.reply(help_text)
    
    @dispatcher.message_handler()
    async def echo_handler(ctx):
        """Эхо-обработчик для сохранения вложений"""
        if ctx.has_attachments:
            # Сохраняем вложения в файл
            attachments = ctx.attachments
            if attachments:
                # Загружаем существующие данные
                existing_data = []
                if os.path.exists("captured_updates.json"):
                    with open("captured_updates.json", 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        # Если файл содержит словарь с ключом 'updates', извлекаем список
                        if isinstance(existing_data, dict) and 'updates' in existing_data:
                            existing_data = existing_data['updates']
                        # Если файл содержит список, используем его как есть
                        elif not isinstance(existing_data, list):
                            existing_data = []
                
                # Преобразуем вложения в словари
                attachment_dicts = []
                for att in attachments:
                    # att уже является объектом BaseAttachment
                    if hasattr(att, 'model_dump'):
                        attachment_dicts.append(att.model_dump())
                    elif hasattr(att, 'dict'):
                        attachment_dicts.append(att.dict())
                    else:
                        # Если это уже словарь
                        attachment_dicts.append(att)
                
                # Добавляем новое сообщение с вложениями
                new_update = {
                    'message': {
                        'body': {
                            'attachments': attachment_dicts
                        }
                    }
                }
                existing_data.append(new_update)
                
                # Сохраняем как список
                with open("captured_updates.json", 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                
                await ctx.reply(f"✅ Сохранено {len(attachments)} вложений для тестирования!")
            else:
                await ctx.reply("❌ Не удалось получить вложения из сообщения")
        else:
            await ctx.reply("Отправьте команду /help для справки")

    print("🤖 Attachment Test Bot запущен!")
    print("Используйте /help для справки")
    
    async with bot:
        await bot.polling(dispatcher=dispatcher)

if __name__ == "__main__":
    asyncio.run(main()) 