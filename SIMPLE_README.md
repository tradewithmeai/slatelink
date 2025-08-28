# SlateLink Simple - JPEG Overlay Tool

**Simplified version for reliable on-set use.**

## Quick Start (macOS/Linux)

```bash
# Run the simple version
python simple_slatelink.py

# Run with debug logging (if issues occur)
python simple_slatelink.py --debug
```

## How to Use

### 1. Load Files
- **Load JPEG Image**: Click to select your source JPEG file
- **Load CSV Metadata**: Click to select your CSV with metadata

### 2. Select Fields
- Check the boxes for fields you want to overlay on the image
- Preview updates automatically as you select fields
- App will try to automatically match your image filename to a CSV row

### 3. Export
- **Export JPEG with Overlay**: Saves a new JPEG file with the overlay burned in
- Choose where to save the output file
- Original image remains unchanged

## Features

### File Matching
- Automatically matches filenames like `Slate57-Take1-MissionImpossible.jpg` to CSV entries
- Supports fuzzy matching for production naming patterns
- Falls back gracefully if no match found

### Overlay Design
- Professional slate bar design for production use
- High contrast text with automatic color adjustment
- Maintains image quality (95% JPEG quality)

### Debug Support
- Run with `--debug` for detailed logging
- Crash reports saved to `~/.slatelink/crash_reports/`
- Safe to share crash files (no personal data included)

## Troubleshooting

### If the app crashes:
1. Run with `--debug` flag: `python simple_slatelink.py --debug`
2. If crash dialog appears, click "Open" to find crash report
3. Share the crash report JSON file for analysis

### If image/CSV won't load:
- Ensure JPEG files are standard format
- Ensure CSV uses UTF-8 encoding
- Check debug console for specific error messages

### If no match found:
- App will still work - you can manually select which fields to overlay
- Fuzzy matching handles slight name differences
- Check that CSV has a 'Name' column matching your image filename pattern

## File Locations

### Debug Logs (macOS)
- Logs: `~/.slatelink/debug/`
- Crash reports: `~/.slatelink/crash_reports/`

### Debug Logs (Windows)
- Logs: `%USERPROFILE%\.slatelink\debug\`
- Crash reports: `%USERPROFILE%\.slatelink\crash_reports\`

## Differences from Full Version

This simplified version:
- ✅ **More reliable**: Removed complex features that could cause crashes
- ✅ **Manual loading**: No automatic CSV detection (prevents file conflicts)
- ✅ **JPEG output**: Exports JPEG with overlay (not XMP sidecar)
- ✅ **Essential UI**: Only the core functionality needed for production
- ✅ **Better error handling**: Comprehensive debug logging and crash reports

## Production Workflow

1. **On Set**: Use this simple version for quick, reliable overlay creation
2. **Post Production**: Use full SlateLink for XMP sidecar workflows and advanced features

This version is designed to "just work" when you need it most.