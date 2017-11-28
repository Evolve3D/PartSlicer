# PartSlicer

This is a simple tool to split a gcode file into multiple individual gcode files to be printed.
The parts are sliced in a way that it allows multicolor print with single extruder. 
This is just another way of doing the job by multiple gcode files rather than having one gcode file to finish it all.
Also useful in situation where the 3d printer's firmware cannot be modified hence unable to add multicolor printing function by the mean of updating firmware.

Features:
- Slice one gcode into multiple by specifying layer numbers
- Heat bed is kept turned on after parts print and only turn off after the final part

Usage:
- Before you start make sure python 2.7 is installed
- Put your stl file in Cura and slice it with "Z Hop when retracted" turned on
- Open the script via console and you will will know what to do
- Oh, the script works only inside the directory it is in, so make sure you move the master gcode file to the same folder to work on it
