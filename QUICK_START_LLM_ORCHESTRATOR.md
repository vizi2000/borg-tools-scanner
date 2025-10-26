# LLM Orchestrator - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install aiohttp
```

### 2. Set API Key
```bash
export OPENROUTER_API_KEY="your_key_here"
```

### 3. Test with Dry Run
```python
import asyncio
from modules.llm_orchestrator import analyze_with_llm

project_data = {
    'name': 'test-project',
    'path': '/path/to/project',
    'languages': ['python'],
    'code_analysis': {},
    'deployment_analysis': {},
    'doc_analysis': {}
}

# Dry run (no API calls, mock responses)
result = asyncio.run(analyze_with_llm(project_data, dry_run=True))
print(result)
```

### 4. Run Real Analysis
```bash
# Full integration example
python3 example_llm_integration.py /path/to/project --real
```

---

## 📋 Quick Command Reference

### Dry Run Test
```bash
python3 modules/llm_orchestrator.py
```

### Comprehensive Test
```bash
python3 test_llm_orchestrator.py
```

### Full Pipeline (Dry Run)
```bash
python3 example_llm_integration.py
```

### Full Pipeline (Real API)
```bash
python3 example_llm_integration.py /path/to/project --real
```

---

## 🎯 Common Use Cases

### Use Case 1: Analyze Current Project
```bash
python3 example_llm_integration.py . --real
```

### Use Case 2: Batch Process Multiple Projects
```python
import asyncio
from pathlib import Path
from modules.llm_orchestrator import analyze_with_llm

async def batch_analyze(project_paths):
    results = {}
    for path in project_paths:
        project_data = prepare_project_data(path)  # Your prep function
        result = await analyze_with_llm(project_data)
        results[path] = result
    return results

# Run
paths = ['/path/to/proj1', '/path/to/proj2']
asyncio.run(batch_analyze(paths))
```

### Use Case 3: Custom Pipeline
```python
from modules.llm_orchestrator import ModelPipeline

pipeline = ModelPipeline(dry_run=False)
result = await pipeline.run_parallel_analysis(your_project_data)

# Access specific analyses
architect = result['llm_results']['architect_analysis']
business = result['llm_results']['business_analysis']
insights = result['llm_results']['aggregated_insights']
```

---

## 📊 Output Structure

```json
{
  "llm_results": {
    "architect_analysis": {
      "architecture_assessment": "...",
      "design_patterns": ["..."],
      "scalability_notes": "...",
      "technical_debt_priority": "low|medium|high"
    },
    "deployment_analysis": {
      "deployment_strategy": "...",
      "infrastructure_recommendations": "...",
      "deployment_blockers": [...],
      "mvp_roadmap": [...]
    },
    "business_analysis": {
      "problem_solved": "...",
      "target_audience": "...",
      "monetization_strategy": "...",
      "market_viability": 0-10,
      "portfolio_suitable": true|false,
      "portfolio_pitch": "..."
    },
    "aggregated_insights": {
      "overall_assessment": "...",
      "top_priorities": [...],
      "vibecodibility_score": 0-10,
      "borg_tools_fit": 0-10
    },
    "metadata": {
      "total_time_seconds": 45.2,
      "api_calls": 4,
      "cache_hits": 0
    }
  }
}
```

---

## ⚡ Performance Tips

1. **Use Dry Run First**
   - Test your integration without API calls
   - Validate data flow before spending API credits

2. **Enable Caching (when Task 2D ready)**
   - 90% cache hit rate on re-scans
   - Massive speedup for repeated analysis

3. **Batch Processing**
   - Rate limiter handles throttling automatically
   - ~6-10 projects/hour on free tier

4. **Error Handling**
   - Pipeline continues even if 1-2 models fail
   - Check `metadata.api_calls` to verify execution

---

## 🔧 Troubleshooting

### "OPENROUTER_API_KEY not set"
```bash
export OPENROUTER_API_KEY="your_key_here"
```

### "Rate limited, waiting Xs"
- **Normal behavior** - free tier limit is 10 req/min
- Pipeline automatically waits and retries
- Consider paid tier for faster processing

### "Model X failed"
- Pipeline uses fallback response
- Check model availability on OpenRouter
- Verify free tier model IDs are current

### Slow execution (>60s)
- **Expected** for 4 models on free tier
- Check network connection
- OpenRouter API response times vary (30-60s normal)

---

## 📚 More Information

- **Full Documentation:** `modules/README_LLM_ORCHESTRATOR.md`
- **Completion Report:** `TASK_2A_COMPLETION_REPORT.md`
- **Spec:** `specs/task_2a_llm_orchestrator_full.md`

---

## 🆘 Need Help?

1. Check the documentation files listed above
2. Run tests: `python3 test_llm_orchestrator.py`
3. Try dry run mode to isolate issues
4. Review test results in `test_llm_results.json`

---

**Created by The Collective Borg.tools**
