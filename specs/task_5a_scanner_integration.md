# Task 5A: Main Scanner Integration

## Objective
Refactor borg_tools_scan.py do orchestration wszystkich modułów.

## Priority: 🔴 CRITICAL | Time: 4h | Dependencies: ALL poprzednie

## Changes
```python
# borg_tools_scan.py v2.0
from modules.code_analyzer import analyze_code
from modules.deployment_detector import detect_deployment
from modules.doc_analyzer import analyze_documentation
from modules.llm_orchestrator import ModelPipeline
from modules.vibesummary_generator import generate_vibesummary

def scan_project(p: Path) -> ProjectSummary:
    # 1. Gather facts (existing)
    # 2. Run deep analysis (NEW)
    code_analysis = analyze_code(...)
    deployment_analysis = detect_deployment(...)
    doc_analysis = analyze_documentation(...)
    # 3. LLM pipeline (NEW)
    llm_results = await ModelPipeline().run_parallel_analysis(...)
    # 4. Generate VibeSummary (NEW)
    generate_vibesummary(...)
    # 5. Return extended ProjectSummary
```

## New CLI Flags
```bash
--deep-scan          # Enable code/deployment/doc analysis
--skip-llm          # Fast mode
--parallel-workers 4  # LLM concurrency
--resume            # Use cache
```

## Test: Full end-to-end scan on 3 projects
