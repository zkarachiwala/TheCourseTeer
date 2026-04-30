import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class SnapshotManager:
    """
    Manages local filesystem caching of scraper results (HTML, JSON).
    Files are stored in scraper/snapshots/<university_id>/<url_hash>.<ext>
    """

    def __init__(self, base_dir: str = "snapshots", ttl_days: int = 7):
        # Resolve absolute path relative to the scraper directory
        scraper_dir = Path(__file__).parent
        self.base_path = scraper_dir / base_dir
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_hash(self, url: str) -> str:
        """Generate a SHA-256 hash for a given URL."""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _get_path(self, university_id: str, url: str, ext: str = "html") -> Path:
        """Construct the filesystem path for a snapshot."""
        uni_path = self.base_path / str(university_id)
        uni_path.mkdir(parents=True, exist_ok=True)
        url_hash = self._get_hash(url)
        return uni_path / f"{url_hash}.{ext}"

    def save(self, university_id: str, url: str, content: str, ext: str = "html") -> Path:
        """Save content to the local snapshot directory."""
        path = self._get_path(university_id, url, ext)
        
        # Save metadata in a companion .meta.json file to avoid collisions
        meta_path = path.parent / f"{path.stem}.meta.json"
        metadata = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "extension": ext
        }
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        return path

    def load(self, university_id: str, url: str, ext: str = "html", force_refresh: bool = False) -> str | None:
        """
        Load content from a local snapshot if it exists and is within TTL.
        Returns None if no valid snapshot is found.
        """
        if force_refresh:
            return None
            
        path = self._get_path(university_id, url, ext)
        if not path.exists():
            return None
            
        # Check TTL
        file_age = time.time() - path.stat().st_mtime
        if file_age > self.ttl_seconds:
            return None
            
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def exists(self, university_id: str, url: str, ext: str = "html") -> bool:
        """Check if a valid snapshot exists for the given URL."""
        path = self._get_path(university_id, url, ext)
        if not path.exists():
            return False
        
        file_age = time.time() - path.stat().st_mtime
        return file_age <= self.ttl_seconds

    def purge_university_cache(self, university_id: str) -> int:
        """
        Delete all snapshots and metadata for a specific university.
        Returns the count of deleted files.
        """
        uni_path = self.base_path / str(university_id)
        if not uni_path.exists():
            return 0
            
        count = 0
        for item in uni_path.iterdir():
            if item.is_file():
                try:
                    item.unlink()
                    count += 1
                except Exception as e:
                    print(f"Failed to delete {item}: {e}")
        
        try:
            uni_path.rmdir()
        except:
            pass # Directory might not be empty if nested or permission issues
            
        return count
