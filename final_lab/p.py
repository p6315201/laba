import serial
import serial.tools.list_ports
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading
import sys
from queue import Queue
import time  # Додано для використання часової осі


# Перевірка наявності серійного порту
def find_serial_port(port_name):
    ports = [port.device for port in serial.tools.list_ports.comports()]
    if port_name not in ports:
        print(f"Помилка: Порт {port_name} недоступний. Доступні порти: {ports}")
        sys.exit(1)
    return port_name


# Параметри серійного порту
PORT = find_serial_port('COM3')  # Замініть на відповідний порт
BAUD_RATE = 115200

# Ініціалізація серійного порту
try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    print(f"Підключено до {PORT}")
except serial.SerialException as e:
    print(f"Не вдалося відкрити порт {PORT}: {e}")
    sys.exit(1)

# Ініціалізуємо чергу та DataFrame
data = pd.DataFrame(columns=['time', 'accelX', 'accelY', 'accelZ', 'gyroX', 'gyroY', 'gyroZ'])
data_queue = Queue()


# Читання даних із серійного порту
def read_serial_data():
    initial_time = None  # Часовий відлік починається з першого рядка даних
    while True:
        try:
            if ser.is_open:
                # Зчитування рядка з даними
                line = ser.readline().decode('utf-8').strip()
                print(f"Сирі дані: {line}")  # Для діагностики

                # Видаляємо префікс "Сирі дані:"
                if line.startswith("Сирі дані:"):
                    line = line.replace("Сирі дані:", "").strip()

                # Парсинг даних
                values = line.split("\t")  # Розбиваємо рядок за табуляціями
                data_dict = {}
                for item in values:
                    if ":" in item:  # Перевіряємо, чи є ключ-значення
                        key, value = item.split(":")
                        data_dict[key.strip()] = float(value.strip())

                # Корекція часової мітки
                timestamp = time.time()
                if initial_time is None:
                    initial_time = timestamp
                timestamp -= initial_time

                # Додаємо нові дані до черги
                new_data = {
                    'time': timestamp,
                    'accelX': data_dict.get('accelX', 0),
                    'accelY': data_dict.get('accelY', 0),
                    'accelZ': data_dict.get('accelZ', 0),
                    'gyroX': data_dict.get('gyroX', 0),
                    'gyroY': data_dict.get('gyroY', 0),
                    'gyroZ': data_dict.get('gyroZ', 0),
                }
                data_queue.put(new_data)

        except Exception as e:
            print(f"Помилка у зчитуванні даних: {e}")
            break
    ser.close()

# Оновлення графіка
def update_plot(frame):
    global data
    try:
        while not data_queue.empty():
            new_data = data_queue.get()
            print(f"Дані для графіка: {new_data}")  # Для діагностики
            data = pd.concat([data, pd.DataFrame([new_data])], ignore_index=True)

        # Очищення осей і малювання графіка
        plt.cla()
        if not data.empty and 'time' in data.columns:
            min_time = data['time'].max() - 20  # Показуємо 10 секунд останніх даних
            data = data[data['time'] >= min_time]
        plt.plot(data['time'], data['accelX'], label='Acceleration X')
        plt.plot(data['time'], data['accelY'], label='Acceleration Y')
        plt.plot(data['time'], data['accelZ'], label='Acceleration Z')
        plt.legend(loc='upper right')
        plt.title("Дані з датчиків у реальному часі")
        plt.xlabel("Час (секунди)")
        plt.ylabel("Значення")
    except Exception as e:
        print(f"Помилка під час оновлення графіка: {e}")


# Запуск читання даних у фоновому режимі
thread = threading.Thread(target=read_serial_data)
thread.daemon = True
thread.start()

# Анімація для оновлення графіка
ani = FuncAnimation(plt.gcf(), update_plot, interval=5, cache_frame_data=False)  # Інтервал у мілісекундах
ani = FuncAnimation(plt.gcf(), update_plot, interval=1, cache_frame_data=False)  # Інтервал у мілісекундах
plt.gca().set_xlim(left=0, auto=True)  # Динамічний перегляд осі x
plt.gca().set_ylim(auto=True)         # Автоматичне оновлення меж осі y

# Відображення графіка
plt.tight_layout()
try:
    plt.show()
except KeyboardInterrupt:
    ser.close()
    sys.exit()


