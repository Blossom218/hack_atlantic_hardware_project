Noise Monitor v2

Python:
  pip install pyserial
  Change SERIAL_PORT = "COM3" to your Arduino port.

Noise ranges are amplitude ranges, not dB:
  OKAY: 0 <= average < 30
  MODERATE: 30 <= average < 70
  NOT FINE: average >= 70

Python computes a 2-second rolling average. A new range must remain
for 5 seconds before it becomes the confirmed status. The LCD timer
shows how long the confirmed status has been active.

Arduino:
  Sound sensor -> A0
  Green -> D8
  Yellow -> D9
  Red -> D10
  I2C LCD: SDA -> A4, SCL -> A5, VCC -> 5V, GND -> GND

Assumes a 16x2 I2C LCD at address 0x27 and LiquidCrystal_I2C library.
If the LCD is blank, try 0x3F.

Close Arduino Serial Monitor before starting Python.
