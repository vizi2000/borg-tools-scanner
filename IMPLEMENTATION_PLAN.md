# OpenRouter Auto Model Integration - Two-Phase Scan Strategy

## 🎯 Implementation Overview

### **Two-Phase Scanning Approach:**

1. **Phase 1: Fast Triage Scan** (All Projects)
   - Use fastest free model: `meta-llama/llama-3.1-8b-instruct:free`
   - Quick heuristic analysis
   - Score all projects
   - Identify duplicates
   - Select top 40% for deep analysis

2. **Phase 2: Deep Analysis** (Top 40%)
   - Use `openrouter/auto` with premium model preference
   - Prefer cloaked models (Sonoma, Horizon, Cypher, Optimus, Quasar)
   - Full LLM pipeline (4 models)
   - Generate VibeSummary.md

---

## 🚀 **Cloaked Premium Models Strategy**

### **OpenRouter Cloaked Models (Free Testing Period):**
- `openrouter/sonoma-dusk-alpha` - Fast, intelligent, 2M context
- `openrouter/sonoma-sky-alpha` - Maximum intelligence, 2M context
- `openrouter/horizon-beta` - Improved version
- `openrouter/cypher-alpha` - All-purpose, long-context
- `openrouter/optimus-alpha` - Real-world use cases
- `openrouter/quasar-alpha` - Powerful, long-context

### **Model Selection Priority:**
```python
PREMIUM_MODEL_PREFERENCE = [
    "openrouter/sonoma-sky-alpha",    # Highest intelligence
    "openrouter/horizon-beta",         # Improved general purpose
    "openrouter/cypher-alpha",         # Long-context specialist
    "deepseek/deepseek-r1",           # Excellent reasoning
    "anthropic/claude-3.5-sonnet",    # Premium fallback
    "openai/gpt-4o",                  # Premium fallback
]
```

---

## 📊 **Duplicate Detection Strategy**

### **Similarity Metrics:**
1. **Exact duplicates**: Same directory name
2. **Functional duplicates**: 
   - Same primary language
   - Similar dependency count (±20%)
   - Similar file structure
   - Matching functional tags from LLM

### **Deduplication Logic:**
```python
def detect_duplicates(projects):
    duplicates = []
    for i, p1 in enumerate(projects):
        for j, p2 in enumerate(projects[i+1:], i+1):
            similarity = calculate_similarity(p1, p2)
            if similarity > 0.8:  # 80% similar
                duplicates.append((p1, p2, similarity))
    return duplicates
```

---

## 🎯 **Top 40% Selection Criteria**

### **Scoring Formula:**
```python
priority_score = (
    value_score * 1.5 +        # 1.5x weight
    (10 - risk_score) * 1.0 +  # 1.0x weight (inverted)
    recency_bonus +            # 0-2 points
    completeness_bonus         # 0-3 points
)
```

### **Bonus Points:**
- **Recency**: +2 if committed in last 14 days
- **Completeness**: 
  - +1 if has README
  - +1 if has tests
  - +1 if has CI/CD

---

## 🔧 **Implementation Files**

### **New Files:**
1. `modules/duplicate_detector.py` - Duplicate detection logic
2. `modules/two_phase_scanner.py` - Orchestrates two-phase scan
3. `modules/premium_model_router.py` - OpenRouter auto with preferences

### **Modified Files:**
1. `borg_tools_scan.py` - Add `--two-phase` flag
2. `modules/llm_orchestrator.py` - Add premium model routing
3. `modules/vibesummary_generator.py` - Add duplicate markers

---

## 📋 **CLI Usage**

```bash
# Two-phase scan with auto model
python3 borg_tools_scan.py \
  --root ~/Projects \
  --two-phase \
  --auto-model \
  --prefer-premium \
  --verbose

# Custom top percentage
python3 borg_tools_scan.py \
  --root ~/Projects \
  --two-phase \
  --top-percent 40 \
  --auto-model

# With duplicate detection
python3 borg_tools_scan.py \
  --root ~/Projects \
  --two-phase \
  --detect-duplicates \
  --auto-model
```

---

## 📈 **Expected Performance**

### **Phase 1 (Fast Triage):**
- **Speed**: ~5-10 seconds per project
- **Cost**: $0.00 (free model)
- **Coverage**: 100% of projects

### **Phase 2 (Deep Analysis):**
- **Speed**: ~30-60 seconds per project
- **Cost**: ~$0.10-0.30 per project (premium models)
- **Coverage**: Top 40% of projects

### **Total Time Estimate:**
- 50 projects: ~10-15 minutes
- 100 projects: ~20-30 minutes
- 200 projects: ~40-60 minutes

---

## 🎯 **Success Metrics**

- ✅ All projects scanned in Phase 1
- ✅ Top 40% identified correctly
- ✅ Duplicates detected and marked
- ✅ Premium models used for deep analysis
- ✅ VibeSummary.md generated for top projects
- ✅ Cost optimized (free for triage, premium for deep)

---

**Status**: Ready for implementation
**Estimated Time**: 45-60 minutes
**Next Step**: Create implementation files
