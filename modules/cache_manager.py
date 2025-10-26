"""
SQLite-based Cache Manager for LLM Responses
Provides persistent caching with staleness detection based on time and file modifications.

Created by The Collective Borg.tools
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    SQLite-based cache manager for LLM responses with automatic staleness detection.

    Features:
    - Persistent storage of LLM responses
    - Time-based cache expiration (configurable, default 7 days)
    - File modification tracking (mtime-based invalidation)
    - Automatic schema migration
    - Thread-safe SQLite operations
    """

    DEFAULT_MAX_AGE_DAYS = 7

    def __init__(self, db_path: str = 'cache.db'):
        """
        Initialize cache manager with SQLite database.

        Args:
            db_path: Path to SQLite database file (default: cache.db)
        """
        self.db_path = Path(db_path).absolute()
        self.conn = None
        self._init_connection()
        self._init_schema()
        logger.info(f"💾 Cache manager initialized with database: {self.db_path}")

    def _init_connection(self):
        """Initialize SQLite connection with proper settings."""
        try:
            self.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=10.0
            )
            # Enable WAL mode for better concurrent access
            self.conn.execute("PRAGMA journal_mode=WAL")
            # Use Row factory for dict-like access
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_path TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    files_mtime TEXT NOT NULL,
                    cache_key TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(project_path, model_name)
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_model
                ON cache(project_path, model_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON cache(timestamp)
            """)

            self.conn.commit()
            logger.info("💾 SQLite schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    def _get_project_files_mtime(self, project_path: str) -> Dict[str, float]:
        """
        Get modification times for all relevant files in project.

        Args:
            project_path: Path to project directory

        Returns:
            Dictionary mapping file paths to their mtime values
        """
        project_dir = Path(project_path)
        files_mtime = {}

        if not project_dir.exists() or not project_dir.is_dir():
            logger.warning(f"Project path does not exist: {project_path}")
            return files_mtime

        # Get all relevant source files (excluding common ignore patterns)
        ignore_patterns = {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', '.mypy_cache', 'dist', 'build', '*.pyc',
            '.DS_Store', 'cache.db', 'cache.db-wal', 'cache.db-shm'
        }

        try:
            for file_path in project_dir.rglob('*'):
                # Skip ignored patterns
                if any(pattern in file_path.parts for pattern in ignore_patterns):
                    continue
                if any(file_path.match(pattern) for pattern in ignore_patterns):
                    continue

                # Only track files, not directories
                if file_path.is_file():
                    try:
                        relative_path = str(file_path.relative_to(project_dir))
                        files_mtime[relative_path] = file_path.stat().st_mtime
                    except Exception as e:
                        logger.warning(f"Could not get mtime for {file_path}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error scanning project directory: {e}")

        return files_mtime

    def _generate_cache_key(self, project_path: str, model_name: str) -> str:
        """
        Generate unique cache key for project and model combination.

        Args:
            project_path: Path to project
            model_name: Name of LLM model

        Returns:
            SHA256 hash of project_path + model_name
        """
        key_string = f"{project_path}:{model_name}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get_cached(self, project_path: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response if available and not stale.

        Args:
            project_path: Path to project directory
            model_name: Name of LLM model used

        Returns:
            Cached response dictionary or None if cache miss/stale
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT response_json, timestamp, files_mtime, created_at
                FROM cache
                WHERE project_path = ? AND model_name = ?
            """, (project_path, model_name))

            row = cursor.fetchone()

            if not row:
                logger.info(f"🔍 Cache miss for {project_path} with model {model_name}")
                return None

            # Parse cache entry
            cache_entry = {
                'response': json.loads(row['response_json']),
                'timestamp': row['timestamp'],
                'files_mtime': json.loads(row['files_mtime']),
                'created_at': row['created_at']
            }

            # Check if cache is stale
            if self.is_stale(cache_entry, project_path):
                logger.info(f"⏰ Cache stale for {project_path}, invalidating...")
                self._invalidate_cache(project_path, model_name)
                return None

            logger.info(f"✅ Cache hit for {project_path} with model {model_name}")
            return cache_entry['response']

        except Exception as e:
            logger.error(f"Error retrieving cached response: {e}")
            return None

    def set_cache(
        self,
        project_path: str,
        model_name: str,
        response: Dict[str, Any]
    ) -> bool:
        """
        Store LLM response in cache with file modification tracking.

        Args:
            project_path: Path to project directory
            model_name: Name of LLM model used
            response: LLM response dictionary to cache

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            # Get current file mtimes
            files_mtime = self._get_project_files_mtime(project_path)

            # Generate cache key
            cache_key = self._generate_cache_key(project_path, model_name)

            # Prepare data
            timestamp = int(time.time())
            created_at = datetime.now().isoformat()

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cache
                (project_path, model_name, response_json, timestamp, files_mtime, cache_key, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                project_path,
                model_name,
                json.dumps(response),
                timestamp,
                json.dumps(files_mtime),
                cache_key,
                created_at
            ))

            self.conn.commit()
            logger.info(f"💾 Cached response for {project_path} with model {model_name}")
            return True

        except Exception as e:
            logger.error(f"Error caching response: {e}")
            self.conn.rollback()
            return False

    def is_stale(
        self,
        cache_entry: Dict[str, Any],
        project_path: str = None,
        max_age_days: int = DEFAULT_MAX_AGE_DAYS
    ) -> bool:
        """
        Check if cache entry is stale based on age and file modifications.

        Args:
            cache_entry: Cache entry dictionary with timestamp and files_mtime
            project_path: Path to project (required for file checking)
            max_age_days: Maximum age in days before considering stale (default: 7)

        Returns:
            True if cache is stale, False otherwise
        """
        try:
            # Check time-based staleness
            cache_timestamp = cache_entry.get('timestamp', 0)
            current_timestamp = int(time.time())
            max_age_seconds = max_age_days * 24 * 60 * 60

            if (current_timestamp - cache_timestamp) > max_age_seconds:
                logger.info(f"⏰ Cache expired (age > {max_age_days} days)")
                return True

            # Check file modification staleness
            if project_path:
                cached_mtimes = cache_entry.get('files_mtime', {})
                current_mtimes = self._get_project_files_mtime(project_path)

                # Check if files were added or removed
                if set(cached_mtimes.keys()) != set(current_mtimes.keys()):
                    logger.info("📝 Cache invalid: files added or removed")
                    return True

                # Check if any file was modified
                for file_path, cached_mtime in cached_mtimes.items():
                    current_mtime = current_mtimes.get(file_path)
                    if current_mtime is None or current_mtime > cached_mtime:
                        logger.info(f"📝 Cache invalid: {file_path} was modified")
                        return True

            return False

        except Exception as e:
            logger.error(f"Error checking cache staleness: {e}")
            # On error, consider cache stale to be safe
            return True

    def _invalidate_cache(self, project_path: str, model_name: str) -> bool:
        """
        Invalidate (delete) cache entry for specific project and model.

        Args:
            project_path: Path to project
            model_name: Name of LLM model

        Returns:
            True if successfully invalidated, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM cache
                WHERE project_path = ? AND model_name = ?
            """, (project_path, model_name))

            self.conn.commit()
            logger.info(f"🗑️ Invalidated cache for {project_path} with model {model_name}")
            return True

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            self.conn.rollback()
            return False

    def clear_all(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM cache")
            self.conn.commit()
            logger.info("🗑️ Cleared all cache entries")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            self.conn.rollback()
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics (total entries, size, oldest/newest)
        """
        try:
            cursor = self.conn.cursor()

            # Get total entries
            cursor.execute("SELECT COUNT(*) as count FROM cache")
            total_entries = cursor.fetchone()['count']

            # Get oldest and newest entries
            cursor.execute("""
                SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest
                FROM cache
            """)
            row = cursor.fetchone()
            oldest = row['oldest']
            newest = row['newest']

            # Get database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                'total_entries': total_entries,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'oldest_entry': datetime.fromtimestamp(oldest).isoformat() if oldest else None,
                'newest_entry': datetime.fromtimestamp(newest).isoformat() if newest else None,
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def get_cache_manager(db_path: str = 'cache.db') -> CacheManager:
    """
    Factory function to get a CacheManager instance.

    Args:
        db_path: Path to SQLite database file

    Returns:
        CacheManager instance
    """
    return CacheManager(db_path)
