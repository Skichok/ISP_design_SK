import sqlite3
import os
import matplotlib.pyplot as plt
from matplotlib.table import Table
from matplotlib.ticker import MaxNLocator
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Путь к базе данных и изображениям
db_path = './User_data/schedules.db'
pic_path = './User_data/pic'

# Создание директории для изображений, если ее нет
os.makedirs(pic_path, exist_ok=True)


# Функция для создания новой таблицы для пользователя
def new_table(username, user_id, timestamp):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создание таблицы для нового пользователя, если она не существует
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS user_{user_id} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        timestamp TEXT,
        monday TEXT,
        tuesday TEXT,
        wednesday TEXT,
        thursday TEXT,
        friday TEXT,
        saturday TEXT,
        sunday TEXT
    )
    ''')

    # Вставка записи в таблицу с пользователем
    cursor.execute(f'''
    INSERT INTO user_{user_id} (username, timestamp, monday, tuesday, wednesday, thursday, friday, saturday, sunday)
    VALUES (?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
    ''', (username, timestamp))

    conn.commit()
    conn.close()


# Функция для добавления события
def add_event(user_id, day, time, notification_status=True):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Добавление события в нужный день
    cursor.execute(f'''
    UPDATE user_{user_id}
    SET {day} = ?
    WHERE id = (SELECT MAX(id) FROM user_{user_id})
    ''', (f'{time} - Notification: {notification_status}',))

    conn.commit()
    conn.close()


# Функция для удаления события
def remove_event(user_id, day, time):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Удаление события из таблицы
    cursor.execute(f'''
    UPDATE user_{user_id}
    SET {day} = NULL
    WHERE id = (SELECT MAX(id) FROM user_{user_id}) AND {day} LIKE ?
    ''', (f'%{time}%',))

    conn.commit()
    conn.close()


# Функция для получения таблицы и рисования на изображении
def get_table(user_id, day="ALL"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверка существования таблицы
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='user_{user_id}'")
    if not cursor.fetchone():
        print("Table does not exist for user:", user_id)
        return

    # Получение данных из таблицы
    cursor.execute(f"SELECT * FROM user_{user_id} WHERE id = (SELECT MAX(id) FROM user_{user_id})")
    row = cursor.fetchone()

    if not row:
        print("No data found for user:", user_id)
        return

    # Проверка корректности параметра day
    if day != "ALL" and day not in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        print("Invalid day. Please specify a valid day or 'ALL'.")
        return

    # Рисование таблицы
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')
    table = Table(ax, bbox=[0, 0, 1, 1])

    # Добавление столбцов и строк
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    data = [row[3:], ]  # Извлекаем только данные о расписании, пропуская id, username, timestamp

    for i, col in enumerate(['Day', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
        table.add_cell(0, i, 1.0 / 8, 0.1, text=col, loc='center', facecolor='white')

    for i, event in enumerate(data[0]):
        # Проверка на None
        if event is None:
            event = ""  # Если события нет, оставляем пустое место
        table.add_cell(i + 1, 0, 1.0 / 8, 0.1, text=days_of_week[i].capitalize(), loc='center', facecolor='white')
        table.add_cell(i + 1, 1, 1.0 / 8, 0.1, text=event, loc='center', facecolor='black', edgecolor='white')

    ax.add_table(table)
    plt.tight_layout()

    # Сохранение таблицы
    timestamp = row[2]
    username = row[1]
    img_filename = f"{pic_path}/{username}_{user_id}_{timestamp}_table.png"
    plt.savefig(img_filename, bbox_inches='tight', pad_inches=0.1)
    plt.close()

    # Статистика по дням
    time_spent = {day: 0 for day in days_of_week}
    for i, event in enumerate(data[0]):
        if event:
            time_spent[days_of_week[i]] += 1  # Примерное время в часах для каждого дня

    # Рисование графика
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(time_spent.keys(), time_spent.values(), color='skyblue')
    ax.set_title(f"Time Spent per Day for User {user_id}")
    ax.set_xlabel("Days")
    ax.set_ylabel("Events Scheduled")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Сохранение графика
    graph_filename = f"{pic_path}/{username}_{user_id}_{timestamp}_graph.png"
    plt.savefig(graph_filename, bbox_inches='tight', pad_inches=0.1)
    plt.close()

    conn.close()

# Пример использования:
new_table('user1', 12345, '2025-01-21')
add_event(12345, 'monday', '10:00', True)
get_table(12345, 'ALL')  # Визуализирует таблицу и график для пользователя с id 12345
