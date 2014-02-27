BIN=fmmod robot36 loctl
LIBS=-lsndfile -ljpeg -lm

all: $(BIN)

robot36: 
	$(CC) -orobot36 robot36.c $(LIBS)

fmmod: 
	$(CC) -ofmmod fmmod.c $(LIBS)

loctl: 
	$(CC) -oloctl loctl.c

.PHONY: clean
clean:
	rm -f $(BIN) $(OBJ)
	rm -f *.jpg *.wav
