import csv
from db import get_all_users

def export_users_to_csv(filename='export.csv'):
    users = get_all_users()
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['№', 'Имя', 'Крестики', 'Цветочки'])
        for index, user in enumerate(users, start=1):
            user_id, name, stitches, flowers = user
            writer.writerow([index, name, stitches, flowers])
    return filename