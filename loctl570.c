/* loctl570 - userspace control software for SI570
 *
 * heavily based on the Linux Kernel Driver clk-si570.c
 * written by Guenter Roeck and Sören Brinkmann 
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */

#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

#include <linux/i2c-dev.h>

/* Si570 registers */
#define SI570_REG_HS_N1		7
#define SI570_REG_N1_RFREQ0	8
#define SI570_REG_CONTROL	135
#define SI570_REG_FREEZE_DCO	137

#define HS_DIV_SHIFT		5
#define HS_DIV_OFFSET		4
#define N1_6_2_MASK		0x1f
#define RFREQ_37_32_MASK	0x3f

#define FDCO_MIN		4850000000LL
#define FDCO_MAX		5670000000LL

#define SI570_CNTRL_NEWFREQ	(1 << 6)

#define SI570_FREEZE_DCO	(1 << 4)

/**
 * globals 
 * @fxtal:	Factory xtal frequency
 * @n1:		Clock divider N1
 * @hs_div:	Clock divider HSDIV
 * @rfreq:	Clock multiplier RFREQ
 * @frequency:	Current output frequency
 */
uint64_t fxtal = 114285000ULL;
unsigned int n1;
unsigned int hs_div;
uint64_t rfreq;
int file; 

/**
 * si570_update_rfreq() - Update clock multiplier
 */
int si570_update_rfreq(void)
{
	uint8_t reg[5];

	reg[0] = ((n1 - 1) << 6) |
		((rfreq >> 32) & RFREQ_37_32_MASK);
	reg[1] = (rfreq >> 24) & 0xff;
	reg[2] = (rfreq >> 16) & 0xff;
	reg[3] = (rfreq >> 8) & 0xff;
	reg[4] = rfreq & 0xff;

	i2c_smbus_write_byte_data(file, SI570_REG_N1_RFREQ0 + 0, reg[0]);
	i2c_smbus_write_byte_data(file, SI570_REG_N1_RFREQ0 + 1, reg[1]);
	i2c_smbus_write_byte_data(file, SI570_REG_N1_RFREQ0 + 2, reg[2]);
	i2c_smbus_write_byte_data(file, SI570_REG_N1_RFREQ0 + 3, reg[3]);
	i2c_smbus_write_byte_data(file, SI570_REG_N1_RFREQ0 + 4, reg[4]);
}

/**
 * si570_calc_divs() - Caluclate clock dividers
 * @frequency:	Target frequency
 * @out_rfreq:	RFREG fractional multiplier (output)
 * @out_n1:	Clock divider N1 (output)
 * @out_hs_div:	Clock divider HSDIV (output)
 *
 * Calculate the clock dividers (@out_hs_div, @out_n1) and clock multiplier
 * (@out_rfreq) for a given target @frequency.
 */
int si570_calc_divs(unsigned long frequency, 
		uint64_t *out_rfreq, unsigned int *out_n1, unsigned int *out_hs_div)
{
	int i;
	unsigned int n1, hs_div;
	uint64_t fdco, best_fdco = ULLONG_MAX;
	static const uint8_t si570_hs_div_values[] = { 11, 9, 7, 6, 5, 4 };

	/* run through all hs_div_values */
	for (i = 0; i < 6; i++) {
		hs_div = si570_hs_div_values[i];
		/* Calculate lowest possible value for n1 */
		n1 = (uint64_t)((uint64_t)FDCO_MIN / (uint32_t)hs_div) / (uint32_t)frequency;
		if (!n1 || (n1 & 1))
			n1++;
		while (n1 <= 128) {
			fdco = (uint64_t)frequency * (uint64_t)hs_div * (uint64_t)n1;
			printf("fdco: %llu\n", fdco);
			if (fdco > FDCO_MAX)
				break;
			if (fdco >= FDCO_MIN && fdco < best_fdco) {
				*out_n1 = n1;
				*out_hs_div = hs_div;
				*out_rfreq = (uint64_t)(fdco << 28) / (uint64_t)fxtal;
				best_fdco = fdco;
				printf("found\n");
			}
			n1 += (n1 == 1 ? 1 : 2);
		}
	}

	if ( best_fdco == ULLONG_MAX ) {
		printf("Error calculating Divider values\n");
		return -1;
	}
	printf("n1: %d, hsdiv %d, rfreq %llu\n", *out_n1, *out_hs_div, *out_rfreq);
	return 0;
}

/**
 * si570_set_frequency() - Adjust output frequency
 * @frequency:	Target frequency
 * Returns 0 on success.
 *
 */
int si570_set_frequency(unsigned long frequency)
{
	int err;

	err = si570_calc_divs(frequency, &rfreq, &n1,
			&hs_div);
	if (err)
		return err;

	i2c_smbus_write_byte_data(file, SI570_REG_FREEZE_DCO, SI570_FREEZE_DCO);
	i2c_smbus_write_byte_data(file, SI570_REG_HS_N1,
			((hs_div - HS_DIV_OFFSET) << HS_DIV_SHIFT) |
			(((n1 - 1) >> 2) & N1_6_2_MASK));
	si570_update_rfreq();
	i2c_smbus_write_byte_data(file, SI570_REG_FREEZE_DCO, 0);
	i2c_smbus_write_byte_data(file, SI570_REG_CONTROL, SI570_CNTRL_NEWFREQ);

	return 0;
}

int main(int argc, char *argv[]) {
	int adapter_nr = 1; 	/* raspberry pi GPIO header i2c bus */
	int addr = 0x55;	/* SI570 i2c address */
	char filename[20];	/* filename to open for i2c-dev */
	unsigned long frequency;

	if (argc != 2) {
		printf("Usage: %s frequency\nFrequency is given in Hz\n", argv[0]);
		return 1;
	}
	frequency = strtoul(argv[1], NULL, 10);
	printf("Setting Frequency to %lu Hz\n", frequency);
  
	snprintf(filename, 19, "/dev/i2c-%d", adapter_nr);
	file = open(filename, O_RDWR);
	if (file < 0) {
		printf("Error opening file, retry as root.\n");
		return 1;
	}
	
	if (ioctl(file, I2C_SLAVE, addr) < 0) {
		printf("Error ioctl'ing the i2c-adapter.\n");
		return 1;
	}

	si570_set_frequency(frequency);	

	return 0;
}
