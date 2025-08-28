#!/usr/bin/env python3
"""
SlateLink Simple - Simplified JPEG Overlay Tool
A streamlined version for reliable on-set use.
Load JPEG → Load CSV → Select Fields → Export JPEG with Overlay
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QListWidget,
                             QFileDialog, QMessageBox, QCheckBox, QScrollArea,
                             QGroupBox, QListWidgetItem)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt
from typing import Optional, List, Dict

from .data.csv_loader import CSVLoader
from .data.matcher import Matcher
from .data.fuzzy_matcher import FuzzyMatcher
from .overlay.renderer import OverlayRenderer
from .models.types import OverlaySpec
from .debug.logger import debug_logger, log_exceptions


class SimpleMainWindow(QMainWindow):
    """Simplified main window with essential functions only."""
    
    def __init__(self):
        super().__init__()
        debug_logger.info("Initializing SimpleMainWindow")
        
        self.setWindowTitle('SlateLink Simple - JPEG Overlay Tool')
        self.setGeometry(100, 100, 1000, 700)
        
        # Core components
        self.csv_loader = CSVLoader()
        self.matcher = Matcher()
        self.fuzzy_matcher = FuzzyMatcher(min_confidence=0.6)
        self.renderer = OverlayRenderer()
        
        # Data storage
        self.current_image_path: Optional[Path] = None
        self.current_csv_path: Optional[Path] = None
        self.csv_headers: List[str] = []
        self.csv_rows: List[Dict[str, str]] = []
        self.current_row: Optional[Dict[str, str]] = None
        self.selected_fields: List[str] = []
        
        self.setup_ui()
        debug_logger.info("SimpleMainWindow initialized successfully")
    
    def setup_ui(self):
        """Setup simplified UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        # File loading section
        file_group = QGroupBox("1. Load Files")
        file_layout = QVBoxLayout(file_group)
        
        # Image loading
        self.load_image_btn = QPushButton("Load JPEG Image")
        self.load_image_btn.clicked.connect(self.load_image)
        file_layout.addWidget(self.load_image_btn)
        
        self.image_status = QLabel("No image loaded")
        self.image_status.setStyleSheet("QLabel { color: #666; }")
        file_layout.addWidget(self.image_status)
        
        # CSV loading
        self.load_csv_btn = QPushButton("Load CSV Metadata")
        self.load_csv_btn.clicked.connect(self.load_csv)
        file_layout.addWidget(self.load_csv_btn)
        
        self.csv_status = QLabel("No CSV loaded")
        self.csv_status.setStyleSheet("QLabel { color: #666; }")
        file_layout.addWidget(self.csv_status)
        
        left_layout.addWidget(file_group)
        
        # Field selection section
        fields_group = QGroupBox("2. Select Fields to Overlay")
        fields_layout = QVBoxLayout(fields_group)
        
        # Scrollable field list
        self.fields_scroll = QScrollArea()
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.fields_scroll.setWidget(self.fields_widget)
        self.fields_scroll.setWidgetResizable(True)
        fields_layout.addWidget(self.fields_scroll)
        
        # Match status
        self.match_status = QLabel("Load files to see available fields")
        self.match_status.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        self.match_status.setWordWrap(True)
        fields_layout.addWidget(self.match_status)
        
        left_layout.addWidget(fields_group)
        
        # Export section
        export_group = QGroupBox("3. Export JPEG with Overlay")
        export_layout = QVBoxLayout(export_group)
        
        self.export_btn = QPushButton("Export JPEG with Overlay")
        self.export_btn.clicked.connect(self.export_jpeg)
        self.export_btn.setEnabled(False)
        export_layout.addWidget(self.export_btn)
        
        self.export_status = QLabel("Select fields and export")
        self.export_status.setStyleSheet("QLabel { color: #666; }")
        export_layout.addWidget(self.export_status)
        
        left_layout.addWidget(export_group)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # Right panel - Image preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        preview_label = QLabel("Preview")
        preview_label.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(preview_label)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel { border: 1px solid #ccc; background: #f0f0f0; }")
        self.image_label.setMinimumSize(400, 300)
        right_layout.addWidget(self.image_label)
        
        main_layout.addWidget(right_panel)
        
        # Field checkboxes storage
        self.field_checkboxes: Dict[str, QCheckBox] = {}
    
    @log_exceptions
    def load_image(self):
        """Load JPEG image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load JPEG Image", "", 
            "JPEG Images (*.jpg *.jpeg);;All Files (*)"
        )
        
        if file_path:
            self.current_image_path = Path(file_path)
            debug_logger.info(f"Loading image: {self.current_image_path}")
            
            # Display image
            pixmap = QPixmap(str(self.current_image_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
                self.image_status.setText(f"✓ {self.current_image_path.name}")
                self.image_status.setStyleSheet("QLabel { color: green; }")
                
                # Try to match with CSV if already loaded
                if self.csv_rows:
                    self.match_current_image()
                    
            else:
                QMessageBox.warning(self, "Error", "Could not load image file")
    
    @log_exceptions
    def load_csv(self):
        """Load CSV metadata file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load CSV Metadata", "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.current_csv_path = Path(file_path)
            debug_logger.info(f"Loading CSV: {self.current_csv_path}")
            
            try:
                # Parse CSV
                headers, rows = self.csv_loader.parse_csv(self.current_csv_path)
                self.csv_headers = headers
                self.csv_rows = rows
                
                # Update status
                self.csv_status.setText(f"✓ {len(rows)} rows, {len(headers)} fields")
                self.csv_status.setStyleSheet("QLabel { color: green; }")
                
                # Setup field checkboxes
                self.setup_field_checkboxes()
                
                # Try to match if image already loaded
                if self.current_image_path:
                    self.match_current_image()
                    
            except Exception as e:
                debug_logger.error("Failed to load CSV", exception=e)
                QMessageBox.warning(self, "CSV Error", f"Could not load CSV file:\n{e}")
    
    def setup_field_checkboxes(self):
        """Create checkboxes for available CSV fields."""
        # Clear existing checkboxes
        for checkbox in self.field_checkboxes.values():
            checkbox.deleteLater()
        self.field_checkboxes.clear()
        
        # Clear layout
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new checkboxes
        for field in self.csv_headers:
            checkbox = QCheckBox(field)
            checkbox.toggled.connect(self.on_field_toggled)
            self.field_checkboxes[field] = checkbox
            self.fields_layout.addWidget(checkbox)
        
        debug_logger.info(f"Created {len(self.csv_headers)} field checkboxes")
    
    def on_field_toggled(self, checked: bool):
        """Handle field checkbox toggle."""
        sender = self.sender()
        if sender:
            field_name = sender.text()
            if checked and field_name not in self.selected_fields:
                self.selected_fields.append(field_name)
            elif not checked and field_name in self.selected_fields:
                self.selected_fields.remove(field_name)
            
            # Update export button state
            self.export_btn.setEnabled(
                bool(self.current_image_path and self.current_row and self.selected_fields)
            )
            
            # Update preview
            self.update_preview()
            
            debug_logger.debug(f"Selected fields: {self.selected_fields}")
    
    def match_current_image(self):
        """Match current image to CSV row."""
        if not self.current_image_path or not self.csv_rows:
            return
        
        debug_logger.info(f"Matching image: {self.current_image_path.name}")
        
        # Try exact match first (using 'Name' as primary key)
        row_index = self.matcher.match_row(
            self.current_image_path, 
            self.csv_rows,
            'Name',  # Primary join key for production workflows
            ['Filename', 'File', 'Clip Name', 'Production']  # Fallbacks
        )
        
        match_type = "exact"
        confidence = 1.0
        
        # Try fuzzy matching if exact fails
        if row_index is None:
            debug_logger.info("Exact match failed, trying fuzzy matching")
            fuzzy_matches = self.fuzzy_matcher.match_row_fuzzy(
                self.current_image_path,
                self.csv_rows,
                'Name',
                ['Filename', 'File', 'Clip Name', 'Production']
            )
            
            if fuzzy_matches:
                row_index = fuzzy_matches[0][0]
                confidence = fuzzy_matches[0][1]
                match_type = "fuzzy"
                debug_logger.info(f"Fuzzy match found: row {row_index}, confidence {confidence:.2f}")
        
        # Update match status
        if row_index is not None:
            self.current_row = self.csv_rows[row_index]
            if match_type == "fuzzy":
                self.match_status.setText(f"✓ Matched row {row_index + 1} ({match_type}, {confidence:.0%} confidence)")
            else:
                self.match_status.setText(f"✓ Matched row {row_index + 1} ({match_type} match)")
            self.match_status.setStyleSheet("QLabel { color: green; font-size: 11px; }")
        else:
            self.current_row = None
            self.match_status.setText("⚠ No matching row found - select fields manually")
            self.match_status.setStyleSheet("QLabel { color: orange; font-size: 11px; }")
        
        # Update export button
        self.export_btn.setEnabled(
            bool(self.current_image_path and self.current_row and self.selected_fields)
        )
    
    def update_preview(self):
        """Update image preview with overlay."""
        if not self.current_image_path:
            return
        
        # Load original image
        pixmap = QPixmap(str(self.current_image_path))
        if pixmap.isNull():
            return
        
        # If we have fields selected and matched row, render overlay
        if self.selected_fields and self.current_row:
            try:
                # Create overlay spec
                overlay_spec = OverlaySpec(
                    fields=self.selected_fields.copy(),
                    slate_bar=True,  # Enable slate bar for production use
                    positions={}  # Use automatic positioning
                )
                
                # Render overlay
                overlay_pixmap = self.renderer.render_overlay(
                    pixmap, self.current_row, overlay_spec
                )
                
                # Scale for display
                scaled = overlay_pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
                
            except Exception as e:
                debug_logger.error("Preview overlay failed", exception=e)
                # Fall back to original image
                scaled = pixmap.scaled(
                    self.image_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
        else:
            # Show original image
            scaled = pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
    
    @log_exceptions
    def export_jpeg(self):
        """Export JPEG with overlay."""
        if not (self.current_image_path and self.current_row and self.selected_fields):
            QMessageBox.warning(self, "Export Error", "Load image, CSV, and select fields first")
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
            
            # Create overlay spec
            overlay_spec = OverlaySpec(
                fields=self.selected_fields.copy(),
                slate_bar=True,
                positions={}
            )
            
            # Render overlay at full resolution
            overlay_pixmap = self.renderer.render_overlay(
                pixmap, self.current_row, overlay_spec
            )
            
            # Save as JPEG
            if overlay_pixmap.save(output_path, "JPEG", quality=95):
                self.export_status.setText(f"✓ Exported: {Path(output_path).name}")
                self.export_status.setStyleSheet("QLabel { color: green; }")
                
                # Show success message
                QMessageBox.information(
                    self, "Export Complete", 
                    f"JPEG with overlay saved to:\n{output_path}"
                )
                
                debug_logger.info(f"JPEG export successful: {output_path}")
            else:
                raise Exception("Failed to save JPEG file")
                
        except Exception as e:
            debug_logger.error("JPEG export failed", exception=e)
            QMessageBox.critical(
                self, "Export Error", 
                f"Failed to export JPEG:\n{e}"
            )
            self.export_status.setText("Export failed")
            self.export_status.setStyleSheet("QLabel { color: red; }")


def main():
    """Run the simplified SlateLink app."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SlateLink Simple - JPEG Overlay Tool')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with verbose logging')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Set logging level (default: INFO)')
    parser.add_argument('--enable-saliency', action='store_true',
                       help='Enable saliency-aware overlay placement (may cause crashes on some systems)')
    
    args = parser.parse_args()
    
    # Initialize debug logging
    from .debug.logger import debug_logger, setup_exception_handler
    debug_logger.initialize(debug_mode=args.debug, log_level=args.log_level)
    setup_exception_handler()
    
    # Apply saliency setting if enabled
    if args.enable_saliency:
        from .config.app_config import app_config
        app_config.saliency_placement = True
        debug_logger.info("Saliency processing enabled via --enable-saliency flag")
    
    debug_logger.info("Starting SlateLink Simple")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("SlateLink Simple")
    app.setApplicationVersion("0.2.0")
    app.setOrganizationName("SlateLink")
    
    # Create and show main window
    try:
        window = SimpleMainWindow()
        window.show()
        debug_logger.info("SlateLink Simple window shown")
    except Exception as e:
        debug_logger.critical("Failed to create simple window", exception=e)
        sys.exit(1)
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()