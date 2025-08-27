from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QDialogButtonBox


class RowPickerDialog(QDialog):
    """Dialog for selecting a row when multiple matches exist."""
    
    def __init__(self, rows: List[Dict[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Multiple Matches Found")
        self.setMinimumWidth(400)
        self.selected_index = None
        
        layout = QVBoxLayout()
        
        label = QLabel("Multiple rows match. Please select one:")
        layout.addWidget(label)
        
        self.list_widget = QListWidget()
        for i, row in enumerate(rows):
            # Show first few fields of each row
            display = ' | '.join([f"{k}: {v}" for k, v in list(row.items())[:3]])
            self.list_widget.addItem(f"Row {i+1}: {display}")
        layout.addWidget(self.list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def accept(self):
        if self.list_widget.currentRow() >= 0:
            self.selected_index = self.list_widget.currentRow()
            super().accept()


class Matcher:
    def __init__(self):
        self.last_match_ambiguous = False
    
    def match_row(self, image_path: Path, rows: List[Dict[str, str]], 
                  join_key: str, fallback_keys: List[str] = None) -> Optional[int]:
        """Find matching row for an image."""
        if not rows:
            return None
        
        fallback_keys = fallback_keys or ['basename', 'clip']
        image_basename = image_path.name
        image_stem = image_path.stem
        
        # Try primary join key
        matches = self._find_matches(rows, join_key, image_basename)
        if not matches and join_key != 'basename':
            matches = self._find_matches(rows, join_key, image_stem)
        
        # Try fallback keys
        if not matches:
            for key in fallback_keys:
                if key == 'basename':
                    matches = self._find_matches(rows, 'filename', image_basename)
                    if not matches:
                        matches = self._find_matches(rows, 'filename', image_stem)
                else:
                    matches = self._find_matches(rows, key, image_stem)
                
                if matches:
                    break
        
        # Handle results
        if len(matches) == 1:
            self.last_match_ambiguous = False
            return matches[0]
        elif len(matches) > 1:
            self.last_match_ambiguous = True
            return matches[0]  # Return first for now, dialog will be shown in UI
        else:
            self.last_match_ambiguous = False
            return None
    
    def _find_matches(self, rows: List[Dict[str, str]], column: str, value: str) -> List[int]:
        """Find all rows where column equals value."""
        matches = []
        for i, row in enumerate(rows):
            if column in row and row[column] == value:
                matches.append(i)
        return matches
    
    def get_multiple_matches(self, image_path: Path, rows: List[Dict[str, str]], 
                            join_key: str) -> List[int]:
        """Get all matching row indices for showing picker."""
        image_basename = image_path.name
        image_stem = image_path.stem
        
        matches = self._find_matches(rows, join_key, image_basename)
        if not matches and join_key != 'basename':
            matches = self._find_matches(rows, join_key, image_stem)
        
        return matches