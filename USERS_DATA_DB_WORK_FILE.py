import sqlite3
from datetime import datetime

class CalendarBotDB:
    dbpath = "./User_data/schedules.db"
    def __init__(self, db_name=dbpath):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        """Creates tables if they do not exist."""
        self.cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                registration_timestamp DATETIME,
                theme INTEGER CHECK (theme IN (0, 1)),
                language TEXT DEFAULT 'en',
                streak INTEGER CHECK (streak IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS single_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_timestamp DATETIME,
                description TEXT,
                duration_minutes INTEGER,
                notify_before_minutes INTEGER,
                UNIQUE(user_id, event_timestamp),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recurring_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
                event_time TIME,
                description TEXT,
                duration_minutes INTEGER,
                notify_before_minutes INTEGER,
                UNIQUE(user_id, day_of_week, event_time),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """
        )
        self.connection.commit()

    def add_user(self, user_id, username, theme=0, language="en", streak=0):
        """Adds a new user."""
        registration_timestamp = datetime.now()
        self.cursor.execute(
            """
            INSERT INTO users (user_id, username, registration_timestamp, theme, language, streak)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, registration_timestamp, theme, language, streak),
        )
        self.connection.commit()

    def add_single_event(self, user_id, event_timestamp, description, duration_minutes, notify_before_minutes):
        """Adds a one-time event."""
        self.cursor.execute(
            """
            INSERT INTO single_events (user_id, event_timestamp, description, duration_minutes, notify_before_minutes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, event_timestamp, description, duration_minutes, notify_before_minutes),
        )
        self.connection.commit()

    def add_recurring_event(self, user_id, day_of_week, event_time, description, duration_minutes, notify_before_minutes):
        """Adds a recurring event."""
        self.cursor.execute(
            """
            INSERT INTO recurring_events (user_id, day_of_week, event_time, description, duration_minutes, notify_before_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, day_of_week, event_time, description, duration_minutes, notify_before_minutes),
        )
        self.connection.commit()

    def get_user(self, user_id):
        """Returns user, if exists."""
        self.cursor.execute(
            """
            SELECT 
                user_id, 
                username, 
                registration_timestamp, 
                theme, 
                language, 
                streak
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return self.cursor.fetchall()

    def get_user_events_single(self, user_id):
        """Returns all events for a user."""
        self.cursor.execute(
            """
            SELECT 
                user_id, 
                event_timestamp, 
                description, 
                duration_minutes, 
                notify_before_minutes 
            FROM single_events 
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return self.cursor.fetchall()

    def get_user_events_recurring(self, user_id):
        """Returns all events for a user."""
        self.cursor.execute(
            """
            SELECT 
                user_id, 
                day_of_week, 
                event_time, 
                description, 
                duration_minutes, 
                notify_before_minutes 
            FROM recurring_events 
            WHERE user_id = ?
            """,
            (user_id,),
        )
        return self.cursor.fetchall()

    def delete_recurring_event(self, user_id, day_of_week, event_time):
        """Deletes a recurring event."""
        self.cursor.execute(
            """
            DELETE FROM recurring_events 
            WHERE user_id = ? AND day_of_week = ? AND event_time = ?
            """,
            (user_id, day_of_week, event_time),
        )
        self.connection.commit()

    def delete_single_event(self, user_id, event_timestamp):
        """Deletes a single event."""
        self.cursor.execute(
            """
            DELETE FROM single_events 
            WHERE user_id = ? AND event_timestamp = ?
            """,
            (user_id, event_timestamp),
        )
        self.connection.commit()

    def switch_theme(self, user_id, theme):
        """Switches the user's theme."""
        theme_value = 1 if theme == "dark" else 0
        self.cursor.execute(
            """
            UPDATE users SET theme = ? WHERE user_id = ?
            """,
            (theme_value, user_id),
        )
        self.connection.commit()

    def change_language(self, user_id, language):
        """Changes the user's language."""
        self.cursor.execute(
            """
            UPDATE users SET language = ? WHERE user_id = ?
            """,
            (language, user_id),
        )
        self.connection.commit()

    def switch_streak(self, user_id, streak):
        """Switches the user's streak."""
        streak_value = 1 if streak else 0
        self.cursor.execute(
            """
            UPDATE users SET streak = ? WHERE user_id = ?
            """,
            (streak_value, user_id),
        )
        self.connection.commit()

    def delete_user(self, user_id):
        """Deletes a user and all their events."""
        self.cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self.connection.commit()

    def language(self, user_id):
        """Returns the language of the user."""
        self.cursor.execute(
            """
            SELECT language FROM users WHERE user_id = ?
            """,
            (user_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def streak(self, user_id):
        """Returns the streak status of the user."""
        self.cursor.execute(
            """
            SELECT streak FROM users WHERE user_id = ?
            """,
            (user_id,)
        )
        result = self.cursor.fetchone()
        return bool(result[0]) if result else None

    def theme(self, user_id):
        """Returns the theme of the user as 'dark' or 'light'."""
        self.cursor.execute(
            """
            SELECT theme FROM users WHERE user_id = ?
            """,
            (user_id,)
        )
        result = self.cursor.fetchone()
        if result:
            return "dark" if result[0] == 1 else "light"
        return None

    def stats(self, user_id):
        """Returns a dictionary with the count of recurring events for each day of the week."""
        self.cursor.execute(
            """
            SELECT day_of_week, COUNT(*) 
            FROM recurring_events 
            WHERE user_id = ? 
            GROUP BY day_of_week
            """,
            (user_id,)
        )
        result = self.cursor.fetchall()

        # Создаем словарь, где для каждого дня недели устанавливается значение 0
        stats_dict = {day: 0 for day in range(7)}

        # Заполняем словарь результатами запроса
        for day_of_week, count in result:
            stats_dict[day_of_week] = count

        return stats_dict

    def close(self):
        """Closes the database connection."""
        self.connection.close()

# Example usage
if __name__ == "__main__":
    db = CalendarBotDB()

    # Adding a user

    # db.add_user(user_id=1, username="test_user", theme=1, language="en", streak=1)
    #
    # # Adding a one-time event
    # db.add_single_event(
    #     user_id=1,
    #     event_timestamp="2025-01-22 15:30:00",
    #     description="Meeting with team",
    #     duration_minutes=60,
    #     notify_before_minutes=15
    # )
    #
    # # Adding a recurring event
    # db.add_recurring_event(
    #     user_id=1,
    #     day_of_week=2,
    #     event_time="09:00:00",
    #     description="Weekly Standup",
    #     duration_minutes=30,
    #     notify_before_minutes=10
    # )

    # Fetching user events
    events = db.get_user_events_single(user_id=1)
    print(events)

    # Changing theme to light
    db.switch_theme(user_id=1, theme="light")

    # Changing language to French
    db.change_language(user_id=1, language="fr")

    # Changing streak status
    db.switch_streak(user_id=1, streak=False)

    print(db.get_user(user_id=3456))

    # Closing the database
    db.close()
