import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any


class AuditLogger:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.log_dir = Path.home() / '.slatelink' / 'audit'
        self.log_file: Optional[Path] = None
        
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            self.log_file = self.log_dir / f'audit_{timestamp}.jsonl'
    
    def log(self, event: str, **kwargs: Any) -> None:
        """Log an event to the audit file."""
        if not self.enabled or not self.log_file:
            return
        
        entry = {
            'event': event,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'os': platform.system(),
            'os_version': platform.version(),
            'app_version': 'SlateLink MVP 0.1',
            **kwargs
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log_export(self, image_path: str, csv_path: str, selected_fields: list[str], 
                   hashes: dict[str, str], join_key: str, precedence_used: str = '',
                   resolved_join_key: str = '') -> None:
        """Log an export operation with precedence tracking."""
        self.log('export', 
                 image_path=image_path,
                 csv_path=csv_path,
                 selected_fields=selected_fields,
                 jpeg_sha256=hashes.get('jpeg', ''),
                 csv_sha256=hashes.get('csv', ''),
                 join_key=join_key,
                 precedence_used=precedence_used,
                 resolved_join_key=resolved_join_key or join_key)
    
    def log_preset_save(self, preset_name: str, fields: list[str]) -> None:
        """Log preset save operation."""
        self.log('preset_save', preset_name=preset_name, fields=fields)
    
    def log_batch_operation(self, image_count: int, preset_name: str) -> None:
        """Log batch operation."""
        self.log('batch_apply', image_count=image_count, preset_name=preset_name)