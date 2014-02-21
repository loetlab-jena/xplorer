OBJ=fmmod.o robot36.o
BIN=fmmod robot36
LIBS=-lsndfile -ljpeg -lm

all: ($BIN)

robot36: robot36.o
	$(CC) -orobot36 robot36.o $(LIBS)

fmmod: fmmod.o
	$(CC) -ofmmod fmmod.o $(LIBS)

.PHONY: clean
clean:
	rm -f $(BIN) $(OBJ)
