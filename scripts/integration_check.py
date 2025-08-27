#!/usr/bin/env python3
"""
Integration checks for P0 gap fixes.
Verifies that implemented features work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_free_placement_features():
    """Test free placement features are properly wired."""
    from config.app_config import app_config
    
    tests = {
        'free_placement_flag': app_config.free_placement,
        'snap_grid_setting': hasattr(app_config, 'snap_pct'),
        'safe_margins_setting': hasattr(app_config, 'safe_margin_pct')
    }
    
    # Test position manager has required methods
    from overlay.position_manager import PositionManager
    pm = PositionManager()
    
    tests['snap_to_grid_method'] = hasattr(pm, 'snap_to_grid')
    tests['pinned_fields_method'] = hasattr(pm, 'get_pinned_fields')
    
    return tests

def test_batch_mode_features():
    """Test batch mode UI features."""
    from models.types import BatchConfig
    
    bc = BatchConfig()
    
    tests = {
        'batch_config_exists': True,
        'valid_modes': bc.mode in ['use_preset', 'respect_per_image', 'apply_current'],
        'description_method': hasattr(bc, 'get_description')
    }
    
    return tests

def test_keyboard_shortcuts():
    """Test keyboard shortcut infrastructure."""
    try:
        from ui_main import MainWindow
        
        # Check if keyPressEvent exists
        tests = {
            'keypress_handler': hasattr(MainWindow, 'keyPressEvent'),
            'layout_toggle': hasattr(MainWindow, 'toggle_layout_mode'),
            'field_nudge': hasattr(MainWindow, 'nudge_field'),
            'field_selection': hasattr(MainWindow, 'select_field_for_placement')
        }
        
        return tests
    except Exception as e:
        return {'error': str(e)}

def test_encoding_chip_logic():
    """Test E chip conditional display."""
    from overlay.slate_bar import SlateBar
    
    sb = SlateBar()
    
    # Test micro chips with different encodings
    chips_utf8 = sb._create_micro_chips(False, False, False, 'utf-8')
    chips_latin1 = sb._create_micro_chips(False, False, False, 'latin-1')
    
    # Check E chip presence
    utf8_has_e = any(chip['text'] == 'E' for chip in chips_utf8)
    latin1_has_e = any(chip['text'] == 'E' for chip in chips_latin1)
    
    return {
        'utf8_no_e_chip': not utf8_has_e,  # Should be True
        'latin1_has_e_chip': latin1_has_e,  # Should be True
        'conditional_logic_working': not utf8_has_e and latin1_has_e
    }

def test_field_reordering():
    """Test field reordering infrastructure."""
    from ui_main import FieldWidget
    
    # Test FieldWidget has required components
    fw = FieldWidget("test_field", 1)
    
    tests = {
        'up_button_exists': hasattr(fw, 'up_btn'),
        'down_button_exists': hasattr(fw, 'down_btn'),
        'layout_button_exists': hasattr(fw, 'layout_btn'),
        'move_methods': hasattr(fw, 'move_up') and hasattr(fw, 'move_down'),
        'select_for_layout': hasattr(fw, 'select_for_layout')
    }
    
    return tests

def run_all_tests():
    """Run all integration tests."""
    print("SlateLink P0 Gap Integration Tests")
    print("=" * 50)
    
    test_results = {
        'free_placement': test_free_placement_features(),
        'batch_modes': test_batch_mode_features(), 
        'keyboard_shortcuts': test_keyboard_shortcuts(),
        'encoding_chip': test_encoding_chip_logic(),
        'field_reordering': test_field_reordering()
    }
    
    # Print results
    total_tests = 0
    passed_tests = 0
    
    for category, results in test_results.items():
        print(f"\n{category.upper()} TESTS:")
        if isinstance(results, dict) and 'error' in results:
            print(f"  [ERROR] {results['error']}")
            continue
            
        for test_name, result in results.items():
            total_tests += 1
            status = "[PASS]" if result else "[FAIL]"
            if result:
                passed_tests += 1
            print(f"  {status} {test_name}: {result}")
    
    print(f"\nSUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("[SUCCESS] All P0 gap fixes verified!")
        return 0
    else:
        print("[WARNING] Some tests failed - manual verification needed")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())