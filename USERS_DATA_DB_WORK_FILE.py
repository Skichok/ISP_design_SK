import sqlite3
import os
import matplotlib.pyplot as plt
from datetime import datetime

# Путь к базе данных и изображениям
db_path = './User_data/schedules.db'
pic_path = './User_data/pic'

# Создание директории для изображений, если ее нет
os.makedirs(pic_path, exist_ok=True)


# Функция для создания новой таблицы для пользователя
def new_table(username, user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверка, существует ли уже таблица для данного пользователя
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='user_{user_id}'")
    if cursor.fetchone():
        print(f"user {user_id} already exists")
        conn.close()
        return

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
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Уникальный timestamp
    cursor.execute(f'''
    INSERT INTO user_{user_id} (username, timestamp, monday, tuesday, wednesday, thursday, friday, saturday, sunday)
    VALUES (?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
    ''', (username, timestamp))

    conn.commit()
    conn.close()


def remove_table(user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверка существования таблицы для пользователя
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='user_{user_id}'")
    if not cursor.fetchone():
        print(f"Table for user {user_id} does not exist.")
        conn.close()
        return

    # Удаление таблицы пользователя
    cursor.execute(f"DROP TABLE IF EXISTS user_{user_id}")
    conn.commit()

    print(f"Table for user {user_id} has been removed.")
    conn.close()


# Функция для добавления события
def add_event(user_id, day, time, event_name, notification_status=True):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверяем существование таблицы для пользователя
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='user_{user_id}'")
    if not cursor.fetchone():
        print(f"Table for user {user_id} does not exist.")
        conn.close()
        return

    # Получаем текущее значение для указанного дня
    cursor.execute(f"SELECT {day} FROM user_{user_id} WHERE id = (SELECT MAX(id) FROM user_{user_id})")
    current_schedule = cursor.fetchone()

    if current_schedule and current_schedule[0]:
        events = current_schedule[0].split(', ')
        for event in events:
            if event.startswith(time):
                print(f"You have {event.split(' - ')[1]} at this time! Delete or move it first.")
                conn.close()
                return

    # Добавляем событие, если конфликта нет
    event = f"{time} - {event_name} - Notification: {notification_status}"
    cursor.execute(f'''
    UPDATE user_{user_id}
    SET {day} = COALESCE({day}, '') || ? || ', '
    WHERE id = (SELECT MAX(id) FROM user_{user_id})
    ''', (event,))

    conn.commit()
    conn.close()
    print(f"Event '{event_name}' added successfully for {day} at {time}.")

def list_user_tables():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Запрос к системной таблице SQLite для получения списка таблиц с именами user_<user_id>
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'user_%'")

    # Получаем все таблицы и выводим их
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])  # Выводим имя таблицы (например, user_12345)

    conn.close()


def view_user_table(user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Проверка существования таблицы для пользователя
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='user_{user_id}'")
    if not cursor.fetchone():
        print(f"Table for user {user_id} does not exist.")
        conn.close()
        return

    # Запрос на извлечение данных из таблицы пользователя
    cursor.execute(f"SELECT * FROM user_{user_id}")
    rows = cursor.fetchall()

    if not rows:
        print(f"No data found for user {user_id}.")
    else:
        # Вывод данных
        for row in rows:
            print(row)

    conn.close()


# Функция для создания графика статистики запланированных событий по дням недели
def stats(user_id, day="ALL", theme="white"):
    unique_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  # stating unique timestamp
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

    # Собираем количество событий по дням недели
    events_count = {day: len(row[i + 3].split(', ')) if row[i + 3] else 0
                    for i, day in
                    enumerate(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])}

    if day != "ALL":
        events_count = {day: events_count[day]}  # Если day не 'ALL', фильтруем по указанному дню

    # Рисование графика
    fig, ax = plt.subplots(figsize=(8, 6))

    if theme == "black":
        ax.set_facecolor("black")
        fig.patch.set_facecolor("black")
        ax.tick_params(colors="white")
        ax.spines[:].set_color("white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        bar_color = "lightblue"
    else:
        bar_color = "skyblue"

    ax.bar(events_count.keys(), events_count.values(), color=bar_color)
    ax.set_title(f"Number of Events Scheduled for User {user_id}")
    ax.set_xlabel("Days")
    ax.set_ylabel("Number of Events")

    # Сохранение графика
    timestamp = row[2]
    username = row[1]
    graph_filename = f"{pic_path}/{username}_{user_id}_{timestamp}_{unique_timestamp}_stats.png"
    plt.savefig(graph_filename, bbox_inches='tight', pad_inches=0.1)
    plt.close()

    conn.close()


# Пример использования:
new_table('user1', 12345)
add_event(12345, 'monday', '08:00', 'Wake up', True)
add_event(12345, 'monday', '18:00', 'Dinner', True)
add_event(12345, 'monday', '20:00', 'TV Show', True)
add_event(12345, 'tuesday', '08:00', 'Wake up', True)
stats(12345, 'ALL', "black")  # Рисует график для всех дней
stats(12345, 'monday')  # Рисует график для понедельника
list_user_tables()
view_user_table(12345)

#remove_table(12345)
