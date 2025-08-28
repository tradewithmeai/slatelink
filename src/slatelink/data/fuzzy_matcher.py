"""
Fuzzy matching system for production file names.
Handles complex naming patterns like 'Slate57-Take1-MissionImpossible'
and matches against CSV entries with abbreviations or partial names.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from ..debug.logger import debug_logger


class FuzzyMatcher:
    """Enhanced matcher with fuzzy string matching for production workflows."""
    
    def __init__(self, min_confidence: float = 0.6):
        """
        Initialize fuzzy matcher.
        
        Args:
            min_confidence: Minimum confidence score (0-1) for fuzzy matches
        """
        self.min_confidence = min_confidence
        self.last_match_confidence = 0.0
        self.last_match_details = {}
    
    def extract_production_name(self, filename: str) -> Dict[str, str]:
        """
        Extract production-related components from filename.
        
        Examples:
            'Slate57-Take1-MissionImpossible.jpg' -> {
                'slate': '57',
                'take': '1', 
                'production': 'MissionImpossible',
                'full': 'Slate57-Take1-MissionImpossible'
            }
        """
        debug_logger.debug(f"Extracting production name from: {filename}")
        
        # Remove extension
        name = Path(filename).stem
        
        # Common patterns in production file naming
        patterns = {
            # Slate-Take-Production pattern
            r'[Ss]late(\d+)[-_][Tt]ake(\d+)[-_](.+)': ('slate', 'take', 'production'),
            # Scene-Take-Production pattern  
            r'[Ss]cene(\d+)[-_][Tt]ake(\d+)[-_](.+)': ('scene', 'take', 'production'),
            # Production-Slate-Take pattern
            r'(.+?)[-_][Ss]late(\d+)[-_][Tt]ake(\d+)': ('production', 'slate', 'take'),
            # Simple Production-Number pattern
            r'(.+?)[-_](\d+)': ('production', 'number'),
        }
        
        result = {'full': name}
        
        for pattern, groups in patterns.items():
            match = re.match(pattern, name)
            if match:
                for i, group_name in enumerate(groups, 1):
                    if i <= len(match.groups()):
                        result[group_name] = match.group(i)
                break
        
        # If no pattern matches, try to extract the last component
        if 'production' not in result:
            # Split by common delimiters
            parts = re.split(r'[-_]', name)
            # Look for the longest part that's not just numbers
            for part in reversed(parts):
                if part and not part.isdigit():
                    result['production'] = part
                    break
        
        # Fallback to full name
        if 'production' not in result:
            result['production'] = name
        
        debug_logger.debug(f"Extracted components: {result}")
        return result
    
    def normalize_string(self, s: str) -> str:
        """
        Normalize string for comparison.
        - Remove spaces and special characters
        - Convert to lowercase
        - Handle common abbreviations
        """
        # Remove non-alphanumeric characters
        s = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
        return s
    
    def expand_abbreviations(self, text: str) -> List[str]:
        """
        Generate possible expansions of abbreviations.
        
        Example: 'MI' -> ['mi', 'missionimpossible', 'mission impossible']
        """
        variations = [text.lower()]
        
        # Common production abbreviations
        abbreviation_map = {
            'mi': ['missionimpossible', 'mission impossible'],
            'jp': ['jurassicpark', 'jurassic park'],
            'sw': ['starwars', 'star wars'],
            'lotr': ['lordoftherings', 'lord of the rings'],
            'got': ['gameofthrones', 'game of thrones'],
        }
        
        normalized = self.normalize_string(text)
        if normalized in abbreviation_map:
            variations.extend(abbreviation_map[normalized])
        
        # Check if text might be initials (all caps or 2-3 letters)
        if len(text) <= 3 and text.isupper():
            # Could be initials, but we need context to expand
            variations.append(text.lower())
        
        return variations
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings.
        
        Returns:
            Similarity score between 0 and 1
        """
        # Normalize strings
        s1 = self.normalize_string(str1)
        s2 = self.normalize_string(str2)
        
        # Exact match after normalization
        if s1 == s2:
            return 1.0
        
        # Check abbreviations
        expansions1 = self.expand_abbreviations(str1)
        expansions2 = self.expand_abbreviations(str2)
        
        for e1 in expansions1:
            for e2 in expansions2:
                if self.normalize_string(e1) == self.normalize_string(e2):
                    return 0.95  # Slightly lower confidence for abbreviation match
        
        # Use SequenceMatcher for fuzzy matching
        matcher = SequenceMatcher(None, s1, s2)
        base_score = matcher.ratio()
        
        # Boost score if one string contains the other
        if s1 in s2 or s2 in s1:
            base_score = max(base_score, 0.8)
        
        # Check if strings start with same characters (common in production names)
        common_prefix_len = len(re.match(r'^([a-z0-9]*)', s1).group(1))
        if common_prefix_len >= 3:
            prefix_boost = common_prefix_len / max(len(s1), len(s2))
            base_score = max(base_score, prefix_boost * 0.7)
        
        return base_score
    
    def match_row_fuzzy(self, image_path: Path, rows: List[Dict[str, str]], 
                       join_key: str, fallback_keys: List[str] = None) -> List[Tuple[int, float]]:
        """
        Find matching rows using fuzzy matching.
        
        Returns:
            List of (row_index, confidence_score) tuples, sorted by confidence
        """
        if not rows:
            return []
        
        fallback_keys = fallback_keys or ['Name', 'Filename', 'File', 'Clip Name', 'Production']
        filename_components = self.extract_production_name(image_path.name)
        
        matches = []
        
        # Try primary join key first
        if join_key in rows[0]:
            matches.extend(self._fuzzy_match_column(
                rows, join_key, filename_components
            ))
        
        # Try fallback keys if no good matches
        if not matches or all(score < self.min_confidence for _, score in matches):
            for key in fallback_keys:
                if key != join_key and key in rows[0]:
                    fallback_matches = self._fuzzy_match_column(
                        rows, key, filename_components
                    )
                    matches.extend(fallback_matches)
        
        # Sort by confidence score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by minimum confidence
        matches = [(idx, score) for idx, score in matches if score >= self.min_confidence]
        
        # Store match details
        if matches:
            self.last_match_confidence = matches[0][1]
            self.last_match_details = {
                'filename': image_path.name,
                'extracted': filename_components,
                'best_match_score': matches[0][1],
                'total_candidates': len(matches)
            }
            debug_logger.info(f"Fuzzy match found: confidence={matches[0][1]:.2f}, details={self.last_match_details}")
        
        return matches
    
    def _fuzzy_match_column(self, rows: List[Dict[str, str]], column: str, 
                           filename_components: Dict[str, str]) -> List[Tuple[int, float]]:
        """
        Perform fuzzy matching against a specific column.
        
        Returns:
            List of (row_index, confidence_score) tuples
        """
        matches = []
        
        for i, row in enumerate(rows):
            if column not in row:
                continue
            
            cell_value = row[column]
            if not cell_value:
                continue
            
            # Try matching against different components
            scores = []
            
            # Match against production name if available
            if 'production' in filename_components:
                score = self.calculate_similarity(
                    filename_components['production'], 
                    cell_value
                )
                scores.append(score)
            
            # Match against full filename
            score = self.calculate_similarity(
                filename_components['full'],
                cell_value
            )
            scores.append(score)
            
            # Take the best score
            best_score = max(scores) if scores else 0.0
            
            if best_score >= self.min_confidence:
                matches.append((i, best_score))
                debug_logger.debug(f"Row {i}, Column '{column}': '{cell_value}' -> score={best_score:.2f}")
        
        return matches
    
    def get_match_explanation(self) -> str:
        """Get human-readable explanation of the last match."""
        if not self.last_match_details:
            return "No match attempted"
        
        details = self.last_match_details
        confidence_pct = self.last_match_confidence * 100
        
        explanation = f"Match confidence: {confidence_pct:.1f}%\n"
        explanation += f"Filename: {details.get('filename', 'Unknown')}\n"
        
        if 'extracted' in details:
            extracted = details['extracted']
            if 'production' in extracted:
                explanation += f"Production name detected: {extracted['production']}\n"
            if 'slate' in extracted:
                explanation += f"Slate: {extracted['slate']}\n"
            if 'take' in extracted:
                explanation += f"Take: {extracted['take']}\n"
        
        return explanation