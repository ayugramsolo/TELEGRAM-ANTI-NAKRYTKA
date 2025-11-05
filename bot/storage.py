import sqlite3
from datetime import datetime
from typing import Optional

def init_db(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS purge_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        join_ts TEXT,
        action_ts TEXT,
        join_count INTEGER,
        reason TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS payments_pending (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        chat_id INTEGER,
        ts TEXT
    )
    ''')
    conn.commit()
    return conn

def log_purge(conn, chat_id, user, join_ts, join_count, reason):
    c = conn.cursor()
    c.execute('INSERT INTO purge_logs (chat_id, user_id, username, first_name, join_ts, action_ts, join_count, reason) VALUES (?,?,?,?,?,?,?,?)',
              (chat_id, user.id, getattr(user, 'username', None), getattr(user, 'first_name', None), join_ts.isoformat(), datetime.utcnow().isoformat(), join_count, reason))
    conn.commit()

def add_pending_payment(conn, user, chat_id):
    c = conn.cursor()
    c.execute('INSERT INTO payments_pending (user_id, username, first_name, chat_id, ts) VALUES (?,?,?,?,?)',
              (user.id, getattr(user, 'username', None), getattr(user, 'first_name', None), chat_id, datetime.utcnow().isoformat()))
    conn.commit()
    return c.lastrowid

def list_pending(conn, limit=100):
    c = conn.cursor()
    rows = c.execute('SELECT id, user_id, username, first_name, chat_id, ts FROM payments_pending ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return rows

def remove_pending(conn, pending_id):
    c = conn.cursor()
    c.execute('DELETE FROM payments_pending WHERE id = ?', (pending_id,))
    conn.commit()
