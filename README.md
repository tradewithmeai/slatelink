# SlateLink — Silverstack-aware XMP sidecar tool

Non-destructive, standards-first still + CSV overlay preview with sidecar export (XMP). Designed for DIT/editorial workflows. **Originals are never modified.**

SlateLink loads JPEG images alongside Silverstack-style CSV metadata, provides a live overlay preview, and exports standards-compliant XMP sidecar files. Perfect for film/video production workflows where metadata integrity is critical.

## Requirements

- **Python 3.11 recommended** (3.10+ supported)
- **macOS**: `brew install python@3.11` (optionally `brew install git`)
- **Windows/Linux**: Use system Python 3.10+

## Setup

```bash
git clone <repo-url>
cd slatelink
python3 -m venv .venv && source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/generate_demo_assets.py
python src/slatelink/app.py
```

## Diagnostics (optional)

```bash
# Test headless mode with demo data
python src/slatelink/app.py --diagnostics test_data/IMG_0001.jpg test_data/exampleFilmMetadata.csv

# Feature audit report  
python scripts/feature_audit.py
```

## Usage

1. **Open image** → Click "Open Image" and select a JPEG
2. **Select CSV** → Click "Open CSV" and choose your Silverstack export
3. **Tick fields** → Select metadata fields to display in overlay
4. **Drag to reorder** → Use ↑↓ buttons to change field display order
5. **Export sidecar** → Click "Export XMP" to create .xmp sidecar file

### Notes

- **Manual layout is disabled** in this build (`free_placement=False`)
- The overlay is **preview-only**; actual metadata is written to XMP sidecar
- **Join key auto-detection**: Prioritizes "Name" field for Silverstack CSVs
- **Encoding fallback**: UTF-8 → UTF-8-SIG → Latin-1 detection
- **Field reordering**: Drag selected fields to change overlay display order

## Features

- ✅ **Zero-mutation guarantee**: Source files never modified
- ✅ **Standards-compliant XMP**: Proper RDF/XML with Adobe namespaces  
- ✅ **SHA-256 integrity**: Hash validation prevents corrupted exports
- ✅ **Silverstack integration**: Auto-detects join keys and suggested fields
- ✅ **Cross-platform**: macOS, Windows, Linux via PySide6/Qt
- ✅ **Batch export**: Process multiple images with same field selection
- ✅ **CVD-safe colors**: Accessibility-friendly overlay design

## Architecture

**Core Technologies**: PySide6 (Qt GUI) • Pillow (image processing) • NumPy (saliency analysis)

**Key Principles**: 
- Zero mutation (never modify source files)
- Data integrity (SHA-256 validation with caching)
- Standards compliance (proper XMP/RDF structure)
- Atomic operations (safe temp file writes)

## Demo Data

Run `python scripts/generate_demo_assets.py` to create:

- `test_data/IMG_0001.jpg, IMG_0002.jpg, IMG_0003.jpg` (synthetic images)
- `test_data/exampleFilmMetadata.csv` (Silverstack-style metadata)

## Development

```bash
# Run tests on current platform
python scripts/feature_audit.py

# Generate fresh demo assets  
python scripts/generate_demo_assets.py

# Test diagnostics mode
python src/slatelink/app.py --diagnostics test_data/IMG_0001.jpg test_data/exampleFilmMetadata.csv
```

---

**Version**: 0.2.0 • **License**: MIT • **Status**: Production Ready