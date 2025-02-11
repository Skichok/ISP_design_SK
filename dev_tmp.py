user_inf = "11:00:00 01.02.25 10 30 Doctor" # Сначала идет время ивента, в формате XX:XX:XX YY.YY.YY после чего продолжительность в минутах, одно число, оповестить за сколько минут, тоже одно число, после описание события
stamp = user_inf.split(" ")[0] + " " + user_inf.split(" ")[1]
duration = user_inf.split(" ")[2]
notify_before = user_inf.split(" ")[3]
description = " ".join(user_inf.split(" ")[4:])


print(stamp)
print(duration)
print(description)
print(notify_before)
print(len(user_inf.split(" ")))

text = """This message is automatically generated.\nYou need to help the user plan his schedule. He will write the text below, and you will have to define and rewrite his events using these commands:\n/adds <HH:MM:SS> <DD.MM.YY> <duration in minutes> <notify before minutes> <description> \u2013 add a new single event\n/deletes <HH:MM:SS> <DD.MM.YY> \u2013 remove an existing single event\n/changes <HH:MM:SS> <DD.MM.YY> <new duration in minutes> <new notify before minutes> <new description> \u2013 modify an existing event by providing its original time and date, then updating the details\n/addr <number-of-day> <HH:MM:SS> <duration in minutes> <notify before minutes> <description> - add a new recurring event\n/deleter <number-of-day> <HH:MM:SS> - delete recurring event\n/changer <number-of-day> <HH:MM:SS> <new duration in minutes> <new notify before minutes> <new description> - change recurring event\n\ntoday's date: {current_date}\n\nhere is the text from the user:\n\nbeginning of the user's text\n\"{user_prompt}\"\nend of the user's text\n\nif there are no events in the text, then reply \"no suitable events found\" in the same language the user wrote. Otherwise, send a list of commands without additional information, only from the text and only clearly defined events (set the duration and notify before to 60 and 0 by default, respectively).\n\nAS ANSWER, GIVE A READY SET OF COMMANDS /adds and /addr.\nIF THE USER ASKS, THEN ADD /changer, /changes, /deleter and /deletes. Examples of using commands with the data above."""
print(text)