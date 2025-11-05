from collections import defaultdict, deque
from datetime import datetime, timedelta
import asyncio
from .storage import log_purge

recent_joins = defaultdict(lambda: deque())

async def process_new_members(bot, conn, chat, new_members, join_window_seconds, join_threshold):
    now = datetime.utcnow()
    dq = recent_joins[chat.id]
    for user in new_members:
        dq.append((user, now))
    # remove old
    window = timedelta(seconds=join_window_seconds)
    while dq and (now - dq[0][1]) > window:
        dq.popleft()
    join_count = len(dq)
    if join_count > join_threshold:
        to_remove = list(dq)
        removed = []
        for user, ts in to_remove:
            try:
                member = await bot.get_chat_member(chat.id, user.id)
                # skip admins/owners
                if getattr(member, 'status', None) in ('administrator','creator') or getattr(member, 'is_chat_admin', lambda: False)():
                    # do not remove admins
                    log_purge(conn, chat.id, user, ts, join_count, 'skipped_admin')
                    continue
            except Exception:
                pass
            try:
                await bot.kick_chat_member(chat.id, user.id)
                await asyncio.sleep(0.2)
                await bot.unban_chat_member(chat.id, user.id)
                log_purge(conn, chat.id, user, ts, join_count, 'auto_threshold_purge')
                removed.append(user.id)
            except Exception as e:
                log_purge(conn, chat.id, user, ts, join_count, f'auto_failed:{e}')
        recent_joins[chat.id].clear()
        try:
            await bot.send_message(chat.id, f'Автоочистка: обнаружено {join_count} новых участников. Удалено: {len(removed)}')
        except Exception:
            pass
