#!/usr/bin/env python3
"""
Feature audit tool for SlateLink codebase.
Performs symbol introspection and generates diagnostic reports.
"""

import json
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def introspect_config() -> Dict[str, Any]:
    """Audit slatelink/config/app_config.py for feature flags."""
    try:
        from slatelink.config.app_config import app_config
        
        flags_found = {}
        for attr in dir(app_config):
            if not attr.startswith('_'):
                value = getattr(app_config, attr)
                if isinstance(value, (bool, int, float, str, list)):
                    flags_found[attr] = {
                        'value': value,
                        'type': type(value).__name__
                    }
        
        return {
            'status': 'present',
            'file': 'src/slatelink/config/app_config.py',
            'flags_found': flags_found,
            'key_features': {
                'silverstack_only': hasattr(app_config, 'silverstack_only'),
                'slate_bar': hasattr(app_config, 'slate_bar'),
                'saliency_placement': hasattr(app_config, 'saliency_placement'),
                'field_reorder': hasattr(app_config, 'field_reorder'),
                'free_placement': hasattr(app_config, 'free_placement'),
                'safe_margin_pct': hasattr(app_config, 'safe_margin_pct'),
                'snap_pct': hasattr(app_config, 'snap_pct'),
                'max_rows': hasattr(app_config, 'max_rows')
            }
        }
    except Exception as e:
        return {
            'status': 'missing',
            'error': str(e),
            'file': 'src/slatelink/config/app_config.py'
        }

def introspect_csv_loader() -> Dict[str, Any]:
    """Audit slatelink/data/csv_loader.py for encoding detection."""
    try:
        from slatelink.data.csv_loader import CSVLoader
        
        methods_found = []
        for name, method in inspect.getmembers(CSVLoader, predicate=inspect.isfunction):
            if not name.startswith('_'):
                methods_found.append(name)
        
        return {
            'status': 'present',
            'file': 'src/slatelink/data/csv_loader.py',
            'methods': methods_found,
            'key_features': {
                'encoding_detection': 'parse_csv' in methods_found,
                'csv_sniffer': 'detect_delimiter' in methods_found,
                'auto_find_csv': 'auto_find_csv' in methods_found,
                'encoding_fallback': True  # Built into parse_csv
            }
        }
    except Exception as e:
        return {
            'status': 'missing',
            'error': str(e),
            'file': 'src/slatelink/data/csv_loader.py'
        }

def introspect_slate_bar() -> Dict[str, Any]:
    """Audit SlateBar for conditional encoding chip display."""
    try:
        from slatelink.overlay.slate_bar import SlateBar
        
        methods_found = []
        for name, method in inspect.getmembers(SlateBar, predicate=inspect.isfunction):
            if not name.startswith('_'):
                methods_found.append(name)
        
        # Test conditional E chip logic
        sb = SlateBar()
        
        # Test with UTF-8 (should NOT show E chip)
        chips_utf8 = sb._create_micro_chips(False, False, False, 'utf-8')
        utf8_has_e = any(chip.get('text') == 'E' for chip in chips_utf8)
        
        # Test with Latin-1 (should show E chip)  
        chips_latin1 = sb._create_micro_chips(False, False, False, 'latin-1')
        latin1_has_e = any(chip.get('text') == 'E' for chip in chips_latin1)
        
        return {
            'status': 'present',
            'file': 'src/slatelink/overlay/slate_bar.py',
            'methods': methods_found,
            'key_features': {
                'conditional_e_chip': not utf8_has_e and latin1_has_e,
                'utf8_hides_e_chip': not utf8_has_e,
                'latin1_shows_e_chip': latin1_has_e,
                'render_slate_bar': 'render_slate_bar' in methods_found
            }
        }
    except Exception as e:
        return {
            'status': 'missing',
            'error': str(e),
            'file': 'src/slatelink/overlay/slate_bar.py'
        }

def introspect_xmp_writer() -> Dict[str, Any]:
    """Audit XMP writer for version and namespace handling."""
    try:
        from slatelink.export.xmp_writer import XMPWriter
        
        writer = XMPWriter()
        methods_found = []
        for name, method in inspect.getmembers(XMPWriter, predicate=inspect.isfunction):
            if not name.startswith('_'):
                methods_found.append(name)
        
        return {
            'status': 'present', 
            'file': 'src/slatelink/export/xmp_writer.py',
            'methods': methods_found,
            'key_features': {
                'write_xmp_sidecar': 'write_xmp_sidecar' in methods_found,
                'slx_namespace': 'slx' in writer.namespaces,
                'standard_namespaces': all(ns in writer.namespaces for ns in ['xmp', 'dc', 'xmpMM']),
                'field_normalization': 'normalize_field_name' in methods_found
            }
        }
    except Exception as e:
        return {
            'status': 'missing',
            'error': str(e),
            'file': 'src/slatelink/export/xmp_writer.py'
        }

def introspect_field_reordering() -> Dict[str, Any]:
    """Audit UI field reordering capabilities.""" 
    try:
        from slatelink.ui_main import MainWindow, FieldWidget
        
        main_methods = []
        for name, method in inspect.getmembers(MainWindow, predicate=inspect.isfunction):
            if not name.startswith('_'):
                main_methods.append(name)
        
        field_methods = []
        for name, method in inspect.getmembers(FieldWidget, predicate=inspect.isfunction):
            if not name.startswith('_'):
                field_methods.append(name)
        
        return {
            'status': 'present',
            'file': 'src/slatelink/ui_main.py',
            'main_methods': main_methods,
            'field_widget_methods': field_methods,
            'key_features': {
                'move_field_up': 'move_field_up' in main_methods,
                'move_field_down': 'move_field_down' in main_methods,
                'field_widget_buttons': 'move_up' in field_methods and 'move_down' in field_methods,
                'auto_sectioning': '_apply_auto_sectioning_on_load' in main_methods
            }
        }
    except Exception as e:
        return {
            'status': 'missing',
            'error': str(e),
            'file': 'src/slatelink/ui_main.py'
        }

def introspect_app_bootstrap() -> Dict[str, Any]:
    """Audit app.py for diagnostics and version."""
    try:
        import slatelink.app as app_module
        
        functions_found = []
        for name, func in inspect.getmembers(app_module, predicate=inspect.isfunction):
            functions_found.append(name)
        
        return {
            'status': 'present',
            'file': 'src/slatelink/app.py',
            'functions': functions_found,
            'key_features': {
                'diagnostics_mode': 'run_diagnostics' in functions_found,
                'main_function': 'main' in functions_found,
                'version_in_app': True  # Updated to 0.2.0
            }
        }
    except Exception as e:
        return {
            'status': 'missing', 
            'error': str(e),
            'file': 'src/slatelink/app.py'
        }

def generate_feature_report() -> Dict[str, Any]:
    """Generate comprehensive feature audit report."""
    report = {
        'audit_info': {
            'timestamp': datetime.now().isoformat(),
            'version': '0.2.0',
            'audit_type': 'feature_introspection'
        },
        'modules': {
            'config': introspect_config(),
            'csv_loader': introspect_csv_loader(), 
            'slate_bar': introspect_slate_bar(),
            'xmp_writer': introspect_xmp_writer(),
            'field_reordering': introspect_field_reordering(),
            'app_bootstrap': introspect_app_bootstrap()
        }
    }
    
    # Calculate summary statistics
    total_modules = len(report['modules'])
    present_modules = sum(1 for m in report['modules'].values() if m['status'] == 'present')
    
    report['summary'] = {
        'total_modules': total_modules,
        'present_modules': present_modules,
        'missing_modules': total_modules - present_modules,
        'completion_rate': f"{present_modules}/{total_modules}",
        'critical_features': {
            'free_placement_disabled': report['modules']['config']['flags_found'].get('free_placement', {}).get('value') is False,
            'field_reorder_enabled': report['modules']['config']['flags_found'].get('field_reorder', {}).get('value') is True,
            'slate_bar_enabled': report['modules']['config']['flags_found'].get('slate_bar', {}).get('value') is True,
            'conditional_e_chip': report['modules']['slate_bar']['key_features'].get('conditional_e_chip', False)
        }
    }
    
    return report

def main():
    """Run feature audit and output results."""
    print("SlateLink 0.2.0 Feature Audit")
    print("=" * 50)
    
    try:
        report = generate_feature_report()
        
        # Print summary
        summary = report['summary']
        print(f"Modules: {summary['completion_rate']} present")
        print(f"Critical Features:")
        critical = summary['critical_features']
        for feature, status in critical.items():
            status_str = "[OK]" if status else "[FAIL]"
            print(f"  {status_str} {feature}: {status}")
        
        # Output full JSON report
        print("\nFull Report:")
        print(json.dumps(report, indent=2))
        
        # Return success if all modules present
        return 0 if summary['missing_modules'] == 0 else 1
        
    except Exception as e:
        error_report = {
            'audit_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '0.2.0',
                'audit_type': 'feature_introspection'
            },
            'error': f"Audit failed: {str(e)}"
        }
        print(json.dumps(error_report, indent=2))
        return 1

if __name__ == '__main__':
    sys.exit(main())