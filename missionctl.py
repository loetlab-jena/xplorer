#!/usr/bin/env python
# the mission control module
#
# Handles the whole flight by connecting the various modules 
# to make up a transmitting schedule, controlling release of the ballon, etc
# 

# flight parameters
RISE_LOOPS = 20		# each is one minute 
STANDBY_LOOPS = 7	# each is three minutes

from transmitter import Transmitter
from gpslistener import GPSListener
import rfmod
import time
import logging
import os
import wave
import sys
import traceback

# import the GPIO modules only if we're running on a raspberry pi
pi = 1
try:
	import RPi.GPIO as GPIO
except ImportError:
	import gpio_dummy as GPIO
	pi = 0;

HEADSHOT = 4
LED = 10
RELEASE = 11
RELEASE_FB = 17

# helper functions

def release_payload():
	logging.info("MC releasing the payload")
	Transmitter.TXQueue.put(["snd/warn.wav", "145.200"])
	Transmitter.TXQueue.join()
	time.sleep(1)
	if not GPIO.input(RELEASE_FB):
		logging.debug("Switch was closed")
	else:
		logging.debug("Switch was open")
	GPIO.output(RELEASE, GPIO.HIGH)
	time.sleep(7)
	GPIO.output(RELEASE, GPIO.LOW)

def queue_numbers(value, filename):
	data = []
	length = 0
	# alternative: use sox
	try:
		for num in str(value):
			try:
				w = wave.open("snd/"+str(num)+".wav", "rb")
				data.append([ w.getparams(), w.readframes(w.getnframes())])
				w.close()
				length = length + 1
				logging.debug("File concatenated: "+str(num)+".wav")
			except IOError:
				logging.warn("File not found: "+str(num)+".wav")
	except Exception:
		logging.warn("MC Could not queue all numbers correctly")
	if length > 0:
		output = wave.open(filename, "wb")
		output.setparams(data[0][0])
		for row in data:
			output.writeframes(row[1])
		output.close()
		Transmitter.TXQueue.put([filename, "145.200"])

def send_aprs():
	lat = GPSListener.lat
	lon = GPSListener.lon
	alt = GPSListener.alt
	logging.debug("MC lat: "+ str(lat))
	logging.debug("MC lon: "+ str(lat))
	logging.debug("MC alt: "+ str(lat))
	try:
		latd = int(lat)
		latm = int((lat-latd)*60)
		lats = int(((lat-latd)*60-latm)*60)
		lond = int(lon)
		lonm = int((lon-lond)*60)
		lons = int(((lon-lond)*60-lonm)*60)
		rfmod.aprs(("%02.0f" % (latd,)) + ("%02.0f" % (latm,)) + "." + ("%02.0f" % (lats,)) + "N",
		("%03.0f" % (lond,)) + ("%02.0f" % (lonm,)) + "." + ("%02.0f" % (lons,)) + "E",
		"%06.0f" % (alt*3.28,))
	except Exception:
		logging.warn("MC Could not convert GPS data to APRS Format (No Fix?)")
	Transmitter.TXQueue.put(["aprs_fmmod.wav", "144.800"])

def log_uncaught_exceptions(ex_cls, ex, tb):
	logging.critical(''.join(traceback.format_tb(tb)))
	logging.critical('{0}: {1}'.format(ex_cls, ex))

sys.excepthook = log_uncaught_exceptions

# main software
# initate logging
logging.basicConfig(filename='xplorer.log', format='%(asctime)s %(levelname)s\t%(message)s', filemode='w', level=logging.DEBUG)
logging.info("MC Xplorer25 Software starting..")
if pi == 1:
	logging.debug("MC running on RPi")
else:
	logging.debug("MC running NOT on RPi")

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT) # status LED
GPIO.output(LED, GPIO.HIGH) # switch on to indicate software startup
GPIO.setup(RELEASE, GPIO.OUT) # release pin
GPIO.output(RELEASE, GPIO.LOW) # disable release
GPIO.setup(RELEASE_FB, GPIO.IN) # release feedback pin
GPIO.setup(HEADSHOT, GPIO.OUT) # set shutoff to output
GPIO.output(HEADSHOT, GPIO.LOW) # disable shutoff

# setup the transmitter thread
txthread = Transmitter()
txthread.setDaemon(True)
txthread.start()

# setup the GPS-listener thread
gpsthread = GPSListener()
gpsthread.setDaemon(True)
gpsthread.start()

# wait for at least a 2D-Fix from the GPS
while GPSListener.fix < 2:
	pass
logging.info("MC GPS fix OK")

# indicate GPS fix on LED 
for i in range(1,15):
	GPIO.output(LED, GPIO.HIGH)
	time.sleep(0.5)
	GPIO.output(LED, GPIO.LOW)
	time.sleep(0.5)

# mission start

# the loop takes 1 minute to run
flight = 1
ascending = 1
loopcnt = 0
sstv_file = 1
while flight == 1:
	time_st = time.time()
	os.system('raspistill -t 1 -o image.jpg')
	if sstv_file == 1:
		sstv_file = 2
		Transmitter.TXQueue.put(["sstv1.wav", "145.200"])
		rfmod.sstv("image.jpg", "sstv2.wav")
	else:
		sstv_file = 1
		Transmitter.TXQueue.put(["sstv2.wav", "145.200"])
		rfmod.sstv("image.jpg", "sstv1.wav")
	
	send_aprs()
	# get lan/lot/alt from gps
	tmp_lat = GPSListener.lat
	tmp_lon = GPSListener.lon
	tmp_alt = GPSListener.alt
	# queue numbers
	try:
		queue_numbers(str(tmp_lat*1000)[2:5], "lat.wav")
		queue_numbers(str(tmp_lon*1000)[2:5], "lon.wav")
		queue_numbers(int(tmp_alt), "alt.wav")
	except Exception:
		logging.warn("MC could not queue numbers properly");

	# wait for end of transmissions
	Transmitter.TXQueue.join()
	# handle state machine logic
	loopcnt = loopcnt + 1
	if loopcnt == RISE_LOOPS and ascending == 0:
		# we leave the loop after this run
		flight = 0
		loopcnt = 0
	if loopcnt == RISE_LOOPS and ascending == 1:
		# rerun the loop, now hopefully falling down...
		release_payload()
		loopcnt = 0
		ascending = 0
	try:
		time_en = time.time()
		time_delta = 60 - (time_en - time_st)
	except Exception:
		logging.warn("MC could not calculate time delta")
		time_delta = 10

	if time_delta > 0:
		logging.debug("MC waiting %f seconds till next loop" % time_delta)
		time.sleep(time_delta)
	else:
		logging.debug("MC loop took longer that 1 minute!")

logging.info("MC Stopping SSTV TX, entering Standby")
# we land here after the main mission is over, continue to send APRS every once in a while
while loopcnt < STANDBY_LOOPS:
	loopcnt = loopcnt + 1
	time_st = time.time()
	send_aprs()
	Transmitter.TXQueue.join()
	time_en = time.time()
	time_delta = 180 - (time_en - time_st)
	if time_delta > 0:
		logging.debug("MC waiting %f seconds till next loop" % time_delta)
		time.sleep(time_delta)
	else:
		logging.debug("MC loop took longer that 3 minutes!")

logging.info("MC Mission End!")
# wait additionally for all TX jobs to terminate
Transmitter.TXQueue.join()
os.system('sync')
GPIO.output(HEADSHOT, GPIO.HIGH)

