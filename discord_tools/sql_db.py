import sqlite3
import asyncio
from contextlib import asynccontextmanager

# Асинхронный контекстный менеджер для блокировки
@asynccontextmanager
async def database_lock():
    lock = asyncio.Lock()
    async with lock:
        yield lock
async def set_get_database_async(section, key, value=None):
    """
    не поддерживается массив секций!
    изменить - await set_get_database_async("test", keys, values)
    получить - await set_get_database_async("test", "500")
    """
    db_path = 'config.db'
    section = str(section)

    async with database_lock():
        # Create SQLite connection and cursor
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create a table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section TEXT,
                key TEXT NOT NULL UNIQUE,
                value TEXT
            )
        ''')
        conn.commit()

        # If both key and value are arrays, insert multiple key-value pairs
        if isinstance(key, list) and isinstance(value, list):
            data = [(section, str(k), str(v)) for k, v in zip(key, value)]
            cursor.executemany('INSERT OR REPLACE INTO config (section, key, value) VALUES (?, ?, ?)', data)
            conn.commit()
        else:
            key = str(key)

            # If value is not provided, fetch the value for the key
            if value is None:
                cursor.execute('SELECT value FROM config WHERE section = ? AND key = ?', (section, key))
                return_value = cursor.fetchone()
                return return_value[0] if return_value else None

            # Set the value for the key
            cursor.execute('INSERT OR REPLACE INTO config (section, key, value) VALUES (?, ?, ?)', (section, key, str(value)))
            conn.commit()

        # Close the connection
        conn.close()


async def get_all_config_async():
    """
    returns massive of sections, keys and values

    :return: section, key, value
    """
    db_path = 'config.db'

    # Create SQLite connection and cursor
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all key-value pairs from the config table
    cursor.execute('SELECT section, key, value FROM config')
    result = cursor.fetchall()

    # Close the connection
    conn.close()

    return result