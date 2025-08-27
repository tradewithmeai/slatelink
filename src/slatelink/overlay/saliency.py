"""Saliency-aware corner detection for optimal overlay placement."""

import numpy as np
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from typing import Tuple, Dict


class SaliencyDetector:
    """Detect least busy corner for overlay placement."""
    
    def __init__(self, corner_size_pct: float = 15.0, busyness_threshold: float = 0.6):
        self.corner_size_pct = corner_size_pct
        self.busyness_threshold = busyness_threshold
    
    def find_best_corner(self, pixmap: QPixmap) -> Tuple[str, bool]:
        """
        Find the least busy corner for overlay placement.
        Returns: (corner_name, needs_backdrop)
        """
        # Convert to numpy array for processing
        scaled_pixmap = self._scale_for_analysis(pixmap)
        image_array = self._pixmap_to_array(scaled_pixmap)
        
        if image_array is None:
            return 'top_left', False  # Fallback
        
        # Calculate busyness scores for each corner
        corners = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
        scores = {}
        
        for corner in corners:
            region = self._extract_corner_region(image_array, corner)
            scores[corner] = self._calculate_busyness_score(region)
        
        # Find least busy corner
        best_corner = min(scores.keys(), key=lambda k: scores[k])
        needs_backdrop = scores[best_corner] > self.busyness_threshold
        
        return best_corner, needs_backdrop
    
    def _scale_for_analysis(self, pixmap: QPixmap) -> QPixmap:
        """Scale image to ~256px width for analysis."""
        target_width = 256
        
        if pixmap.width() <= target_width:
            return pixmap
        
        aspect_ratio = pixmap.height() / pixmap.width()
        target_height = int(target_width * aspect_ratio)
        
        return pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    def _pixmap_to_array(self, pixmap: QPixmap) -> np.ndarray:
        """Convert QPixmap to numpy array."""
        try:
            # Convert to QImage
            image = pixmap.toImage()
            if image.isNull():
                return None
            
            # Convert to RGB format
            image = image.convertToFormat(QImage.Format_RGB888)
            
            # Get image data
            width = image.width()
            height = image.height()
            bytes_per_line = image.bytesPerLine()
            
            # Convert to numpy array
            buffer = image.constBits()
            if hasattr(buffer, 'tobytes'):
                # PySide6 newer versions
                img_array = np.frombuffer(buffer.tobytes(), dtype=np.uint8)
            else:
                # Fallback for older versions
                img_array = np.frombuffer(bytes(buffer), dtype=np.uint8)
            
            # Reshape to (height, width, 3)
            img_array = img_array.reshape((height, bytes_per_line // 3, 3))[:, :width, :]
            
            return img_array
            
        except Exception:
            return None
    
    def _extract_corner_region(self, image_array: np.ndarray, corner: str) -> np.ndarray:
        """Extract corner region based on corner_size_pct."""
        height, width = image_array.shape[:2]
        
        corner_w = int(width * self.corner_size_pct / 100)
        corner_h = int(height * self.corner_size_pct / 100)
        
        if corner == 'top_left':
            return image_array[:corner_h, :corner_w]
        elif corner == 'top_right':
            return image_array[:corner_h, -corner_w:]
        elif corner == 'bottom_left':
            return image_array[-corner_h:, :corner_w]
        else:  # bottom_right
            return image_array[-corner_h:, -corner_w:]
    
    def _calculate_busyness_score(self, region: np.ndarray) -> float:
        """Calculate busyness score using luminance variance + edge magnitude."""
        if region.size == 0:
            return 0.0
        
        try:
            # Convert to grayscale (luminance)
            gray = np.dot(region[...,:3], [0.299, 0.587, 0.114])
            
            # Normalize to 0-1
            if gray.max() > gray.min():
                gray = (gray - gray.min()) / (gray.max() - gray.min())
            
            # Calculate luminance variance
            luminance_variance = np.var(gray)
            
            # Calculate edge magnitude using simple Sobel approximation
            edge_score = self._simple_edge_score(gray)
            
            # Combine scores (weight edges more heavily)
            busyness = luminance_variance + 3.0 * edge_score
            
            return min(busyness, 1.0)  # Cap at 1.0
            
        except Exception:
            return 1.0  # Max busyness on error
    
    def _simple_edge_score(self, gray: np.ndarray) -> float:
        """Calculate simple edge score using basic gradients."""
        try:
            if gray.shape[0] < 3 or gray.shape[1] < 3:
                return 0.0
            
            # Simple gradient approximation (3x3 Sobel-like)
            gy, gx = np.gradient(gray)
            
            # Edge magnitude
            edge_magnitude = np.sqrt(gx**2 + gy**2)
            
            # Return normalized mean edge magnitude
            return np.mean(edge_magnitude)
            
        except Exception:
            return 0.0