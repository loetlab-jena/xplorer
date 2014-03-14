#!/usr/bin/env python
#
# dummy routines for GPIO
# if not running on a raspberry pi, here are stubs for the GPIO functions

import logging

IN = 0
OUT = 1
LOW = 0
HIGH = 1
BOARD = 1
BCM = 2

def setmode(mode):
	logging.debug("DM GPIO mode was set to %d" % mode)

def setup(number, mode):
	logging.debug("DM GPIO %d mode set: %d" %  (number, mode))

def output(number, value):
	logging.debug("DM GPIO %d new value: %d" % (number, value))

def input(number, value):
	logging.debug("DM GPIO %d status requested." % number)
	return HIGH


