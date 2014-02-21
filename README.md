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

gcc fmmod.c -lsndfile -lm -ofmmod -Wall
