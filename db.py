import sqlite3
from typing import Callable, Any, Tuple, List

DB_NAME: str = 'garden.db'

def with_db_connection(func: Callable) -> Callable:
    """Decorator to manage database connection for a function.

    Args:
        func (Callable): The function to wrap.

    Returns:
        Callable: The wrapped function.
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        conn: sqlite3.Connection = sqlite3.connect(DB_NAME)
        cursor: sqlite3.Cursor = conn.cursor()
        try:
            result: Any = func(cursor, conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    return wrapper

@with_db_connection
def init_db(c: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """Initializes the database by creating the users table if it doesn't exist and adds an index.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
    """
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        stitches INTEGER DEFAULT 0,
        flowers TEXT DEFAULT '',
        caterpillars INTEGER DEFAULT 0
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_stitches ON users (stitches DESC)')

@with_db_connection
def add_user(c: sqlite3.Cursor, conn: sqlite3.Connection, user_id: int, name: str) -> None:
    """Adds a new user to the database if they don't already exist.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
        user_id (int): The ID of the user.
        name (str): The name of the user.
    """
    c.execute('INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)', (user_id, name))

@with_db_connection
def update_stitches(c: sqlite3.Cursor, conn: sqlite3.Connection, user_id: int, amount: int) -> None:
    """Updates the number of stitches for a user.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
        user_id (int): The ID of the user.
        amount (int): The amount of stitches to add.
    """
    c.execute('UPDATE users SET stitches = stitches + ? WHERE user_id = ?', (amount, user_id))

@with_db_connection
def subtract_stitches(c: sqlite3.Cursor, conn: sqlite3.Connection, user_id: int, amount: int) -> None:
    """Subtracts stitches from a user, ensuring the total doesn't go below zero.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
        user_id (int): The ID of the user.
        amount (int): The amount of stitches to subtract.
    """
    c.execute('UPDATE users SET stitches = MAX(stitches - ?, 0) WHERE user_id = ?', (amount, user_id))

@with_db_connection
def get_user(c: sqlite3.Cursor, conn: sqlite3.Connection, user_id: int) -> Tuple[str, int, str] | None:
    """Retrieves user data by user ID.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
        user_id (int): The ID of the user.

    Returns:
        Tuple[str, int, str] | None: A tuple containing (name, stitches, flowers) or None if user not found.
    """
    c.execute('SELECT name, stitches, flowers FROM users WHERE user_id = ?', (user_id,))
    result: Tuple[str, int, str] | None = c.fetchone()
    return result

@with_db_connection
def update_flowers(c: sqlite3.Cursor, conn: sqlite3.Connection, user_id: int, new_flower: str) -> None:
    """Adds a new flower to a user's bouquet.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
        user_id (int): The ID of the user.
        new_flower (str): The emoji string of the new flower.
    """
    user_data: Tuple[str, int, str] | None = get_user(c, conn, user_id)
    if user_data:
        current_flowers: str = user_data[2] or ''
        updated_flowers: str = (current_flowers + ' ' + new_flower).strip()
        c.execute('UPDATE users SET flowers = ? WHERE user_id = ?', (updated_flowers, user_id))

@with_db_connection
def reset_all(c: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """Deletes all user data from the database.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
    """
    c.execute('DELETE FROM users')

@with_db_connection
def get_all_users(c: sqlite3.Cursor, conn: sqlite3.Connection) -> List[Tuple[Any, ...]]:
    """Retrieves all users from the database.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.

    Returns:
        List[Tuple[Any, ...]]: A list of tuples, each representing a user.
    """
    c.execute('SELECT * FROM users ORDER BY rowid ASC')
    result: List[Tuple[Any, ...]] = c.fetchall()
    return result

@with_db_connection
def get_top_users(c: sqlite3.Cursor, conn: sqlite3.Connection, limit: int = 10) -> List[Tuple[str, int, str]]:
    """Retrieves the top users based on stitches.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
        limit (int): The maximum number of top users to retrieve.

    Returns:
        List[Tuple[str, int, str]]: A list of tuples, each containing (name, stitches, flowers).
    """
    c.execute('SELECT name, stitches, flowers FROM users ORDER BY stitches DESC LIMIT ?', (limit,))
    result: List[Tuple[str, int, str]] = c.fetchall()
    return result

@with_db_connection
def get_caterpillars(c: sqlite3.Cursor, conn: sqlite3.Connection, user_id: int) -> int:
    """Retrieves the number of caterpillars for a specific user.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
        user_id (int): The ID of the user.

    Returns:
        int: The number of caterpillars for the user, or 0 if not found.
    """
    c.execute('SELECT caterpillars FROM users WHERE user_id = ?', (user_id,))
    result: Tuple[int] | None = c.fetchone()
    return result[0] if result else 0

@with_db_connection
def increment_caterpillars(c: sqlite3.Cursor, conn: sqlite3.Connection, user_id: int) -> None:
    """Increments the caterpillar count for a specific user.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.
        user_id (int): The ID of the user.
    """
    c.execute('UPDATE users SET caterpillars = caterpillars + 1 WHERE user_id = ?', (user_id,))

@with_db_connection
def get_all_users_with_headers(c: sqlite3.Cursor, conn: sqlite3.Connection) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """Retrieves all user data along with column headers.

    Args:
        c (sqlite3.Cursor): The database cursor.
        conn (sqlite3.Connection): The database connection.

    Returns:
        Tuple[List[str], List[Tuple[Any, ...]]]: A tuple containing a list of headers and a list of user data tuples.
    """
    c.execute("SELECT * FROM users")
    rows: List[Tuple[Any, ...]] = c.fetchall()
    headers: List[str] = [description[0] for description in c.description]
    return headers, rows