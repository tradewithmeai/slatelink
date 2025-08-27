import csv
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from ..config.app_config import app_config


class CSVLoader:
    def __init__(self):
        self.encoding_used = 'utf-8'
        self.delimiter_used = ','
        self.encoding_fallback = False
    
    def auto_find_csv(self, image_path: Path) -> Optional[Path]:
        """Auto-locate CSV file for an image."""
        image_dir = image_path.parent
        image_stem = image_path.stem
        
        # First try: same name as image
        same_name_csv = image_dir / f"{image_stem}.csv"
        if same_name_csv.exists():
            return same_name_csv
        
        # Second try: first CSV in directory
        csv_files = list(image_dir.glob("*.csv"))
        if csv_files:
            return csv_files[0]
        
        return None
    
    def detect_delimiter(self, sample: str) -> str:
        """Detect CSV delimiter using csv.Sniffer."""
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            return dialect.delimiter
        except:
            return ','
    
    def parse_csv(self, path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
        """Parse CSV with encoding and delimiter detection."""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1']
        content = None
        
        for i, encoding in enumerate(encodings):
            try:
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
                self.encoding_used = encoding
                self.encoding_fallback = (i > 0)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise ValueError(f"Could not decode CSV file {path}")
        
        # Detect delimiter
        sample = '\n'.join(content.split('\n')[:5])
        self.delimiter_used = self.detect_delimiter(sample)
        
        # Parse CSV
        lines = content.splitlines()
        reader = csv.DictReader(lines, delimiter=self.delimiter_used)
        
        headers = reader.fieldnames or []
        rows = list(reader)
        
        # Preserve all values as strings (no conversion)
        for row in rows:
            for key in row:
                if row[key] is None:
                    row[key] = ''
        
        return headers, rows
    
    def get_encoding_info(self) -> Dict[str, any]:
        """Get information about encoding used."""
        return {
            'encoding': self.encoding_used,
            'delimiter': self.delimiter_used,
            'fallback_used': self.encoding_fallback
        }
    
    def detect_join_key(self, headers: List[str]) -> str:
        """Detect best join key from Silverstack priority list."""
        if not app_config.silverstack_only:
            return 'filename'  # Default fallback
        
        # Search priority list
        for candidate in app_config.silverstack_join_priority:
            if candidate in headers:
                return candidate
        
        # Fallback to first available or default
        return headers[0] if headers else 'filename'
    
    def get_suggested_fields(self, headers: List[str]) -> List[str]:
        """Get fields that should be pre-selected."""
        if not app_config.silverstack_only:
            return []
        
        # Use dataset-specific defaults
        dataset_defaults = app_config.get_dataset_defaults(headers)
        return dataset_defaults['selected_fields']
    
    def get_dataset_field_order(self, headers: List[str]) -> List[str]:
        """Get dataset-specific field order."""
        if not app_config.silverstack_only:
            return []
        
        dataset_defaults = app_config.get_dataset_defaults(headers)
        return dataset_defaults['field_order']
    
    def validate_name_column(self, rows: List[Dict[str, str]], join_key: str) -> Dict[str, any]:
        """Validate Name column for missing/duplicate values."""
        if join_key not in ['Name'] or not rows:
            return {'valid': True, 'issues': []}
        
        issues = []
        name_counts = {}
        
        for i, row in enumerate(rows):
            name_value = row.get(join_key, '').strip()
            
            if not name_value:
                issues.append({
                    'type': 'missing',
                    'row': i + 1,  # 1-based for user display
                    'message': f"Row {i + 1}: Missing or blank Name"
                })
            else:
                name_counts[name_value] = name_counts.get(name_value, 0) + 1
        
        # Check for duplicates
        for name, count in name_counts.items():
            if count > 1:
                duplicate_rows = [i + 1 for i, row in enumerate(rows) if row.get(join_key, '').strip() == name]
                issues.append({
                    'type': 'duplicate',
                    'name': name,
                    'rows': duplicate_rows,
                    'message': f"Duplicate Name '{name}' in rows: {', '.join(map(str, duplicate_rows))}"
                })
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'total_rows': len(rows),
            'missing_count': len([i for i in issues if i['type'] == 'missing']),
            'duplicate_count': len([i for i in issues if i['type'] == 'duplicate'])
        }