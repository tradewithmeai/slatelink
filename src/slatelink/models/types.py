from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, List, Tuple
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class OverlaySpec:
    anchor: Literal['top_left', 'top_right', 'bottom_left', 'bottom_right'] = 'top_left'
    font_pt: int = 16
    padding_px: int = 12
    line_spacing_px: int = 6
    box_opacity: float = 0.8
    show_background: bool = True
    field_order: List[str] = field(default_factory=list)
    overlay_positions: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    def to_json(self) -> str:
        return json.dumps({
            'anchor': self.anchor,
            'font_pt': self.font_pt,
            'padding_px': self.padding_px,
            'line_spacing_px': self.line_spacing_px,
            'box_opacity': self.box_opacity,
            'show_background': self.show_background,
            'field_order': self.field_order,
            'overlay_positions': {k: [round(v[0], 4), round(v[1], 4)] for k, v in self.overlay_positions.items()}
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'OverlaySpec':
        data = json.loads(json_str)
        # Handle position tuples
        if 'overlay_positions' in data:
            data['overlay_positions'] = {k: tuple(v) for k, v in data['overlay_positions'].items()}
        return cls(**data)
    
    def validate_fields(self, csv_headers: List[str]) -> 'OverlaySpec':
        """Validate and clean field_order against current CSV headers."""
        if not self.field_order:
            return self
        
        valid_fields = [f for f in self.field_order if f in csv_headers]
        ignored = set(self.field_order) - set(valid_fields)
        
        if ignored:
            logger.info(f"Ignored unknown fields in order: {ignored}")
        
        # Clean positions for unknown fields
        valid_positions = {k: v for k, v in self.overlay_positions.items() if k in csv_headers}
        ignored_pos = set(self.overlay_positions.keys()) - set(csv_headers)
        
        if ignored_pos:
            logger.info(f"Ignored unknown fields in positions: {ignored_pos}")
        
        return OverlaySpec(
            anchor=self.anchor,
            font_pt=max(12, self.font_pt),  # Enforce minimum font size
            padding_px=self.padding_px,
            line_spacing_px=self.line_spacing_px,
            box_opacity=self.box_opacity,
            show_background=self.show_background,
            field_order=valid_fields,
            overlay_positions=valid_positions
        )
    
    def clamp_positions(self) -> 'OverlaySpec':
        """Clamp positions to 0-1 range with 4 decimal precision."""
        clamped_positions = {}
        for field, (x, y) in self.overlay_positions.items():
            clamped_x = max(0.0, min(1.0, round(x, 4)))
            clamped_y = max(0.0, min(1.0, round(y, 4)))
            
            if x != clamped_x or y != clamped_y:
                logger.warning(f"Position for '{field}' clamped from ({x:.4f}, {y:.4f}) to ({clamped_x:.4f}, {clamped_y:.4f})")
            
            clamped_positions[field] = (clamped_x, clamped_y)
        
        return OverlaySpec(
            anchor=self.anchor,
            font_pt=self.font_pt,
            padding_px=self.padding_px,
            line_spacing_px=self.line_spacing_px,
            box_opacity=self.box_opacity,
            show_background=self.show_background,
            field_order=self.field_order,
            overlay_positions=clamped_positions
        )


@dataclass
class MatchConfig:
    join_key: str = 'filename'
    fallback_keys: list[str] = field(default_factory=lambda: ['basename', 'clip'])
    
    def to_dict(self) -> dict:
        return {
            'join_key': self.join_key,
            'fallback_keys': self.fallback_keys
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MatchConfig':
        return cls(
            join_key=data.get('join_key', 'filename'),
            fallback_keys=data.get('fallback_keys', ['basename', 'clip'])
        )


@dataclass
class Preset:
    name: str
    selected_fields: list[str]
    overlay: OverlaySpec
    match: MatchConfig
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'selected_fields': self.selected_fields,
            'overlay': json.loads(self.overlay.to_json()),
            'match': self.match.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Preset':
        return cls(
            name=data['name'],
            selected_fields=data['selected_fields'],
            overlay=OverlaySpec(**data['overlay']),
            match=MatchConfig.from_dict(data['match'])
        )


@dataclass
class ExportConfig:
    mode: Literal['skip', 'overwrite', 'suffix'] = 'skip'
    suffix_pattern: str = '_{n}'
    
    def get_output_path(self, base_path: str, existing_count: int = 0) -> str:
        if self.mode == 'suffix' and existing_count > 0:
            return base_path.replace('.xmp', self.suffix_pattern.format(n=existing_count) + '.xmp')
        return base_path


@dataclass 
class BatchConfig:
    """Configuration for batch operations."""
    mode: Literal['use_preset', 'respect_per_image', 'apply_current'] = 'use_preset'
    
    def get_description(self) -> str:
        """Get human-readable description of batch mode."""
        descriptions = {
            'use_preset': 'Use preset order/positions',
            'respect_per_image': 'Respect per-image overlayPositions if present',
            'apply_current': "Apply current image's order/positions to all selected images"
        }
        return descriptions[self.mode]


@dataclass
class PrecedenceInfo:
    """Track precedence sources for order and positions."""
    order_source: Literal['per-image', 'preset', 'dataset', 'auto'] = 'auto'
    position_source: Literal['per-image', 'preset', 'auto'] = 'auto'
    tc_source: Literal['Start', 'End', 'none'] = 'none'
    match_type: str = 'unknown'
    match_confidence: Optional[float] = None
    
    def format_status(self) -> str:
        """Format as single status line."""
        match_info = self.match_type
        if self.match_confidence is not None and self.match_confidence < 1.0:
            match_info += f" ({self.match_confidence:.0%})"
        return f"Order: {self.order_source} · Positions: {self.position_source} · TC: {self.tc_source} · Match: {match_info}"