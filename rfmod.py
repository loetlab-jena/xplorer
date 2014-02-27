#!/usr/bin/env python
#
# python wrapper for modulation and encoding methods

import os

gain = 0.5

def fmmod(in_fname, out_fname, fc):
	# call fmmod with its parameters
	os.system('./fmmod %s %s %s 3000 %s' % (in_fname, out_fname, str(fc), str(gain)))
	pass

def aprs(lat, lon, alt):
	os.system('./afsk-encoder.py %s %s %s aprs_enc.wav' % (str(lat), str(lon), str(alt)))
	os.system('resample -to 48000 aprs_enc.wav aprs_resamp.wav')
	fmmod('aprs_resamp.wav', 'aprs_fmmod.wav', 5000)
	pass

def sstv(in_fname, out_fname):
	os.system('./robot36 %s sstv_enc.wav' % in_fname)
	os.system('resample -to 48000 sstv_enc.wav sstv_resamp.wav')
	fmmod('sstv_resamp.wav', out_fname, 5000)
	pass
