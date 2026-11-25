# PowerWatch SA

Load-shedding & backup-power monitor for South African small businesses and
home-based entrepreneurs. Raspberry Pi 4, Python, CherryPy, SQLite.

## Run it (simulation mode — no hardware needed)
    pip install -r requirements.txt
    python webapp.py
Then open http://localhost:8080 — the dashboard updates every 4 seconds and
simulates an outage/recovery cycle every 45 seconds so you can see the full
behaviour without wiring anything up.

## Run it on real hardware
1. Wire the ZMPT101B and battery voltage divider to an MCP3008 ADC as
   described in sensors.py's docstring.
2. In sensors.py, set `USE_SIMULATION = False`.
3. (Optional) Add your EskomSePush token and area ID in config.py to enable
   the official-schedule comparison.
4. `python webapp.py`

## Files
- sensors.py    — real + simulated sensor interfaces
- monitor.py     — background polling loop, alert logic
- database.py    — SQLite schema and queries
- eskom_api.py   — EskomSePush API client
- webapp.py      — CherryPy app (dashboard + JSON status endpoint)
- templates/dashboard.html — the dashboard UI
