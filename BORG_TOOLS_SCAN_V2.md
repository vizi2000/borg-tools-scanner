# Borg.tools Scanner v2.0 - Deep Dive Technical Guide

**Complete Technical Documentation for the Multi-Model LLM-Powered Analysis Engine**

---

## Table of Contents

1. [Scoring Algorithms](#scoring-algorithms)
2. [LLM Pipeline Details](#llm-pipeline-details)
3. [Agent Zero Integration](#agent-zero-integration)
4. [VibeSummary Structure](#vibesummary-structure)
5. [Cache System](#cache-system)
6. [Deployment Detection Logic](#deployment-detection-logic)
7. [Extension Guide](#extension-guide)

---

## Scoring Algorithms

### 6 Category Scoring System

Each project receives scores across 6 dimensions, weighted to produce an overall **Vibecodibility Score**.

#### 1. Code Quality Score (0-10)

**Formula:**
```python
score = base_score + readability_bonus + security_penalty + complexity_penalty

base_score = 5.0  # Starting point

# Readability bonus (0-3 points)
if avg_function_length < 30:
    readability_bonus += 1.5
if documentation_coverage > 0.7:
    readability_bonus += 1.5

# Security penalty (0 to -5 points)
security_penalty = min(5, len(high_severity_issues) * 0.5)

# Complexity penalty (0 to -3 points)
if avg_cyclomatic_complexity > 10:
    complexity_penalty += 2
if max_complexity > 20:
    complexity_penalty += 1

final_score = max(0, min(10, score))
```

**Key Metrics:**
- **Cyclomatic Complexity** - Number of independent paths through code
- **Cognitive Complexity** - Difficulty of understanding code
- **Documentation Coverage** - Percentage of functions with docstrings
- **Security Issues** - SQL injection, eval/exec, hardcoded secrets
- **Architecture Patterns** - MVC, Factory, Singleton detection

**Scoring Breakdown:**
- **9-10** - Production-ready, excellent practices
- **7-8** - Good quality, minor improvements needed
- **5-6** - Acceptable, significant improvements recommended
- **3-4** - Poor quality, major refactoring needed
- **0-2** - Critical issues, not maintainable

---

#### 2. Deployment Readiness Score (0-10)

**Formula:**
```python
score = 0

# Infrastructure artifacts (0-4 points)
if has_dockerfile:
    score += 2
if has_docker_compose:
    score += 1
if has_ci_cd:
    score += 1

# Environment configuration (0-2 points)
if has_env_example:
    score += 1
if all_env_vars_documented:
    score += 1

# Build & validation (0-2 points)
if has_build_script:
    score += 1
if build_testable:
    score += 1

# Platform detection (0-2 points)
if deployment_type != "unknown":
    score += 1
if has_deployment_instructions:
    score += 1

final_score = min(10, score)
```

**Deployment Types Detected:**
- `docker` - Dockerfile present
- `kubernetes` - K8s manifests detected
- `serverless` - Lambda/Cloud Functions
- `traditional` - systemd/init scripts
- `static` - HTML/CSS/JS only
- `unknown` - No deployment config

**Platform Inference:**
- AWS (ECS, Lambda, Elastic Beanstalk)
- Google Cloud (Cloud Run, App Engine)
- Heroku (Procfile)
- Vercel/Netlify (static sites)
- Railway/Render (docker)

---

#### 3. Documentation Score (0-10)

**Formula:**
```python
completeness_score = (found_sections / total_required_sections) * 5
accuracy_score = (1 - accuracy_issues_count / total_checks) * 3
bonus_score = 2 if has_api_docs else 0

final_score = min(10, completeness_score + accuracy_score + bonus_score)
```

**Required README Sections:**
1. Installation
2. Usage
3. Configuration
4. API (if applicable)
5. Testing
6. Deployment
7. Contributing
8. License

**Accuracy Checks:**
- Declared dependencies vs. actual usage
- API endpoints documented vs. implemented
- Environment variables mentioned vs. code references
- Command examples validity

**Bonus Points:**
- API documentation (+2)
- CHANGELOG.md (+1)
- Architecture diagrams (+1)
- Examples directory (+1)

---

#### 4. Borg.tools Fit Score (0-10)

**LLM-Powered Assessment** - Uses Aggregator model

**Criteria:**
- **MCP-VIBE Integration** - Can specs be generated?
- **Workflow Automation** - Suitable for Agent Zero?
- **Code Generation** - Can AI assist development?
- **Testing Automation** - AI-generatable tests?
- **Documentation Generation** - Auto-doc potential?

**Scoring Guide:**
- **9-10** - Perfect fit, immediate MCP integration
- **7-8** - Good fit, minor adjustments needed
- **5-6** - Moderate fit, some refactoring required
- **3-4** - Poor fit, significant changes needed
- **0-2** - Not suitable for Borg.tools ecosystem

---

#### 5. MVP Proximity Score (0-10)

**Formula:**
```python
# Calculate completion percentage
completed_tasks = sum(1 for task in mvp_checklist if task.status == "done")
total_tasks = len(mvp_checklist)
completion_ratio = completed_tasks / total_tasks

# Time-weighted score
estimated_hours = sum(task.hours for task in mvp_checklist if task.status != "done")
time_penalty = min(5, estimated_hours / 10)  # Penalty for >50h remaining

base_score = completion_ratio * 10
final_score = max(0, base_score - time_penalty)
```

**MVP Checklist Items:**
1. Core functionality working
2. Documentation complete
3. Tests passing (>60% coverage)
4. Deployment configuration
5. CI/CD pipeline
6. Error handling
7. Logging/monitoring
8. Security hardening

**Time Estimates:**
- **Blocked** - Cannot proceed (assigned high penalty)
- **Missing** - Not started (full time estimate)
- **Pending** - In progress (50% time estimate)
- **Done** - Completed (0 time)

---

#### 6. Monetization Viability Score (0-10)

**LLM-Powered Assessment** - Uses Business model

**Factors:**
- **Problem Solved** - Clear value proposition?
- **Target Audience** - Well-defined market?
- **Competitive Advantage** - Unique features?
- **Scalability** - Can it handle growth?
- **Revenue Model** - Clear monetization path?

**Monetization Strategies Identified:**
- **SaaS** - Subscription model
- **API** - Pay-per-use
- **Marketplace** - Transaction fees
- **Enterprise** - Custom licensing
- **Freemium** - Free tier + premium features
- **Open Source** - Sponsorship/support

**Scoring:**
- **9-10** - Ready to launch, clear revenue path
- **7-8** - Strong potential, minor validation needed
- **5-6** - Moderate potential, market research required
- **3-4** - Weak potential, pivot recommended
- **0-2** - Not viable, hobby project

---

### Overall Vibecodibility Score

**Weighted Average:**
```python
weights = {
    "code_quality": 0.20,
    "deployment": 0.20,
    "documentation": 0.15,
    "borg_fit": 0.15,
    "mvp_proximity": 0.15,
    "monetization": 0.15
}

vibecodibility = sum(score * weight for score, weight in zip(scores, weights.values()))
```

**Final Rating:**
- **9-10** ✅ - Production-ready, portfolio-worthy
- **7-8** ⚠️ - Good project, polish needed
- **5-6** ⚠️ - Functional, improvements critical
- **3-4** ❌ - Early stage, major work required
- **0-2** ❌ - Prototype, not ready

---

## LLM Pipeline Details

### 4-Model Parallel Execution

The scanner uses **4 specialized AI models** running in parallel for comprehensive analysis.

#### Model Roles

**1. Architect Model**
- **Purpose:** Technical architecture assessment
- **Input:** Code metrics, file structure, dependencies
- **Output:**
  ```json
  {
    "architecture_assessment": "string",
    "design_patterns": ["MVC", "Factory"],
    "scalability_notes": "string",
    "technical_debt_priority": "low|medium|high"
  }
  ```

**2. Business Model**
- **Purpose:** Market viability & monetization
- **Input:** Project description, README, target audience
- **Output:**
  ```json
  {
    "problem_solved": "string",
    "target_audience": "string",
    "market_viability": 0-10,
    "monetization_strategy": "string",
    "portfolio_suitable": boolean,
    "portfolio_pitch": "string"
  }
  ```

**3. Deployment Model**
- **Purpose:** Infrastructure & MVP roadmap
- **Input:** Deployment config, environment vars, build scripts
- **Output:**
  ```json
  {
    "deployment_strategy": "docker|k8s|serverless|...",
    "infrastructure_recommendations": "string",
    "mvp_roadmap": ["task1", "task2", "task3"]
  }
  ```

**4. Aggregator Model**
- **Purpose:** Synthesize all analyses into final assessment
- **Input:** All previous model outputs + raw data
- **Output:**
  ```json
  {
    "overall_assessment": "string",
    "vibecodibility_score": 0-10,
    "top_priorities": ["priority1", "priority2"],
    "borg_tools_fit": 0-10
  }
  ```

---

### Execution Flow

```
┌────────────────────────────────────────────┐
│  Project Data Collection                   │
│  (Code, Deployment, Documentation)         │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│  Prompt Generation                         │
│  (4 specialized prompts with context)      │
└──────────────┬─────────────────────────────┘
               │
               ▼
      ┌────────┴────────┐
      │  Parallel Exec  │
      └────────┬────────┘
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Architect│ │Business│ │Deploy  │ │Aggreg  │
│ Model  │ │ Model  │ │ Model  │ │ Model  │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │
    └──────────┼──────────┴──────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│  Response Parsing & Validation             │
│  (JSON extraction, error recovery)         │
└──────────────┬─────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────┐
│  Cache Storage                             │
│  (SQLite with file-hash key)               │
└────────────────────────────────────────────┘
```

---

### Error Recovery

**Multi-Level Fallback:**

1. **JSON Extraction** - Try multiple parsing strategies
   ```python
   # Strategy 1: Direct parse
   obj = json.loads(content)

   # Strategy 2: Extract from markdown
   json_match = re.search(r'```json\n(.*)\n```', content, re.DOTALL)

   # Strategy 3: Find first {...} block
   json_start = content.find('{')
   json_end = content.rfind('}') + 1
   ```

2. **Field Validation** - Use defaults for missing fields
   ```python
   result = {
       "field": obj.get("field", "default_value"),
       "score": obj.get("score", 5.0),  # Neutral default
       "list_field": list(obj.get("list_field", []))
   }
   ```

3. **Model Retry** - Fall back to simpler model on failure
   ```python
   try:
       response = call_model("gpt-4o")
   except Exception:
       response = call_model("gpt-4o-mini")  # Cheaper fallback
   ```

---

### Caching Strategy

**Cache Key:**
```python
import hashlib

def generate_cache_key(project_path: str, analysis_type: str) -> str:
    """Generate cache key based on file hashes"""
    file_hashes = []

    for file in relevant_files:
        content = file.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        file_hashes.append(file_hash)

    combined = f"{project_path}:{analysis_type}:{':'.join(sorted(file_hashes))}"
    return hashlib.sha256(combined.encode()).hexdigest()
```

**Invalidation Rules:**
- **Code change** - Any .py/.js/.ts file modified
- **Config change** - package.json, requirements.txt, Dockerfile
- **Doc change** - README.md, docs/ directory
- **Time-based** - Cache expires after 7 days

---

## Agent Zero Integration

### Workflow Submission

**Agent Zero Bridge** submits project audits to MCP-VIBE server for bonus scoring.

#### Available Workflows

**1. Code Review Workflow**
```python
{
    "workflow_type": "code_review",
    "context": {
        "language": "python",
        "files": ["file1.py", "file2.py"],
        "complexity_threshold": 10
    }
}
```
**Bonus:** +0.5 to Code Quality score

**2. Security Audit Workflow**
```python
{
    "workflow_type": "security_audit",
    "context": {
        "scan_dependencies": True,
        "check_secrets": True,
        "validate_inputs": True
    }
}
```
**Bonus:** +1.0 to Code Quality score (if passed)

**3. Architecture Review Workflow**
```python
{
    "workflow_type": "architecture_review",
    "context": {
        "pattern": "MVC",
        "modularity_threshold": 7
    }
}
```
**Bonus:** +0.5 to Borg.tools Fit score

**4. Deployment Check Workflow**
```python
{
    "workflow_type": "deployment_check",
    "context": {
        "platform": "docker",
        "validate_env": True
    }
}
```
**Bonus:** +1.0 to Deployment score (if deployable)

---

### Bonus Scoring Logic

```python
def calculate_bonus_score(workflow_results: Dict) -> float:
    """Calculate bonus score from Agent Zero workflows"""
    bonus = 0.0

    for workflow in workflow_results.get("workflows", []):
        if workflow["status"] == "success":
            bonus += workflow.get("bonus_points", 0)

        # Penalty for failures
        if workflow["status"] == "failed":
            bonus -= workflow.get("penalty_points", 0)

    # Cap bonus at ±2 points
    return max(-2.0, min(2.0, bonus))
```

---

### MCP-VIBE API Integration

**Endpoint:** `https://mcp.borg.tools/api/v1/audit`

**Request:**
```json
{
    "project_path": "/path/to/project",
    "workflows": ["code_review", "security_audit"],
    "context": {
        "language": "python",
        "complexity": {...},
        "security": {...}
    }
}
```

**Response:**
```json
{
    "audit_id": "uuid",
    "status": "completed",
    "workflows": [
        {
            "type": "code_review",
            "status": "success",
            "bonus_points": 0.5,
            "findings": [...]
        }
    ],
    "total_bonus": 0.5
}
```

---

## VibeSummary Structure

### Section-by-Section Breakdown

**VibeSummary.md** is a comprehensive markdown report with 15+ sections:

#### Header
```markdown
# VibeSummary: <project_name>

**Generated:** <timestamp>
**Project Path:** <path>
**Languages:** <lang1>, <lang2>
```

#### 1. Project Essence
- **What it does** - One-line description
- **Target Audience** - User personas
- **Problem Solved** - Value proposition
- **Current Stage** - idea/prototype/mvp/beta/prod

#### 2. Vibecodibility Scores
Table with 6 categories + overall score

#### 3. Architecture & Design
- **Pattern** - MVC, microservices, etc.
- **Modularity** - 0-10 score
- **Design Patterns** - Detected patterns
- **Complexity Metrics** - Cyclomatic, cognitive
- **Code Health** - Readability, docs, security
- **Technical Debt** - TODOs, FIXMEs, deprecated APIs

#### 4. Deployment Status
- **Deployment Type** - docker/k8s/serverless/etc.
- **Target Platform** - AWS/GCP/Heroku/etc.
- **Is Deployable** - YES/NO
- **Readiness Score** - 0-10
- **Deployment Artifacts** - Checklist
- **Environment Variables** - List with status
- **Deployment Blockers** - Critical issues

#### 5. MVP Checklist
- **Estimated Time to MVP** - Hours
- **Task List** - With priorities and time estimates

#### 6. Documentation Quality
- **Overall Score** - 0-10
- **Completeness** - Percentage
- **Accuracy** - Percentage
- **Found Documentation** - Files detected
- **Missing Sections** - What's needed

#### 7. Monetization Analysis
- **Market Viability** - 0-10
- **Monetization Strategy** - Model type
- **Revenue Potential** - Assessment
- **Target Market** - Description
- **Competitive Advantage** - Unique features

#### 8. Portfolio Suitability
- **Suitable** - YES/NO
- **Why/Why Not** - Explanation

#### 9. Actionable Next Steps
Prioritized tasks in 3 tiers:
- **Priority 1: Critical** - Must-do (HIGH impact, BLOCKING)
- **Priority 2: High Impact** - Should-do (HIGH impact, not blocking)
- **Priority 3: Quick Wins** - Nice-to-do (LOW effort, visible results)

#### 10. AI Acceleration Opportunities
Suggested AI-assisted tasks with:
- **Documentation Generation** - Auto-generate missing sections
- **Deployment Setup** - Generate Dockerfile
- **Test Generation** - Create test suites
- **Code Refactoring** - Complexity reduction

#### 11. Borg.tools Integration
- **Fit Score** - 0-10
- **Integration Opportunities** - MCP-VIBE suggestions
- **Deployment Instructions** - Platform-specific commands

#### 12. Raw Analysis Data
Expandable `<details>` section with full JSON outputs from:
- Code Quality Metrics
- Deployment Analysis
- Documentation Analysis
- LLM Analysis (all 4 models)

---

### Generation Algorithm

```python
def generate_vibesummary(project_data: Dict) -> str:
    """Generate VibeSummary.md from all analysis data"""

    sections = []

    # Header
    sections.append(format_header(project_data))

    # Scores table
    sections.append(format_scores_table(project_data["scores"]))

    # Architecture
    sections.append(format_architecture(project_data["code_analysis"]))

    # Deployment
    sections.append(format_deployment(project_data["deployment"]))

    # Documentation
    sections.append(format_documentation(project_data["docs"]))

    # LLM insights
    sections.append(format_llm_insights(project_data["llm"]))

    # Actionable tasks
    sections.append(format_next_steps(project_data["todos"]))

    # Raw data
    sections.append(format_raw_data(project_data))

    return "\n\n---\n\n".join(sections)
```

---

## Cache System

### SQLite Schema

```sql
CREATE TABLE llm_cache (
    cache_key TEXT PRIMARY KEY,
    project_path TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    response TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    file_hashes TEXT,
    hit_count INTEGER DEFAULT 0
);

CREATE INDEX idx_project_path ON llm_cache(project_path);
CREATE INDEX idx_analysis_type ON llm_cache(analysis_type);
CREATE INDEX idx_expires_at ON llm_cache(expires_at);
```

### Cache Operations

**Write:**
```python
def cache_response(key: str, response: str, ttl: int = 604800):
    """Cache LLM response for 7 days"""
    expires_at = datetime.now() + timedelta(seconds=ttl)

    cursor.execute("""
        INSERT OR REPLACE INTO llm_cache
        (cache_key, project_path, analysis_type, response, model, expires_at, file_hashes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (key, project_path, analysis_type, response, model, expires_at, file_hashes))
```

**Read:**
```python
def get_cached_response(key: str) -> Optional[str]:
    """Retrieve cached response if valid"""
    cursor.execute("""
        SELECT response, expires_at, file_hashes
        FROM llm_cache
        WHERE cache_key = ?
    """, (key,))

    row = cursor.fetchone()
    if not row:
        return None

    response, expires_at, cached_hashes = row

    # Check expiration
    if datetime.now() > expires_at:
        return None

    # Validate file hashes
    current_hashes = compute_file_hashes(project_path)
    if current_hashes != cached_hashes:
        return None

    # Update hit count
    cursor.execute("UPDATE llm_cache SET hit_count = hit_count + 1 WHERE cache_key = ?", (key,))

    return response
```

**Cleanup:**
```python
def cleanup_expired_cache():
    """Remove expired entries"""
    cursor.execute("DELETE FROM llm_cache WHERE expires_at < ?", (datetime.now(),))
```

---

### Invalidation Rules

**Automatic Invalidation:**
- File content change (hash mismatch)
- TTL expiration (7 days default)
- Manual purge

**File Monitoring:**
```python
WATCHED_PATTERNS = [
    "**/*.py",
    "**/*.js",
    "**/*.ts",
    "**/package.json",
    "**/requirements.txt",
    "**/Dockerfile",
    "**/README.md"
]
```

---

## Deployment Detection Logic

### Heuristics

**1. Docker Detection**
```python
if (project_path / "Dockerfile").exists():
    deployment_type = "docker"

    # Check for multi-stage builds
    content = read_dockerfile()
    if "FROM" in content and content.count("FROM") > 1:
        patterns.append("multi-stage")
```

**2. Kubernetes Detection**
```python
k8s_files = [
    "k8s/",
    "kubernetes/",
    "deployment.yaml",
    "service.yaml"
]

if any((project_path / f).exists() for f in k8s_files):
    deployment_type = "kubernetes"
```

**3. Serverless Detection**
```python
serverless_hints = {
    "serverless.yml": "serverless_framework",
    "template.yaml": "aws_sam",
    "app.yaml": "google_app_engine",
    ".netlify/": "netlify",
    "vercel.json": "vercel"
}
```

**4. Traditional Detection**
```python
if (project_path / "systemd").exists() or \
   (project_path / "init.d").exists():
    deployment_type = "traditional"
```

---

### Platform Inference

**Cloud Provider Detection:**
```python
def infer_platform(deployment_config: Dict) -> str:
    """Infer cloud platform from config files"""

    # AWS
    if "Dockerrun.aws.json" in files:
        return "aws_elastic_beanstalk"
    if ".ebextensions/" in dirs:
        return "aws_elastic_beanstalk"
    if "task-definition.json" in files:
        return "aws_ecs"

    # Google Cloud
    if "app.yaml" in files:
        return "google_app_engine"
    if "cloudbuild.yaml" in files:
        return "google_cloud_build"

    # Heroku
    if "Procfile" in files:
        return "heroku"

    # Vercel/Netlify
    if "vercel.json" in files:
        return "vercel"
    if "_redirects" in files or "netlify.toml" in files:
        return "netlify"

    return "unknown"
```

---

## Extension Guide

### Adding New Languages

**1. Add File Patterns**
```python
# In borg_tools_scan.py
RUBY_FILES = {"Gemfile", "Gemfile.lock", "Rakefile"}

def detect_languages(p: Path) -> List[str]:
    langs = set()

    # Add Ruby detection
    if any(n in names for n in RUBY_FILES) or \
       any(str(f).endswith(".rb") for f in p.rglob("*.rb")):
        langs.add("ruby")

    return sorted(langs)
```

**2. Add Dependency Parser**
```python
def parse_deps(p: Path) -> Dict[str, List[str]]:
    deps = {}

    # Ruby gems
    gemfile = p / "Gemfile"
    if gemfile.exists():
        lines = gemfile.read_text().splitlines()
        gems = []
        for line in lines:
            if line.strip().startswith("gem"):
                gem_name = re.search(r"gem ['\"](.+?)['\"]", line)
                if gem_name:
                    gems.append(gem_name.group(1))
        deps["ruby"] = gems

    return deps
```

**3. Update Code Analyzer**
```python
# In modules/code_analyzer.py
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
    "ruby": [".rb"],  # Add new language
}
```

---

### Adding Custom Prompts

**1. Create Prompt File**
```bash
# prompts/custom_model_prompt.md
You are a specialist in {specialty}.

Analyze the project based on:
{context}

Return JSON with:
{
  "analysis": "string",
  "score": 0-10,
  "recommendations": ["item1", "item2"]
}
```

**2. Register in Orchestrator**
```python
# In modules/llm_orchestrator.py
PROMPT_TEMPLATES = {
    "architect": "prompts/architect_prompt.md",
    "business": "prompts/business_prompt.md",
    "deployment": "prompts/deployment_prompt.md",
    "aggregator": "prompts/aggregator_prompt.md",
    "custom": "prompts/custom_model_prompt.md",  # Add custom
}

def analyze_project(self, project_data: Dict) -> Dict:
    responses = {}

    # Add custom model call
    responses["custom"] = self._call_model(
        prompt=self._load_prompt("custom", project_data),
        temperature=0.3
    )

    return responses
```

---

### Creating Custom Analyzers

**Template:**
```python
# modules/my_analyzer.py
from pathlib import Path
from typing import Dict, List

def analyze_feature(
    project_path: str,
    languages: List[str],
    facts: Dict
) -> Dict:
    """
    Analyze custom feature

    Args:
        project_path: Absolute path to project
        languages: List of detected languages
        facts: Project metadata

    Returns:
        {
            "score": float,  # 0-10
            "details": {},
            "suggestions": []
        }
    """
    p = Path(project_path)

    # Your analysis logic
    score = calculate_custom_score(p)

    return {
        "score": score,
        "details": {
            "metric1": value1,
            "metric2": value2
        },
        "suggestions": [
            "Do this to improve",
            "Consider that"
        ]
    }

def calculate_custom_score(p: Path) -> float:
    """Calculate score based on custom criteria"""
    # Implementation
    return 7.5
```

**Integration:**
```python
# In main scanner
from modules.my_analyzer import analyze_feature

# Add to analysis pipeline
custom_analysis = analyze_feature(
    project_path=str(project_path),
    languages=detected_languages,
    facts=project_facts
)

# Include in VibeSummary
vibesummary_data["custom"] = custom_analysis
```

---

## Performance Optimization

### Parallel Execution

**Async LLM Calls:**
```python
import asyncio

async def analyze_all_models(project_data: Dict) -> Dict:
    """Execute all 4 models in parallel"""
    tasks = [
        call_model_async("architect", project_data),
        call_model_async("business", project_data),
        call_model_async("deployment", project_data),
        call_model_async("aggregator", project_data)
    ]

    results = await asyncio.gather(*tasks)
    return dict(zip(["architect", "business", "deployment", "aggregator"], results))
```

**File Processing:**
```python
from concurrent.futures import ThreadPoolExecutor

def analyze_files_parallel(files: List[Path]) -> List[Dict]:
    """Process files in parallel"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(analyze_file, files))
    return results
```

---

## Troubleshooting

### Common Issues

**1. LLM API Errors**
```python
# Solution: Implement exponential backoff
import time

def call_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)
```

**2. Cache Corruption**
```bash
# Clear cache manually
rm -f ~/.borg_tools_cache.db
```

**3. JSON Parsing Failures**
```python
# Enable debug mode
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**Created by The Collective Borg.tools**
**Version:** 2.0.0
**Last Updated:** 2025-10-25
