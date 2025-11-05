import logging, os, asyncio
from aiogram import Bot, Dispatcher, executor, types
import bot.bot_config as config
from .utils import load_keys
from .storage import init_db
from .commands import cmd_start, cmd_buy, buy_callback, cmd_list_pending, cmd_issue, cmd_genkey
from .purge_logic import process_new_members

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

if config.BOT_TOKEN == 'PUT_YOUR_BOT_TOKEN_HERE':
    print('Please set BOT_TOKEN in bot/bot_config.py')
    exit(1)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

# init db
conn = init_db(config.DB_FILE)

# handlers
@dp.message_handler(commands=['start'])
async def _start(message: types.Message):
    await cmd_start(message, config)

@dp.message_handler(commands=['buy'])
async def _buy(message: types.Message):
    await cmd_buy(message, config, conn, bot)

@dp.callback_query_handler(lambda c: c.data=='paid_btn')
async def _paid(call: types.CallbackQuery):
    await buy_callback(call, config, conn, bot)

@dp.message_handler(commands=['list_pending'])
async def _list_pending(message: types.Message):
    # restrict to admin chat if configured
    if config.ADMIN_CHAT_ID and message.chat.id != config.ADMIN_CHAT_ID:
        await message.reply('Команда доступна только администратору.')
        return
    await cmd_list_pending(message, conn)

@dp.message_handler(commands=['issue'])
async def _issue(message: types.Message):
    parts = message.text.split()
    # restrict
    if config.ADMIN_CHAT_ID and message.chat.id != config.ADMIN_CHAT_ID:
        await message.reply('Команда доступна только администратору.')
        return
    await cmd_issue(message, parts, conn, config)

@dp.message_handler(commands=['genkey'])
async def _genkey(message: types.Message):
    parts = message.text.split()
    if config.ADMIN_CHAT_ID and message.chat.id != config.ADMIN_CHAT_ID:
        await message.reply('Команда доступна только администратору.')
        return
    await cmd_genkey(message, parts, config)

@dp.message_handler(commands=['set_auto'])
async def _set_auto(message: types.Message):
    await message.reply('Эта реализация использует глобальные настройки. Для per-key включения/выключения нужно доработать.')

@dp.message_handler(commands=['logs'])
async def _logs(message: types.Message):
    await message.reply('Use /list_pending or check purge_events.db')


@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def on_new_members(message: types.Message):
    await process_new_members(bot, conn, message.chat, message.new_chat_members, config.JOIN_WINDOW_SECONDS, config.JOIN_THRESHOLD)

if __name__ == '__main__':
    print('Starting bot...')
    executor.start_polling(dp, skip_updates=True)
