# CacheManager - SQLite-based LLM Response Caching

## Overview

The `CacheManager` module provides persistent caching for LLM responses with intelligent staleness detection. It eliminates redundant API calls by caching results and automatically invalidating cache when project files change.

**Key Features:**
- SQLite-based persistent storage
- Time-based cache expiration (default: 7 days)
- File modification tracking (mtime-based invalidation)
- Thread-safe operations (WAL mode)
- Support for multiple projects and models
- Comprehensive statistics and monitoring

## Installation

The module is located in `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/cache_manager.py`

```python
from modules import CacheManager, get_cache_manager
```

## Quick Start

```python
from modules import CacheManager

# Initialize cache
cache = CacheManager('cache.db')

# Cache a response
response = {'analysis': 'Code quality is good', 'score': 85}
cache.set_cache('/path/to/project', 'gpt-4', response)

# Retrieve cached response
cached = cache.get_cached('/path/to/project', 'gpt-4')
if cached:
    print("Using cached response")
else:
    print("Cache miss - need to call LLM")
```

## Usage Patterns

### Basic Caching Workflow

```python
from modules import CacheManager

def analyze_with_cache(project_path: str, model: str) -> dict:
    with CacheManager('cache.db') as cache:
        # Try to get cached response
        result = cache.get_cached(project_path, model)

        if result:
            print("✅ Cache hit")
            return result

        # Perform expensive LLM analysis
        print("🤖 Calling LLM API...")
        result = call_llm_api(project_path, model)

        # Cache the result
        cache.set_cache(project_path, model, result)
        return result
```

### Multiple Projects and Models

```python
cache = CacheManager('cache.db')

# Cache responses for different projects
cache.set_cache('/project1', 'gpt-4', {'score': 90})
cache.set_cache('/project2', 'gpt-4', {'score': 85})

# Cache responses for different models
cache.set_cache('/project1', 'gpt-4', {'score': 90})
cache.set_cache('/project1', 'claude-3', {'score': 92})

# Each combination is cached separately
result1 = cache.get_cached('/project1', 'gpt-4')    # Returns {'score': 90}
result2 = cache.get_cached('/project2', 'gpt-4')    # Returns {'score': 85}
result3 = cache.get_cached('/project1', 'claude-3') # Returns {'score': 92}
```

### Custom Cache Expiration

```python
# Check staleness with custom max age
cache_entry = {
    'response': {'data': 'test'},
    'timestamp': cache_timestamp,
    'files_mtime': files_dict
}

# Default: 7 days
is_stale = cache.is_stale(cache_entry, '/project', max_age_days=7)

# Custom: 30 days
is_stale = cache.is_stale(cache_entry, '/project', max_age_days=30)
```

### Manual Cache Management

```python
cache = CacheManager('cache.db')

# Get cache statistics
stats = cache.get_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Database size: {stats['database_size_mb']} MB")
print(f"Oldest entry: {stats['oldest_entry']}")

# Clear all cache entries
cache.clear_all()

# Invalidate specific entry
cache._invalidate_cache('/project', 'gpt-4')
```

## API Reference

### CacheManager Class

#### `__init__(db_path: str = 'cache.db')`
Initialize cache manager with SQLite database.

**Parameters:**
- `db_path`: Path to SQLite database file (default: `cache.db`)

#### `get_cached(project_path: str, model_name: str) -> Optional[Dict]`
Retrieve cached response if available and not stale.

**Parameters:**
- `project_path`: Path to project directory
- `model_name`: Name of LLM model used

**Returns:**
- Cached response dictionary or `None` if cache miss/stale

#### `set_cache(project_path: str, model_name: str, response: Dict) -> bool`
Store LLM response in cache with file modification tracking.

**Parameters:**
- `project_path`: Path to project directory
- `model_name`: Name of LLM model used
- `response`: LLM response dictionary to cache

**Returns:**
- `True` if successfully cached, `False` otherwise

#### `is_stale(cache_entry: Dict, project_path: str, max_age_days: int = 7) -> bool`
Check if cache entry is stale based on age and file modifications.

**Parameters:**
- `cache_entry`: Cache entry dictionary with timestamp and files_mtime
- `project_path`: Path to project (required for file checking)
- `max_age_days`: Maximum age in days before considering stale (default: 7)

**Returns:**
- `True` if cache is stale, `False` otherwise

#### `get_stats() -> Dict[str, Any]`
Get cache statistics.

**Returns:**
- Dictionary with cache statistics:
  - `total_entries`: Number of cached entries
  - `database_size_bytes`: Database size in bytes
  - `database_size_mb`: Database size in MB
  - `oldest_entry`: ISO timestamp of oldest entry
  - `newest_entry`: ISO timestamp of newest entry

#### `clear_all() -> bool`
Clear all cache entries.

**Returns:**
- `True` if successful, `False` otherwise

#### `close()`
Close database connection.

### Factory Function

#### `get_cache_manager(db_path: str = 'cache.db') -> CacheManager`
Factory function to get a CacheManager instance.

**Parameters:**
- `db_path`: Path to SQLite database file

**Returns:**
- CacheManager instance

## Staleness Detection

The cache automatically invalidates when:

### 1. Time-Based Staleness
Cache entries older than `max_age_days` (default: 7 days) are considered stale.

```python
# Cache expires after 7 days
cached = cache.get_cached('/project', 'gpt-4')  # None after 7 days
```

### 2. File Modification
Cache invalidates when any project file is:
- Modified (different mtime)
- Added (new file)
- Removed (deleted file)

```python
# Initial cache
cache.set_cache('/project', 'gpt-4', response)

# Modify a file
Path('/project/main.py').write_text('new content')

# Cache is now stale
cached = cache.get_cached('/project', 'gpt-4')  # None
```

### 3. Ignored Files/Directories
The following patterns are ignored for staleness checking:
- `__pycache__`, `.git`, `.venv`, `venv`, `node_modules`
- `.pytest_cache`, `.mypy_cache`, `dist`, `build`
- `*.pyc`, `.DS_Store`
- `cache.db` and related WAL files

## Database Schema

```sql
CREATE TABLE cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path TEXT NOT NULL,
    model_name TEXT NOT NULL,
    response_json TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    files_mtime TEXT NOT NULL,
    cache_key TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(project_path, model_name)
);

CREATE INDEX idx_project_model ON cache(project_path, model_name);
CREATE INDEX idx_timestamp ON cache(timestamp);
```

## Performance

### Test Results
From `test_cache_manager.py`:

```
Cache Hit Rate Test (10 consecutive scans):
✅ Cache hit rate: 100.0% (target: 90%)
✅ All 19 unit tests passed

Performance metrics:
- First scan (cache miss): ~0.003s
- Second scan (cache hit): ~0.003s
- Cache speedup: 1.06x faster (for DB operations only)
```

**Real-world LLM scenario:**
- LLM API call: ~2-5 seconds
- Cache retrieval: ~0.003 seconds
- **Speedup: 700-1600x faster**

### Cache Hit Rate Goal
Per specification: **90% cache hit rate on re-scan**

Achieved: **100% cache hit rate** when files haven't changed

## Examples

See `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/cache_manager_example.py` for a complete working example:

```bash
cd /Users/wojciechwiesner/ai/_Borg.tools_scan/modules
python3 cache_manager_example.py
```

## Testing

Run the comprehensive test suite:

```bash
cd /Users/wojciechwiesner/ai/_Borg.tools_scan/modules
python3 test_cache_manager.py
```

**Test Coverage:**
- Cache hit/miss scenarios
- Time-based staleness detection
- File modification detection
- Multiple projects and models
- Concurrent access (SQLite locking)
- Cache invalidation
- Large response handling
- Error handling

## Integration Example

Integrate with existing scanner:

```python
from modules import CacheManager

class ProjectScanner:
    def __init__(self, cache_db='cache.db'):
        self.cache = CacheManager(cache_db)

    def scan_project(self, project_path: str, model: str = 'gpt-4') -> dict:
        # Try cache first
        cached_result = self.cache.get_cached(project_path, model)
        if cached_result:
            print(f"✅ Using cached scan results")
            return cached_result

        # Perform scan
        print(f"🔍 Scanning {project_path}...")
        result = self._perform_scan(project_path, model)

        # Cache for future use
        self.cache.set_cache(project_path, model, result)
        return result

    def _perform_scan(self, project_path: str, model: str) -> dict:
        # Your actual scanning logic here
        pass
```

## Best Practices

1. **Use context manager for automatic cleanup:**
   ```python
   with CacheManager('cache.db') as cache:
       # Your code here
   # Connection automatically closed
   ```

2. **Check cache before expensive operations:**
   ```python
   cached = cache.get_cached(project, model)
   if not cached:
       # Only call LLM API if cache miss
       result = expensive_llm_call()
       cache.set_cache(project, model, result)
   ```

3. **Monitor cache statistics:**
   ```python
   stats = cache.get_stats()
   if stats['database_size_mb'] > 100:
       print("Consider clearing old cache entries")
   ```

4. **Use appropriate cache expiration:**
   ```python
   # Short-lived projects: 1-3 days
   # Stable projects: 7-30 days
   is_stale = cache.is_stale(entry, project, max_age_days=30)
   ```

## Thread Safety

The cache uses SQLite's WAL (Write-Ahead Logging) mode for improved concurrent access:

```python
# Multiple cache instances can safely access the same database
cache1 = CacheManager('cache.db')
cache2 = CacheManager('cache.db')

cache1.set_cache('/project1', 'model1', data1)
cache2.set_cache('/project2', 'model2', data2)
```

## Troubleshooting

### Database Locked Error
If you encounter database locking issues:
```python
# Increase timeout
cache = CacheManager('cache.db')
cache.conn.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
```

### Large Database Size
```python
# Check size
stats = cache.get_stats()
print(f"Size: {stats['database_size_mb']} MB")

# Clear old entries
cache.clear_all()

# Or use VACUUM to reclaim space
cache.conn.execute("VACUUM")
```

### Cache Not Invalidating
Ensure project_path is absolute:
```python
from pathlib import Path

# Bad: relative path
cache.set_cache('project', 'model', data)

# Good: absolute path
cache.set_cache(str(Path('project').absolute()), 'model', data)
```

## License

Created by The Collective Borg.tools

## Related Files

- Implementation: `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/cache_manager.py`
- Tests: `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/test_cache_manager.py`
- Example: `/Users/wojciechwiesner/ai/_Borg.tools_scan/modules/cache_manager_example.py`
- Specification: `/Users/wojciechwiesner/ai/_Borg.tools_scan/specs/task_2d_cache_manager.md`
