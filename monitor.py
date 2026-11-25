"""
monitor.py
PowerWatch SA — background monitoring thread.

Polls the sensor interface on a fixed interval, detects grid state
*transitions* (not just the current state), writes them to the database, and
drives a local buzzer/LED alert when the grid drops or the backup battery
runs low. Runs as a daemon thread started by webapp.py so the CherryPy
dashboard and the monitoring loop share one process on the Pi.
"""

import threading
import time

import config
import database
from sensors import get_sensor_interface

try:
    from gpiozero import Buzzer, LED  # type: ignore
    _HAS_GPIO = True
except Exception:
    _HAS_GPIO = False


class Monitor:
    def __init__(self):
        self.sensors = get_sensor_interface()
        self._last_grid_state = None
        self._low_battery_alerted = False
        self.current = {
            "grid_up": True,
            "battery_percent": 100.0,
            "battery_voltage": 13.0,
            "last_update": None,
        }

        if _HAS_GPIO:
            self.buzzer = Buzzer(17)
            self.led = LED(27)
        else:
            self.buzzer = None
            self.led = None

    def _alert(self, on: bool):
        if self.buzzer and self.led:
            if on:
                self.buzzer.beep(on_time=0.3, off_time=0.3, n=3, background=True)
                self.led.on()
            else:
                self.led.off()

    def _poll_once(self):
        grid_up = self.sensors.grid_is_up()
        battery_pct = self.sensors.battery_percent()
        battery_v = self.sensors.battery_voltage()

        database.log_reading(battery_pct, battery_v, grid_up)

        if self._last_grid_state is not None and grid_up != self._last_grid_state:
            if not grid_up:
                database.log_event("outage_start", battery_pct)
                self._alert(True)
            else:
                database.log_event("recovery", battery_pct)
                self._alert(False)
                self._low_battery_alerted = False

        if not grid_up and battery_pct < config.LOW_BATTERY_THRESHOLD and not self._low_battery_alerted:
            self._alert(True)
            self._low_battery_alerted = True

        self._last_grid_state = grid_up
        self.current = {
            "grid_up": grid_up,
            "battery_percent": battery_pct,
            "battery_voltage": battery_v,
            "last_update": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def run_forever(self):
        database.init_db()
        while True:
            self._poll_once()
            time.sleep(config.POLL_INTERVAL_SECONDS)

    def start_background(self):
        t = threading.Thread(target=self.run_forever, daemon=True)
        t.start()
        return t
