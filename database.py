import sqlite3

DB_NAME = 'agent_v2.db'

def init_db():
    # دالة تأكيدية للتأكد من وجود الجداول
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS preferences (user_id TEXT PRIMARY KEY, fav_airline TEXT, seating TEXT, budget_limit REAL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, origin TEXT, dest TEXT, target_price REAL)''')

def save_preferences(user_id, airline, seating, budget):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR REPLACE INTO preferences VALUES (?, ?, ?, ?)", (user_id, airline, seating, budget))

def get_preferences(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM preferences WHERE user_id = ?", (user_id,))
        return cursor.fetchone()