#!/usr/bin/env python
# The RF-Control module
#
# Stefan Biereigel
#
# Implements a thread and workqueue where any file to be transmitted and the corresponding frequency can be input. 

import threading
import Queue
import time
import logging

# import the GPIO modules only if we're running on a raspberry pi
pi = 1
try:
	import RPi.GPIO as GPIO
except ImportError:
	import gpio_dummy as GPIO

RF_ENBL = 18

class Transmitter(threading.Thread):
	TXQueue = Queue.Queue()

	def run(self):
		if pi == 1:
			GPIO.setup(RF_ENBL, GPIO.OUT) # RF enable pin is output
			GPIO.output(RF_ENBL, GPIO.LOW) # switch it off
		while True: 
			transmission = Transmitter.TXQueue.get()
			logging.info("TX File TX started: Filename: " + transmission[0] + "\tFrequency: "+transmission[1])
			GPIO.output(RF_ENBL, GPIO.HIGH)
			# TODO set LO frequency
			os.system('aplay -D hw:1,0 %s' % transmission[0])
			# TODO this needs checking: is empty() only valid after we do task_done()?
			GPIO.output(RF_ENBL, GPIO.LOW)
			logging.info("TX File TX finished")
			Transmitter.TXQueue.task_done()
