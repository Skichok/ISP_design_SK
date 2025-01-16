import matplotlib.pyplot as plt
import numpy as np

# Данные для таблицы
columns = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
rows = [f"Строка {i+1}" for i in range(10)]
data = np.random.randint(1, 100, size=(10, 7))  # Генерация случайных данных

# Создание фигуры
fig, ax = plt.subplots(figsize=(10, 6))  # Размер изображения

# Настройка фона
fig.patch.set_facecolor('black')  # Чёрный фон для всей фигуры
ax.axis('tight')
ax.axis('off')

# Добавление таблицы
table = ax.table(cellText=data, colLabels=columns, rowLabels=rows, loc='center', cellLoc='center')

# Настройка стиля таблицы
table.auto_set_font_size(False)
table.set_fontsize(10)
table.auto_set_column_width(col=list(range(len(columns))))

# Изменение цветов ячеек
for key, cell in table.get_celld().items():
    cell.set_edgecolor('white')  # Белые границы
    cell.set_text_props(color='white')  # Белый текст
    cell.set_facecolor('black')  # Чёрный фон ячеек

# Сохранение изображения
plt.savefig("table_image_black_bg.png", dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.show()
