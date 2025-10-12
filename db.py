import sqlite3

DB_NAME = 'garden.db'

def with_db_connection(func):
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            result = func(cursor, conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    return wrapper

@with_db_connection
def init_db(c, conn):
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        stitches INTEGER DEFAULT 0,
        flowers TEXT DEFAULT '',
        caterpillars INTEGER DEFAULT 0
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_stitches ON users (stitches DESC)')

@with_db_connection
def add_user(c, conn, user_id, name):
    c.execute('INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)', (user_id, name))

@with_db_connection
def update_stitches(c, conn, user_id, amount):
    c.execute('UPDATE users SET stitches = stitches + ? WHERE user_id = ?', (amount, user_id))

@with_db_connection
def subtract_stitches(c, conn, user_id, amount):
    c.execute('UPDATE users SET stitches = MAX(stitches - ?, 0) WHERE user_id = ?', (amount, user_id))

@with_db_connection
def get_user(c, conn, user_id):
    c.execute('SELECT name, stitches, flowers FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    return result

@with_db_connection
def update_flowers(c, conn, user_id, new_flower):
    user_data = get_user(c, conn, user_id)
    if user_data:
        current_flowers = user_data[2] or ''
        updated = (current_flowers + ' ' + new_flower).strip()
        c.execute('UPDATE users SET flowers = ? WHERE user_id = ?', (updated, user_id))

@with_db_connection
def reset_all(c, conn):
    c.execute('DELETE FROM users')

@with_db_connection
def get_all_users(c, conn):
    c.execute('SELECT * FROM users ORDER BY rowid ASC')
    result = c.fetchall()
    return result

@with_db_connection
def get_top_users(c, conn, limit=10):
    c.execute('SELECT name, stitches, flowers FROM users ORDER BY stitches DESC LIMIT ?', (limit,))
    result = c.fetchall()
    return result

@with_db_connection
def get_caterpillars(c, conn, user_id):
    c.execute('SELECT caterpillars FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    return result[0] if result else 0

@with_db_connection
def increment_caterpillars(c, conn, user_id):
    c.execute('UPDATE users SET caterpillars = caterpillars + 1 WHERE user_id = ?', (user_id,))

@with_db_connection
def get_all_users_with_headers(c, conn) -> tuple[list[str], list[tuple]]:
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    headers = [description[0] for description in c.description]
    return headers, rows