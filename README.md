# z-offset-test

Model, Orca 3mf project and Python script for calibrating the z-offset on 3D printers.

## Files

- **`z-offset-test.py`** - Python script that processes G-code files to add Z-height adjustments for testing different z-offset values
- **`z-offset-test-model.step`** - 3D model file containing the calibration geometry designed for z-offset testing
- **`z-offset-test.3mf`** - Orca Slicer project file with pre-configured settings and post-processing script integration

## How to Use

### Purpose
This tool helps calibrate the z-offset by automatically adding incremental Z-height adjustments to specific regions of your G-code. It's designed to test different z-offset values in a single print.

### Usage

Regardless of method below, the test can be used like this:
1. Get your z-offset set to a value that is slightly too close to the bed. Look for thin lines or tearing on the top surface.
2. Slice / process / print the model
3. Choose the best "section" of the print. Look for flat surface with no tearing, but make sure you cannot see gaps in between the print lines. Pick a section in the middle of the "good" range.
4. Modify your z-offset accordingly. Count the sections and add 0.01mm to the offset for each section after the first one (the first section is printed at exactly your current z-offset)

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
1. The script processes G-code files and looks for movement commands (G1) with X coordinates
2. When it finds X coordinates between 130.0-140.0mm (the "short" region), it adds:
   - A Z-height adjustment (starting at 0.21mm, incrementing by 0.01mm each time)
   - A beep command (M300) for audio feedback
3. This creates a test pattern where different z-offset values are tested in sequence

### Advanced Configuration
You can adjust these parameters in the script:
- `SHORT_LINE_X_MIN = 130.0` - Lower bound of the test region
- `SHORT_LINE_X_MAX = 140.0` - Upper bound of the test region

### Manual setup in slicer
These are the settings that are needed for the test script to work and for the print to show the differences of z-offset changes:
- Make sure your layer height is equal to the model height (so you get 1 layer only)
- Wall loops: 0
- Solid infill direction: 0
- Apply gap fill: Nowhere
- Post-processing Scripts: `[your file location]/z-offset-test/z-offset-test.py;`

### Tips
- Listen for the beeps to know when z-offset changes occur
- The first test starts at 0.20mm and increments by 0.01mm each time
- Look for a section of correctly squished first layer, then adjust your z-offset by the required amount (count the sections, the first one is exactly the current z-offset)
