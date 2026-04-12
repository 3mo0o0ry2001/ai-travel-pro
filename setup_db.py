import sqlite3

def setup():
    conn = sqlite3.connect('agent_v2.db')
    # جدول التفضيلات
    conn.execute('''CREATE TABLE IF NOT EXISTS preferences 
                    (user_id TEXT PRIMARY KEY, fav_airline TEXT, seating TEXT, budget_limit REAL)''')
    # جدول المراقبة
    conn.execute('''CREATE TABLE IF NOT EXISTS watchlist 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, origin TEXT, dest TEXT, target_price REAL)''')
    conn.commit()
    conn.close()
    print("Database Ready! 🚀")

if __name__ == "__main__":
    setup()