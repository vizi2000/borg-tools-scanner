# Borg.tools Scanner v2.0

**Multi-Model LLM-Powered Project Analysis & Scoring Engine**

A comprehensive project scanner that analyzes codebases, detects deployment configurations, evaluates documentation quality, and generates actionable insights using parallel LLM execution across multiple AI models.

---

## 🎯 Project Overview

Borg.tools Scanner v2.0 is an advanced project analysis tool designed for developers managing multiple codebases. It combines traditional static analysis with cutting-edge multi-model LLM intelligence to provide deep insights into code quality, deployment readiness, documentation completeness, and monetization viability.

**What makes it special:**
- **6-Category Scoring System** - Code Quality, Deployment, Documentation, Borg.tools Fit, MVP Proximity, Monetization
- **Multi-Model LLM Pipeline** - Parallel execution across 4 specialized AI models (Architect, Business, Deployment, Aggregator)
- **Agent Zero Integration** - Bonus scoring from Borg.tools MCP-VIBE server workflows
- **Intelligent Caching** - SQLite-based cache with smart invalidation
- **Rich Console UI** - Beautiful terminal output with progress bars and emoji indicators
- **VibeSummary Generation** - Comprehensive markdown reports with actionable next steps

---

## ✨ Key Features

### 🔍 Analysis Modules (11 Total)

**Core Analyzers:**
1. **Code Analyzer** - Complexity metrics, security scanning, architecture patterns
2. **Deployment Detector** - Infrastructure detection, platform inference, MVP checklists
3. **Doc Analyzer** - README validation, API endpoint detection, auto-generation

**LLM Infrastructure:**
4. **LLM Orchestrator** - Parallel execution across 4 AI models
5. **Prompt System** - Specialized prompts for Architect/Business/Deployment/Aggregator
6. **Response Handler** - JSON parsing, validation, error recovery
7. **Cache Manager** - SQLite caching with file-hash invalidation

**Output & Integration:**
8. **VibeSummary Generator** - Markdown report synthesis
9. **Progress Reporter** - Rich console UI with colors and progress bars
10. **Agent Zero Bridge** - MCP-VIBE server communication
11. **Agent Zero Auditor** - Workflow submission and bonus scoring

### 📊 Scoring Categories

| Category | Weight | Criteria |
|----------|--------|----------|
| **🎨 Code Quality** | 20% | Complexity, readability, security, patterns |
| **🚀 Deployment** | 20% | Docker, CI/CD, environment config, platform detection |
| **📚 Documentation** | 15% | README completeness, API docs, accuracy |
| **🎯 Borg.tools Fit** | 15% | MCP-VIBE compatibility, workflow integration |
| **🎪 MVP Proximity** | 15% | Completeness vs. MVP checklist, time estimation |
| **💰 Monetization** | 15% | Market viability, revenue potential, target audience |

**Overall Vibecodibility Score:** Weighted average (0-10 scale)

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/borg-tools-scan.git
cd borg-tools-scan

# Install dependencies (optional - for rich UI)
python3 -m pip install --break-system-packages rich

# Set up environment variables (optional - for LLM features)
export OPENAI_API_KEY="your-openai-key"
export OPENROUTER_API_KEY="your-openrouter-key"
```

### Basic Usage

```bash
# Scan all projects in a directory (heuristic mode - no LLM)
python3 borg_tools_scan.py --root ~/Projects

# Scan with LLM enhancements (OpenAI)
python3 borg_tools_scan.py --root ~/Projects --use-llm openai --model gpt-4o-mini

# Scan with LLM enhancements (OpenRouter)
python3 borg_tools_scan.py --root ~/Projects --use-llm openrouter --model anthropic/claude-3-haiku:beta

# Limit number of projects
python3 borg_tools_scan.py --root ~/Projects --limit 5
```

### Output Files

After scanning, you'll find:
- **`BORG_INDEX.md`** - Portfolio dashboard (in root directory)
- **`borg_dashboard.csv`** - Tabular view (current directory)
- **`borg_dashboard.json`** - Machine-readable summary (current directory)
- **`REPORT.md`** - Per-project detailed report (in each project folder)
- **`VibeSummary.md`** - Comprehensive analysis (when using LLM mode)

---

## 📊 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  borg_tools_scan.py (Main CLI)               │
└────────────────────────┬─────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│    Code     │  │ Deployment   │  │     Doc      │
│  Analyzer   │  │  Detector    │  │  Analyzer    │
└──────┬──────┘  └──────┬───────┘  └──────┬───────┘
       │                │                  │
       └────────────────┼──────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │   LLM Orchestrator      │
          │  (4 models parallel)    │
          ├─────────────────────────┤
          │ • Architect Model       │
          │ • Business Model        │
          │ • Deployment Model      │
          │ • Aggregator Model      │
          └───────────┬─────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Response │  │  Cache   │  │  Agent   │
  │ Handler  │  │ Manager  │  │   Zero   │
  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ VibeSummary Generator│
          │   + Progress UI      │
          └──────────────────────┘
                     │
                     ▼
              VibeSummary.md
```

### Module Interactions

1. **Analysis Phase** - Code/Deployment/Doc analyzers run in parallel
2. **LLM Phase** - 4 models execute concurrently with cached results
3. **Agent Zero Phase** - Optional workflow submission for bonus scoring
4. **Synthesis Phase** - VibeSummary generation with all collected data
5. **Output Phase** - Markdown/CSV/JSON files written to disk

---

## ⚙️ Configuration

### Environment Variables

```bash
# LLM Providers (Optional - for advanced features)
export OPENAI_API_KEY="sk-..."           # OpenAI API key
export OPENROUTER_API_KEY="sk-or-..."   # OpenRouter API key

# Agent Zero Integration (Optional)
export BORG_TOOLS_API_KEY="..."         # MCP-VIBE server key (for bonus scoring)
```

### CLI Flags

```bash
--root <path>           # Root directory to scan (default: ..)
--use-llm <provider>    # Enable LLM: openai | openrouter
--model <model_id>      # Model to use (e.g., gpt-4o-mini, claude-3-haiku)
--limit <n>             # Limit number of projects to scan (0 = all)
```

### Custom Configuration

Edit constants in `borg_tools_scan.py`:

```python
# File detection patterns
TEST_DIR_NAMES = {"tests", "test", "__tests__"}
CI_HINTS = {".github/workflows", ".gitlab-ci.yml", ...}
PY_FILES = {"pyproject.toml", "requirements.txt", ...}
JS_FILES = {"package.json", "pnpm-lock.yaml", ...}

# Analysis limits
SAFE_IGNORE_PATTERNS = [r"\.venv/", r"node_modules/", ...]
BINARY_EXTENSIONS = {'.jpg', '.png', '.pdf', ...}
```

---

## 🔧 Advanced Usage

### Custom Prompts

Modify prompts for specialized domains:

```bash
# Edit prompt templates
vim prompts/architect_prompt.md
vim prompts/business_prompt.md
vim prompts/deployment_prompt.md
vim prompts/aggregator_prompt.md
```

Each prompt includes:
- **Context** - Project facts, code metrics, deployment data
- **Instructions** - Specific analysis tasks
- **Output Format** - Required JSON schema
- **Examples** - Sample responses

### Agent Zero Workflows

Enable bonus scoring via Borg.tools MCP-VIBE server:

```python
from modules.agent_zero_bridge import AgentZeroBridge

# Initialize bridge
bridge = AgentZeroBridge(api_key="your-api-key")

# Submit workflow
result = bridge.submit_workflow(
    workflow_type="code_review",
    project_path="/path/to/project",
    context={"language": "python", "files": [...]}
)

# Get bonus score
bonus_score = result.get("bonus_score", 0)
```

**Available Workflows:**
- `code_review` - Deep code analysis
- `security_audit` - Vulnerability scanning
- `architecture_review` - Design pattern validation
- `deployment_check` - Infrastructure audit

### Programmatic API

Use scanner as a library:

```python
from pathlib import Path
from borg_tools_scan import scan_project, heuristic_suggestions

# Scan single project
project_path = Path("/path/to/project")
summary = scan_project(project_path)

# Access results
print(f"Stage: {summary.scores.stage}")
print(f"Value: {summary.scores.value_score}/10")
print(f"Risk: {summary.scores.risk_score}/10")
print(f"Priority: {summary.scores.priority}/20")

# Get suggestions
suggestions = heuristic_suggestions(summary.facts, summary.scores)
print("TODO now:", suggestions.todo_now)
print("TODO next:", suggestions.todo_next)
```

### Module Integration

Use individual analyzers:

```python
# Code Analysis
from modules.code_analyzer import analyze_code_quality
result = analyze_code_quality("/path/to/project", ["python"])

# Deployment Detection
from modules.deployment_detector import detect_deployment
deployment = detect_deployment("/path/to/project", {})

# Documentation Analysis
from modules.doc_analyzer import analyze_documentation
docs = analyze_documentation("/path/to/project", ["python"], {})

# LLM Orchestration
from modules.llm_orchestrator import LLMOrchestrator
orchestrator = LLMOrchestrator(provider="openai", model="gpt-4o-mini")
responses = orchestrator.analyze_project(project_data)
```

---

## 📚 Documentation Links

### Module Documentation

- **[Code Analyzer](modules/README_CODE_ANALYZER.md)** - Complexity, security, patterns
- **[Deployment Detector](modules/README_deployment_detector.md)** - Platform detection, MVP checklists
- **[Doc Analyzer](modules/QUICK_START_DOC_ANALYZER.md)** - README validation, auto-generation
- **[LLM Orchestrator](modules/README_LLM_ORCHESTRATOR.md)** - Multi-model parallel execution
- **[Response Handler](modules/README_RESPONSE_HANDLER.md)** - JSON parsing, error recovery
- **[Cache Manager](CACHE_MANAGER_README.md)** - SQLite caching, invalidation
- **[VibeSummary Generator](modules/README_VIBESUMMARY.md)** - Report synthesis
- **[Progress Reporter](modules/README_PROGRESS_REPORTER.md)** - Rich console UI
- **[Agent Zero Bridge](modules/README_AGENT_ZERO_BRIDGE.md)** - MCP-VIBE integration
- **[Agent Zero Auditor](AGENT_ZERO_AUDITOR_README.md)** - Workflow submission

### Quick Start Guides

- **[LLM Orchestrator Quick Start](QUICK_START_LLM_ORCHESTRATOR.md)**
- **[Progress Reporter Quick Start](QUICK_START_PROGRESS_REPORTER.md)**
- **[Agent Zero Quick Start](QUICK_START_AGENT_ZERO_BRIDGE.md)**

### Task Completion Reports

- [Task 1C: Doc Analyzer](TASK_1C_COMPLETION_REPORT.md)
- [Task 2A: LLM Orchestrator](TASK_2A_COMPLETION_REPORT.md)
- [Task 2C: Response Handler](TASK_2C_COMPLETION_REPORT.md)
- [Task 2D: Cache Manager](TASK_2D_COMPLETION_REPORT.md)
- [Task 3A: VibeSummary](TASK_3A_COMPLETION_REPORT.md)
- [Task 3B: Progress Reporter](TASK_3B_COMPLETION_REPORT.md)
- [Task 4A: Agent Zero Bridge](TASK_4A_COMPLETION_REPORT.md)
- [Task 4B: Agent Zero Auditor](TASK_4B_COMPLETION_REPORT.md)

### Specification Documents

See **[specs/](specs/)** directory for detailed task specifications.

---

## 🤝 Contributing

Contributions are welcome! This project follows a modular architecture - each analyzer is independent and can be enhanced separately.

### Development Setup

```bash
# Install development dependencies
python3 -m pip install --break-system-packages pytest rich

# Run tests
pytest tests/ -v
pytest modules/test_*.py -v

# Run integration tests
pytest tests/integration_test.py -v
```

### Adding New Analyzers

1. Create module in `modules/your_analyzer.py`
2. Follow the pattern:
   ```python
   def analyze_feature(project_path: str, languages: List[str], facts: Dict) -> Dict:
       """Analyze specific feature"""
       return {
           "score": 0-10,
           "details": {...},
           "suggestions": [...]
       }
   ```
3. Add tests in `modules/test_your_analyzer.py`
4. Update `modules/__init__.py` exports
5. Document in `modules/README_YOUR_ANALYZER.md`

### Code Style

- **Type hints** - All functions must have full type annotations
- **Docstrings** - Use Google-style docstrings
- **Error handling** - Always gracefully degrade, never crash
- **No external deps** - Core modules use stdlib only (except `rich` for UI)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

**Created by The Collective Borg.tools**

This project is part of the Borg.tools ecosystem - a suite of AI-powered developer productivity tools.

---

## 🔗 Related Projects

- **[MCP-VIBE Server](https://mcp.borg.tools)** - Specification generation and validation API
- **[Agent Zero](https://borg.tools)** - AI workflow automation platform
- **[Borg.tools CLI](https://github.com/borg-tools)** - Command-line interface for all tools

---

## 📈 Roadmap

- [ ] Support for more languages (Java, Rust, Go)
- [ ] GitHub Actions integration
- [ ] VSCode extension
- [ ] Real-time monitoring dashboard
- [ ] Team collaboration features
- [ ] CI/CD pipeline templates
- [ ] Docker image for easy deployment

---

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/borg-tools-scan/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/borg-tools-scan/discussions)
- **Email:** support@borg.tools
- **SSH Access:** `ssh vizi@borg.tools` (passwordless)

---

**Version:** 2.0.0
**Last Updated:** 2025-10-25
**Status:** Production Ready ✅
