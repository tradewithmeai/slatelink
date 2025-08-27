import json
from pathlib import Path
from typing import List, Optional
from ..models.types import Preset, OverlaySpec, MatchConfig


class PresetManager:
    def __init__(self):
        self.preset_dir = Path.home() / '.slatelink' / 'presets'
        self.preset_dir.mkdir(parents=True, exist_ok=True)
        self.presets: dict[str, Preset] = {}
        self.load_all_presets()
    
    def load_all_presets(self) -> None:
        """Load all presets from disk."""
        for preset_file in self.preset_dir.glob('*.json'):
            try:
                with open(preset_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    preset = Preset.from_dict(data)
                    self.presets[preset.name] = preset
            except Exception as e:
                print(f"Error loading preset {preset_file}: {e}")
    
    def save_preset(self, preset: Preset) -> None:
        """Save a preset to disk."""
        self.presets[preset.name] = preset
        preset_file = self.preset_dir / f"{preset.name}.json"
        
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(preset.to_dict(), f, indent=2)
    
    def delete_preset(self, name: str) -> None:
        """Delete a preset."""
        if name in self.presets:
            del self.presets[name]
            preset_file = self.preset_dir / f"{name}.json"
            if preset_file.exists():
                preset_file.unlink()
    
    def get_preset(self, name: str) -> Optional[Preset]:
        """Get a preset by name."""
        return self.presets.get(name)
    
    def get_preset_names(self) -> List[str]:
        """Get list of all preset names."""
        return list(self.presets.keys())
    
    def create_default_preset(self, name: str, selected_fields: List[str]) -> Preset:
        """Create a preset with default settings."""
        return Preset(
            name=name,
            selected_fields=selected_fields,
            overlay=OverlaySpec(),
            match=MatchConfig()
        )