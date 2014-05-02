#!/bin/bash

# Save a camera picture every minute

filename=$(ls -1 /home/pi/missions/ | wc -l)
raspistill -t 1 -o /home/pi/missions/$filename.jpg

