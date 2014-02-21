/* complex frequency modulator for i/q signal processing
 * Sebastian Weiss <dl3yc@darc.de>
 */

#include <stdio.h>
#include <stdlib.h>
#include <sndfile.h>
#include <math.h>

#define BUFFER_LEN  1024

void usage(void)
{
    printf("Usage: fmmod inputfile outputfile [carrier] [freqdev] [gain]\n \
            inputfile: path to input file(needs to be single channel)\n \
            outputfile: path to output file\n \
            carrier: carrier frequency in Hz(standard: 0.0)\n \
            freqdev: frequency deviation in Hz(standard: 3000)\n \
            gain: factor for amplification of modulated signal(0.0 < gain < 1.0)\n");
}

void process_data(double *data, int count, int fs, double fc, double freqdev, double gain)
{
    static double old_phase = 0.0;
    double cumsum[BUFFER_LEN];
    double phase;
    int i;

    if (count == 0)
        return;

    cumsum[0] = data[0]/fs;
    for (i = 1; i < count; i++) {
        cumsum[i] = cumsum[i-1] + data[i]/fs;
    }

    for (i=0; i < count; i++) {
        phase = 2*M_PI*fc/fs*(i+1) + 2*M_PI*freqdev*cumsum[i] + old_phase;
        data[2*i] = gain * cos(phase);
        data[2*i + 1] = - gain * sin(phase);
    }

    old_phase = fmod(phase, 2*M_PI);
    return;
}

int main(int argc, char *argv[])
{
    static double data[2*BUFFER_LEN];
    SNDFILE *infile, *outfile;
    SF_INFO sfinfo;
    int readcount;
    double carrier;
    double freqdev;
    double gain;

    if ((argc > 6) || (argc < 3)) {
        usage();
        return 1;
    }

    freqdev = (argc == 5) ? atof(argv[4]) : 3000.0;
    carrier = (argc > 3) ? atof(argv[3]) : 0.0;
    gain = (argc == 6) ? atof(argv[5]) : 1.0;
    
    if (freqdev < 0.0) {
        printf("%s: negative frequency deviation is unsupported\n", argv[0]);
        return 1;
    }
    
    if ((gain < 0.0) || (gain > 1.0)) {
        printf("%s: gain parameter is outside of range(0.0..1.0)\n", argv[0]);
        return 1;
    }
    
    infile = sf_open(argv[1], SFM_READ, &sfinfo);
    if (!infile) {
        printf("%s: Not able to open input file %s\n", argv[0], argv[1]);
        sf_perror(NULL);
        return 1;
    }

    if (sfinfo.channels > 1) {
        printf("%s: Not able to process more than 1 channel\n", argv[0]);
        return 1;
    }
    
    if (abs(carrier) + abs(freqdev) >= sfinfo.samplerate / 2.0) {
        printf("%s: Given carrier frequency, frequency deviation and samplerate are not able to comply with nyquist criterion\n", argv[0]);
        return 1;
    }

    sfinfo.channels = 2;

    outfile = sf_open(argv[2], SFM_WRITE, &sfinfo);
    if (!outfile) {
        printf("%s: Not able to open output file %s\n", argv[0], argv[2]);
        sf_perror(NULL);
        return 1;
    }

    while ((readcount = sf_read_double(infile, data, BUFFER_LEN))) {
        process_data(data, readcount, sfinfo.samplerate, carrier, freqdev, gain);
        sf_write_double(outfile, data, 2*readcount);
    }

    sf_close(infile);
    sf_write_sync(outfile);
    sf_close(outfile);

    return 0;
}
