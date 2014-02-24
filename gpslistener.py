#!/usr/bin/env python
#
# the GPS listener
# connects to GPSd and presents the available data to the other modules
# it is implemented as a thread, exposing fix data via variables

import threading
import logging
import time
from gps import *


class GPSListener(threading.Thread):
	lat = 0
	lon = 0
	alt = 0
	fix = 0

	def run(self):
		logging.info("GP GPS Listener started")
		logging.debug("GP connecting to GPSd")
		gpsok = 0
		while gpsok == 0:
			try:
				gpsd = gps(mode=WATCH_ENABLE)
				gpsok = 1
			except Exception:
				logging.warn("GL Could not connect to GPSd .. retrying")
				time.sleep(3)
		logging.debug("GP connected to GPSd")
		for report in gpsd:
			GPSListener.lat = gpsd.fix.latitude
			GPSListener.lon = gpsd.fix.longitude
			GPSListener.alt = gpsd.fix.altitude
			GPSListener.fix = gpsd.fix.mode

