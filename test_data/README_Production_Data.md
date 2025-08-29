# Production Test Data

This folder contains realistic test data based on actual Silverstack CSV export formats used in film and television production.

## Files Generated

### CSV Files
- **`silverstack_production.csv`** - Comprehensive 25-clip production dataset
  - Multi-camera shoot (A/B/C cameras)  
  - Feature film scenes (12B, 13A) with takes
  - Documentary interviews
  - Steadicam and drone footage
  - VFX plates with tracking data
  - Full Silverstack column structure

- **`silverstack_minimal.csv`** - Essential 8-clip dataset for quick testing
  - Core fields: Clip Name, Scene, Take, Camera, FPS
  - Representative sample from main dataset

### Test Images
- **25 production-style JPEG images** (1920x1080)
  - Matching filenames from CSV "Clip Name" column
  - Professional production naming conventions:
    - `A001_C001_0315_001.jpg` (Alexa-style)
    - `DOC_Interview_01.jpg` (Documentary)
    - `Steadicam_03.jpg` (Equipment-based)
    - `VFX_Plate_02.jpg` (VFX workflow)

## Image Features
- **Resolution**: 1920x1080 (standard proxy/dailies size)
- **Production elements**:
  - Slate information overlay
  - Frame guides (action safe/title safe)
  - Corner registration marks  
  - Timecode burn-in
  - Film grain texture
  - Camera/scene metadata

## Based on Silverstack Research

This test data follows the specifications from **Pomfort Silverstack CSV Export Recreation Guide**, including:

- **Primary matching key**: "Clip Name" column
- **Standard production fields**: Scene, Shot, Take, Camera, FPS, Timecode
- **Professional metadata**: Lens, ISO, Codec, Resolution, Circle Take
- **Workflow categories**: Multi-cam, documentary, aerial, VFX, steadicam

## Testing Workflow

### 1. Load Production Images
```bash
python -m src.slatelink.app
# Click "Open Image" → select any .jpg from test_data folder
```

### 2. Load Matching CSV
```bash
# Click "Open CSV (Manual)" → select silverstack_production.csv or silverstack_minimal.csv
# App will automatically match image filename to CSV "Clip Name"
```

### 3. Test Features
- **Field Selection**: Check/uncheck metadata fields (Scene, Take, Camera, etc.)
- **Overlay Rendering**: See professional slate bar with production data
- **Export Options**: XMP sidecar or JPEG with burned-in overlay

## Expected Matches

| Image File | CSV Row | Scene | Camera | Notes |
|------------|---------|-------|---------|-------|
| A001_C001_0315_003.jpg | Row 3 | 12B | Alexa Mini | Circle Take = Yes |
| B001_C001_0315_003.jpg | Row 8 | 12B | RED Komodo | Multi-cam angle |
| DOC_Interview_01.jpg | Row 17 | INT | Sony FX9 | Documentary format |
| Steadicam_03.jpg | Row 23 | 12B | Alexa Mini | Perfect execution |
| VFX_Plate_02.jpg | Row 25 | 99 | Alexa 65 | Green screen |

## Verification

All test data matches real-world production patterns:
- **Naming conventions** from major camera systems
- **Metadata fields** from actual Silverstack exports  
- **Technical specs** (frame rates, codecs, resolutions)
- **Production workflows** (multi-cam, documentary, VFX)

This enables testing SlateLink with realistic data without using protected content from actual productions.

## Generation

To regenerate the images:
```bash
cd test_data
python generate_production_images.py
```

This will create 25 unique 1920x1080 JPEG images with production-style elements, matching the CSV data exactly.