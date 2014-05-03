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
import os
from uuid import getnode as get_mac

# import the GPIO modules only if we're running on a raspberry pi
pi = 1
try:
	import RPi.GPIO as GPIO
except ImportError:
	import gpio_dummy as GPIO

PA_ENBL = 7
MOD_ENBL = 9
PRE_ENBL = 8
	
def rfon():
	GPIO.output(PA_ENBL, GPIO.HIGH)
	GPIO.output(MOD_ENBL, GPIO.HIGH)
	GPIO.output(PRE_ENBL, GPIO.LOW)

def rfoff():
	GPIO.output(PA_ENBL, GPIO.LOW)
	GPIO.output(MOD_ENBL, GPIO.LOW)
	GPIO.output(PRE_ENBL, GPIO.HIGH)

class Transmitter(threading.Thread):
	TXQueue = Queue.Queue()

	def run(self):
		if pi == 1:
			GPIO.setup(PA_ENBL, GPIO.OUT) # RF enable pin is output
			GPIO.setup(MOD_ENBL, GPIO.OUT) # RF enable pin is output
			GPIO.setup(PRE_ENBL, GPIO.OUT) # RF enable pin is output
			rfoff();
		while True: 
			try:
				transmission = Transmitter.TXQueue.get()
				rfon()
				mac = get_mac();
				if int(mac) == int(0xb827ebbae859): 
					# Raspberry B
					logging.debug("TX Raspberry B, using 10kHz SI offset")
					if transmission[1] == "144.800":
						ret = os.system('./loctl570 144810000')
					else:
						ret = os.system('./loctl570 145210000')
				else:
					logging.debug("TX Raspberry A, using 5kHz SI offset")
					if transmission[1] == "144.800":
						ret = os.system('./loctl570 144805000')
					else:
						ret = os.system('./loctl570 145205000')
	
				if ret:
					logging.warn("TX Error setting LO frequency")
				logging.info("TX File TX started: Filename: " + transmission[0] + "\tFrequency: "+transmission[1])
				os.system('aplay -D hw:1,0 %s' % transmission[0])
				Transmitter.TXQueue.task_done()
				if Transmitter.TXQueue.empty():
					rfoff()
				logging.info("TX File TX finished")
			except Exception:
				logging.warn("TX could not get transmission..")
