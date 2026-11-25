"""
config.py
Fill these in with your own details before a real-hardware run.

ESKOM_TOKEN : free personal-use token from https://eskomsepush.gumroad.com/l/api
              (50 requests/day). Leave blank to run without schedule
              comparison — sensor monitoring still works normally.
AREA_ID     : your specific suburb's area ID, found by calling the
              areas_search endpoint with your suburb/postal code once you
              have a token. Example format: "capetown-10-sea point"
"""

ESKOM_TOKEN = ""
AREA_ID = ""

LOW_BATTERY_THRESHOLD = 20       # percent — triggers an alert
POLL_INTERVAL_SECONDS = 5        # how often the monitor reads the sensors
