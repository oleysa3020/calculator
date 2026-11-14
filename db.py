import sqlite3

DB_NAME = 'rates.db'


def init_db() -> None:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rates (
                id INTEGER PRIMARY KEY,
                currency TEXT UNIQUE,
                rate REAL,
                fetched_at TEXT
            )
        ''')
        conn.commit()


def save_rate(id: int, target_currency: str, rate: float, date_str: str) -> None:
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO rates (id, currency, rate, fetched_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            rate = excluded.rate,
            fetched_at = excluded.fetched_at
        """, (id, target_currency, rate, date_str))
        conn.commit()


def get_saved_rate(target_currency: str) -> float:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT rate FROM rates WHERE currency = ?', (target_currency,))
        result = cursor.fetchone()
        return result[0] if result else 0.0
    
