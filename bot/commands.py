from aiogram import types
from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from .utils import load_keys, save_key
from .storage import add_pending_payment, list_pending, remove_pending
import secrets
import asyncio

async def cmd_start(message: types.Message, config):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply('Привет! Чтобы активировать бот, пришлите: /start <ключ>') 
        return
    key = parts[1].strip()
    keys = load_keys(config.KEYS_FILE)
    if key not in keys:
        await message.reply('Неверный ключ. Чтобы купить ключ: /buy') 
        return
    await message.reply('Ключ принят. Бот активирован. Добавьте бота в группу и дайте права администратора с баном участников.')

async def cmd_buy(message: types.Message, config, conn, bot):
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Я оплатил (нажать после платежа)', callback_data='paid_btn'))
    text = f'Оплата через {config.OWNER_CONTACT}\n\n1) Перейдите к продавцу и оплатите согласно инструкции.\n2) После оплаты вернитесь сюда и нажмите кнопку снизу — это создаст запрос на проверку платежа.\n\nПоддержка автоматической интеграции: крипто-боты (B) и Telegram Payments (C) — для автоматической выдачи ключей требуется подключение внешнего провайдера.'
    await message.reply(text, reply_markup=kb)

async def buy_callback(call: types.CallbackQuery, config, conn, bot):
    user = call.from_user
    pending_id = add_pending_payment(conn, user, call.message.chat.id)
    await call.answer('Запрос отмечен. Ожидайте подтверждения продавца.')
    # notify admin chat if set
    if config.ADMIN_CHAT_ID:
        await bot.send_message(config.ADMIN_CHAT_ID, f'Новый запрос оплаты #{pending_id} от {user.id} @{getattr(user,"username",None)} {getattr(user,"first_name",None)}. Используйте /list_pending чтобы увидеть.')
    else:
        # if no admin chat - leave note in group
        try:
            await bot.send_message(call.message.chat.id, f'Запрос создан: id {pending_id}. Продавец должен подтвердить оплату.')
        except Exception:
            pass

async def cmd_list_pending(message: types.Message, conn):
    rows = list_pending(conn)
    if not rows:
        await message.reply('Нет ожидающих платежей.')
        return
    lines = [] 
    for r in rows:
        lines.append(f'#{r[0]} user={r[1]} @{r[2]} name={r[3]} chat={r[4]} at={r[5]}')
    text = '\n'.join(lines)
    if len(text) > 3800:
        path='pending.txt'
        with open(path,'w',encoding='utf-8') as f: f.write(text)
        await message.reply_document(open(path,'rb'))
        os.remove(path)
    else:
        await message.reply(text)

async def cmd_issue(message: types.Message, parts, conn, config):
    # Usage: /issue <pending_id> OR /issue user_id
    if len(parts) < 2:
        await message.reply('Использование: /issue <pending_id>') 
        return
    target = parts[1]
    try:
        pid = int(target)
        # find pending
        rows = list_pending(conn, limit=1000)
        row = next((r for r in rows if r[0]==pid), None)
        if not row:
            await message.reply('Pending id не найден.')
            return
        user_id = row[1]
        # generate key
        new_key = secrets.token_urlsafe(16)
        save_key(config.KEYS_FILE, new_key)
        # remove pending
        remove_pending(conn, pid)
        await message.bot.send_message(user_id, f'Ваш ключ: `{new_key}`', parse_mode=ParseMode.MARKDOWN)
        await message.reply(f'Ключ выдан и отправлен пользователю {user_id}.')
    except ValueError:
        await message.reply('Неверный id.')

async def cmd_genkey(message: types.Message, parts, config):
    # protected by admin secret in caller (we will check text for secret)
    if len(parts) < 2:
        await message.reply('Использование: /genkey <admin_secret>') 
        return
    if parts[1] != config.ADMIN_SECRET:
        await message.reply('Неверный административный секрет.')
        return
    new_key = secrets.token_urlsafe(16)
    save_key(config.KEYS_FILE, new_key)
    await message.reply(f'Новый ключ сгенерирован: `{new_key}`', parse_mode=ParseMode.MARKDOWN)
