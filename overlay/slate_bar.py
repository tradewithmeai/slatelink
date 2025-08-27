"""SlateBar overlay renderer with chips and status indicators."""

from PySide6.QtGui import QPainter, QPixmap, QFont, QColor, QFontMetrics, QPen
from PySide6.QtCore import Qt, QRect
from typing import List, Dict, Tuple, Optional


class SlateBar:
    """Compact horizontal bar with rounded chip display."""
    
    # CVD-safe colors
    COLORS = {
        'verified': QColor(34, 139, 34),      # Forest green
        'warning': QColor(255, 140, 0),       # Dark orange  
        'info': QColor(30, 144, 255),         # Dodger blue
        'background': QColor(0, 0, 0, 200),   # Semi-transparent black
        'text': QColor(255, 255, 255),        # White
        'chip_bg': QColor(60, 60, 60, 220),   # Dark gray
    }
    
    def __init__(self):
        self.chip_height = 28
        self.chip_padding = 8
        self.chip_spacing = 6
        self.corner_radius = 8
        self.micro_chip_size = 20
    
    def render_slate_bar(self, pixmap: QPixmap, row: Dict[str, str], 
                        selected_fields: List[str], corner: str = 'top_left',
                        font_pt: int = 12, safe_margin_pct: int = 5,
                        max_rows: int = 2, hash_verified: bool = False,
                        match_fallback: bool = False, encoding_fallback: bool = False,
                        pinned_fields: List[str] = None, encoding_used: str = 'utf-8',
                        show_background: bool = True) -> QPixmap:
        """Render SlateBar with chips and micro-indicators."""
        
        result = QPixmap(pixmap)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate safe margins
        margin_w = int(pixmap.width() * safe_margin_pct / 100)
        margin_h = int(pixmap.height() * safe_margin_pct / 100)
        
        # Set font
        font = QFont('Arial', font_pt)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        
        # Get priority fields for chips (excluding pinned fields)
        if pinned_fields is None:
            pinned_fields = []
        chip_fields = self._get_chip_fields(row, selected_fields, pinned_fields)
        if not chip_fields:
            painter.end()
            return result
        
        # Create chips
        chips = self._create_chips(chip_fields, metrics)
        
        # Add micro-chips
        micro_chips = self._create_micro_chips(hash_verified, match_fallback, encoding_fallback, encoding_used)
        
        # Layout chips in rows
        rows = self._layout_chips(chips + micro_chips, pixmap.width() - 2 * margin_w, max_rows)
        
        # Calculate total bar size
        bar_width = max(sum(chip['width'] + self.chip_spacing for chip in row) - self.chip_spacing 
                       for row in rows) if rows else 0
        bar_height = len(rows) * (self.chip_height + self.chip_spacing) - self.chip_spacing
        
        # Position bar based on corner
        x, y = self._get_bar_position(corner, pixmap.width(), pixmap.height(), 
                                     bar_width, bar_height, margin_w, margin_h)
        
        # Draw chips
        self._draw_chips(painter, rows, x, y, show_background)
        
        painter.end()
        return result
    
    def _get_chip_fields(self, row: Dict[str, str], selected_fields: List[str], 
                        pinned_fields: List[str] = None) -> List[Tuple[str, str]]:
        """Get fields for chip display, excluding pinned fields."""
        if pinned_fields is None:
            pinned_fields = []
        
        chip_fields = []
        tc_fields_added = set()  # Track which TC fields we've added
        
        # Respect the order of selected_fields (already ordered by position_manager)
        for field in selected_fields:
            if field in pinned_fields:
                continue
                
            if field not in row or not row[field]:
                continue
            
            # Special handling for TC fields - label as "TC" and avoid duplicates
            if field in ['TC Start', 'TC End', 'Timecode Start', 'Timecode In']:
                if 'TC' not in tc_fields_added:
                    chip_fields.append(('TC', row[field]))
                    tc_fields_added.add('TC')
            else:
                chip_fields.append((field, row[field]))
            
            if len(chip_fields) >= 6:  # Reasonable limit
                break
        
        return chip_fields
    
    def _resolve_tc_field(self, row: Dict[str, str], selected_fields: List[str]) -> Optional[str]:
        """Resolve TC field: TC Start → TC End → omit."""
        # Priority order for TC fields
        tc_candidates = ['TC Start', 'TC End', 'Timecode Start', 'Timecode In']
        
        for field in tc_candidates:
            if field in selected_fields and field in row and row[field]:
                return field
        
        return None
    
    def _create_chips(self, fields: List[Tuple[str, str]], metrics: QFontMetrics) -> List[Dict]:
        """Create chip data structures."""
        chips = []
        for field, value in fields:
            # Abbreviate field names for compact display
            label = self._abbreviate_field(field)
            text = f"{label}: {value}"
            
            text_width = metrics.horizontalAdvance(text)
            chip_width = text_width + 2 * self.chip_padding
            
            chips.append({
                'text': text,
                'width': chip_width,
                'type': 'field',
                'color': self.COLORS['chip_bg']
            })
        
        return chips
    
    def _create_micro_chips(self, hash_verified: bool, match_fallback: bool, 
                           encoding_fallback: bool, encoding_used: str = 'utf-8') -> List[Dict]:
        """Create micro-chips for status indicators."""
        micro_chips = []
        
        if hash_verified:
            micro_chips.append({
                'text': '✓',
                'width': self.micro_chip_size,
                'type': 'micro',
                'color': self.COLORS['verified']
            })
        
        if match_fallback:
            micro_chips.append({
                'text': '⚠',
                'width': self.micro_chip_size,
                'type': 'micro',
                'color': self.COLORS['warning']
            })
        
        # Show E chip only when encoding is NOT UTF-8
        if encoding_used.lower() != 'utf-8':
            micro_chips.append({
                'text': 'E',
                'width': self.micro_chip_size,
                'type': 'micro',
                'color': self.COLORS['info']
            })
        
        return micro_chips
    
    def _layout_chips(self, chips: List[Dict], max_width: int, max_rows: int) -> List[List[Dict]]:
        """Layout chips in rows within width constraints."""
        if not chips:
            return []
        
        rows = []
        current_row = []
        current_width = 0
        
        for chip in chips:
            chip_width = chip['width'] + (self.chip_spacing if current_row else 0)
            
            if current_width + chip_width <= max_width:
                current_row.append(chip)
                current_width += chip_width
            else:
                if current_row:
                    rows.append(current_row)
                    if len(rows) >= max_rows:
                        break
                current_row = [chip]
                current_width = chip['width']
        
        if current_row and len(rows) < max_rows:
            rows.append(current_row)
        
        return rows
    
    def _get_bar_position(self, corner: str, img_width: int, img_height: int,
                         bar_width: int, bar_height: int, margin_w: int, margin_h: int) -> Tuple[int, int]:
        """Calculate bar position based on corner."""
        if 'left' in corner:
            x = margin_w
        else:  # right
            x = img_width - bar_width - margin_w
        
        if 'top' in corner:
            y = margin_h
        else:  # bottom
            y = img_height - bar_height - margin_h
        
        return x, y
    
    def _draw_chips(self, painter: QPainter, rows: List[List[Dict]], start_x: int, start_y: int, show_background: bool = True) -> None:
        """Draw all chip rows."""
        y = start_y
        
        for row in rows:
            x = start_x
            
            for chip in row:
                self._draw_single_chip(painter, chip, x, y, show_background)
                x += chip['width'] + self.chip_spacing
            
            y += self.chip_height + self.chip_spacing
    
    def _draw_single_chip(self, painter: QPainter, chip: Dict, x: int, y: int, show_background: bool = True) -> None:
        """Draw a single chip."""
        width = chip['width']
        height = self.micro_chip_size if chip['type'] == 'micro' else self.chip_height
        
        # Draw rounded rectangle background if enabled
        if show_background:
            painter.setBrush(chip['color'])
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, width, height, self.corner_radius, self.corner_radius)
        
        # Draw text with appropriate color
        if show_background:
            text_color = self._get_contrast_color(chip['color'])
        else:
            text_color = Qt.white  # White text on transparent background
        painter.setPen(text_color)
        
        text_rect = QRect(x, y, width, height)
        painter.drawText(text_rect, Qt.AlignCenter, chip['text'])
    
    def _abbreviate_field(self, field: str) -> str:
        """Abbreviate field names for compact display."""
        abbreviations = {
            'Scene': 'SC',
            'Slate': 'SL', 
            'Take': 'TK',
            'Roll': 'RL',
            'Reel': 'RL',
            'Camera': 'CAM',
            'Timecode In': 'TC',
            'Timecode Start': 'TC',
            'Look': 'LK',
            'LUT': 'LUT'
        }
        return abbreviations.get(field, field[:3].upper())
    
    def _get_contrast_color(self, bg_color: QColor) -> QColor:
        """Calculate contrasting text color."""
        # Simple luminance-based contrast
        r, g, b, a = bg_color.getRgb()
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        return QColor(255, 255, 255) if luminance < 0.5 else QColor(0, 0, 0)