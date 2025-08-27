"""Application configuration and feature flags."""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class AppConfig:
    """Main application configuration."""

    # Silverstack mode settings
    silverstack_only: bool = True
    silverstack_join_priority: List[str] = None
    silverstack_suggested_fields: List[str] = None

    # Feature flags
    slate_bar: bool = True
    saliency_placement: bool = True
    field_reorder: bool = True          # enable drag-to-reorder list
    free_placement: bool = True         # enable per-field on-image placement (L toggle)

    # UI / overlay settings
    safe_margin_pct: int = 5            # safe-area inset as percent of min(image W,H)
    max_rows: int = 2                   # max SlateBar rows when wrapping
    snap_pct: float = 1.0               # grid step for layout mode (percent of min(image W,H))

    def __post_init__(self):
        if self.silverstack_join_priority is None:
            # Dataset-aware: prioritize "Name" for film metadata, then common alternates
            self.silverstack_join_priority = [
                "Name", "Filename", "File", "Clip Name", "Clip", "Basename"
            ]

        if self.silverstack_suggested_fields is None:
            # Dataset-aware: fields present in exampleFilmMetadata.csv + common extras
            self.silverstack_suggested_fields = [
                "Scene", "Take", "Camera", "TC Start", "Bin Name", "Episode",
                "Slate", "Roll", "Reel", "Timecode In", "Timecode Start", "Look", "LUT"
            ]

    # Compatibility aliases (some modules may reference camelCase flags)
    @property
    def slateBar(self) -> bool:
        return self.slate_bar

    @property
    def saliencyPlacement(self) -> bool:
        return self.saliency_placement

    @property
    def freePlacement(self) -> bool:
        return self.free_placement

    def get_dataset_defaults(self, csv_headers: List[str]) -> Dict[str, Any]:
        """Return dataset-specific defaults based on available CSV headers."""
        # Initial field selection for this dataset (filter to headers actually present)
        initial_selection = ["Scene", "Take", "Camera", "TC Start", "Bin Name", "Episode"]
        available_selection = [f for f in initial_selection if f in csv_headers]

        # Field order (same as selection for this dataset)
        field_order = available_selection.copy()

        return {
            "selected_fields": available_selection,
            "field_order": field_order,
            "join_key": self.get_preferred_join_key(csv_headers),
            "safe_margin_pct": self.safe_margin_pct,
            "snap_pct": self.snap_pct,
            "max_rows": self.max_rows,
        }

    def get_preferred_join_key(self, csv_headers: List[str]) -> str:
        """Pick the preferred join key based on priority list and available headers."""
        for candidate in self.silverstack_join_priority:
            if candidate in csv_headers:
                return candidate
        # Fallback: first header if available, else a conservative default
        return csv_headers[0] if csv_headers else "filename"


# Global app config instance
app_config = AppConfig()
