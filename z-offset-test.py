#!/usr/bin/env python3
import sys
import re
from typing import Optional, List, Tuple

START_Z_VALUE     = 21         # first Z height to write, 0.21mm, 0.01mm increments

# captures the first X value on a line
X_RE = re.compile(r'X(-?\d+(?:\.\d+)?)', re.IGNORECASE)

def extract_x(line: str) -> Optional[float]:
    """Return the first X value in a G-code line (or None if absent)."""
    m = X_RE.search(line)
    return float(m.group(1)) if m else None


def determine_x_values(lines: List[str]) -> Tuple[float, float]:
    """Analyze G-code to determine long and short X values."""
    x_values = []
    
    for line in lines:
        if line.startswith('G1'):
            x_val = extract_x(line)
            if x_val is not None:
                x_values.append(x_val)
    
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
        return
    
    # Second pass: process the file with determined values
    current_z = START_Z_VALUE
    in_short_section = False
    printing_object_encountered = False

    with open(path, 'w') as out:
        out.write('; Post‑processed to add Z moves before short lines\n')
        out.write(f'; Long line X: {long_x}, Short line X: {short_x}\n\n')

        for line in lines:
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

            # --- Entering a "short" section ---------------------------------
            if (
                x_val is not None and
                abs(x_val - short_x) < 0.001 and  # Use tolerance for float comparison
                not in_short_section
            ):
                out.write(f';move Z up 0.01mm\n')
                out.write(f'G1 Z.{current_z}\n')
                out.write(f'M300 P20 S{current_z}00\n')
                current_z += 1
                in_short_section = True

            # --- Leaving a "short" section ----------------------------------
            elif x_val is not None and abs(x_val - long_x) < 0.001:
                in_short_section = False

            # Write the original (unchanged) G‑code line
            out.write(line)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: z-offset-test.py <file.gcode>')
    main(sys.argv[1])
