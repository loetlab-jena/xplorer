#!/usr/bin/env python
# the mission control module
#
# Handles the whole flight by connecting the various modules 
# to make up a transmitting schedule, controlling release of the ballon, etc
# 

from transmitter import Transmitter
from gpslistener import GPSListener
import time
import logging

# import the GPIO modules only if we're running on a raspberry pi
pi = 1
try:
	import RPi.GPIO as GPIO
except ImportError:
	import gpio_dummy as GPIO
	pi = 0;

LED = 21

# initate logging
logging.basicConfig(filename='xplorer.log', format='%(asctime)s %(levelname)s\t%(message)s', filemode='w', level=logging.DEBUG)
logging.info("MC Xplorer25 Software starting..")
if pi == 1:
	logging.debug("MC running on RPi")
else:
	logging.debug("MC running NOT on RPi")

GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED, GPIO.OUT) # status LED
GPIO.output(LED, GPIO.HIGH) # switch on to indicate software startup

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

# indicate GPS fix on LED (blinking)
for i in range(1,60):
	GPIO.output(LED, GPIO.HIGH)
	time.sleep(1)
	GPIO.output(LED, GPIO.LOW)
	time.sleep(1)

logging.info("MC GPS fix OK")

time.sleep(1)
logging.info("MC APRS und Ansage queued")
Transmitter.TXQueue.put(["test.wav", "144.500"])
Transmitter.TXQueue.put(["test2.wav", "144.500"])

time.sleep(3)
logging.info("MC SSTV queued")
Transmitter.TXQueue.put(["test3.wav", "145.200"])

Transmitter.TXQueue.join()
logging.info("MC Absprengung")
Transmitter.TXQueue.put(["test4.wav", "145.200"])

# Ende
Transmitter.TXQueue.join()

