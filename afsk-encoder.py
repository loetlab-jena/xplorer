#!/usr/bin/env python
# AFSK1200 encoder for APRS packet radio
# Stefan Biereigel
# 
# proof of concept implementation
# will need sufficient optimisation (pre-calculated header FCS and/or output-data)
# for actual mission use
#
# created with input from
# http://n1vg.net/packet/
# http://www.tapr.org/pub_ax25.html
# http://vkalra.tripod.com/hdlc.html

from struct import pack
import sys
import wave
import math
import numpy

# setting parameters
fs = 44100 
fmark = 1200
fspace = 2200
baud = 1200
outfile = "out.wav"


def hdlc_encode(datastring):
	# add HDLC information
	# see AX25 spec for coding
	# 
	# dest address
	# source address
	# path (wide 1)
	# frame type (Unnumbered Information UI)
	# frame PID (0xF0)
	hdlcstring = [ 	ord('A')*2, ord('P')*2, ord('R')*2, ord('S')*2, ord(' ')*2, ord(' ')*2, 0x60,
			ord('D')*2, ord('K')*2, ord('3')*2, ord('S')*2, ord('B')*2, ord(' ')*2, 0x68,
			ord('W')*2, ord('I')*2, ord('D')*2, ord('E')*2, ord('1')*2, ord(' ')*2, 0x63,
			0x03, 0xf0]
	hdlcstring.extend(ord(a) for a in datastring)
	return hdlcstring

def fcs_calc(hdlcstring):
	# calculates the frame check sequence for every bit
	fcs = 0xffff
	for char in hdlcstring:
		for i in xrange(8):
			temp = fcs & 0x0001
			fcs = (fcs >> 1) & 0xffff
			if ( ((char >> i) & 1) != temp):
				fcs = fcs ^ 0x8408
	fcs = fcs ^ 0xffff
	return list(divmod(fcs, 0x100))

def create_bitstream(hdlcstring):
	# transforms the string of chars to an array of bits (highly inefficient, i guess)
	output = []
	ones = 0
	# add start flags
	for i in range(0,20):
		output.extend([0, 1, 1, 1, 1, 1, 1, 0])
	# add and bitstuff the data (incl. FCS)
	for char in hdlcstring:
		for i in xrange(8):
			output.append((char >> i) & 1)
			if (char >> i) & 1 == 1:
				ones = ones + 1
			else:
				ones = 0
			if (ones == 5):
				output.append(0)
				ones = 0
	# append end flag
	output.extend([0, 1, 1, 1, 1, 1, 1, 0])
	return output

def nrzi_encode(bitstream):
	# applies NRZI-coding to the created bitstream
	output = []
	last = 0
	for testbit in bitstream:
		if testbit == 0:
			last = int(not last)
		output.append(last)
	return output



def phase_acc(bitstream):
	# creates the NCO phase over time for the FSK signal
	tsym = 1.0/baud			# symbol time
	dt = 1.0/fs			# time step
	symsamp = tsym / dt		# samples per symbol
	symsamp = float(fs) / baud
	markinc = (2*math.pi*fmark) / fs;	# phase increment for mark
	spaceinc = (2*math.pi*fspace) / fs;	# phase increment for space
	phi = [0]
	bitcnt = 1
	# because of double precision baudrate is either 1210 or 1190 baud, but 10 baud seem to be too much error.
	# ones may be sent slower than zeros, to account for that
	# average baud rate is then 1200 baud
	# NOTE: this seems not to be needed for actual hardware decoder ICs, only for bad software implementation
	# (QTMM decoder was very senstive to this error)
	for bit in bitstream:
				if bit == 0:
					for i in range(0, int(symsamp)):
						phi.append(phi[-1] + markinc)
				if bit == 1:
					for i in range(0, int(symsamp)):
						phi.append(phi[-1] + spaceinc)
	return phi	

def write_output(phase, outfile):
	# creates the FSK signal from the phase over time signal and writes it to a wav-file
	# adds silence to begin and end, to account for TXdelay and sound card frame dropping
	outf = wave.open(outfile, 'w')
	outf.setparams((1, 2, fs, 0, 'NONE', 'not compressed'))

	data = ''
	for x in range(1,50000):
		data += pack('h', 0)
	for x in phase:
		data += pack('h', ((2**15)-20) * math.sin(x))
	for x in range(1,50000):
		data += pack('h', 0)

	outf.writeframes(data)
	outf.close()

def build_string(lat, lon, height):
	# builds a string from the input data
	# TODO: checks for data validity and type convert everything
	out = '!' + lat + 'Z' + lon + '-/A=' + height + ' Ballonmissionstest'
	return out

def build_packet(lat, lon, height, filename):
	if lat == '' or lon == '' or height == '' or filename == '':
		print 'ERROR: Check Parameters'
		return 1
	# add HDLC header to start
	message = build_string(lat, lon, height)
	hdlc = hdlc_encode(message)
	# calculate FCS
	fcs = fcs_calc(hdlc)
	fcs.reverse()
	hdlc.extend(fcs);
	# create bitstream
	output = create_bitstream(hdlc);
	# encode nrzi
	nrzi = nrzi_encode(output)
	# encode afsk
	phi = phase_acc(nrzi)
	# write output file
	write_output(phi, filename)
	return 0


def main():
	build_packet('5055.42N', '01152.75E', '000300', 'aprs.wav')

main()
