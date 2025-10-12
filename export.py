import csv
from typing import List, Tuple, Any
from db import get_all_users

def export_users_to_csv(filename: str = 'export.csv') -> str:
    """Exports all user data from the database to a CSV file.

    Args:
        filename (str): The name of the CSV file to create.

    Returns:
        str: The name of the created CSV file.
    """
    users: List[Tuple[Any, ...]] = get_all_users()
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['№', 'Имя', 'Крестики', 'Цветочки'])
        for index, user in enumerate(users, start=1):
            user_id: Any
            name: str
            stitches: int
            flowers: str
            user_id, name, stitches, flowers = user  # Type hints for unpacking
            writer.writerow([index, name, stitches, flowers])
    return filename