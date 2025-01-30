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