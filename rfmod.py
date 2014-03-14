#!/usr/bin/env python
#
# python wrapper for modulation and encoding methods

import os
import afskencoder

gain = 0.5

def fmmod(in_fname, out_fname, fc):
	# call fmmod with its parameters
	os.system('./fmmod %s %s %s 3000 %s' % (in_fname, out_fname, str(fc), str(gain)))
	pass

def aprs(lat, lon, alt):
	# no LO offset needed
	afskencoder.build_packet(str(lat), str(lon), str(alt), 'aprs_enc.wav')
	os.system('rm aprs_resamp.wav')
	os.system('resample -to 48000 aprs.wav aprs_resamp.wav')
	fmmod('aprs_resamp.wav', 'aprs_fmmod.wav', 0)
	pass

def sstv(in_fname, out_fname):
	# no LO offset needed
	os.system('convert %s -resize 320x240 -rotate 180 sstv.jpg' % in_fname)
	os.system('./robot36 sstv.jpg sstv_enc.wav')
	os.system('rm sstv_resamp.wav')
	os.system('resample -to 48000 sstv_enc.wav sstv_resamp.wav')
	fmmod('sstv_resamp.wav', out_fname, 0)
	pass
