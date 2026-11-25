"""
eskom_api.py
PowerWatch SA — EskomSePush API client.

EskomSePush (sepush.co.za) is the widely used South African load-shedding
data API, covering the national stage and area-level schedules. A free
personal-use token (50 requests/day) is obtained from the developer portal
and placed in config.py. If no token is configured, this module degrades
gracefully and the dashboard simply shows "schedule unavailable" instead of
crashing — the sensor-based monitoring (the core of the project) keeps
working either way.
"""

import requests

API_BASE = "https://developer.sepush.co.za/business/3.0"


def _headers(token: str):
    return {"Token": token}


def get_national_stage(token: str):
    """Current national load-shedding stage, or None if unavailable."""
    if not token:
        return None
    try:
        resp = requests.get(f"{API_BASE}/status", headers=_headers(token), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("status", {}).get("eskom", {}).get("stage")
    except requests.RequestException:
        return None


def get_area_schedule(token: str, area_id: str):
    """Upcoming scheduled slots for a specific area ID (from areas_search)."""
    if not token or not area_id:
        return []
    try:
        resp = requests.get(
            f"{API_BASE}/area",
            headers=_headers(token),
            params={"id": area_id},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json().get("events", [])
    except requests.RequestException:
        return []
