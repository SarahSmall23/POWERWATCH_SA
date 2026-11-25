"""
sensors.py
PowerWatch SA — sensor interface layer.

Provides two implementations behind the same interface:
  - RealSensors   : reads actual hardware (ZMPT101B mains-voltage sensor via
                    an MCP3008 ADC, and a battery voltage divider on a second
                    ADC channel).
  - SimulatedSensors : generates realistic mock readings so the system can be
                    demonstrated end-to-end without the physical build. This
                    is the prototype fallback explicitly allowed by the
                    assignment brief when there is not enough time to
                    assemble the hardware.

Both expose the same three methods, so webapp.py and monitor.py never need
to know which one is in use.
"""

import random
import time

USE_SIMULATION = True  # flip to False once real hardware is wired up


class RealSensors:
    """Reads the physical sensors through an MCP3008 ADC over SPI.

    Wiring (BCM numbering):
      MCP3008: VDD->3V3, VREF->3V3, AGND->GND, DGND->GND,
               CLK->GPIO11, DOUT->GPIO9, DIN->GPIO10, CS->GPIO8
      CH0: output of the ZMPT101B AC voltage sensor (mains presence)
      CH1: output of the battery voltage divider (two 100k resistors
           halve a 12V battery's range down into the Pi's 0-3.3V ADC range)
    """

    def __init__(self):
        import spidev  # type: ignore

        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 1350000

    def _read_adc(self, channel: int) -> int:
        cmd = [1, (8 + channel) << 4, 0]
        reply = self.spi.xfer2(cmd)
        return ((reply[1] & 3) << 8) + reply[2]  # 0-1023

    def grid_is_up(self) -> bool:
        raw = self._read_adc(0)
        # ZMPT101B idles near mid-rail with no AC present; a present 50Hz
        # mains signal swings the ADC reading well above a quiet threshold.
        return raw > 60

    def battery_percent(self) -> float:
        raw = self._read_adc(1)
        voltage = (raw / 1023.0) * 3.3 * 2  # undo the 2:1 divider
        # Typical 12V lead-acid/LiFePO4 backup bank: 10.5V empty, 13.0V full
        pct = (voltage - 10.5) / (13.0 - 10.5) * 100
        return max(0.0, min(100.0, pct))

    def battery_voltage(self) -> float:
        raw = self._read_adc(1)
        return round((raw / 1023.0) * 3.3 * 2, 2)


class SimulatedSensors:
    """Deterministic-ish mock sensors for demos and development.

    Cycles through grid-up / grid-down phases on a timer so a live demo
    shows a real outage-to-recovery transition without needing to physically
    unplug anything, and drains/recharges a virtual battery accordingly.
    """

    def __init__(self):
        self._phase_start = time.time()
        self._phase = "up"          # "up" or "down"
        self._phase_len = 45        # seconds per phase, for a short demo
        self._battery_pct = 92.0

    def _tick(self):
        elapsed = time.time() - self._phase_start
        if elapsed > self._phase_len:
            self._phase = "down" if self._phase == "up" else "up"
            self._phase_start = time.time()

        if self._phase == "down":
            self._battery_pct = max(5.0, self._battery_pct - random.uniform(0.3, 0.9))
        else:
            self._battery_pct = min(100.0, self._battery_pct + random.uniform(0.1, 0.4))

    def grid_is_up(self) -> bool:
        self._tick()
        return self._phase == "up"

    def battery_percent(self) -> float:
        self._tick()
        return round(self._battery_pct, 1)

    def battery_voltage(self) -> float:
        return round(10.5 + (self.battery_percent() / 100.0) * 2.5, 2)


def get_sensor_interface():
    return SimulatedSensors() if USE_SIMULATION else RealSensors()
