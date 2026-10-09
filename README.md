# z-offset-test

Model, Orca 3mf project and Python script for calibrating the z-offset on 3D printers.

## Files

- **`z-offset-test.py`** - Python script that detects the long and short line X values in sliced G-code and adds incremental Z-height adjustments for testing different z-offset values
- **`z-offset-test-model.step`** - 3D model file containing the calibration geometry designed for z-offset testing
- **`z-offset-test.3mf`** - Orca Slicer project file with pre-configured settings and post-processing script integration

## How to Use

### Purpose
This tool helps calibrate the z-offset by automatically adding incremental Z-height adjustments to specific regions of your G-code. It's designed to test different z-offset values in a single print.

### Usage

Regardless of method below, the test can be used like this:
1. Leave your current z-offset as-is if first layers are already roughly okay. The script starts 0.05mm closer to the bed than the sliced 0.2mm layer, then steps farther away by 0.01mm each section.
2. Slice / process / print the model
3. Choose the best "section" of the print. Look for a flat surface with no tearing, but make sure you cannot see gaps in between the print lines. Pick a section in the middle of the "good" range.
4. Modify your z-offset accordingly. The first section is 0.05mm closer than your current z-offset. Count the sections and add 0.01mm (farther from the bed) for each section after the first.
5. If every section still looks too far from the bed (gaps between lines, no squish), your current z-offset is more than 0.05mm too high. Move it 0.05mm closer and run the test again.

#### Method 1: Orca Slicer Integration
1. Open `z-offset-test.3mf` in Orca Slicer
2. The project is pre-configured with the correct settings and post-processing script
3. Update the location of the script in the "others" tab of the process settings
4. Select your printer and filament, then slice the model and the script will automatically run when you generate the G-code

#### Method 2: Command Line
```bash
python3 z-offset-test.py <your_file.gcode>
```

### How it Works
1. The script starts processing after the `printing object` comment in the G-code (so travel and start G-code are ignored)
2. It collects every X coordinate from G1 moves, then works out the long and short section X values automatically:
   - Unique X values are split at the midpoint between the leftmost and rightmost X
   - Only the right-hand boundary values (above that midpoint) are considered
   - The most frequent of those is the long line; the second most frequent is the short line
   - Those two values must differ by at least 5 mm
3. On a second pass, when a G1 move hits the short-line X, the script inserts:
   - A Z-height adjustment (starting at 0.15 mm, 0.05 mm closer than the 0.2 mm layer, incrementing by 0.01 mm each time)
   - A beep command (M300) for audio feedback
4. A later G1 move that hits the long-line X marks the end of that short section
5. This creates a test pattern where different z-offset values are tested in sequence

The determined long and short X values are written as comments at the top of the processed G-code.

### Manual setup in slicer
These are the settings that are needed for the test script to work and for the print to show the differences of z-offset changes:
- Make sure your layer height is equal to the model height (so you get 1 layer only)
- Wall loops: 0
- Solid infill direction: 0
- Apply gap fill: Nowhere
- Post-processing Scripts: `[your file location]/z-offset-test/z-offset-test.py;`

### Tips
- Listen for the beeps to know when z-offset changes occur
- The first test starts at 0.15mm (0.05mm closer than the 0.2mm layer) and increments by 0.01mm each time
- Look for a section of correctly squished first layer, then adjust your z-offset by the required amount (first section is 0.05mm closer than your current z-offset; add 0.01mm farther from the bed for each later section)
- If the whole print is still too far from the bed, move your z-offset 0.05mm closer and try again
