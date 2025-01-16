#include <WiFi.h>
#include <esp_now.h>

// Структура для отримання даних
typedef struct sensor_data {
  float accelX;
  float accelY;
  float accelZ;
  float gyroX;
  float gyroY;
  float gyroZ;
} sensor_data;

// Створюємо змінну для отриманих даних
sensor_data sensorReadings;

// Функція зворотного виклику для отримання даних
void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
  // Копіюємо отримані дані в структуру
  memcpy(&sensorReadings, incomingData, sizeof(sensorReadings));

  // Виводимо отримані дані на Serial Monitor для візуалізації графіка
  Serial.print("accelX:");
  Serial.print(sensorReadings.accelX);
  Serial.print("\taccelY:");
  Serial.print(sensorReadings.accelY);
  Serial.print("\taccelZ:");
  Serial.print(sensorReadings.accelZ);

  Serial.print("\tgyroX:");
  Serial.print(sensorReadings.gyroX);
  Serial.print("\tgyroY:");
  Serial.print(sensorReadings.gyroY);
  Serial.print("\tgyroZ:");
  Serial.println(sensorReadings.gyroZ);
}

void setup() {
  // Ініціалізація Serial Monitor
  Serial.begin(115200);

  // Встановлюємо ESP32 як Wi-Fi станцію
  WiFi.mode(WIFI_STA);

  // Ініціалізуємо ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Помилка ініціалізації ESP-NOW");
    return;
  }

  // Реєструємо функцію зворотного виклику для обробки отриманих даних
  esp_now_register_recv_cb(OnDataRecv);

  Serial.println("ESP-NOW Отримувач запущений");
}

void loop() {
  // Головний цикл порожній, оскільки дані обробляються у функції зворотного виклику
}
