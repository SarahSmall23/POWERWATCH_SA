"""
webapp.py
PowerWatch SA — CherryPy web application (the "web integration" layer).

Serves the dashboard page and a small JSON endpoint the page polls every
few seconds, using the same CherryPy expose-and-quickstart pattern from
Lesson 6 of this module. Run with: python webapp.py
"""

import os

import cherrypy

import config
import database
import eskom_api
from monitor import Monitor


class Dashboard:
    def __init__(self, monitor: Monitor):
        self.monitor = monitor

    @cherrypy.expose
    def index(self):
        with open(os.path.join("templates", "dashboard.html"), encoding="utf-8") as f:
            return f.read()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def status(self):
        """Polled by the dashboard's JavaScript every few seconds."""
        stats = database.outage_stats()
        return {
            "current": self.monitor.current,
            "recent_events": database.recent_events(limit=10),
            "readings": database.recent_readings(limit=60),
            "stats": stats,
            "national_stage": eskom_api.get_national_stage(config.ESKOM_TOKEN),
        }


def main():
    database.init_db()
    monitor = Monitor()
    monitor.start_background()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    conf = {
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': os.path.join(BASE_DIR, 'static')
        }
    }

    cherrypy.config.update({
        "server.socket_host": "0.0.0.0",
        "server.socket_port": 8080,
    })

    cherrypy.quickstart(Dashboard(monitor), "/", conf)

if __name__ == "__main__":
    main()
