xplorer
=======

Software for the balloon project "XPlorer 25"

fmmod
======

complex frequency modulator for i/q signal processing

Usage: fmmod inputfile outputfile [carrier] [freqdev] [gain]

             inputfile: path to input file(needs to be single channel)
             outputfile: path to output file
             carrier: carrier frequency in Hz(standard: 0.0)
             freqdev: frequency deviation in Hz(standard: 3000)
             gain: factor for amplification of modulated signal(0.0 < gain < 1.0)

command for compiling:

make fmmod

missionctl
==========

connects the various modules to implement the actual mission schedule. it takes pictures from the camera, 
converts them to the format used by sstv, generates the SSTV and APRS signals, controls the release etc

transmitter
===========

implements a workqueue on the raspberry pi for files to send. with this logic, missionctl doesn't have to keep track
on transmitting files but instead just tells the workqueue to send a file as soon as the RF is free
