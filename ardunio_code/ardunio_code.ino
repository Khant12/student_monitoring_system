#include <Adafruit_NeoPixel.h>
#include <Servo.h>

#define PIN_LED_STRIP 6       // Define the pin for the NeoPixels LED strip
#define NUM_LEDS 8            // Define the number of LEDs in your strip
#define DELAY_MS 1000         // Delay between color changes (1 second)
#define BUZZER_PIN 7          // Define the pin for the active buzzer
#define SERVO_PIN 9           // Define the pin for the servo
#define GREEN_COLOR 0, 255, 0 // RGB values for green
#define RED_COLOR 255, 0, 0   // RGB values for red

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, PIN_LED_STRIP, NEO_GRB + NEO_KHZ800);
Servo servo;

void setup() {
  Serial.begin(9600);
  strip.begin();
  strip.show();  // Initialize all pixels to 'off'

  pinMode(BUZZER_PIN, OUTPUT);
  servo.attach(SERVO_PIN);  // Attach servo to the specified pin
  servo.write(90);          // Start with the servo at 90 degrees
}

void loop() {
  if (Serial.available() > 0) {
    char signal = Serial.read();

    if (signal == '0') {
      // Turn NeoPixels green
      for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(GREEN_COLOR));
      }
      strip.show();

      // Set servo to 180 degrees and turn off the buzzer
      servo.write(180);
      digitalWrite(BUZZER_PIN, LOW);
    } else if (signal == '1') {
      // Turn NeoPixels red
      for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(RED_COLOR));
      }
      strip.show();

      // Turn on the buzzer and set servo to 90 degrees
      digitalWrite(BUZZER_PIN, HIGH);
      servo.write(90);
      delay(200); // Buzz for 200ms
      digitalWrite(BUZZER_PIN, LOW);
    } else if (signal == '2') {
      // Turn off NeoPixels, buzzer, and set servo to 90 degrees
      for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(0, 0, 0)); // Turn off all LEDs
      }
      strip.show();
      digitalWrite(BUZZER_PIN, LOW); // Turn off the buzzer
      servo.write(90); // Set servo to 90 degrees
    }
  }
  // delay(DELAY_MS); // Add a delay to prevent rapid signal changes
}
