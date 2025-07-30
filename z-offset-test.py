#!/usr/bin/env python3
import sys
import re
from typing import Optional

# ----- Tunable parameters ----------------------------------------------------
SHORT_LINE_X_MIN = 130.0       # lower bound of “short” region   (inclusive)
SHORT_LINE_X_MAX = 140.0       # upper bound of “short” region   (inclusive)
# -----------------------------------------------------------------------------

START_Z_VALUE     = 21         # first Z height to write, 0.21mm, 0.01mm increments

# captures the first X value on a line
X_RE = re.compile(r'X(-?\d+(?:\.\d+)?)', re.IGNORECASE)

def extract_x(line: str) -> Optional[float]:
    """Return the first X value in a G‑code line (or None if absent)."""
    m = X_RE.search(line)
    return float(m.group(1)) if m else None


def main(path: str) -> None:
    with open(path) as f:
        lines = f.readlines()

    current_z = START_Z_VALUE
    in_short_section = False

    with open(path, 'w') as out:
        out.write('; Post‑processed to add Z moves before short lines\n\n')

        for line in lines:
            x_val = extract_x(line) if line.startswith('G1') else None

            # --- Entering a “short” section ---------------------------------
            if (
                x_val is not None and
                SHORT_LINE_X_MIN <= x_val <= SHORT_LINE_X_MAX and
                not in_short_section
            ):
                out.write(f';move Z up 0.01mm\n')
                out.write(f'G1 Z.{current_z}\n')
                out.write(f'M300 P20 S{current_z}00\n')
                current_z += 1
                in_short_section = True

            # --- Leaving a “short” section ----------------------------------
            elif x_val is not None and x_val > SHORT_LINE_X_MAX:
                in_short_section = False

            # Write the original (unchanged) G‑code line
            out.write(line)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: add_z_for_short_lines.py <file.gcode>')
    main(sys.argv[1])
