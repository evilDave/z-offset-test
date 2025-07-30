#!/usr/bin/env python3
import sys

# Thresholds for detecting normal and short lines
SHORT_LINE_X_VALUE = 134.769
NORMAL_LINE_X_VALUE = 144.769

# Starting Z value
START_Z_VALUE = 21

# Read the G-code file path from command line arguments
file = sys.argv[1]

# Read the entire G-code file into memory
with open(file, "r") as f:
    lines = f.readlines()

# Initialize the Z value counter and tracking variables
current_z_value = START_Z_VALUE
in_short_section = False

# Overwrite the G-code file
with open(file, "w") as of:
    # Add a header indicating the file was postprocessed
    of.write('; Postprocessed to add Z commands before short lines\n\n')

    for i in range(len(lines)):
        line = lines[i]

        # Check if the line contains a short X value
        if f"X{SHORT_LINE_X_VALUE}" in line and not in_short_section:
            # Insert the G1 Z.nn command before the first short line in the section
            of.write(f"G1 Z.{current_z_value}\n")
            of.write(f"M300 P20 S{current_z_value}00\n")
            current_z_value += 1
            in_short_section = True

        # Check if the line contains a normal X value
        elif f"X{NORMAL_LINE_X_VALUE}" in line:
            # Reset the short section flag after encountering a normal line
            in_short_section = False

        # Write the original line back to the file
        of.write(line)
