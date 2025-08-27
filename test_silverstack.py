#!/usr/bin/env python3
"""Test script for Silverstack features."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.app_config import app_config
from data.csv_loader import CSVLoader
from export.hash_utils import sha256_file
from overlay.slate_bar import SlateBar
from overlay.saliency import SaliencyDetector
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication


def test_silverstack_features():
    """Test Silverstack mode features."""
    print("=== Testing Silverstack Features ===\n")
    
    # Test CSV loader
    csv_loader = CSVLoader()
    test_csv = Path("test_data/silverstack_metadata.csv")
    
    if test_csv.exists():
        print(f"[OK] Loading CSV: {test_csv}")
        headers, rows = csv_loader.parse_csv(test_csv)
        
        # Test join key detection
        detected_key = csv_loader.detect_join_key(headers)
        print(f"[OK] Detected join key: {detected_key}")
        
        # Test suggested fields
        suggested = csv_loader.get_suggested_fields(headers)
        print(f"[OK] Suggested fields: {suggested}")
        
        # Test encoding info
        encoding_info = csv_loader.get_encoding_info()
        print(f"[OK] Encoding: {encoding_info}")
    else:
        print("[WARN] Test CSV not found")
    
    # Test hash utilities
    test_image = Path("test_data/IMG_0001.jpg")
    if test_image.exists():
        print(f"\n[OK] Computing hash for: {test_image}")
        hash_value = sha256_file(test_image)
        print(f"[OK] SHA-256: {hash_value[:16]}...")
    else:
        print("[WARN] Test image not found")
    
    # Test saliency detection (if PySide6 available)
    try:
        app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        
        if test_image.exists():
            pixmap = QPixmap(str(test_image))
            if not pixmap.isNull():
                saliency = SaliencyDetector()
                corner, needs_backdrop = saliency.find_best_corner(pixmap)
                print(f"[OK] Saliency detected corner: {corner} (backdrop: {needs_backdrop})")
            else:
                print("[WARN] Could not load test image for saliency")
    except Exception as e:
        print(f"[WARN] Saliency test failed: {e}")
    
    # Test app config
    print(f"\n[OK] Silverstack mode: {app_config.silverstack_only}")
    print(f"[OK] SlateBar enabled: {app_config.slate_bar}")
    print(f"[OK] Saliency placement: {app_config.saliency_placement}")
    print(f"[OK] Join key priority: {app_config.silverstack_join_priority}")
    print(f"[OK] Suggested fields: {app_config.silverstack_suggested_fields}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_silverstack_features()