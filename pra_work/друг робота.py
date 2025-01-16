import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import serial
import serial.tools.list_ports
import sys
import time
from queue import Queue
import threading


# Пошук серійного порту
def find_serial_port(port_name):
    ports = [port.device for port in serial.tools.list_ports.comports()]
    if port_name not in ports:
        print(f"Помилка: Порт {port_name} недоступний. Доступні порти: {ports}")
        sys.exit(1)
    return port_name


# Ініціалізація серійного порту
def init_serial(port_name, baud_rate):
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=1)
        print(f"Підключено до {port_name}")
        return ser
    except serial.SerialException as e:
        print(f"Не вдалося відкрити порт {port_name}: {e}")
        sys.exit(1)


# Параметри серійного порту
PORT = find_serial_port('COM4')  # Заміна на правильний порт
BAUD_RATE = 115200
ser = init_serial(PORT, BAUD_RATE)

# Глобальні змінні
ax = ay = az = 0.0
ax_values = []
ay_values = []
az_values = []
yaw_mode = False
data_queue = Queue()


def check_gl_errors():
    """
    Діагностика помилок OpenGL
    """
    error = glGetError()
    if error != GL_NO_ERROR:
        print(f"[ERROR] OpenGL Error: {gluErrorString(error).decode('utf-8')}")


def init_opengl():
    """
    Ініціалізація OpenGL з встановленням базових параметрів.
    """
    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Чорний фон
    glClearDepth(1.0)  # Глибина буфера
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glViewport(0, 0, 640, 480)  # Встановлення в’юпорту
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (640 / 480), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    check_gl_errors()


def read_serial_data():
    """
    Потік читання серійних даних та додавання їх до черги
    """
    global ax, ay, az, data_queue
    while True:
        try:
            ser.write(b".")  # Надсилаємо запит до пристрою
            line = ser.readline().decode("utf-8").strip()  # Зчитуємо рядок
            print(f"[DEBUG] Отримано необроблені дані: '{line}'")
            if not line:
                print("[DEBUG] Порожній рядок, пропускаємо...")
                continue
            print(f"[DEBUG] Зчитані сирі дані: {line}")

            # Перевірка та обробка рядка
            try:
                data_dict = {}
                values = line.split("\t")
                for val in values:
                    key, value = val.split(":")
                    data_dict[key.strip()] = float(value.strip())
                print(f"[DEBUG] Конвертовані дані: {data_dict}")
            except ValueError as e:
                print(f"[ERROR] Неможливо розпарсити рядок: {line}, помилка: {e}")
                continue

            # Оновлення змінних
            if "accelX" in data_dict and "accelY" in data_dict and "accelZ" in data_dict:
                ax_values.append(data_dict["accelX"] * 5)
                ay_values.append(data_dict["accelY"] * 5)
                az_values.append(data_dict["accelZ"] * 5)
                if len(ax_values) > 10: ax_values.pop(0)
                if len(ay_values) > 10: ay_values.pop(0)
                if len(az_values) > 10: az_values.pop(0)
                ax = sum(ax_values) / len(ax_values)
                ay = sum(ay_values) / len(ay_values)
                az = sum(az_values) / len(az_values)
                print(f"[DEBUG] Оновлено середні дані: ax={ax:.2f}, ay={ay:.2f}, az={az:.2f}")
                data_queue.put((ax, ay, az))
                print(f"[DEBUG] Дані додані в чергу: {ax:.2f}, {ay:.2f}, {az:.2f}")
        except (serial.SerialException, IOError) as e:
            print(f"[ERROR] Помилка читання серійного порту: {e}")
        


def draw_text(position, text, font_size=18):
    """
    Відображення тексту через Pygame у форматі OpenGL
    """
    font = pygame.font.SysFont("Courier", font_size, True)
    text_surface = font.render(text, True, (255, 255, 255))
    text_data = pygame.image.tostring(text_surface, "RGB", True)

    # Позиціонування тексту
    glRasterPos2f(position[0] / 640 * 2 - 1, 1 - position[1] / 480 * 2)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                 GL_RGB, GL_UNSIGNED_BYTE, text_data)


def draw_scene():
    """
    Рендеринг сцени з відображенням тексту та куба
    """
    global ax, ay, az, yaw_mode

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -5.0)

    # Відображення тексту
    osd_text = f"pitch: {ay:.2f}, roll: {ax:.2f}"
    if yaw_mode:
        osd_text += f", yaw: {az:.2f}"
    print(f"Відображуваний текст: {osd_text}")
    print(f"Обертання: ax={ax}, ay={ay}, az={az}")
    draw_text((10, 460), osd_text)

    # Поворот за осями
    print(f"Збільшене обертання: ax={ax * 5}, ay={ay * 5}, az={az * 5}")
    if yaw_mode:
        glRotatef(az, 0.0, 1.0, 0.0)  # Yaw
    glRotatef(ay, 1.0, 0.0, 0.0)  # Pitch
    glRotatef(-ax, 0.0, 0.0, 1.0)  # Roll

    # Малювання куба
    glBegin(GL_QUADS)

    # Верхнє обличчя
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(1.0, 0.2, -1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(1.0, 0.2, 1.0)

    # Нижнє обличчя
    glColor3f(1.0, 0.5, 0.0)
    glVertex3f(1.0, -0.2, 1.0)
    glVertex3f(-1.0, -0.2, 1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(1.0, -0.2, -1.0)

    # Переднє обличчя
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(1.0, 0.2, 1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(-1.0, -0.2, 1.0)
    glVertex3f(1.0, -0.2, 1.0)

    glEnd()

    # Перевірка помилок OpenGL
    check_gl_errors()


def main():
    global ax, ay, az, yaw_mode, data_queue

    # Ініціалізація Pygame і OpenGL
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((640, 480), OPENGL | DOUBLEBUF)
    pygame.display.set_caption("Press Esc to quit, Z to toggle yaw mode")
    init_opengl()

    # Потік для читання серійних даних
    threading.Thread(target=read_serial_data, daemon=True).start()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                ser.close()
                return
            elif event.type == KEYDOWN and event.key == K_z:
                yaw_mode = not yaw_mode
                print(f"Режим yaw змінено: {yaw_mode}")
                ser.write(b"z")

        # Оновлення даних
        try:
            while not data_queue.empty():
                ax, ay, az = data_queue.get_nowait()
                print(f"[DEBUG] Отримані дані: ax={ax:.2f}, ay={ay:.2f}, az={az:.2f}")
        except Exception as e:
            print(f"[ERROR] Помилка отримання даних з черги: {e}")

        # Малювання сцени
        draw_scene()
        pygame.display.flip()


if __name__ == "__main__":
    main()