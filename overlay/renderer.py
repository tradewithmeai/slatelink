from PySide6.QtGui import QPainter, QPixmap, QFont, QColor, QFontMetrics
from PySide6.QtCore import Qt, QRect
from typing import List, Dict
from config.app_config import app_config
from .slate_bar import SlateBar
from .saliency import SaliencyDetector


class OverlayRenderer:
    """Enhanced overlay renderer with SlateBar support."""
    
    def __init__(self):
        self.slate_bar = SlateBar()
        self.saliency_detector = SaliencyDetector()
    def render_overlay(self, pixmap: QPixmap, texts: List[str], 
                      anchor: str = 'top_left', font_pt: int = 16,
                      padding_px: int = 12, line_spacing_px: int = 6,
                      box_opacity: float = 0.8, show_background: bool = True) -> QPixmap:
        """Render text overlay on a copy of the pixmap."""
        
        # Work on a copy
        result = QPixmap(pixmap)
        
        if not texts:
            return result
        
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set font
        font = QFont('Arial', font_pt)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        
        # Calculate text dimensions
        max_width = 0
        total_height = 0
        for i, text in enumerate(texts):
            text_width = metrics.horizontalAdvance(text)
            max_width = max(max_width, text_width)
            total_height += metrics.height()
            if i < len(texts) - 1:
                total_height += line_spacing_px
        
        # Add padding
        box_width = max_width + (padding_px * 2)
        box_height = total_height + (padding_px * 2)
        
        # Calculate position based on anchor
        img_width = result.width()
        img_height = result.height()
        
        if 'left' in anchor:
            x = padding_px
        else:  # right
            x = img_width - box_width - padding_px
        
        if 'top' in anchor:
            y = padding_px
        else:  # bottom
            y = img_height - box_height - padding_px
        
        # Draw background box if enabled
        if show_background:
            bg_color = QColor(0, 0, 0, int(255 * box_opacity))
            painter.fillRect(x, y, box_width, box_height, bg_color)
        
        # Draw text
        painter.setPen(Qt.white)
        text_y = y + padding_px + metrics.ascent()
        
        for i, text in enumerate(texts):
            painter.drawText(x + padding_px, text_y, text)
            text_y += metrics.height()
            if i < len(texts) - 1:
                text_y += line_spacing_px
        
        painter.end()
        return result
    
    
    def get_overlay_values(self, row: dict, selected_fields: List[str]) -> List[str]:
        """Extract values for selected fields from row."""
        values = []
        for field in selected_fields:
            if field in row:
                value = row[field]
                if value:  # Skip empty values
                    values.append(f"{field}: {value}")
        return values
    
    def render_slate_bar(self, pixmap: QPixmap, row: Dict[str, str], 
                        selected_fields: List[str], font_pt: int = 12,
                        safe_margin_pct: int = 5, max_rows: int = 2,
                        hash_verified: bool = False, match_fallback: bool = False,
                        encoding_fallback: bool = False, corner: str = None,
                        pinned_fields: List[str] = None, encoding_used: str = 'utf-8',
                        show_background: bool = True) -> QPixmap:
        """Render SlateBar overlay with optional saliency-aware placement."""
        
        if not app_config.slate_bar:
            return pixmap
        
        # Determine corner placement
        if corner is None:
            if app_config.saliency_placement:
                corner, needs_backdrop = self.saliency_detector.find_best_corner(pixmap)
                # Could use needs_backdrop to adjust opacity, but keeping simple for MVP
            else:
                corner = 'top_left'
        
        return self.slate_bar.render_slate_bar(
            pixmap=pixmap,
            row=row,
            selected_fields=selected_fields,
            corner=corner,
            font_pt=font_pt,
            safe_margin_pct=safe_margin_pct,
            max_rows=max_rows,
            hash_verified=hash_verified,
            match_fallback=match_fallback,
            encoding_fallback=encoding_fallback,
            pinned_fields=pinned_fields,
            encoding_used=encoding_used,
            show_background=show_background
        )