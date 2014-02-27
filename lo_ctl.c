/* controller for local oscillator(GPCLK0)
 * Sebastian Weiss <dl3yc@darc.de>
 * heavily based on PiFM(http://www.icrobotics.co.uk/wiki/index.php/Turning_the_Raspberry_Pi_Into_an_FM_Transmitter)
 */

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <ctype.h>
#include <math.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <signal.h>
#include <malloc.h>

#define BCM2708_PERI_BASE 0x20000000
#define GPIO_BASE (BCM2708_PERI_BASE + 0x200000)
#define PAGE_SIZE (4*1024)
#define BLOCK_SIZE (4*1024)

int  mem_fd;
char *gpio_mem, *gpio_map;

volatile unsigned *gpio = NULL;
volatile unsigned *allof7e = NULL;

#define ACCESS(base) *(volatile int*)((int)allof7e+base-0x7e000000)
#define SETBIT(base, bit) ACCESS(base) |= 1<<bit
#define CLRBIT(base, bit) ACCESS(base) &= ~(1<<bit)
#define CM_GP0CTL (0x7e101070)
#define GPFSEL0 (0x7E200000)
#define PADS_GPIO_0_27  (0x7e10002c)
#define CM_GP0DIV (0x7e101074)

struct GPCTL {
    char SRC         : 4;
    char ENAB        : 1;
    char KILL        : 1;
    char             : 1;
    char BUSY        : 1;
    char FLIP        : 1;
    char MASH        : 2;
    unsigned int     : 13;
    char PASSWD      : 8;
};

void txctl(int state, int strength)
{
    SETBIT(GPFSEL0 , 14);
    CLRBIT(GPFSEL0 , 13);
    CLRBIT(GPFSEL0 , 12);

    ACCESS(PADS_GPIO_0_27) = 0x5a000018 + 4; // 50Ohm Ausgangswiderstand

    struct GPCTL setupword = {5, state, 0, 0, 0, 1,0x5a};
    ACCESS(CM_GP0CTL) = *((int*)&setupword);
}

void usage(void)
{
    printf("Usage: lo_ctl on/off [frequency] [driver strength]\n");
}

int main(int argc, char *argv[])
{
    int state;
    double frequency;
    int strength;

    if ((argc > 4) || (argc < 2)) {
        usage();
        return 1;
    }

    if(strcmp(argv[1],"on")==0) {
        state = 1;
    }
    else if(strcmp(argv[1],"off")==0) {
        state = 0;
    }
    else {
        usage();
        return 1;
    }

    frequency = (argc > 2) ? atof(argv[2]) : 0.0;
    strength = (argc = 4) ? atof(argv[3]) : 8;

    if ((mem_fd = open("/dev/mem", O_RDWR|O_SYNC) ) < 0) {
        printf("%s: can't open /dev/mem, try it as root\n", argv[0]);
        return 1;
    }

    /* Allocate MAP block */
    if ((gpio_mem = malloc(BLOCK_SIZE + (PAGE_SIZE-1))) == NULL) {
        printf("%s, gpio allocation error \n", argv[0]);
        return 1;
    }

    /* Make sure pointer is on 4K boundary */
    if ((unsigned long)gpio_mem % PAGE_SIZE)
        gpio_mem += PAGE_SIZE - ((unsigned long)gpio_mem % PAGE_SIZE);

    gpio_map = (unsigned char *)mmap(
        gpio_mem,
        BLOCK_SIZE,
        PROT_READ|PROT_WRITE,
        MAP_SHARED|MAP_FIXED,
        mem_fd,
        GPIO_BASE
    );

    if ((long)gpio_map < 0) {
        printf("%s, mmap error %d\n", argv[0], (int)gpio_map);
        return 1;
    }

    gpio = (volatile unsigned *)gpio_map;

    allof7e = (unsigned *)mmap(
	NULL,
	0x01000000,  //len
	PROT_READ|PROT_WRITE,
	MAP_SHARED,
	mem_fd,
	0x20000000  //base
	);
    if ((int)allof7e == -1) {
	    printf("%s, allof7e error\n", argv[0]);
	    return 1;
    }

    txctl(state, strength);
    // TODO: convert frequency to DIVI and DIVF + function/macro setfreq(divi,divf)
    ACCESS(CM_GP0DIV) = (0x5a << 24) | (6 << 12) | (896<<2); // 6, 928 für aprs 144,796; 6, 912 für 145,125; 6, 896 für 145,450
    return 0;
}
