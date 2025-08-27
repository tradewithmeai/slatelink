#!/usr/bin/env python3
"""Test script for dataset-aware features."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.app_config import app_config
from data.csv_loader import CSVLoader
from overlay.position_manager import PositionManager
from models.types import OverlaySpec, PrecedenceInfo


def test_dataset_features():
    """Test dataset-aware features with exampleFilmMetadata.csv."""
    print("=== Testing Dataset-Aware Features ===\n")
    
    # Test CSV loader with film metadata
    csv_loader = CSVLoader()
    test_csv = Path("exampleFilmMetadata.csv")
    
    if not test_csv.exists():
        print("[ERROR] exampleFilmMetadata.csv not found")
        return
    
    print(f"[OK] Loading CSV: {test_csv}")
    headers, rows = csv_loader.parse_csv(test_csv)
    print(f"[OK] Headers ({len(headers)}): {headers[:10]}...")  # First 10 headers
    print(f"[OK] Rows: {len(rows)}")
    
    # Test dataset defaults
    dataset_defaults = app_config.get_dataset_defaults(headers)
    print(f"\n[OK] Dataset join key: {dataset_defaults['join_key']}")
    print(f"[OK] Selected fields: {dataset_defaults['selected_fields']}")
    print(f"[OK] Field order: {dataset_defaults['field_order']}")
    
    # Test Name validation
    name_validation = csv_loader.validate_name_column(rows, 'Name')
    print(f"\n[OK] Name validation: {name_validation['valid']}")
    if not name_validation['valid']:
        for issue in name_validation['issues'][:3]:  # First 3 issues
            print(f"[WARN] {issue['message']}")
    
    # Test encoding detection
    encoding_info = csv_loader.get_encoding_info()
    print(f"[OK] Encoding: {encoding_info['encoding']} (fallback: {encoding_info['fallback_used']})")
    
    # Test field order from dataset
    field_order = csv_loader.get_dataset_field_order(headers)
    print(f"[OK] Dataset field order: {field_order}")
    
    # Test position manager
    position_manager = PositionManager()
    
    # Test precedence resolution
    overlay_spec = OverlaySpec(field_order=field_order)
    precedence = PrecedenceInfo()
    
    resolved_spec, resolved_precedence = position_manager.resolve_precedence(
        per_image_spec=None,
        preset_spec=None,
        dataset_defaults=dataset_defaults,
        csv_headers=headers
    )
    
    print(f"\n[OK] Precedence - Order: {resolved_precedence.order_source}")
    print(f"[OK] Precedence - Positions: {resolved_precedence.position_source}")
    print(f"[OK] Resolved field order: {resolved_spec.field_order}")
    
    # Test TC detection with sample row
    if rows:
        sample_row = rows[0]
        tc_source = position_manager.detect_tc_source(sample_row, dataset_defaults['selected_fields'])
        print(f"[OK] TC source detected: {tc_source}")
        
        # Test SlateBar field filtering (no pinned fields)
        slate_bar_fields = position_manager.get_slate_bar_fields(
            dataset_defaults['selected_fields'], resolved_spec)
        print(f"[OK] SlateBar fields: {slate_bar_fields}")
    
    # Test position validation and clamping
    test_positions = {
        'Scene': (0.1, 0.1),
        'Take': (-0.5, 1.5),  # Will be clamped
        'Camera': (0.12345678, 0.87654321)  # Will be rounded to 4 decimals
    }
    
    validated_positions = position_manager._validate_positions(test_positions, headers)
    print(f"\n[OK] Position validation:")
    for field, pos in validated_positions.items():
        print(f"  {field}: {pos}")
    
    # Test snap to grid
    snapped = position_manager.snap_to_grid(0.123, 0.456)
    print(f"[OK] Grid snap (0.123, 0.456) -> {snapped}")
    
    print("\n=== Dataset Tests Complete ===")


if __name__ == "__main__":
    test_dataset_features()