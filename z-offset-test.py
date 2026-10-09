#!/usr/bin/env python3
import sys
import re
from typing import Optional, List, Tuple

START_Z_VALUE     = 15         # first Z height to write, 0.15mm (0.05mm closer than a 0.2mm layer), 0.01mm increments

SCRIPT_NAME = 'z-offset-test.py'
SCRIPT_URL  = 'https://github.com/evilDave/z-offset-test'
TAG         = f'[{SCRIPT_NAME}]'   # prefixes every comment this script writes, so all changes can be found with one search

# captures the first X value on a line
X_RE = re.compile(r'X(-?\d+(?:\.\d+)?)', re.IGNORECASE)
E_RE = re.compile(r'E(-?\d*\.?\d+)', re.IGNORECASE)
Z_RE = re.compile(r'Z(-?\d*\.?\d+)', re.IGNORECASE)

def extract_x(line: str) -> Optional[float]:
    """Return the first X value in a G-code line (or None if absent)."""
    m = X_RE.search(line)
    return float(m.group(1)) if m else None


def extract_e(line: str) -> Optional[float]:
    """Return the E value in a G-code line (or None if absent)."""
    m = E_RE.search(line)
    return float(m.group(1)) if m else None


def extract_z(line: str) -> Optional[float]:
    """Return the Z value of a G0/G1 move (or None if absent)."""
    if not line.startswith(('G0', 'G1')):
        return None
    m = Z_RE.search(line.split(';', 1)[0])
    return float(m.group(1)) if m else None


def z_move_comment(last_z: Optional[float], new_z: int) -> str:
    """Describe the move from the previous Z height to new_z (in 0.01mm units)."""
    target = new_z / 100
    if last_z is None:
        return f';move Z to {target:.2f}mm\n'
    direction = 'up' if target > last_z else 'down'
    return f';move Z {direction} {abs(target - last_z):.2f}mm to {target:.2f}mm\n'


def determine_x_values(lines: List[str]) -> Tuple[float, float]:
    """Analyze G-code to determine long and short X values."""
    x_values = []
    current_x = None

    # Only the ends of extruding moves count: travel moves between lines (e.g. with the
    # Monotonic line pattern) stop near the line ends and would be mistaken for them.
    for line in lines:
        if line.startswith('G1'):
            x_val = extract_x(line)
            e_val = extract_e(line)
            if x_val is not None:
                if e_val is not None and e_val > 0:
                    if current_x is not None:
                        x_values.append(current_x)
                    x_values.append(x_val)
                current_x = x_val
    
    if not x_values:
        raise ValueError("No X values found in G-code")
    
    # Get all unique X values and sort them
    unique_x_values = sorted(set(x_values))
    
    if len(unique_x_values) < 3:
        raise ValueError("Need at least 3 different X values to determine long/short sections")
    
    # Find the midpoint between min and max to separate left and right boundaries
    min_x = min(unique_x_values)
    max_x = max(unique_x_values)
    midpoint = (min_x + max_x) / 2
    
    # Filter to only right boundary values (above midpoint)
    right_boundary_values = [x for x in unique_x_values if x > midpoint]
    
    if len(right_boundary_values) < 2:
        raise ValueError("Need at least 2 right boundary values to determine long/short sections")
    
    # Count frequency of each right boundary value
    from collections import Counter
    x_counter = Counter(x_values)
    
    # Get the two most common right boundary values
    right_boundary_counts = [(x, x_counter[x]) for x in right_boundary_values]
    right_boundary_counts.sort(key=lambda x: x[1], reverse=True)  # Sort by frequency
    
    # The most frequent is the long section, second most frequent is short section
    long_x = right_boundary_counts[0][0]
    short_x = right_boundary_counts[1][0]
    
    # Ensure there's a meaningful difference (at least 5 units)
    if abs(long_x - short_x) < 5:
        raise ValueError(f"Long and short X values too close: {long_x} vs {short_x}")
    
    print(f"Found X values: {unique_x_values}")
    print(f"Midpoint: {midpoint}")
    print(f"Right boundaries: {right_boundary_values}")
    print(f"Frequency counts: {right_boundary_counts}")
    
    return long_x, short_x


def main(path: str) -> None:
    with open(path) as f:
        lines = f.readlines()

    # First pass: find "printing object" line and determine X values
    printing_object_found = False
    lines_after_printing = []
    
    for line in lines:
        if "printing object" in line.lower():
            printing_object_found = True
            continue
        
        if printing_object_found:
            lines_after_printing.append(line)
    
    if not printing_object_found:
        print("Warning: 'printing object' not found, processing entire file")
        lines_after_printing = lines
    
    # Determine X values from the G-code
    try:
        long_x, short_x = determine_x_values(lines_after_printing)
        print(f"Determined: Long line X = {long_x}, Short line X = {short_x}")
    except ValueError as e:
        print(f"Error determining X values: {e}")
        # non-zero exit so the slicer reports the failure instead of silently exporting unmodified G-code
        sys.exit(f"{SCRIPT_NAME}: could not find the tab lines, G-code was not modified ({e})")
    
    # Second pass: process the file with determined values
    current_z = START_Z_VALUE
    in_short_section = False
    printing_object_encountered = False
    z_change_written = False
    current_x = None
    last_z = None

    with open(path, 'w') as out:
        out.write(f'; {TAG} This G-code was modified by {SCRIPT_NAME}\n')
        out.write(f'; {TAG} {SCRIPT_URL}\n')
        out.write(f'; {TAG} Z-offset calibration: before each test tab a Z height change (and beep) is added, so every\n')
        out.write(f'; {TAG} tab prints at a different nozzle height. Heights start at 0.{START_Z_VALUE}mm and step 0.01mm per tab.\n')
        out.write(f'; {TAG} Every added line is preceded by a comment starting with "{TAG}".\n')
        out.write('; Post‑processed to add Z moves before short lines\n')
        out.write(f'; Long line X: {long_x}, Short line X: {short_x}\n\n')

        for line in lines:
            z_val = extract_z(line)
            if z_val is not None:
                last_z = z_val

            # Check for "printing object" line
            if "printing object" in line.lower():
                printing_object_encountered = True
                out.write(line)
                continue
            
            # Before "printing object", just pass through unchanged
            if not printing_object_encountered:
                out.write(line)
                continue
            
            # After "printing object", apply the logic
            x_val = extract_x(line) if line.startswith('G1') else None
            e_val = extract_e(line) if line.startswith('G1') else None

            # Extruding into the tab area (past the short line end). Rounded tabs never reach
            # long_x exactly, so this is what marks a tab being printed.
            extruding_in_tab = (
                x_val is not None and
                e_val is not None and e_val > 0 and
                max(x_val, current_x if current_x is not None else x_val) > short_x + 1
            )

            # --- First tab: no gap comes before it, so set its height here ---
            if extruding_in_tab and not z_change_written:
                out.write(f'; {TAG} added the following 3 lines: Z height 0.{current_z}mm and beep for the next tab\n')
                out.write(z_move_comment(last_z, current_z))
                out.write(f'G1 Z.{current_z}\n')
                out.write(f'M300 P20 S{current_z}00\n')
                last_z = current_z / 100
                current_z += 1
                z_change_written = True

            # --- Entering a "short" section ---------------------------------
            if (
                x_val is not None and
                abs(x_val - short_x) < 0.001 and  # Use tolerance for float comparison
                not in_short_section
            ):
                out.write(f'; {TAG} added the following 3 lines: Z height 0.{current_z}mm and beep for the next tab\n')
                out.write(z_move_comment(last_z, current_z))
                out.write(f'G1 Z.{current_z}\n')
                out.write(f'M300 P20 S{current_z}00\n')
                last_z = current_z / 100
                current_z += 1
                in_short_section = True
                z_change_written = True

            # --- Leaving a "short" section ----------------------------------
            elif x_val is not None and (abs(x_val - long_x) < 0.001 or extruding_in_tab):
                in_short_section = False

            if x_val is not None:
                current_x = x_val

            # Write the original (unchanged) G‑code line
            out.write(line)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: z-offset-test.py <file.gcode>')
    main(sys.argv[1])
