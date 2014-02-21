#

CFLAGS=-I/u0/markv/include -g
LDFLAGS=-L/u0/markv/lib 
LIBS=-lsndfile -ljpeg -lm

all: robot36 fmmod

robot36: robot36.o
	$(CC) -orobot36 $(LDFLAGS) robot36.o $(LIBS)

fmmod: fmmod.o
	$(CC) -ofmmod $(LDFLAGS) fmmod.o $(LIBS)
