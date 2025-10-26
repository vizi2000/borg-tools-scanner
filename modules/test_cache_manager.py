"""
Comprehensive test suite for CacheManager module.

Tests:
- Cache hit/miss scenarios
- Staleness detection (time-based and file-based)
- Concurrent access (SQLite locking)
- Cache invalidation
- Error handling

Created by The Collective Borg.tools
"""

import unittest
import tempfile
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import logging

from cache_manager import CacheManager

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


class TestCacheManager(unittest.TestCase):
    """Test suite for CacheManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_cache.db"
        self.cache = CacheManager(str(self.db_path))

        # Create temporary project directory
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project_dir.mkdir()

        # Create some test files
        (self.project_dir / "file1.py").write_text("# Test file 1")
        (self.project_dir / "file2.py").write_text("# Test file 2")

    def tearDown(self):
        """Clean up test fixtures."""
        self.cache.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_initialization(self):
        """Test that cache initializes correctly."""
        self.assertTrue(self.db_path.exists())
        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 0)

    def test_cache_miss(self):
        """Test cache miss scenario."""
        result = self.cache.get_cached(
            str(self.project_dir),
            "test-model"
        )
        self.assertIsNone(result)

    def test_cache_hit(self):
        """Test cache hit scenario."""
        test_response = {
            'analysis': 'Test analysis',
            'score': 95,
            'findings': ['finding1', 'finding2']
        }

        # Set cache
        success = self.cache.set_cache(
            str(self.project_dir),
            "test-model",
            test_response
        )
        self.assertTrue(success)

        # Get cached response
        cached = self.cache.get_cached(
            str(self.project_dir),
            "test-model"
        )
        self.assertIsNotNone(cached)
        self.assertEqual(cached['analysis'], 'Test analysis')
        self.assertEqual(cached['score'], 95)
        self.assertEqual(len(cached['findings']), 2)

    def test_cache_update(self):
        """Test updating cached response."""
        response1 = {'version': 1}
        response2 = {'version': 2}

        # Set initial cache
        self.cache.set_cache(str(self.project_dir), "test-model", response1)

        # Update cache
        self.cache.set_cache(str(self.project_dir), "test-model", response2)

        # Verify updated response
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertEqual(cached['version'], 2)

        # Verify only one entry exists
        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 1)

    def test_staleness_time_based(self):
        """Test time-based staleness detection."""
        test_response = {'data': 'test'}

        # Set cache
        self.cache.set_cache(str(self.project_dir), "test-model", test_response)

        # Get cache entry directly from database to manipulate timestamp
        cursor = self.cache.conn.cursor()
        cursor.execute("""
            SELECT response_json, timestamp, files_mtime, created_at
            FROM cache WHERE project_path = ?
        """, (str(self.project_dir),))
        row = cursor.fetchone()

        # Create cache entry with old timestamp (8 days ago)
        old_timestamp = int(time.time()) - (8 * 24 * 60 * 60)
        cache_entry = {
            'response': json.loads(row['response_json']),
            'timestamp': old_timestamp,
            'files_mtime': json.loads(row['files_mtime']),
            'created_at': row['created_at']
        }

        # Check staleness (should be stale)
        is_stale = self.cache.is_stale(cache_entry, str(self.project_dir), max_age_days=7)
        self.assertTrue(is_stale)

        # Check with longer max_age (should not be stale)
        is_stale = self.cache.is_stale(cache_entry, str(self.project_dir), max_age_days=10)
        self.assertFalse(is_stale)

    def test_staleness_file_modification(self):
        """Test file modification-based staleness detection."""
        test_response = {'data': 'test'}

        # Set cache
        self.cache.set_cache(str(self.project_dir), "test-model", test_response)

        # Verify cache hit before modification
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNotNone(cached)

        # Wait a moment to ensure different mtime
        time.sleep(0.1)

        # Modify a file
        (self.project_dir / "file1.py").write_text("# Modified content")

        # Cache should now be stale
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNone(cached)

    def test_staleness_file_added(self):
        """Test staleness when new file is added."""
        test_response = {'data': 'test'}

        # Set cache
        self.cache.set_cache(str(self.project_dir), "test-model", test_response)

        # Verify cache hit
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNotNone(cached)

        # Add new file
        (self.project_dir / "file3.py").write_text("# New file")

        # Cache should be stale
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNone(cached)

    def test_staleness_file_removed(self):
        """Test staleness when file is removed."""
        test_response = {'data': 'test'}

        # Set cache
        self.cache.set_cache(str(self.project_dir), "test-model", test_response)

        # Verify cache hit
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNotNone(cached)

        # Remove file
        (self.project_dir / "file2.py").unlink()

        # Cache should be stale
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNone(cached)

    def test_multiple_projects(self):
        """Test caching for multiple projects."""
        # Create second project
        project2_dir = Path(self.temp_dir) / "project2"
        project2_dir.mkdir()
        (project2_dir / "file.py").write_text("# Project 2")

        response1 = {'project': 1}
        response2 = {'project': 2}

        # Cache both projects
        self.cache.set_cache(str(self.project_dir), "test-model", response1)
        self.cache.set_cache(str(project2_dir), "test-model", response2)

        # Verify both are cached separately
        cached1 = self.cache.get_cached(str(self.project_dir), "test-model")
        cached2 = self.cache.get_cached(str(project2_dir), "test-model")

        self.assertEqual(cached1['project'], 1)
        self.assertEqual(cached2['project'], 2)

        # Verify stats
        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 2)

    def test_multiple_models(self):
        """Test caching for multiple models on same project."""
        response_gpt = {'model': 'gpt-4'}
        response_claude = {'model': 'claude-3'}

        # Cache with different models
        self.cache.set_cache(str(self.project_dir), "gpt-4", response_gpt)
        self.cache.set_cache(str(self.project_dir), "claude-3", response_claude)

        # Verify both are cached separately
        cached_gpt = self.cache.get_cached(str(self.project_dir), "gpt-4")
        cached_claude = self.cache.get_cached(str(self.project_dir), "claude-3")

        self.assertEqual(cached_gpt['model'], 'gpt-4')
        self.assertEqual(cached_claude['model'], 'claude-3')

    def test_invalidation(self):
        """Test manual cache invalidation."""
        test_response = {'data': 'test'}

        # Set cache
        self.cache.set_cache(str(self.project_dir), "test-model", test_response)

        # Verify cached
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNotNone(cached)

        # Invalidate
        success = self.cache._invalidate_cache(str(self.project_dir), "test-model")
        self.assertTrue(success)

        # Verify cache miss
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNone(cached)

    def test_clear_all(self):
        """Test clearing all cache entries."""
        # Create multiple cache entries
        self.cache.set_cache(str(self.project_dir), "model1", {'data': 1})
        self.cache.set_cache(str(self.project_dir), "model2", {'data': 2})

        # Verify entries exist
        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 2)

        # Clear all
        success = self.cache.clear_all()
        self.assertTrue(success)

        # Verify all cleared
        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 0)

    def test_get_stats(self):
        """Test cache statistics."""
        # Empty cache
        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 0)
        self.assertIsNone(stats['oldest_entry'])
        self.assertIsNone(stats['newest_entry'])

        # Add entry
        self.cache.set_cache(str(self.project_dir), "test-model", {'data': 'test'})

        # Check stats
        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 1)
        self.assertIsNotNone(stats['oldest_entry'])
        self.assertIsNotNone(stats['newest_entry'])
        self.assertGreater(stats['database_size_bytes'], 0)

    def test_context_manager(self):
        """Test using CacheManager as context manager."""
        with CacheManager(str(self.db_path)) as cache:
            cache.set_cache(str(self.project_dir), "test-model", {'data': 'test'})
            cached = cache.get_cached(str(self.project_dir), "test-model")
            self.assertIsNotNone(cached)

    def test_concurrent_access(self):
        """Test concurrent access to cache (SQLite locking)."""
        # Create second cache instance
        cache2 = CacheManager(str(self.db_path))

        try:
            # Write from first instance
            self.cache.set_cache(str(self.project_dir), "model1", {'instance': 1})

            # Write from second instance
            cache2.set_cache(str(self.project_dir), "model2", {'instance': 2})

            # Read from both
            cached1 = self.cache.get_cached(str(self.project_dir), "model1")
            cached2 = cache2.get_cached(str(self.project_dir), "model2")

            self.assertEqual(cached1['instance'], 1)
            self.assertEqual(cached2['instance'], 2)

        finally:
            cache2.close()

    def test_nonexistent_project(self):
        """Test handling of nonexistent project path."""
        fake_path = "/nonexistent/project/path"
        test_response = {'data': 'test'}

        # Should handle gracefully
        success = self.cache.set_cache(fake_path, "test-model", test_response)
        self.assertTrue(success)

        # Should cache even though project doesn't exist
        cached = self.cache.get_cached(fake_path, "test-model")
        self.assertIsNotNone(cached)

    def test_ignored_files(self):
        """Test that ignored files/directories don't affect cache."""
        # Create ignored directories
        (self.project_dir / "__pycache__").mkdir()
        (self.project_dir / "__pycache__" / "test.pyc").write_text("bytecode")
        (self.project_dir / ".git").mkdir()
        (self.project_dir / ".git" / "config").write_text("git config")

        test_response = {'data': 'test'}

        # Set cache
        self.cache.set_cache(str(self.project_dir), "test-model", test_response)

        # Modify ignored file
        (self.project_dir / "__pycache__" / "test.pyc").write_text("modified bytecode")

        # Cache should still be valid (ignored files don't count)
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNotNone(cached)

    def test_large_response(self):
        """Test caching large responses."""
        # Create large response
        large_response = {
            'files': [f'file_{i}.py' for i in range(1000)],
            'analysis': 'x' * 10000,  # 10KB string
            'metrics': {f'metric_{i}': i * 1.5 for i in range(100)}
        }

        # Cache it
        success = self.cache.set_cache(str(self.project_dir), "test-model", large_response)
        self.assertTrue(success)

        # Retrieve it
        cached = self.cache.get_cached(str(self.project_dir), "test-model")
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached['files']), 1000)
        self.assertEqual(len(cached['analysis']), 10000)

    def test_cache_key_uniqueness(self):
        """Test that cache keys are unique for different projects/models."""
        key1 = self.cache._generate_cache_key("/project1", "model1")
        key2 = self.cache._generate_cache_key("/project2", "model1")
        key3 = self.cache._generate_cache_key("/project1", "model2")
        key4 = self.cache._generate_cache_key("/project1", "model1")

        # Different projects or models should have different keys
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key1, key3)

        # Same project and model should have same key
        self.assertEqual(key1, key4)


def run_performance_test():
    """
    Performance test to verify cache hit rate on re-scan.
    Target: 90% cache hit rate on re-scan (per spec).
    """
    print("\n" + "="*60)
    print("PERFORMANCE TEST: Cache Hit Rate")
    print("="*60)

    temp_dir = tempfile.mkdtemp()
    try:
        db_path = Path(temp_dir) / "perf_cache.db"
        cache = CacheManager(str(db_path))

        # Create test project
        project_dir = Path(temp_dir) / "perf_project"
        project_dir.mkdir()

        # Create 50 test files
        for i in range(50):
            (project_dir / f"file_{i}.py").write_text(f"# File {i}")

        test_response = {
            'analysis': 'Performance test analysis',
            'files_analyzed': 50
        }

        # First scan - cache miss
        print(f"\n📊 First scan (expect cache miss)...")
        start = time.time()
        cached = cache.get_cached(str(project_dir), "test-model")
        assert cached is None, "Expected cache miss on first scan"

        cache.set_cache(str(project_dir), "test-model", test_response)
        first_scan_time = time.time() - start
        print(f"✅ First scan completed in {first_scan_time:.4f}s (cache populated)")

        # Second scan - cache hit
        print(f"\n📊 Second scan (expect cache hit)...")
        start = time.time()
        cached = cache.get_cached(str(project_dir), "test-model")
        second_scan_time = time.time() - start

        assert cached is not None, "Expected cache hit on second scan"
        print(f"✅ Second scan completed in {second_scan_time:.4f}s (cache hit)")

        # Calculate speedup
        if first_scan_time > 0:
            speedup = first_scan_time / second_scan_time
            print(f"\n⚡ Cache speedup: {speedup:.2f}x faster")

        # Test multiple scans
        print(f"\n📊 Testing 10 consecutive scans...")
        hits = 0
        for i in range(10):
            cached = cache.get_cached(str(project_dir), "test-model")
            if cached is not None:
                hits += 1

        hit_rate = (hits / 10) * 100
        print(f"✅ Cache hit rate: {hit_rate:.1f}% (target: 90%)")

        assert hit_rate >= 90, f"Cache hit rate {hit_rate}% below target 90%"

        # Test stats
        stats = cache.get_stats()
        print(f"\n📈 Cache Statistics:")
        print(f"   Total entries: {stats['total_entries']}")
        print(f"   Database size: {stats['database_size_mb']} MB")

        print("\n" + "="*60)
        print("✅ PERFORMANCE TEST PASSED")
        print("="*60)

        cache.close()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # Run performance test
    run_performance_test()
