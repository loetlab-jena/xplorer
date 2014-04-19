#!/usr/bin/env python
# the mission control module
#
# Handles the whole flight by connecting the various modules 
# to make up a transmitting schedule, controlling release of the ballon, etc
# 

# flight parameters
RISE_LOOPS = 2		# each is one minute 
STANDBY_LOOPS = 2	# each is three minutes

from transmitter import Transmitter
from gpslistener import GPSListener
import rfmod
import time
import logging
import os
import wave

# import the GPIO modules only if we're running on a raspberry pi
pi = 1
try:
	import RPi.GPIO as GPIO
except ImportError:
	import gpio_dummy as GPIO
	pi = 0;

HEADSHOT = 10
LED = 18
RELEASE = 27
RELEASE_FB = 17 

# helper functions

def release_payload():
	logging.info("MC releasing the payload")
	Transmitter.TXQueue.put(["snd/warn.wav", "145.200"])
	if not GPIO.input(RELEASE_FB):
		logging.debug("Switch was closed")
		# if the switch is still closed, heat until it's open
		GPIO.output(RELEASE, GPIO.HIGH)
		# TODO timeout!!!11
		while not GPIO.input(RELEASE_FB):
			pass
		GPIO.output(RELEASE, GPIO.LOW)
	else:
		logging.debug("Switch was open")
		# if the switch was open, heat half a second
		GPIO.output(RELEASE, GPIO.HIGH)
		time.sleep(0.5)
		GPIO.output(RELEASE, GPIO.LOW)

def queue_numbers(value, filename):
	data = []
	length = 0
	# alternative: use sox
	for num in str(value):
		try:
			w = wave.open("snd/"+str(num)+".wav", "rb")
			data.append([ w.getparams(), w.readframes(w.getnframes())])
			w.close()
			length = length + 1
			logging.debug("File concatenated: "+str(num)+".wav")
		except IOError:
			logging.warn("File not found: "+str(num)+".wav")
	if length > 0:
		output = wave.open(filename, "wb")
		output.setparams(data[0][0])
		for row in data:
			output.writeframes(row[1])
		output.close()
		Transmitter.TXQueue.put([filename, "145.200"])

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

# indicate GPS fix on LED (blinking for 1 minute)
# TODO: UNCOMMENT WHEN FINISHED TESTING
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
	
	# get lan/lot/alt from gps
	tmp_lat = GPSListener.lat
	tmp_lon = GPSListener.lon
	tmp_alt = GPSListener.alt
	# TODO check if nan etc is a problem, should be no problem as they are directly inserted as a string
	rfmod.aprs("%04.2f" % (GPSListener.lat*100,) + "N", 
		"%04.2f" % (GPSListener.lon*100,) + "E", 
		"%06.0f" % (GPSListener.alt,))
	Transmitter.TXQueue.put(["aprs_fmmod.wav", "144.800"])
	# queue numbers
	queue_numbers(str(tmp_lat*1000)[2:5], "lat.wav")
	queue_numbers(str(tmp_lon*1000)[2:5], "lon.wav")
	queue_numbers(int(tmp_alt), "alt.wav")

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
	time_en = time.time()
	time_delta = 60 - (time_en - time_st)
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
	rfmod.aprs("%04.2f" % (GPSListener.lat*100,) + "N", 
		"%04.2f" % (GPSListener.lon*100,) + "E", 
		"%06.0f" % (GPSListener.alt,))
	Transmitter.TXQueue.put(["aprs_fmmod.wav", "144.800"])
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

