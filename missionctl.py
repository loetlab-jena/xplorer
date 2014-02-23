#!/usr/bin/env python3
# the mission control module
#
# Handles the whole flight by connecting the various modules 
# to make up a transmitting schedule, controlling release of the ballon, etc
# 

from transmitter import Transmitter
import time

txthread = Transmitter()
txthread.setDaemon(True)
txthread.start()

time.sleep(1)
print("2 files queued")
Transmitter.TXQueue.put(["test.wav", "144.500"])
Transmitter.TXQueue.put(["test2.wav", "144.500"])

time.sleep(3)
print("1 file queued")
Transmitter.TXQueue.put(["test3.wav", "145.200"])
Transmitter.TXQueue.join()
