import sqlite3

DB_NAME = 'garden.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        stitches INTEGER DEFAULT 0,
        flowers TEXT DEFAULT '',
        caterpillars INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def add_user(user_id, name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)', (user_id, name))
    conn.commit()
    conn.close()

def update_stitches(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET stitches = stitches + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def subtract_stitches(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET stitches = MAX(stitches - ?, 0) WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name, stitches, flowers FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def update_flowers(user_id, new_flower):
    user = get_user(user_id)
    if user:
        current_flowers = user[2] or ''
        updated = (current_flowers + ' ' + new_flower).strip()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('UPDATE users SET flowers = ? WHERE user_id = ?', (updated, user_id))
        conn.commit()
        conn.close()

def reset_all():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM users')
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY rowid ASC')
    result = c.fetchall()
    conn.close()
    return result

def get_top_users(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name, stitches, flowers FROM users ORDER BY stitches DESC LIMIT ?', (limit,))
    result = c.fetchall()
    conn.close()
    return result
def get_caterpillars(user_id):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT caterpillars FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0

def increment_caterpillars(user_id):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('UPDATE users SET caterpillars = caterpillars + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()