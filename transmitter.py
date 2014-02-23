#!/usr/bin/env python3
# The RF-Control module
#
# Stefan Biereigel
#
# Implements a thread and workqueue where any file to be transmitted and the corresponding frequency can be input. 

import threading
import queue
import time
import logging

class Transmitter(threading.Thread):
	TXQueue = queue.Queue()

	def run(self):
		while True: 
			transmission = Transmitter.TXQueue.get()
			logging.info("TX File TX started: Filename: " + transmission[0] + "\tFrequency: "+transmission[1])
			# TODO check for existence of file, abort if not found
			# TODO activate PA
			# TODO set LO frequency
			# TODO play the audio file
			# TODO deactivate LO and PA
			time.sleep(5)
			logging.info("TX File TX finished")
			Transmitter.TXQueue.task_done()
