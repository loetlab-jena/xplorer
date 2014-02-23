#!/usr/bin/env python3
# the mission control module
#
# Handles the whole flight by connecting the various modules 
# to make up a transmitting schedule, controlling release of the ballon, etc
# 

from transmitter import Transmitter
import time
import logging

# initate logging
logging.basicConfig(filename='xplorer.log', format='%(asctime)s %(levelname)s\t%(message)s', filemode='w', level=logging.DEBUG)
logging.info("MC\tXplorer25 Software starting..")

# setup the transmitter thread
txthread = Transmitter()
txthread.setDaemon(True)
txthread.start()

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

