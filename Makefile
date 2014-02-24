OBJ=fmmod.o robot36.o loctl.o
BIN=fmmod robot36 loctl
LIBS=-lsndfile -ljpeg -lm

all: $(BIN)

robot36: robot36.o 
	$(CC) -orobot36 robot36.o $(LIBS)

fmmod: fmmod.o
	$(CC) -ofmmod fmmod.o $(LIBS)

loctl: loctl.o
	$(CC) -oloctl loctl.o

.PHONY: clean
clean:
	rm -f $(BIN) $(OBJ)
