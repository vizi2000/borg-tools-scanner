# Task 2D: Caching & Resume Support

## Objective
Persist LLM responses, enable incremental scans.

## Priority: 🟡 HIGH | Time: 4h | Dependencies: None (standalone)

## Output
```python
# cache_manager.py
class CacheManager:
    def get_cached(project_path, model_name) -> Optional[Dict]
    def set_cache(project_path, model_name, response: Dict)
    def is_stale(cache_entry, max_age_days=7) -> bool
```

## Storage
- SQLite DB: `cache.db`
- Schema: project_path, model, response_json, timestamp
- Invalidate if: files changed (mtime), >7 days old

## Test: Cache hit rate 90% on re-scan
