from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QListWidget, QComboBox,
                             QCheckBox, QScrollArea, QFileDialog, QMessageBox,
                             QSplitter, QGroupBox, QSpinBox, QSlider,
                             QInputDialog, QListWidgetItem, QFrame)
from PySide6.QtGui import QPixmap, QAction, QKeyEvent
from PySide6.QtCore import Qt, Signal, QPointF
from pathlib import Path
from typing import Optional, List, Dict

from .data.csv_loader import CSVLoader
from .data.matcher import Matcher, RowPickerDialog
from .data.fuzzy_matcher import FuzzyMatcher
from .overlay.renderer import OverlayRenderer
from .export.xmp_writer import XMPWriter
from .export.hash_utils import compute_hashes_async, validate_files_unchanged, hash_status
from .presets.manager import PresetManager
from .audit.logger import AuditLogger
from .models.types import Preset, OverlaySpec, MatchConfig, ExportConfig, BatchConfig, PrecedenceInfo
from .config.app_config import app_config
from .overlay.position_manager import PositionManager
from .debug.logger import debug_logger, log_exceptions


class FieldWidget(QFrame):
    """Custom widget for field selection with reordering controls."""
    
    def __init__(self, field_name: str, position: int, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.position = position
        self.parent_window = parent
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(5)
        
        # Position number
        self.pos_label = QLabel(f"{self.position}")
        self.pos_label.setFixedWidth(20)
        self.pos_label.setStyleSheet("QLabel { color: #666; font-size: 10px; }")
        layout.addWidget(self.pos_label)
        
        # Checkbox
        self.checkbox = QCheckBox(self.field_name)
        self.checkbox.toggled.connect(self.on_toggled)
        layout.addWidget(self.checkbox)
        
        layout.addStretch()
        
        # Up button
        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(20, 20)
        self.up_btn.setEnabled(False)
        self.up_btn.clicked.connect(self.move_up)
        layout.addWidget(self.up_btn)
        
        # Down button
        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedSize(20, 20)
        self.down_btn.setEnabled(False)
        self.down_btn.clicked.connect(self.move_down)
        layout.addWidget(self.down_btn)
        
    
    def on_toggled(self, checked: bool):
        """Handle checkbox toggle."""
        self.up_btn.setEnabled(checked)
        self.down_btn.setEnabled(checked)
    
    def move_up(self):
        """Move field up in order."""
        if self.parent_window:
            self.parent_window.move_field_up(self.field_name)
    
    def move_down(self):
        """Move field down in order."""
        if self.parent_window:
            self.parent_window.move_field_down(self.field_name)
    
    def set_position(self, position: int):
        """Update position display."""
        self.position = position
        self.pos_label.setText(f"{position}")
    
    def is_checked(self) -> bool:
        """Get checkbox state."""
        return self.checkbox.isChecked()
    
    def set_checked(self, checked: bool):
        """Set checkbox state."""
        self.checkbox.setChecked(checked)
    


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.debug_mode = False  # Will be set by app.py
        debug_logger.info("Initializing MainWindow")
        self.setWindowTitle('SlateLink - XMP Sidecar MVP')
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.csv_loader = CSVLoader()
        self.matcher = Matcher()
        self.fuzzy_matcher = FuzzyMatcher(min_confidence=0.6)
        self.renderer = OverlayRenderer()
        self.xmp_writer = XMPWriter()
        self.preset_manager = PresetManager()
        self.audit_logger = AuditLogger(enabled=False)
        self.position_manager = PositionManager()
        
        # State
        self.current_image_path: Optional[Path] = None
        self.current_csv_path: Optional[Path] = None
        self.csv_headers: List[str] = []
        self.original_csv_headers: List[str] = []  # Store original order for position numbers
        self.csv_rows: List[Dict[str, str]] = []
        self.current_row: Optional[Dict[str, str]] = None
        self.selected_fields: List[str] = []
        self.overlay_spec = OverlaySpec()
        self.match_config = MatchConfig()
        self.export_config = ExportConfig()
        self.batch_config = BatchConfig()
        
        # UI widgets
        self.field_widgets: Dict[str, 'FieldWidget'] = {}
        self.field_checkboxes: Dict[str, QCheckBox] = {}
        
        # Hash and status tracking
        self.current_hashes: Dict[str, str] = {}
        self.hash_verified = False
        self.match_used_fallback = False
        self.encoding_used_fallback = False
        
        # Precedence and validation
        self.precedence_info = PrecedenceInfo()
        self.csv_validation: Dict = {'valid': True, 'issues': []}
        self.current_encoding = 'utf-8'
        
        
        self.setup_ui()
        self.setup_menu()
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard shortcuts."""
        
        
        
        super().keyPressEvent(event)
    
    
    
    
    
    def setup_ui(self):
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main horizontal layout with splitter
        main_layout = QHBoxLayout(central)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - File operations
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center panel - Image preview
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("QLabel { background: #222; border: 1px solid #444; }")
        self.image_label.setScaledContents(False)
        
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.addWidget(self.image_label)
        
        # Status bar at bottom of center
        self.status_label = QLabel("No image loaded")
        self.status_label.setStyleSheet("QLabel { padding: 5px; background: #333; color: #fff; }")
        center_layout.addWidget(self.status_label)
        
        splitter.addWidget(center_widget)
        
        # Right panel - CSV fields and controls
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([250, 500, 450])
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with file operations."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Open image button
        self.open_btn = QPushButton("Open Image")
        self.open_btn.clicked.connect(self.open_image)
        layout.addWidget(self.open_btn)
        
        # Open CSV button
        self.open_csv_btn = QPushButton("Open CSV (Manual)")
        self.open_csv_btn.clicked.connect(self.open_csv_manual)
        layout.addWidget(self.open_csv_btn)
        
        # Batch operations
        batch_group = QGroupBox("Batch Operations")
        batch_layout = QVBoxLayout()
        
        self.batch_folder_btn = QPushButton("Select Folder")
        self.batch_folder_btn.clicked.connect(self.select_batch_folder)
        batch_layout.addWidget(self.batch_folder_btn)
        
        self.batch_apply_btn = QPushButton("Apply Preset to Batch")
        self.batch_apply_btn.clicked.connect(self.apply_batch)
        self.batch_apply_btn.setEnabled(False)
        batch_layout.addWidget(self.batch_apply_btn)
        
        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)
        
        layout.addStretch()
        return widget
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with CSV fields and controls."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Join key selector
        join_group = QGroupBox("Join Configuration")
        join_layout = QVBoxLayout()
        
        self.join_combo = QComboBox()
        self.join_combo.addItems(['filename', 'basename', 'clip', 'slate'])
        self.join_combo.currentTextChanged.connect(self.on_join_key_changed)
        join_layout.addWidget(QLabel("Join Key:"))
        join_layout.addWidget(self.join_combo)
        
        # Encoding indicator
        self.encoding_label = QLabel("Encoding: -")
        self.encoding_label.setStyleSheet("QLabel { padding: 3px; }")
        join_layout.addWidget(self.encoding_label)
        
        join_group.setLayout(join_layout)
        layout.addWidget(join_group)
        
        # CSV fields
        fields_group = QGroupBox("CSV Fields")
        fields_layout = QVBoxLayout()
        
        self.fields_scroll = QScrollArea()
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.fields_scroll.setWidget(self.fields_widget)
        self.fields_scroll.setWidgetResizable(True)
        fields_layout.addWidget(self.fields_scroll)
        
        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)
        
        # Overlay settings
        overlay_group = QGroupBox("Overlay Settings")
        overlay_layout = QVBoxLayout()
        
        # Anchor position
        self.anchor_combo = QComboBox()
        self.anchor_combo.addItems(['top_left', 'top_right', 'bottom_left', 'bottom_right'])
        self.anchor_combo.currentTextChanged.connect(self.update_overlay)
        overlay_layout.addWidget(QLabel("Anchor:"))
        overlay_layout.addWidget(self.anchor_combo)
        
        # Font size
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Size:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 48)
        self.font_spin.setValue(16)
        self.font_spin.valueChanged.connect(self.update_overlay)
        font_layout.addWidget(self.font_spin)
        overlay_layout.addLayout(font_layout)
        
        # Background opacity
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Background:"))
        self.bg_check = QCheckBox("Show")
        self.bg_check.setChecked(True)
        self.bg_check.toggled.connect(self.update_overlay)
        opacity_layout.addWidget(self.bg_check)
        overlay_layout.addLayout(opacity_layout)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)
        
        # Presets
        preset_group = QGroupBox("Presets")
        preset_layout = QVBoxLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("-- Select Preset --")
        self.preset_combo.addItems(self.preset_manager.get_preset_names())
        preset_layout.addWidget(self.preset_combo)
        
        preset_btn_layout = QHBoxLayout()
        self.save_preset_btn = QPushButton("Save")
        self.save_preset_btn.clicked.connect(self.save_preset)
        self.apply_preset_btn = QPushButton("Apply")
        self.apply_preset_btn.clicked.connect(self.apply_preset)
        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.clicked.connect(self.delete_preset)
        
        preset_btn_layout.addWidget(self.save_preset_btn)
        preset_btn_layout.addWidget(self.apply_preset_btn)
        preset_btn_layout.addWidget(self.delete_preset_btn)
        preset_layout.addLayout(preset_btn_layout)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # Export
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        
        self.export_mode_combo = QComboBox()
        self.export_mode_combo.addItems(['Skip existing', 'Overwrite', 'Add suffix'])
        self.export_mode_combo.currentIndexChanged.connect(self.on_export_mode_changed)
        export_layout.addWidget(QLabel("If sidecar exists:"))
        export_layout.addWidget(self.export_mode_combo)
        
        # Batch mode selection (mutually exclusive)
        batch_label = QLabel("Batch Mode:")
        export_layout.addWidget(batch_label)
        
        self.batch_preset_radio = QCheckBox("Use preset order/positions")
        self.batch_per_image_radio = QCheckBox("Respect per-image settings")
        self.batch_current_radio = QCheckBox("Apply current to all")
        
        # Make mutually exclusive
        self.batch_preset_radio.toggled.connect(lambda checked: self._on_batch_mode_changed('use_preset', checked))
        self.batch_per_image_radio.toggled.connect(lambda checked: self._on_batch_mode_changed('respect_per_image', checked))
        self.batch_current_radio.toggled.connect(lambda checked: self._on_batch_mode_changed('apply_current', checked))
        
        # Set default
        self.batch_preset_radio.setChecked(True)
        self.batch_config.mode = 'use_preset'
        
        export_layout.addWidget(self.batch_preset_radio)
        export_layout.addWidget(self.batch_per_image_radio)
        export_layout.addWidget(self.batch_current_radio)
        
        self.export_btn = QPushButton("Export XMP Sidecar")
        self.export_btn.clicked.connect(self.export_xmp)
        self.export_btn.setEnabled(False)
        export_layout.addWidget(self.export_btn)
        
        self.export_jpeg_btn = QPushButton("Export JPEG with Overlay")
        self.export_jpeg_btn.clicked.connect(self.export_jpeg_overlay)
        self.export_jpeg_btn.setEnabled(False)
        export_layout.addWidget(self.export_jpeg_btn)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        return widget
    
    def setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Image", self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        self.audit_action = QAction("Enable Audit Logging", self)
        self.audit_action.setCheckable(True)
        self.audit_action.toggled.connect(self.toggle_audit)
        settings_menu.addAction(self.audit_action)
    
    def open_image(self):
        """Open an image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "JPEG Images (*.jpg *.jpeg);;All Files (*.*)")
        
        if not file_path:
            return
        
        self.current_image_path = Path(file_path)
        
        # Load and display image
        pixmap = QPixmap(str(self.current_image_path))
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "Failed to load image")
            return
        
        # Scale to fit
        scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        
        # Reset hash status
        self.hash_verified = False
        self.match_used_fallback = False
        self.encoding_used_fallback = False
        
        # Auto-find CSV
        self.current_csv_path = self.csv_loader.auto_find_csv(self.current_image_path)
        if self.current_csv_path:
            self.load_csv(self.current_csv_path)
        else:
            self.clear_fields()
            # Still start hash computation for image only
            self.start_hash_computation()
            self.update_status_bar()
    
    def open_csv_manual(self):
        """Manually select a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV", "",
            "CSV Files (*.csv);;All Files (*.*)")
        
        if file_path:
            self.current_csv_path = Path(file_path)
            self.load_csv(self.current_csv_path)
    
    def load_csv(self, csv_path: Path):
        """Load and parse CSV file."""
        try:
            self.csv_headers, self.csv_rows = self.csv_loader.parse_csv(csv_path)
            self.original_csv_headers = self.csv_headers.copy()  # Store original order
            
            # Update encoding indicator and track fallback
            encoding_info = self.csv_loader.get_encoding_info()
            self.encoding_used_fallback = encoding_info['fallback_used']
            self.current_encoding = encoding_info['encoding']
            
            encoding_text = f"Encoding: {encoding_info['encoding']}"
            if encoding_info['fallback_used']:
                encoding_text += " (fallback)"
                self.encoding_label.setStyleSheet("QLabel { padding: 3px; background: #ff6; }")
            else:
                self.encoding_label.setStyleSheet("QLabel { padding: 3px; }")
            self.encoding_label.setText(encoding_text)
            
            # Silverstack mode: auto-detect join key
            if app_config.silverstack_only:
                detected_join_key = self.csv_loader.detect_join_key(self.csv_headers)
                self.match_config.join_key = detected_join_key
                # Update UI combo box
                index = self.join_combo.findText(detected_join_key)
                if index >= 0:
                    self.join_combo.setCurrentIndex(index)
                else:
                    # Add detected key if not in standard list
                    self.join_combo.addItem(detected_join_key)
                    self.join_combo.setCurrentText(detected_join_key)
            
            # Populate field checkboxes
            self.populate_fields()
            
            # Apply dataset defaults and validate
            if app_config.silverstack_only:
                dataset_defaults = app_config.get_dataset_defaults(self.csv_headers)
                self.selected_fields = dataset_defaults['selected_fields']
                
                # Set field order from dataset defaults
                self.overlay_spec.field_order = dataset_defaults['field_order']
                
                # Update checkboxes
                for header, checkbox in self.field_checkboxes.items():
                    checkbox.setChecked(header in self.selected_fields)
                
                # Apply auto-sectioning: move selected fields to top
                self._apply_auto_sectioning_on_load()
            
            # Validate Name column if using Name join key
            if self.match_config.join_key == 'Name':
                self.csv_validation = self.csv_loader.validate_name_column(
                    self.csv_rows, self.match_config.join_key)
            
            # Start background hash computation
            if self.current_image_path:
                self.start_hash_computation()
                self.match_current_image()
            
        except Exception as e:
            QMessageBox.warning(self, "CSV Error", f"Failed to load CSV: {e}")
    
    def populate_fields(self):
        """Populate the field widgets with reordering controls."""
        # Clear existing
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.field_widgets = {}
        self.field_checkboxes = {}  # Keep for backward compatibility
        
        for header in self.csv_headers:
            # Use original CSV position for numbering
            original_position = self.original_csv_headers.index(header) + 1 if header in self.original_csv_headers else 0
            field_widget = FieldWidget(header, original_position, self)
            field_widget.checkbox.toggled.connect(lambda checked, h=header: self.on_field_toggled(h, checked))
            
            self.fields_layout.addWidget(field_widget)
            self.field_widgets[header] = field_widget
            self.field_checkboxes[header] = field_widget.checkbox  # For compatibility
        
        self.fields_layout.addStretch()
    
    def on_field_toggled(self, field: str, checked: bool):
        """Handle field checkbox toggle."""
        if checked and field not in self.selected_fields:
            # Add to selected fields
            self.selected_fields.append(field)
            # Also add to field_order if not present
            if field not in self.overlay_spec.field_order:
                self.overlay_spec.field_order.append(field)
            
            # Move selected field to top of csv_headers (with other selected fields)
            self._move_field_to_selected_section(field)
            
        elif not checked and field in self.selected_fields:
            # Remove from selected fields
            self.selected_fields.remove(field)
            # Also remove from field_order
            if field in self.overlay_spec.field_order:
                self.overlay_spec.field_order.remove(field)
            
            # Move unselected field to bottom of csv_headers (with other unselected fields)
            self._move_field_to_unselected_section(field)
        
        # Update field order and selected fields to match new csv_headers order
        self.overlay_spec.field_order = [f for f in self.csv_headers if f in self.selected_fields]
        self.selected_fields = [f for f in self.csv_headers if f in self.selected_fields]
        
        # Update the widget positions without recreating them
        self._update_widget_positions()
        
        # Update overlay and export buttons
        self.update_overlay()
        has_fields = bool(self.selected_fields)
        self.export_btn.setEnabled(has_fields)
        self.export_jpeg_btn.setEnabled(has_fields and bool(self.current_image_path))
    
    def _move_field_to_selected_section(self, field: str):
        """Move field to the selected section (top of the list)."""
        if field not in self.csv_headers:
            return
        
        # Remove field from current position
        self.csv_headers.remove(field)
        
        # Find the position to insert (after the last selected field)
        insert_position = 0
        for i, header in enumerate(self.csv_headers):
            if header in self.selected_fields:
                insert_position = i + 1
            else:
                break
        
        # Insert field in the selected section
        self.csv_headers.insert(insert_position, field)
    
    def _move_field_to_unselected_section(self, field: str):
        """Move field to the unselected section (bottom of the list)."""
        if field not in self.csv_headers:
            return
        
        # Remove field from current position
        self.csv_headers.remove(field)
        
        # Find the position to insert (before the first unselected field)
        insert_position = len(self.csv_headers)
        for i, header in enumerate(self.csv_headers):
            if header not in self.selected_fields:
                insert_position = i
                break
        
        # Insert field in the unselected section
        self.csv_headers.insert(insert_position, field)
    
    def _apply_auto_sectioning_on_load(self):
        """Apply auto-sectioning logic when loading image with pre-selected fields."""
        # Separate selected and unselected fields
        selected_fields_in_order = [f for f in self.csv_headers if f in self.selected_fields]
        unselected_fields_in_order = [f for f in self.csv_headers if f not in self.selected_fields]
        
        # Reorder csv_headers: selected first, then unselected
        self.csv_headers = selected_fields_in_order + unselected_fields_in_order
        
        # Update field order and selected fields to match
        self.overlay_spec.field_order = [f for f in self.csv_headers if f in self.selected_fields]
        self.selected_fields = [f for f in self.csv_headers if f in self.selected_fields]
        
        # Refresh UI to reflect new order
        self._update_widget_positions()
    
    def _update_widget_positions(self):
        """Update widget positions and numbers without recreating them."""
        # Remove all widgets from layout
        widget_order = []
        for header in self.csv_headers:
            if header in self.field_widgets:
                widget = self.field_widgets[header]
                self.fields_layout.removeWidget(widget)
                widget_order.append(widget)
        
        # Add widgets back in the new order but keep original position numbers
        for i, widget in enumerate(widget_order):
            # Don't change position numbers - they should reflect original CSV order
            self.fields_layout.insertWidget(i, widget)
    
    def move_field_up(self, field_name: str):
        """Move field up in the display order."""
        if field_name not in self.csv_headers:
            return
        
        current_index = self.csv_headers.index(field_name)
        if current_index > 0:
            # Swap with previous field in csv_headers
            prev_field = self.csv_headers[current_index - 1]
            self.csv_headers[current_index], self.csv_headers[current_index - 1] = \
                prev_field, field_name
            
            # Update field_order to match csv_headers order for all selected fields
            self.overlay_spec.field_order = [f for f in self.csv_headers if f in self.selected_fields]
            
            # Update selected_fields to match csv_headers order
            self.selected_fields = [f for f in self.csv_headers if f in self.selected_fields]
            
            # Refresh the UI
            self.populate_fields()
            self._restore_field_states()
            self.update_overlay()
    
    def move_field_down(self, field_name: str):
        """Move field down in the display order."""
        if field_name not in self.csv_headers:
            return
        
        current_index = self.csv_headers.index(field_name)
        if current_index < len(self.csv_headers) - 1:
            # Swap with next field in csv_headers
            next_field = self.csv_headers[current_index + 1]
            self.csv_headers[current_index], self.csv_headers[current_index + 1] = \
                next_field, field_name
            
            # Update field_order to match csv_headers order for all selected fields
            self.overlay_spec.field_order = [f for f in self.csv_headers if f in self.selected_fields]
            
            # Update selected_fields to match csv_headers order
            self.selected_fields = [f for f in self.csv_headers if f in self.selected_fields]
            
            # Refresh the UI
            self.populate_fields()
            self._restore_field_states()
            self.update_overlay()
    
    def _restore_field_states(self):
        """Restore checkbox states after reordering."""
        for field_name, widget in self.field_widgets.items():
            widget.set_checked(field_name in self.selected_fields)
    
    def match_current_image(self):
        """Match current image to CSV row."""
        if not self.current_image_path or not self.csv_rows:
            return
        
        # Try exact matching first
        row_index = self.matcher.match_row(
            self.current_image_path, 
            self.csv_rows,
            self.match_config.join_key,
            self.match_config.fallback_keys
        )
        
        # Track if fallback was used
        self.match_used_fallback = self.matcher.last_match_ambiguous
        self.fuzzy_match_used = False
        self.match_confidence = 1.0
        
        # If exact matching fails, try fuzzy matching
        if row_index is None:
            debug_logger.info(f"Exact match failed for {self.current_image_path.name}, trying fuzzy matching")
            fuzzy_matches = self.fuzzy_matcher.match_row_fuzzy(
                self.current_image_path,
                self.csv_rows,
                self.match_config.join_key,
                self.match_config.fallback_keys
            )
            
            if fuzzy_matches:
                row_index = fuzzy_matches[0][0]  # Best match index
                self.match_confidence = fuzzy_matches[0][1]  # Confidence score
                self.fuzzy_match_used = True
                debug_logger.info(f"Fuzzy match found: row {row_index}, confidence {self.match_confidence:.2f}")
            else:
                debug_logger.warning(f"No fuzzy match found for {self.current_image_path.name}")
        
        if row_index is not None:
            if self.matcher.last_match_ambiguous:
                # Multiple matches - show picker for Silverstack mode
                matches = self.matcher.get_multiple_matches(
                    self.current_image_path, self.csv_rows, self.match_config.join_key)
                matched_rows = [self.csv_rows[i] for i in matches]
                dialog = RowPickerDialog(matched_rows, self)
                if dialog.exec():
                    self.current_row = self.csv_rows[matches[dialog.selected_index]]
                    self.match_used_fallback = False  # User selected, no longer ambiguous
                else:
                    self.current_row = None
                    self.update_status_bar()
                    return
            else:
                self.current_row = self.csv_rows[row_index]
        else:
            self.current_row = None
        
        self.update_status_bar()
        self.update_overlay()
    
    @log_exceptions
    def update_overlay(self):
        """Update the image overlay."""
        if not self.current_image_path:
            debug_logger.debug("No image loaded, skipping overlay update")
            return
        
        # Add safety check for missing CSV data
        if not self.csv_rows and self.selected_fields:
            debug_logger.warning("Selected fields but no CSV rows, clearing overlay")
            self.selected_fields = []
            return
        
        # Load original image
        pixmap = QPixmap(str(self.current_image_path))
        if pixmap.isNull():
            return
        
        # Scale first
        scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Apply SlateBar overlay if we have data
        if self.current_row and self.selected_fields:
            # Update overlay spec from UI
            self.overlay_spec.anchor = self.anchor_combo.currentText()
            self.overlay_spec.font_pt = self.font_spin.value()
            self.overlay_spec.show_background = self.bg_check.isChecked()
            
            # Get pinned fields and determine SlateBar fields
            pinned_fields = self.position_manager.get_pinned_fields(self.overlay_spec)
            slate_bar_fields = self.position_manager.get_slate_bar_fields(
                self.selected_fields, self.overlay_spec)
            
            # Update precedence info
            self.precedence_info.tc_source = self.position_manager.detect_tc_source(
                self.current_row, self.selected_fields)
            
            # Render SlateBar with status indicators
            overlaid = self.renderer.render_slate_bar(
                scaled, 
                self.current_row, 
                slate_bar_fields,  # Use filtered fields
                font_pt=self.overlay_spec.font_pt,
                safe_margin_pct=app_config.safe_margin_pct,
                max_rows=app_config.max_rows,
                hash_verified=self.hash_verified,
                match_fallback=self.match_used_fallback,
                encoding_fallback=self.encoding_used_fallback,
                corner=self.overlay_spec.anchor,
                pinned_fields=pinned_fields,
                encoding_used=self.current_encoding,
                show_background=self.overlay_spec.show_background
            )
            
            
            self.image_label.setPixmap(overlaid)
        else:
            self.image_label.setPixmap(scaled)
    
    def on_join_key_changed(self, key: str):
        """Handle join key change."""
        self.match_config.join_key = key
        if self.current_image_path and self.csv_rows:
            self.match_current_image()
    
    def on_export_mode_changed(self, index: int):
        """Handle export mode change."""
        modes = ['skip', 'overwrite', 'suffix']
        self.export_config.mode = modes[index]
    
    def _on_batch_mode_changed(self, mode: str, checked: bool):
        """Handle batch mode change (mutually exclusive)."""
        if not checked:
            return
        
        # Uncheck others (mutually exclusive)
        if mode != 'use_preset':
            self.batch_preset_radio.setChecked(False)
        if mode != 'respect_per_image':
            self.batch_per_image_radio.setChecked(False)
        if mode != 'apply_current':
            self.batch_current_radio.setChecked(False)
        
        # Set the selected mode
        if mode == 'use_preset':
            self.batch_preset_radio.setChecked(True)
        elif mode == 'respect_per_image':
            self.batch_per_image_radio.setChecked(True)
        elif mode == 'apply_current':
            self.batch_current_radio.setChecked(True)
        
        self.batch_config.mode = mode
    
    def clear_fields(self):
        """Clear field checkboxes."""
        try:
            debug_logger.debug("Clearing fields")
            while self.fields_layout.count():
                item = self.fields_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.csv_headers = []
            self.original_csv_headers = []
            self.csv_rows = []
            self.current_row = None
            self.selected_fields = []
            self.field_checkboxes = {}
            self.field_widgets = {}
            
            # Clear overlay if no CSV data
            if self.current_image_path and hasattr(self, 'image_label'):
                pixmap = QPixmap(str(self.current_image_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled)
        except Exception as e:
            debug_logger.error("Error clearing fields", exception=e)
    
    def start_hash_computation(self):
        """Start background hash computation."""
        if not self.current_image_path:
            return
        
        def on_hashes_computed(hashes: Dict[str, str]):
            if 'error' in hashes:
                print(f"Hash computation error: {hashes['error']}")
                return
            
            self.current_hashes = hashes
            self.hash_verified = True
            self.update_status_bar()
            self.update_overlay()  # Refresh overlay to show hash status
        
        compute_hashes_async(self.current_image_path, self.current_csv_path, on_hashes_computed)
    
    def update_status_bar(self):
        """Update status bar with comprehensive state info."""
        if not self.current_image_path:
            self.status_label.setText("No image loaded")
            return
        
        # Update precedence info with fuzzy matching
        if getattr(self, 'fuzzy_match_used', False):
            self.precedence_info.match_type = f"{self.match_config.join_key} (fuzzy)"
            self.precedence_info.match_confidence = getattr(self, 'match_confidence', None)
        else:
            self.precedence_info.match_type = f"{self.match_config.join_key} ({'exact' if not self.match_used_fallback else 'fallback'})"
            self.precedence_info.match_confidence = None
        
        # Check for validation issues
        if not self.csv_validation['valid']:
            issues = self.csv_validation['issues']
            if any(i['type'] == 'duplicate' for i in issues):
                duplicate_issue = next(i for i in issues if i['type'] == 'duplicate')
                status_text = f"Multiple rows for 'Name={duplicate_issue['name']}'. Choose a row before export."
            elif any(i['type'] == 'missing' for i in issues):
                status_text = f"Missing Name values in CSV. Check rows and resolve before export."
            else:
                status_text = "CSV validation issues detected."
            
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("QLabel { padding: 5px; background: #c33; color: #fff; }")
            return
        
        # Normal status display
        status_text = self.precedence_info.format_status()
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet("QLabel { padding: 5px; background: #333; color: #fff; }")
    
    def save_preset(self):
        """Save current settings as preset."""
        if not self.selected_fields:
            QMessageBox.warning(self, "Warning", "No fields selected")
            return
        
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if ok and name:
            # Update overlay spec from UI
            self.overlay_spec.anchor = self.anchor_combo.currentText()
            self.overlay_spec.font_pt = self.font_spin.value()
            self.overlay_spec.show_background = self.bg_check.isChecked()
            
            preset = Preset(
                name=name,
                selected_fields=self.selected_fields.copy(),
                overlay=self.overlay_spec,
                match=self.match_config
            )
            
            self.preset_manager.save_preset(preset)
            self.audit_logger.log_preset_save(name, self.selected_fields)
            
            # Update combo
            if name not in [self.preset_combo.itemText(i) 
                          for i in range(self.preset_combo.count())]:
                self.preset_combo.addItem(name)
            
            QMessageBox.information(self, "Success", f"Preset '{name}' saved")
    
    def apply_preset(self):
        """Apply selected preset."""
        preset_name = self.preset_combo.currentText()
        if preset_name == "-- Select Preset --":
            return
        
        preset = self.preset_manager.get_preset(preset_name)
        if not preset:
            return
        
        # Apply settings
        self.selected_fields = preset.selected_fields.copy()
        self.overlay_spec = preset.overlay
        self.match_config = preset.match
        
        # Update UI
        self.anchor_combo.setCurrentText(preset.overlay.anchor)
        self.font_spin.setValue(preset.overlay.font_pt)
        self.bg_check.setChecked(preset.overlay.show_background)
        self.join_combo.setCurrentText(preset.match.join_key)
        
        # Update field checkboxes
        for header, checkbox in self.field_checkboxes.items():
            checkbox.setChecked(header in self.selected_fields)
        
        self.update_overlay()
    
    def delete_preset(self):
        """Delete selected preset."""
        preset_name = self.preset_combo.currentText()
        if preset_name == "-- Select Preset --":
            return
        
        reply = QMessageBox.question(self, "Delete Preset", 
                                    f"Delete preset '{preset_name}'?")
        if reply == QMessageBox.Yes:
            self.preset_manager.delete_preset(preset_name)
            index = self.preset_combo.findText(preset_name)
            if index >= 0:
                self.preset_combo.removeItem(index)
    
    def export_xmp(self):
        """Export XMP sidecar for current image."""
        if not self.current_image_path or not self.current_row or not self.selected_fields:
            QMessageBox.warning(self, "Export Error", 
                              "Missing image, CSV match, or selected fields")
            return
        
        # Block export if CSV validation failed
        if not self.csv_validation['valid']:
            issues_text = '\n'.join([issue['message'] for issue in self.csv_validation['issues'][:3]])
            QMessageBox.critical(self, "Export Blocked", 
                               f"Cannot export due to CSV validation issues:\n\n{issues_text}")
            return
        
        try:
            # Preflight validation - check if files changed
            files_valid, error_msg = validate_files_unchanged(
                self.current_image_path, self.current_csv_path)
            
            if not files_valid:
                QMessageBox.critical(self, "Export Blocked", 
                                   f"Export blocked: {error_msg}\n\n"
                                   "Files have been modified since loading. Please reload the image/CSV.")
                return
            
            # Check for existing sidecar
            xmp_path = self.current_image_path.with_suffix('.xmp')
            
            if xmp_path.exists():
                if self.export_config.mode == 'skip':
                    QMessageBox.information(self, "Skipped", 
                                          f"Sidecar already exists: {xmp_path.name}")
                    return
                elif self.export_config.mode == 'suffix':
                    # Find next available suffix
                    counter = 1
                    while True:
                        new_path = self.current_image_path.with_suffix(f'_{counter}.xmp')
                        if not new_path.exists():
                            xmp_path = new_path
                            break
                        counter += 1
            
            # Use cached hashes if available, otherwise compute fresh
            hashes = self.current_hashes if self.hash_verified else {}
            if not hashes.get('jpeg'):
                from .export.hash_utils import compute_file_hashes
                hashes = compute_file_hashes(self.current_image_path, self.current_csv_path)
            
            # Write XMP with new field order and positions
            output_path = self.xmp_writer.write_xmp_sidecar(
                self.current_image_path,
                self.current_row,
                self.selected_fields,
                self.overlay_spec.to_json(),
                self.match_config.join_key,
                self.current_csv_path,
                hashes,
                field_order=self.overlay_spec.field_order if self.overlay_spec.field_order else None,
                overlay_positions=self.overlay_spec.overlay_positions if self.overlay_spec.overlay_positions else None
            )
            
            # Log with precedence tracking
            precedence_used = f"order:{self.precedence_info.order_source},positions:{self.precedence_info.position_source}"
            self.audit_logger.log_export(
                str(self.current_image_path),
                str(self.current_csv_path),
                self.selected_fields,
                hashes,
                self.match_config.join_key,
                precedence_used=precedence_used,
                resolved_join_key=self.match_config.join_key
            )
            
            QMessageBox.information(self, "Success", 
                                  f"XMP sidecar written: {output_path.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export XMP: {e}")
    
    @log_exceptions
    def export_jpeg_overlay(self):
        """Export JPEG with overlay burned in."""
        if not self.current_image_path or not self.current_row or not self.selected_fields:
            QMessageBox.warning(self, "Export Error", 
                              "Missing image, CSV match, or selected fields")
            return
        
        # Choose output location
        suggested_name = f"{self.current_image_path.stem}_overlay{self.current_image_path.suffix}"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save JPEG with Overlay", suggested_name,
            "JPEG Images (*.jpg *.jpeg);;All Files (*)"
        )
        
        if not output_path:
            return
        
        try:
            debug_logger.info(f"Exporting JPEG with overlay to: {output_path}")
            
            # Load full-resolution image
            pixmap = QPixmap(str(self.current_image_path))
            if pixmap.isNull():
                raise Exception("Could not load source image")
            
            # Create overlay spec from current settings
            overlay_spec = OverlaySpec(
                fields=self.selected_fields.copy(),
                slate_bar=True,  # Use slate bar for production
                positions=self.position_manager.get_current_positions()
            )
            
            # Apply current display settings
            overlay_spec.anchor = self.anchor_combo.currentText()
            overlay_spec.font_pt = self.font_spin.value()
            overlay_spec.show_background = self.bg_check.isChecked()
            
            # Render overlay at full resolution
            overlay_pixmap = self.renderer.render_overlay(
                pixmap, self.current_row, overlay_spec
            )
            
            # Save as JPEG
            if overlay_pixmap.save(output_path, "JPEG", quality=95):
                QMessageBox.information(
                    self, "Export Complete", 
                    f"JPEG with overlay saved to:\n{output_path}"
                )
                debug_logger.info(f"JPEG export successful: {output_path}")
                
                # Log the export operation
                self.audit_logger.log_export(
                    str(self.current_image_path),
                    str(output_path),
                    self.selected_fields,
                    export_type="jpeg_overlay"
                )
            else:
                raise Exception("Failed to save JPEG file")
                
        except Exception as e:
            debug_logger.error("JPEG export failed", exception=e)
            QMessageBox.critical(
                self, "Export Error", 
                f"Failed to export JPEG with overlay:\n{e}"
            )
    
    def select_batch_folder(self):
        """Select folder for batch operations."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.batch_folder = Path(folder)
            self.batch_apply_btn.setEnabled(True)
            
            # Count images
            image_count = len(list(self.batch_folder.glob("*.jpg")) + 
                            list(self.batch_folder.glob("*.jpeg")))
            self.batch_apply_btn.setText(f"Apply Preset ({image_count} images)")
    
    def apply_batch(self):
        """Apply preset to batch of images."""
        preset_name = self.preset_combo.currentText()
        if preset_name == "-- Select Preset --":
            QMessageBox.warning(self, "Warning", "Please select a preset first")
            return
        
        preset = self.preset_manager.get_preset(preset_name)
        if not preset or not hasattr(self, 'batch_folder'):
            return
        
        # Process images
        images = list(self.batch_folder.glob("*.jpg")) + list(self.batch_folder.glob("*.jpeg"))
        processed = 0
        errors = []
        
        for image_path in images:
            try:
                # Find CSV
                csv_path = self.csv_loader.auto_find_csv(image_path)
                if not csv_path:
                    errors.append(f"{image_path.name}: No CSV found")
                    continue
                
                # Load CSV
                headers, rows = self.csv_loader.parse_csv(csv_path)
                
                # Match row
                row_index = self.matcher.match_row(
                    image_path, rows, preset.match.join_key, preset.match.fallback_keys)
                
                if row_index is None:
                    errors.append(f"{image_path.name}: No match in CSV")
                    continue
                
                if self.matcher.last_match_ambiguous:
                    errors.append(f"{image_path.name}: Multiple matches (skipped)")
                    continue
                
                row = rows[row_index]
                
                # Compute hashes
                hashes = compute_file_hashes(image_path, csv_path)
                
                # Write XMP
                self.xmp_writer.write_xmp_sidecar(
                    image_path, row, preset.selected_fields,
                    preset.overlay.to_json(), preset.match.join_key,
                    csv_path, hashes
                )
                
                processed += 1
                
            except Exception as e:
                errors.append(f"{image_path.name}: {e}")
        
        # Log batch operation
        self.audit_logger.log_batch_operation(processed, preset_name)
        
        # Show results
        message = f"Processed {processed}/{len(images)} images"
        if errors:
            message += f"\n\nErrors:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                message += f"\n... and {len(errors)-10} more"
        
        QMessageBox.information(self, "Batch Complete", message)
    
    def toggle_audit(self, checked: bool):
        """Toggle audit logging."""
        self.audit_logger.enabled = checked
        if checked:
            self.audit_logger.__init__(enabled=True)
            QMessageBox.information(self, "Audit", 
                                  f"Audit logging enabled.\nLogs: {self.audit_logger.log_dir}")