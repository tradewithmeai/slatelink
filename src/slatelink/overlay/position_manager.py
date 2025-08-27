"""Position manager for free placement overlay system."""

from typing import Dict, Tuple, List, Optional
from pathlib import Path
from PySide6.QtCore import QRectF, QPointF
from ..models.types import OverlaySpec, PrecedenceInfo
import logging

logger = logging.getLogger(__name__)


class PositionManager:
    """Manages overlay positions with precedence rules and validation."""
    
    def __init__(self):
        self.safe_margin = 0.05  # 5% safe margin
        self.snap_grid = 0.01    # 1% snap grid
    
    def resolve_precedence(self, 
                          per_image_spec: Optional[OverlaySpec],
                          preset_spec: Optional[OverlaySpec],
                          dataset_defaults: Dict,
                          csv_headers: List[str]) -> Tuple[OverlaySpec, PrecedenceInfo]:
        """
        Resolve field order and positions using precedence rules.
        
        Precedence: per-image XMP → preset → dataset defaults → auto
        """
        precedence = PrecedenceInfo()
        
        # Start with base spec
        result_spec = OverlaySpec()
        
        # Resolve field order
        if per_image_spec and per_image_spec.field_order:
            # Per-image XMP has field order
            result_spec.field_order = self._validate_fields(per_image_spec.field_order, csv_headers)
            precedence.order_source = 'per-image'
        elif preset_spec and preset_spec.field_order:
            # Preset has field order
            result_spec.field_order = self._validate_fields(preset_spec.field_order, csv_headers)
            precedence.order_source = 'preset'
        elif dataset_defaults.get('field_order'):
            # Dataset defaults
            result_spec.field_order = self._validate_fields(dataset_defaults['field_order'], csv_headers)
            precedence.order_source = 'dataset'
        else:
            # Auto (no specific order)
            precedence.order_source = 'auto'
        
        # Resolve positions
        if per_image_spec and per_image_spec.overlay_positions:
            # Per-image XMP has positions
            result_spec.overlay_positions = self._validate_positions(per_image_spec.overlay_positions, csv_headers)
            precedence.position_source = 'per-image'
        elif preset_spec and preset_spec.overlay_positions:
            # Preset has positions
            result_spec.overlay_positions = self._validate_positions(preset_spec.overlay_positions, csv_headers)
            precedence.position_source = 'preset'
        else:
            # Auto (saliency/default corner)
            precedence.position_source = 'auto'
        
        # Copy other properties from preset or defaults
        if preset_spec:
            result_spec.anchor = preset_spec.anchor
            result_spec.font_pt = max(12, preset_spec.font_pt)  # Minimum 12pt
            result_spec.padding_px = preset_spec.padding_px
            result_spec.line_spacing_px = preset_spec.line_spacing_px
            result_spec.box_opacity = preset_spec.box_opacity
            result_spec.show_background = preset_spec.show_background
        
        return result_spec, precedence
    
    def _validate_fields(self, field_list: List[str], csv_headers: List[str]) -> List[str]:
        """Validate fields against CSV headers."""
        valid_fields = [f for f in field_list if f in csv_headers]
        ignored = set(field_list) - set(valid_fields)
        
        if ignored:
            logger.info(f"Ignored unknown fields in order: {ignored}")
        
        return valid_fields
    
    def _validate_positions(self, positions: Dict[str, Tuple[float, float]], 
                           csv_headers: List[str]) -> Dict[str, Tuple[float, float]]:
        """Validate positions against CSV headers."""
        valid_positions = {}
        ignored_fields = set()
        
        for field, (x, y) in positions.items():
            if field not in csv_headers:
                ignored_fields.add(field)
                continue
            
            # Clamp to 0-1 with 4 decimal precision
            clamped_x = max(0.0, min(1.0, round(x, 4)))
            clamped_y = max(0.0, min(1.0, round(y, 4)))
            
            if x != clamped_x or y != clamped_y:
                logger.warning(f"Position for '{field}' clamped from ({x:.4f}, {y:.4f}) to ({clamped_x:.4f}, {clamped_y:.4f})")
            
            valid_positions[field] = (clamped_x, clamped_y)
        
        if ignored_fields:
            logger.info(f"Ignored unknown fields in positions: {ignored_fields}")
        
        return valid_positions
    
    def get_pinned_fields(self, overlay_spec: OverlaySpec) -> List[str]:
        """Get list of fields that have pinned positions."""
        return list(overlay_spec.overlay_positions.keys())
    
    def get_slate_bar_fields(self, selected_fields: List[str], overlay_spec: OverlaySpec) -> List[str]:
        """
        Get fields that should appear in SlateBar (excluding pinned fields).
        
        If any field that would appear in the SlateBar is pinned, exclude it from the bar
        and render at its pinned location; remaining chips keep the user list order.
        """
        pinned_fields = set(self.get_pinned_fields(overlay_spec))
        
        # Use field_order if available and contains all selected fields, otherwise selected_fields order
        if overlay_spec.field_order:
            # Ensure all selected fields are in the order, add missing ones at the end
            ordered_fields = []
            for f in overlay_spec.field_order:
                if f in selected_fields:
                    ordered_fields.append(f)
            # Add any selected fields not in field_order
            for f in selected_fields:
                if f not in ordered_fields:
                    ordered_fields.append(f)
            field_order = ordered_fields
        else:
            field_order = selected_fields
        
        # Filter out pinned fields
        slate_bar_fields = [f for f in field_order if f not in pinned_fields]
        
        return slate_bar_fields
    
    def snap_to_grid(self, x: float, y: float) -> Tuple[float, float]:
        """Snap position to grid with safe margins."""
        # Apply snap grid
        snapped_x = round(x / self.snap_grid) * self.snap_grid
        snapped_y = round(y / self.snap_grid) * self.snap_grid
        
        # Apply safe margins
        min_pos = self.safe_margin
        max_pos = 1.0 - self.safe_margin
        
        snapped_x = max(min_pos, min(max_pos, snapped_x))
        snapped_y = max(min_pos, min(max_pos, snapped_y))
        
        return round(snapped_x, 4), round(snapped_y, 4)
    
    def position_to_pixel(self, normalized_pos: Tuple[float, float], 
                         image_width: int, image_height: int) -> Tuple[int, int]:
        """Convert normalized position to pixel coordinates."""
        x, y = normalized_pos
        pixel_x = int(x * image_width)
        pixel_y = int(y * image_height)
        return pixel_x, pixel_y
    
    def pixel_to_position(self, pixel_pos: Tuple[int, int], 
                         image_width: int, image_height: int) -> Tuple[float, float]:
        """Convert pixel coordinates to normalized position."""
        x, y = pixel_pos
        norm_x = x / image_width if image_width > 0 else 0.0
        norm_y = y / image_height if image_height > 0 else 0.0
        return round(norm_x, 4), round(norm_y, 4)
    
    def detect_tc_source(self, row: Dict[str, str], selected_fields: List[str]) -> str:
        """Detect TC source for status display."""
        if 'TC Start' in selected_fields and 'TC Start' in row and row['TC Start']:
            return 'Start'
        elif 'TC End' in selected_fields and 'TC End' in row and row['TC End']:
            return 'End'
        elif 'Timecode Start' in selected_fields and 'Timecode Start' in row and row['Timecode Start']:
            return 'Start'
        elif 'Timecode In' in selected_fields and 'Timecode In' in row and row['Timecode In']:
            return 'Start'
        else:
            return 'none'