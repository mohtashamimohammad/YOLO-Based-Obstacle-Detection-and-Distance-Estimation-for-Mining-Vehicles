#define TRIG_PIN 14   // D5 روی NodeMCU
#define ECHO_PIN 12   // D6 روی NodeMCU (از طریق دیوایدر ولتاژ)

// سرعت صدا ~343 m/s
const float SOUND_SPEED = 0.0343; 

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.println("Ultrasonic Test Started...");
}

void loop() {
  // ارسال پالس
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(5);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // دریافت پالس
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // timeout = 30ms (≈5m)

  if (duration == 0) {
    Serial.println("⚠️ No Echo detected! (Check wiring or power)");
  } else {
    float distance = (duration * SOUND_SPEED) / 2; 
    Serial.print("✅ Distance: ");
    Serial.print(distance);
    Serial.println(" cm");
  }

  delay(500);
}
