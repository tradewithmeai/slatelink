#!/usr/bin/env python3
"""
SlateLink MVP - XMP Sidecar Generator
A cross-platform desktop app for viewing JPEG images with CSV metadata overlays
and exporting standards-compliant XMP sidecar files.
"""

import sys
import json
import argparse
from pathlib import Path
from PySide6.QtWidgets import QApplication
from ui_main import MainWindow


def run_diagnostics(image_path: str = None, csv_path: str = None):
    """Run headless diagnostics mode."""
    print("SlateLink Diagnostics Mode")
    print("=" * 40)
    
    try:
        # Load config without GUI
        from config.app_config import app_config
        
        runtime_flags = {
            'silverstack_mode': app_config.silverstack_only,
            'slate_bar_enabled': app_config.slate_bar,
            'saliency_enabled': app_config.saliency_placement,
            'field_reorder_enabled': app_config.field_reorder,
            'free_placement_enabled': app_config.free_placement,
            'safe_margin_pct': app_config.safe_margin_pct,
            'max_rows': app_config.max_rows
        }
        
        result = {
            'mode': 'diagnostics',
            'runtime_flags': runtime_flags,
            'qt_available': True
        }
        
        # If paths provided, test data loading
        if image_path and csv_path:
            image_file = Path(image_path)
            csv_file = Path(csv_path)
            
            if not image_file.exists():
                result['error'] = f"Image not found: {image_path}"
            elif not csv_file.exists():
                result['error'] = f"CSV not found: {csv_path}"
            else:
                # Test CSV loading
                try:
                    from data.csv_loader import CSVLoader
                    loader = CSVLoader()
                    headers, rows = loader.parse_csv(csv_file)
                    
                    result['data_test'] = {
                        'csv_loaded': True,
                        'headers_count': len(headers),
                        'rows_count': len(rows),
                        'encoding_used': loader.encoding_used,
                        'encoding_fallback': loader.encoding_fallback
                    }
                    
                    # Test hash computation (background allowed)
                    from export.hash_utils import get_cached_hashes, compute_file_hashes
                    try:
                        hashes = compute_file_hashes(image_file, csv_file)
                        result['hash_test'] = {
                            'jpeg_hash': hashes.get('jpeg', '')[:8] + '...',  # Truncated for security
                            'csv_hash': hashes.get('csv', '')[:8] + '...',
                            'computed': True
                        }
                    except Exception as e:
                        result['hash_test'] = {'error': str(e)}
                        
                except Exception as e:
                    result['data_test'] = {'error': str(e)}
        
        # Print and return results
        print(json.dumps(result, indent=2))
        return 0
        
    except Exception as e:
        error_result = {
            'mode': 'diagnostics', 
            'error': f"Diagnostics failed: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))
        return 1


def main():
    parser = argparse.ArgumentParser(description='SlateLink MVP - XMP Sidecar Generator')
    parser.add_argument('--diagnostics', nargs='*', 
                       help='Run diagnostics mode. Optional: [image_path] [csv_path]')
    
    args = parser.parse_args()
    
    # Handle diagnostics mode
    if args.diagnostics is not None:
        image_path = args.diagnostics[0] if len(args.diagnostics) > 0 else None
        csv_path = args.diagnostics[1] if len(args.diagnostics) > 1 else None
        return run_diagnostics(image_path, csv_path)
    
    # Normal GUI mode
    app = QApplication(sys.argv)
    app.setApplicationName("SlateLink")
    app.setOrganizationName("SolvX")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()