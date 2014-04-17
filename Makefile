BIN=fmmod robot36 loctl loctl570
LIBS=-lsndfile -ljpeg -lm

all: $(BIN)

robot36: 
	$(CC) -orobot36 robot36.c $(LIBS)

fmmod: 
	$(CC) -ofmmod fmmod.c $(LIBS)

loctl: 
	$(CC) -oloctl loctl.c

loctl570:
	$(CC) -oloctl570 loctl570.c

.PHONY: clean
clean:
	rm -f $(BIN) $(OBJ)
	rm -f *.jpg *.wav
	rm -f *.log
