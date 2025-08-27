import hashlib
import threading
from pathlib import Path
from typing import Dict, Tuple, Optional, Callable
from dataclasses import dataclass
import os


@dataclass
class FileInfo:
    """File metadata for cache validation."""
    size: int
    mtime: float
    hash: str


class HashCache:
    """Thread-safe hash cache using size+mtime as key."""
    
    def __init__(self):
        self._cache: Dict[str, FileInfo] = {}
        self._lock = threading.Lock()
    
    def get(self, path: Path) -> Optional[str]:
        """Get cached hash if file hasn't changed."""
        key = str(path)
        stat = path.stat()
        
        with self._lock:
            if key in self._cache:
                cached = self._cache[key]
                if cached.size == stat.st_size and cached.mtime == stat.st_mtime:
                    return cached.hash
            return None
    
    def put(self, path: Path, hash_value: str) -> None:
        """Cache hash with current file metadata."""
        key = str(path)
        stat = path.stat()
        
        with self._lock:
            self._cache[key] = FileInfo(
                size=stat.st_size,
                mtime=stat.st_mtime,
                hash=hash_value
            )
    
    def is_file_changed(self, path: Path) -> bool:
        """Check if file has changed since last hash."""
        key = str(path)
        stat = path.stat()
        
        with self._lock:
            if key in self._cache:
                cached = self._cache[key]
                return cached.size != stat.st_size or cached.mtime != stat.st_mtime
            return True  # Not in cache = changed


# Global cache instance
_hash_cache = HashCache()


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    """Compute SHA-256 hash of a file with streaming."""
    # Check cache first
    cached_hash = _hash_cache.get(path)
    if cached_hash:
        return cached_hash
    
    # Compute hash
    sha256_hash = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    hash_value = sha256_hash.hexdigest()
    _hash_cache.put(path, hash_value)
    return hash_value


def compute_file_hashes(image_path: Path, csv_path: Path) -> dict[str, str]:
    """Compute SHA-256 hashes for both image and CSV files."""
    return {
        'jpeg': sha256_file(image_path),
        'csv': sha256_file(csv_path) if csv_path and csv_path.exists() else ''
    }


def compute_hashes_async(image_path: Path, csv_path: Optional[Path], 
                        callback: Callable[[Dict[str, str]], None]) -> threading.Thread:
    """Compute hashes in background thread."""
    def _compute():
        try:
            hashes = compute_file_hashes(image_path, csv_path)
            callback(hashes)
        except Exception as e:
            callback({'error': str(e)})
    
    thread = threading.Thread(target=_compute, daemon=True)
    thread.start()
    return thread


def validate_files_unchanged(image_path: Path, csv_path: Optional[Path]) -> Tuple[bool, str]:
    """Check if files have changed since last hash computation."""
    if _hash_cache.is_file_changed(image_path):
        return False, f"JPEG file {image_path.name} has been modified"
    
    if csv_path and csv_path.exists() and _hash_cache.is_file_changed(csv_path):
        return False, f"CSV file {csv_path.name} has been modified"
    
    return True, ""


def get_cached_hashes(image_path: Path, csv_path: Optional[Path]) -> Optional[Dict[str, str]]:
    """Get cached hashes if available and files unchanged."""
    jpeg_hash = _hash_cache.get(image_path)
    if jpeg_hash is None:
        return None
    
    csv_hash = ""
    if csv_path and csv_path.exists():
        csv_hash = _hash_cache.get(csv_path)
        if csv_hash is None:
            return None
    
    return {'jpeg': jpeg_hash, 'csv': csv_hash}


def hash_status() -> Dict[str, bool]:
    """Get hash verification status for UI."""
    return {
        'hashes_computed': len(_hash_cache._cache) > 0,
        'cache_size': len(_hash_cache._cache)
    }