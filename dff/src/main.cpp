/*********
  Rui Santos & Sara Santos - Random Nerd Tutorials
  Complete project details at https://RandomNerdTutorials.com/esp-now-one-to-many-esp32-esp8266/
  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.
*********/

#include <esp_now.h>
#include <WiFi.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// REPLACE WITH YOUR ESP RECEIVER'S MAC ADDRESS
uint8_t broadcastAddress1[] = {0xA0, 0xB7, 0x65, 0x20, 0xC3, 0x6C};

// Structure to hold sensor data
typedef struct sensor_data {
  float accelX;
  float accelY;
  float accelZ;
  float gyroX;
  float gyroY;
  float gyroZ;
  float temperature;
} sensor_data;

// Create an instance of the struct
sensor_data sensorReadings;

// ESP-NOW peer info
esp_now_peer_info_t peerInfo;

// MPU6050 instance
Adafruit_MPU6050 mpu;

// Callback when data is sent
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
           mac_addr[0], mac_addr[1], mac_addr[2], mac_addr[3], mac_addr[4], mac_addr[5]);
  Serial.print("Packet to: ");
  Serial.print(macStr);
  Serial.print(" send status: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
}

void setup() {
  // Serial monitor
  Serial.begin(115200);

  // Initialize WiFi in station mode
  WiFi.mode(WIFI_STA);

  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Register the send callback
  esp_now_register_send_cb(OnDataSent);

  // Add peer
  memcpy(peerInfo.peer_addr, broadcastAddress1, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    return;
  }

  // Initialize the MPU6050 sensor
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      
    }
  }
  Serial.println("MPU6050 Found!");

  // Configure the MPU6050
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);

  Serial.println("MPU6050 Initialized");
}

void loop() {
  // Get new sensor events with the readings
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Populate the sensorReadings struct
  sensorReadings.accelX = a.acceleration.x;
  sensorReadings.accelY = a.acceleration.y;
  sensorReadings.accelZ = a.acceleration.z;
  sensorReadings.gyroX = g.gyro.x;
  sensorReadings.gyroY = g.gyro.y;
  sensorReadings.gyroZ = g.gyro.z;
  sensorReadings.temperature = temp.temperature;

  // Print sensor data to Serial
  Serial.print("Acceleration X: ");
  Serial.print(sensorReadings.accelX);
  Serial.print(", Y: ");
  Serial.print(sensorReadings.accelY);
  Serial.print(", Z: ");
  Serial.println(sensorReadings.accelZ);

  Serial.print("Rotation X: ");
  Serial.print(sensorReadings.gyroX);
  Serial.print(", Y: ");
  Serial.print(sensorReadings.gyroY);
  Serial.print(", Z: ");
  Serial.println(sensorReadings.gyroZ);


  // Send the sensor data via ESP-NOW
  esp_err_t result = esp_now_send(broadcastAddress1, (uint8_t *)&sensorReadings, sizeof(sensor_data));

  if (result == ESP_OK) {
    Serial.println("Sent with success");
  } else {
    Serial.println("Error sending the data");
  }


}
