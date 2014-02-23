#!/usr/bin/env python3
# The RF-Control module
#
# Stefan Biereigel
#
# Implements a thread and workqueue where any file to be transmitted and the corresponding frequency can be input. 

import threading
import queue
import time

class Transmitter(threading.Thread):
	TXQueue = queue.Queue()

	def run(self):
		while True: 
			transmission = Transmitter.TXQueue.get()
			print("Filename: " + transmission[0] + "\tFrequency: "+transmission[1])
			# TODO set LO frequency
			# TODO play the audio file
			time.sleep(1)
			Transmitter.TXQueue.task_done()
