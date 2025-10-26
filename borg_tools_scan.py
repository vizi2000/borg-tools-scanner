#!/usr/bin/env python3
"""
Borg Tools – Project Scanner (single-file MVP)

What it does (offline, local, zero external deps):
- Scans a root directory for projects (top-level subfolders)
- Collects facts: language(s), presence of README/tests/CI/LICENSE, git stats, TODO/FIXME, basic deps
- Scores each project: stage, value_score, risk_score, priority
- Generates suggestions:
    * Heuristic (no LLM) — always available
    * Optional LLM: if env vars are set (OPENAI_API_KEY etc.), will ask an LLM to refine TODOs/next steps
- Produces outputs:
    * ./BORG_INDEX.md – portfolio dashboard
    * ./borg_dashboard.csv – table view
    * ./borg_dashboard.json – machine-readable summary
    * per-project REPORT.md files within each project folder

Run:
    python borg_tools_scan.py --root ~/Projects [--use-llm openai] [--model gpt-5-thinking]

Notes:
- Git stats are gathered if the folder is a git repo.
- No internet used unless you pass --use-llm and have API keys set.
- Designed to be fast, robust, and ADHD-friendly: focuses on Top 5 "90‑minute tasks".
"""

from __future__ import annotations
import argparse
import asyncio
import dataclasses
import datetime as dt
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import new v2.0 modules
from modules.code_analyzer import analyze_code
from modules.deployment_detector import detect_deployment
from modules.doc_analyzer import analyze_documentation
from modules.llm_orchestrator import analyze_with_llm
from modules.vibesummary_generator import generate_vibesummary
from modules.progress_reporter import ProgressReporter
from modules.agent_zero_bridge import AgentZeroBridge, create_bridge
from modules.agent_zero_auditor import AgentZeroAuditor, calculate_bonus_score
from modules.cache_manager import CacheManager, get_cache_manager

# ----------------------------- Utilities -----------------------------

NOW = dt.datetime.now()
DAY = dt.timedelta(days=1)

TEST_DIR_NAMES = {"tests", "test", "__tests__"}
CI_HINTS = {".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml", "circleci", ".circleci"}
PY_FILES = {"pyproject.toml", "requirements.txt", "requirements.in", "Pipfile"}
JS_FILES = {"package.json", "pnpm-lock.yaml", "package-lock.json", "yarn.lock"}
RUST_FILES = {"Cargo.toml"}
GO_FILES = {"go.mod"}
LICENSE_HINTS = {"LICENSE", "LICENSE.md", "LICENSE.txt"}
README_HINTS = {"README.md", "README", "readme.md"}

SAFE_IGNORE_PATTERNS = [
    r"\.venv/", r"node_modules/", r"\.git/", r"\.idea/", r"\.vscode/",
    r"dist/", r"build/", r"\.DS_Store", r"\.env", r"\.env\.local", r"\.pem$", r"id_rsa$",
]
SAFE_IGNORE_RE = re.compile("|".join(SAFE_IGNORE_PATTERNS))

TODO_FIXME_RE = re.compile(r"(?i)\b(TODO|FIXME|BUG|HACK)\b[^\n\r]*")

BINARY_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    # Videos
    '.mp4', '.mkv', '.avi', '.mov', '.webm',
    # Audio
    '.mp3', '.wav', '.ogg', '.flac',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # System/Executables
    '.iso', '.img', '.bin', '.exe', '.dll', '.so', '.dmg', '.jar',
    # Other
    '.pyc', '.pyd', '.egg', '.whl',
}


# ----------------------------- Data Models -----------------------------

@dataclasses.dataclass
class Facts:
    name: str
    path: str
    languages: List[str]
    has_readme: bool
    has_license: bool
    has_tests: bool
    has_ci: bool
    last_commit_dt: Optional[str]
    commits_count: int
    branches_count: int
    todos: List[str]
    deps: Dict[str, List[str]]  # { eco: [deps] }

@dataclasses.dataclass
class Scores:
    stage: str
    value_score: int
    risk_score: int
    priority: int
    fundamental_errors: List[str]

@dataclasses.dataclass
class Suggestions:
    todo_now: List[str]
    todo_next: List[str]
    rationale: str
    confidence: float
    ai_accel: List[str]
    skills_tags: List[str]
    # New LLM-audit fields
    description: str = ""
    declared_vs_actual: str = ""
    structure_summary: str = ""
    best_practices: List[str] = dataclasses.field(default_factory=list)
    vibe_notes: str = ""
    # Business & Career Analysis
    problem_solved: str = ""
    monetization_potential: str = ""
    mvp_launch_todo: List[str] = dataclasses.field(default_factory=list)
    frontend_todo: List[str] = dataclasses.field(default_factory=list)
    portfolio_suitable: bool = False
    portfolio_description: str = ""
    # New similarity analysis fields
    functional_tags: List[str] = dataclasses.field(default_factory=list)
    similar_projects: List[str] = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class ProjectSummary:
    facts: Facts
    scores: Scores
    suggestions: Suggestions

# ----------------------------- Detection -----------------------------

def list_projects(root: Path) -> List[Path]:
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    return [p for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith(('.', '_')) and p != script_dir]


def detect_languages(p: Path) -> List[str]:
    langs = set()
    names = {f.name for f in p.glob("*.* ")} | {f.name for f in p.glob("**/*.* ")}
    if any(n in names for n in PY_FILES) or any(str(f).endswith(".py") for f in p.rglob("*.py")):
        langs.add("python")
    if any(n in names for n in JS_FILES) or any(str(f).endswith((".js", ".ts", ".tsx")) for f in p.rglob("* ")):
        # don't double-count from random assets; presence of package.json is strongest
        if "package.json" in names:
            langs.add("nodejs")
        else:
            langs.add("javascript-typescript")
    if any(n in names for n in RUST_FILES) or any(str(f).endswith(".rs") for f in p.rglob("*.rs")):
        langs.add("rust")
    if any(n in names for n in GO_FILES) or any(str(f).endswith(".go") for f in p.rglob("*.go")):
        langs.add("go")
    if any(str(f).endswith((".java",)) for f in p.rglob("*.java")):
        langs.add('java')
    if any(str(f).endswith((".swift",)) for f in p.rglob("*.swift")):
        langs.add('swift')
    if not langs:
        # fallback heuristic by file mix
        if any(str(f).endswith((".sh",)) for f in p.rglob("*.sh")):
            langs.add('bash')
    return sorted(langs)


def has_any(p: Path, hints: set[str]) -> bool:
    for h in hints:
        if (p / h).exists():
            return True
    return False


def detect_tests(p: Path) -> bool:
    for name in TEST_DIR_NAMES:
        if (p / name).exists():
            return True
    # simple heuristic: any *_test.* files
    for f in p.rglob("*test*.py"):
        return True
    for f in p.rglob("*.spec.*"):
        return True
    return False


def gather_git_stats(p: Path) -> Tuple[Optional[str], int, int]:
    if not (p / ".git").exists():
        return None, 0, 0
    def run(cmd: List[str]) -> str:
        try:
            out = subprocess.check_output(cmd, cwd=p, stderr=subprocess.DEVNULL)
            return out.decode().strip()
        except Exception:
            return ""
    last_commit_ts = run(["git", "log", "-1", "--format=%ct"]) or None
    last_commit_dt = None
    if last_commit_ts:
        try:
            last_commit_dt = dt.datetime.fromtimestamp(int(last_commit_ts)).isoformat()
        except Exception:
            last_commit_dt = None
    commits = 0
    c = run(["git", "rev-list", "--count", "HEAD"]) or "0"
    try:
        commits = int(c)
    except Exception:
        commits = 0
    branches = 0
    b = run(["git", "branch", "--list"]) or ""
    if b:
        branches = len([line for line in b.splitlines() if line.strip()])
    return last_commit_dt, commits, branches


def collect_todos(p: Path, max_per_file: int = 3, max_total: int = 50) -> List[str]:
    todos: List[str] = []
    
    try:
        files_to_scan = list(p.rglob("*.* "))
    except Exception as e:
        print(f"  [WARN] Could not list files in {p}: {e}")
        return todos

    for file in files_to_scan:
        rel_path_str = str(file.relative_to(p))

        if SAFE_IGNORE_RE.search(rel_path_str):
            continue
        
        if file.suffix.lower() in BINARY_EXTENSIONS:
            continue

        try:
            if file.stat().st_size > 5 * 1024 * 1024:  # 5 MB limit
                continue
        except (OSError, FileNotFoundError):
            continue

        try:
            text = file.read_text(errors="ignore")
            # Basic check if it's still a binary file we tried to read
            if '\0' in text:
                continue
        except Exception:
            continue
        
        try:
            # Using finditer for better memory usage than findall on large files
            matches_found = 0
            for m in re.finditer(r".*(?i)(TODO|FIXME|BUG|HACK)[^\n\r]*", text):
                line = m.group(0).strip()
                if line:
                    todos.append(f"{rel_path_str}: {line[:200]}")
                    matches_found += 1
                    if len(todos) >= max_total:
                        return todos
            if matches_found >= max_per_file:
                continue # Move to next file
        except Exception:
            continue
            
    return todos


def parse_deps(p: Path) -> Dict[str, List[str]]:
    deps: Dict[str, List[str]] = {}
    # Python
    for fname in PY_FILES:
        fp = p / fname
        if fp.exists():
            try:
                lines = fp.read_text(errors="ignore").splitlines()
                pkgs = []
                for ln in lines:
                    ln = ln.strip()
                    if not ln or ln.startswith(("#", "[", "url", "path")):
                        continue
                    if "=" in ln and fname == 'pyproject.toml':
                        # ignore toml sections
                        continue
                    # crude split
                    pkg = re.split(r"[<>=~!;[\] ]", ln)[0]
                    if pkg and re.match(r"^[A-Za-z0-9_.-]+$", pkg):
                        pkgs.append(pkg)
                if pkgs:
                    deps.setdefault('python', []).extend(sorted(set(pkgs))[:50])
            except Exception:
                pass
    # Node
    pkgjson = p / 'package.json'
    if pkgjson.exists():
        try:
            data = json.loads(pkgjson.read_text(errors='ignore'))
            node_deps = []
            for k in ('dependencies', 'devDependencies'):
                d = data.get(k) or {}
                node_deps.extend(list(d.keys()))
            if node_deps:
                deps.setdefault('node', []).extend(sorted(set(node_deps))[:50])
        except Exception:
            pass
    return deps

# ----------------------------- Scoring -----------------------------

def classify_stage(f: Facts) -> str:
    # Highest satisfied wins
    last_days = 9999
    if f.last_commit_dt:
        try:
            last_days = (NOW - dt.datetime.fromisoformat(f.last_commit_dt)).days
        except Exception:
            pass
    has_release_tag = False  # advanced: could parse tags; left false in MVP

    if has_release_tag and f.has_tests and f.has_ci:
        return 'prod'
    if f.has_tests and (f.has_ci or 'python' in f.languages or 'nodejs' in f.languages):
        return 'beta'
    if f.commits_count >= 5 and f.has_readme:
        return 'mvp'
    if f.commits_count >= 1:
        return 'prototype'
    if last_days > 90 and f.commits_count > 0:
        return 'abandoned'
    return 'idea'


def score_value(f: Facts) -> int:
    score = 0
    # heuristics for value
    if f.has_readme:
        score += 1
    if 'node' in f.deps or 'python' in f.deps:
        score += 1  # reuse potential as lib/app
    if f.has_tests:
        score += 2
    if f.has_ci:
        score += 2
    if f.commits_count >= 20:
        score += 2
    if f.branches_count >= 2:
        score += 1
    # penalties
    if not f.has_readme:
        score -= 1
    if not f.has_tests and f.commits_count >= 10:
        score -= 2
    if not f.has_ci and f.commits_count >= 10:
        score -= 2
    # clamp 0..10
    return max(0, min(10, score))


def score_risk(f: Facts) -> int:
    risk = 0
    if not f.has_tests:
        risk += 3
    if not f.has_ci:
        risk += 2
    if not f.has_license:
        risk += 1
    if len(f.todos) > 20:
        risk += 2
    if f.last_commit_dt:
        try:
            days = (NOW - dt.datetime.fromisoformat(f.last_commit_dt)).days
            if days > 90:
                risk += 2
            elif days > 30:
                risk += 1
        except Exception:
            pass
    return max(0, min(10, risk))


def fundamental_errors(f: Facts) -> List[str]:
    errs = []
    if not f.has_readme:
        errs.append('brak README')
    if not f.has_tests:
        errs.append('brak testów')
    if not f.has_ci:
        errs.append('brak CI')
    if not f.has_license:
        errs.append('brak LICENSE')
    if any('API_KEY' in t or 'SECRET' in t for t in f.todos):
        errs.append('możliwe sekrety w TODO/FIXME – sprawdź .env')
    return errs


def compute_priority(value: int, risk: int, last_commit_dt: Optional[str]) -> int:
    bonus = 0
    if last_commit_dt:
        try:
            days = (NOW - dt.datetime.fromisoformat(last_commit_dt)).days
            if days <= 14:
                bonus += 1
        except Exception:
            pass
    pr = round(1.5 * value - 1.0 * risk + bonus)
    return int(max(0, min(20, pr)))

# ----------------------------- Skills & AI acceleration -----------------------------

def infer_skills(f: Facts) -> List[str]:
    skills = set()
    for lang in f.languages:
        skills.add(lang)
    if 'python' in f.languages:
        skills.update({'pytest', 'poetry/pip', 'pandas?'})
    if 'node' in f.deps or 'nodejs' in f.languages:
        if 'node' in f.deps:
            pkgs = set(f.deps['node'])
            if 'react' in pkgs or any(x in pkgs for x in ('next', 'nextjs', '@types/react')):
                skills.add('react/next')
            if 'express' in pkgs:
                skills.add('express')
            if 'typescript' in pkgs or any(x.endswith('types') for x in pkgs):
                skills.add('typescript')
    if f.has_ci:
        skills.add('ci/cd')
    if f.has_tests:
        skills.add('testing')
    return sorted(skills)


def ai_acceleration_suggestions(f: Facts, scores: Scores) -> List[str]:
    tips = []
    # Focus: biggest leverage in 90 minutes
    if not f.has_tests:
        tips.append('Użyj LLM do wygenerowania szkielety testów jednostkowych dla kluczowych modułów (max 5 plików).')
    if not f.has_ci:
        tips.append('Wygeneruj minimalny workflow CI (pytest/jest + lint) i dodaj badge do README.')
    if not f.has_readme:
        tips.append('Poproś LLM o wygenerowanie README z sekcjami: quickstart, scripts, architektura, TODO.')
    if 'python' in f.languages and 'python' in f.deps:
        tips.append('Automatyczne stuby typów i refaktor: użyj LLM do dodania type hints w głównych modułach.')
    if 'node' in f.deps:
        tips.append('Przejdź `package.json` z LLM i wygeneruj skrypty: build, test, lint, release.')
    if f.todos:
        tips.append('Zgrupuj TODO/FIXME tematycznie z pomocą LLM i utwórz 5 zadań „now”.')
    if not tips:
        tips.append('Poproś LLM o audyt struktury katalogów i propozycję 3 usprawnień DX.')
    return tips[:5]

# ----------------------------- Structure snapshot helpers -----------------------------

def build_structure_snapshot(p: Path, max_items_per_dir: int = 8) -> str:
    lines = []
    for child in sorted(p.iterdir()):
        if child.name.startswith('.'):
            continue
        if child.is_dir():
            subitems = [c.name for c in sorted(child.iterdir()) if not c.name.startswith('.')][:max_items_per_dir]
            lines.append(f"/{child.name}/ -> {len(subitems)} items: {', '.join(subitems)}")
        else:
            lines.append(child.name)
        if len(lines) >= 40:
            break
    # key config files
    cfgs = []
    for fname in list(PY_FILES | JS_FILES | RUST_FILES | GO_FILES | LICENSE_HINTS | README_HINTS | CI_HINTS):
        if (p / fname).exists():
            cfgs.append(fname)
    if cfgs:
        lines.append("CONFIGS: " + ", ".join(sorted(set(cfgs))))
    return "\n".join(lines[:80])

# ----------------------------- LLM integration -----------------------------

def refine_with_llm(base: Suggestions, f: Facts, s: Scores, provider: Optional[str], model: Optional[str]) -> Suggestions:
    """LLM-powered refinement of suggestions using OpenRouter or OpenAI"""
    if not provider:
        return base

    try:
        p = Path(f.path)
        extras = {
            'readme': '',
            'package_json': '',
            'pyproject': '',
            'structure': build_structure_snapshot(p),
        }

        # Collect sample content from key files
        for key, fname in [('readme', 'README.md'), ('package_json', 'package.json'), ('pyproject', 'pyproject.toml')]:
            fp = p / fname
            if fp.exists():
                try:
                    extras[key] = fp.read_text(encoding='utf-8', errors='ignore')[:4000]
                except Exception:
                    pass

        # Prepare prompt
        prompt = f"""
Na podstawie FAKTÓW o projekcie przygotuj WSZYSTKIE wymienione pola:

FAKTY TECHNICZNE: {json.dumps(dataclasses.asdict(f), ensure_ascii=False)[:8000]}
OCENY PROJEKTU: {json.dumps(dataclasses.asdict(s), ensure_ascii=False)}

ZAWARTOŚĆ PLIKÓW:
README: {extras['readme']}

STRUKTURA PROJEKTU:
{extras['structure']}

ZALEŻNOŚCI:
{json.dumps(f.deps, ensure_ascii=False)}

TODOs:
{json.dumps(f.todos, ensure_ascii=False)}

Zwróć TYLKO valid JSON z polami: description, declared_vs_actual, structure_summary, best_practices, vibe_notes, problem_solved, monetization_potential, mvp_launch_todo, frontend_todo, portfolio_suitable, portfolio_description, functional_tags.
""".strip()

        if provider.lower() == 'openai':
            import urllib.request
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return base

            payload = json.dumps({
                "model": model or "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }).encode('utf-8')

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                method="POST",
                data=payload,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
            )

            content = data['choices'][0]['message']['content']
            obj = {}
            json_content = content
            try:
                obj = json.loads(json_content) # Try to parse the whole content first
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract a JSON block
                json_match = re.search(r'```json\n(.*)\n```', content, re.DOTALL) # Specific markdown
                if json_match:
                    json_content = json_match.group(1)
                else:
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL) # General JSON object
                    if json_match:
                        json_content = json_match.group(1)
                    else:
                        # Fallback to finding first { and last }
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_content = content[json_start:json_end]
                        else:
                            json_content = "{}" # Default to empty JSON if nothing found
                try:
                    obj = json.loads(json_content)
                except json.JSONDecodeError as e:
                    print(f"  [LLM] JSON Decode Error for {p.name}: {e} - Content: {json_content[:500]}...")
                    return base # Return base suggestions on JSON error
            except Exception as e:
                print(f"  [LLM] Unexpected error during JSON parsing for {p.name}: {e}")
                return base # Return base suggestions on other errors

        elif provider.lower() == 'openrouter':
            import urllib.request
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                return base

            payload = json.dumps({
                "model": model or "anthropic/claude-3-haiku:beta",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "reasoning_enabled": True
            }).encode('utf-8')

            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                method="POST",
                data=payload,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://borg-tools',
                    'X-Title': 'Borg Tools Scanner'
                }
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            content = data['choices'][0]['message']['content']
            # Extract JSON from response if wrapped in markdown or text
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            # Try to find JSON object in response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                obj = json.loads(json_content)
            else:
                # Fallback to direct parsing
                obj = json.loads(content)

        else:
            return base

        # Apply LLM insights
        return Suggestions(
            todo_now=base.todo_now,
            todo_next=base.todo_next,
            rationale=base.rationale,
            confidence=base.confidence,
            ai_accel=base.ai_accel,
            skills_tags=base.skills_tags,
            description=obj.get('description', ''),
            declared_vs_actual=obj.get('declared_vs_actual', ''),
            structure_summary=obj.get('structure_summary', ''),
            best_practices=list(obj.get('best_practices', []))[:5],
            vibe_notes=obj.get('vibe_notes', ''),
            problem_solved=obj.get('problem_solved', ''),
            monetization_potential=obj.get('monetization_potential', ''),
            mvp_launch_todo=list(obj.get('mvp_launch_todo', []))[:8],
            frontend_todo=list(obj.get('frontend_todo', []))[:6],
            portfolio_suitable=obj.get('portfolio_suitable', False),
            portfolio_description=obj.get('portfolio_description', ''),
            functional_tags=list(obj.get('functional_tags', []))
        )

    except Exception as e:
        # If LLM fails, return base suggestions
        print(f"[LLM] Failed to refine suggestions for {p.name}: {e}")
        return base

# ----------------------------- Suggestions (Heuristic only) -----------------------------

def heuristic_suggestions(f: Facts, s: Scores) -> Suggestions:
    todo_now: List[str] = []
    todo_next: List[str] = []

    # Fundamental first
    if 'brak README' in s.fundamental_errors:
        todo_now.append('Dodaj README: cel, instalacja, uruchomienie, testy, struktura.')
    if 'brak testów' in s.fundamental_errors:
        todo_now.append('Dodaj minimalne testy jednostkowe (1-2 pliki) dla krytycznych funkcji.')
    if 'brak CI' in s.fundamental_errors:
        todo_now.append('Dodaj prosty workflow CI (lint + test).')
    if 'brak LICENSE' in s.fundamental_errors:
        todo_next.append('Dodaj LICENSE (MIT/Apache-2.0).')

    if not todo_now:
        todo_now.append('Utwórz listę 5 zadań na najbliższe 90 minut (małe, atomowe).')

    # Next steps based on stage
    if s.stage in ('idea', 'prototype'):
        todo_next.append('Zamknij pętlę E2E: działający przykład od wejścia do wyniku.')
    if s.stage == 'mvp':
        todo_next.append('Stabilizacja: testy krytyczne + minimalny monitoring.')
    if s.stage == 'beta':
        todo_next.append('Automatyzuj release (semver + changelog).')

    rationale = 'Zadania priorytetyzowane pod największą dźwignię w 90 minut, najpierw błędy fundamentalne.'
    skills_tags = infer_skills(f)
    ai_accel = ai_acceleration_suggestions(f, s)

    return Suggestions(
        todo_now=todo_now[:5],
        todo_next=todo_next[:5],
        rationale=rationale,
        confidence=0.6,
        ai_accel=ai_accel,
        skills_tags=skills_tags,
        description="",
        declared_vs_actual="",
        structure_summary="",
        best_practices=[],
        vibe_notes="",
    )

# ----------------------------- Rendering -----------------------------

def render_report_md(ps: ProjectSummary) -> str:
    f, s, g = ps.facts, ps.scores, ps.suggestions
    last = f.last_commit_dt or "brak"
    todos = "\n".join(f"- {t}" for t in f.todos[:20]) if f.todos else "(brak)"
    deps_py = ", ".join(f.deps.get('python', [])[:20]) or "(brak)"
    deps_js = ", ".join(f.deps.get('node', [])[:20]) or "(brak)"

    return textwrap.dedent(f"""
    # {f.name}

    **Ścieżka:** `{f.path}`  
    **Języki:** {', '.join(f.languages) or '(nie wykryto)'}  
    **Ostatni commit:** {last}  
    **Commity/gałęzie:** {f.commits_count}/{f.branches_count}  

    ## Etap i ocena
    - **Etap:** {s.stage}
    - **Value:** {s.value_score}/10
    - **Risk:** {s.risk_score}/10
    - **Priority:** {s.priority}/20
    - **Fundamentalne błędy:** {', '.join(s.fundamental_errors) or '(brak)'}

    ## Fakty
    - README: {"TAK" if f.has_readme else "NIE"}
    - LICENSE: {"TAK" if f.has_license else "NIE"}
    - Testy: {"TAK" if f.has_tests else "NIE"}
    - CI: {"TAK" if f.has_ci else "NIE"}
    - TODO/FIXME (próbka):
    {todos}

    ### Zależności (skrót)
    - Python: {deps_py}
    - Node: {deps_js}

    ## Umiejętności / tagi
    {', '.join(g.skills_tags) or '(brak)'}

    ## AI Acceleration – najlepsze kroki
    {os.linesep.join('- ' + t for t in g.ai_accel)}

    ## TODO – na dziś (45–90 min)
    {os.linesep.join('- ' + t for t in g.todo_now)}

    ## TODO – następne (1–2 dni)
    {os.linesep.join('- ' + t for t in g.todo_next)}

    **Uzasadnienie:** {g.rationale}

    ---

    ## Opis projektu (LLM)
    {g.description or '(brak / LLM wyłączony)'}

    ## Deklarowane funkcje vs. zastane w kodzie (LLM)
    {g.declared_vs_actual or '(brak / LLM wyłączony)'}

    ## Struktura projektu (snapshot)
    {g.structure_summary or '(brak / LLM wyłączony)'}

    ## Best practices – checklist
    {os.linesep.join('- [x] ' + bp if isinstance(bp, str) else '- [ ] ' + str(bp) for bp in (g.best_practices or [])) or '(brak / LLM wyłączony)'}

    ## "Vibe" kodowania – notatki
    {g.vibe_notes or '(brak / LLM wyłączony)'}

    ---

    ## Problem jaki rozwiązuje projekt (LLM)
    {g.problem_solved or '(brak / LLM wyłączony)'}

    ## Potencjał monetyzacji (LLM)
    {g.monetization_potential or '(brak / LLM wyłączony)'}

    ## Realna lista TODO do uruchomienia MVP (LLM)
    {os.linesep.join('- ' + todo for todo in (g.mvp_launch_todo or [])) or '(brak / LLM wyłączony)'}

    ## Frontend TODO list (LLM)
    {os.linesep.join('- ' + todo for todo in (g.frontend_todo or [])) or '(brak / LLM wyłączony)'}

    ## Portfolio suitability (LLM)
    - **Nadaje się do portfolio:** {"TAK" if g.portfolio_suitable else "NIE"}

    ## Portfolio description (świadectwo umiejętności) (LLM)
    {g.portfolio_description or '(brak / LLM wyłączony)'}

    ---

    ## Podobne Projekty (LLM)
    {os.linesep.join('- ' + p for p in g.similar_projects) or '(brak)'}
    """)


def render_index_md(rows: List[ProjectSummary]) -> str:
    header = "| Projekt | Stage | Value | Risk | Priority | Last Commit | Błędy |\n|---|---|---:|---:|---:|---|---|"
    lines = [header]
    for ps in rows:
        f, s = ps.facts, ps.scores
        last = f.last_commit_dt.split('T')[0] if f.last_commit_dt else "—"
        errs = ", ".join(s.fundamental_errors) if s.fundamental_errors else "—"
        lines.append(f"| {f.name} | {s.stage} | {s.value_score} | {s.risk_score} | {s.priority} | {last} | {errs} |")
    return "\n".join(["# Borg Tools – INDEX", "", *lines, "", "_autogenerated_"])

# ----------------------------- Main pipeline -----------------------------

def scan_project(p: Path, args=None, reporter=None, cache_manager=None) -> ProjectSummary:
    """
    v2.0 Enhanced project scanner with deep analysis and LLM orchestration

    Args:
        p: Project path
        args: CLI arguments (for --deep-scan, --skip-llm, --use-agent-zero)
        reporter: ProgressReporter instance for UI updates
        cache_manager: CacheManager instance for --resume support

    Returns:
        ProjectSummary with extended analysis data
    """
    name = p.name

    # Report progress
    if reporter:
        reporter.log_step("🔍", f"Starting scan of {name}...")

    # Step 1: Basic fact gathering (unchanged from v1)
    langs = detect_languages(p)
    facts = Facts(
        name=name,
        path=str(p),
        languages=langs,
        has_readme=has_any(p, README_HINTS),
        has_license=has_any(p, LICENSE_HINTS),
        has_tests=detect_tests(p),
        has_ci=has_any(p, CI_HINTS),
        last_commit_dt=None,
        commits_count=0,
        branches_count=0,
        todos=[],
        deps=parse_deps(p),
    )
    last_dt, commits, branches = gather_git_stats(p)
    facts.last_commit_dt = last_dt
    facts.commits_count = commits
    facts.branches_count = branches
    facts.todos = collect_todos(p)

    if reporter:
        reporter.log_step("✅", f"Basic facts gathered: {len(langs)} languages, {commits} commits")

    # Step 2: Deep analysis (NEW - Tasks 1A, 1B, 1C)
    code_analysis = None
    deployment_analysis = None
    doc_analysis = None

    if args and args.deep_scan:
        if reporter:
            reporter.log_step("🏗️", "Running deep code analysis...")

        # Check cache first
        if cache_manager and args.resume:
            cached = cache_manager.get_cached(str(p), "deep_analysis")
            if cached:
                code_analysis = cached.get('code_analysis')
                deployment_analysis = cached.get('deployment_analysis')
                doc_analysis = cached.get('doc_analysis')
                if reporter:
                    reporter.log_step("📦", "Loaded deep analysis from cache")

        if not code_analysis:
            # Task 1A: Code Analysis
            code_analysis = analyze_code(str(p), langs)
            if reporter:
                score = code_analysis.get('code_quality', {}).get('overall_score', 0)
                reporter.log_step("📊", f"Code quality score: {score}/10")

            # Task 1B: Deployment Detection
            deployment_analysis = detect_deployment(str(p), langs, dataclasses.asdict(facts))
            if reporter:
                readiness = deployment_analysis.get('deployment_readiness', {}).get('overall_score', 0)
                reporter.log_step("🚀", f"Deployment readiness: {readiness}/10")

            # Task 1C: Documentation Analysis
            doc_analysis = analyze_documentation(str(p), langs, dataclasses.asdict(facts))
            if reporter:
                doc_score = doc_analysis.get('documentation', {}).get('overall_score', 0)
                reporter.log_step("📄", f"Documentation score: {doc_score}/10")

            # Cache deep analysis results
            if cache_manager:
                cache_manager.set_cache(str(p), "deep_analysis", {
                    'code_analysis': code_analysis,
                    'deployment_analysis': deployment_analysis,
                    'doc_analysis': doc_analysis
                })

    # Step 3: LLM Pipeline (NEW - Task 2A+2C)
    llm_results = None
    if args and not args.skip_llm:
        if reporter:
            reporter.log_step("🤖", "Running LLM analysis pipeline...")

        # Check cache
        if cache_manager and args.resume:
            llm_results = cache_manager.get_cached(str(p), "llm_analysis")
            if llm_results and reporter:
                reporter.log_step("📦", "LLM results loaded from cache")

        if not llm_results:
            try:
                project_data = {
                    'name': name,
                    'path': str(p),
                    'languages': langs,
                    'code_analysis': code_analysis,
                    'deployment_analysis': deployment_analysis,
                    'doc_analysis': doc_analysis
                }

                # Run async LLM orchestration
                llm_results = asyncio.run(analyze_with_llm(project_data))

                if reporter:
                    reporter.log_step("✨", "LLM analysis complete")

                # Cache results
                if cache_manager:
                    cache_manager.set_cache(str(p), "llm_analysis", llm_results)

            except Exception as e:
                if reporter:
                    reporter.log_step("⚠️", f"LLM analysis failed: {e}")
                llm_results = None

    # Step 4: Agent Zero Integration (NEW - Optional)
    agent_zero_results = None
    bonus_score = 0.0

    if args and args.use_agent_zero:
        if reporter:
            reporter.log_step("🤖", "Running Agent Zero autonomous audit...")

        try:
            auditor = AgentZeroAuditor()
            # Note: Agent Zero auditor requires actual workflow execution
            # For now, we'll skip if not available
            if reporter:
                reporter.log_step("⚠️", "Agent Zero workflows not configured (requires borg.tools connection)")
        except Exception as e:
            if reporter:
                reporter.log_step("⚠️", f"Agent Zero unavailable: {e}")

    # Step 5: Scoring (enhanced with deep analysis)
    stage = classify_stage(facts)
    value = score_value(facts)
    risk = score_risk(facts)

    # Enhance value score with deep analysis
    if code_analysis:
        code_quality_score = code_analysis.get('code_quality', {}).get('overall_score', 0)
        value = min(10, value + int(code_quality_score * 0.2))  # Add up to 2 points

    if deployment_analysis:
        deploy_readiness = deployment_analysis.get('deployment_readiness', {}).get('overall_score', 0)
        value = min(10, value + int(deploy_readiness * 0.1))  # Add up to 1 point

    # Add Agent Zero bonus
    value = min(10, value + bonus_score)

    prio = compute_priority(value, risk, facts.last_commit_dt)
    errs = fundamental_errors(facts)

    scores = Scores(stage=stage, value_score=value, risk_score=risk, priority=prio, fundamental_errors=errs)

    # Step 6: Generate suggestions (heuristic + optional LLM)
    sug = heuristic_suggestions(facts, scores)

    # Attach extended analysis data to suggestions for VibeSummary
    if code_analysis:
        sug.vibe_notes = f"Code Quality: {code_analysis.get('code_quality', {}).get('overall_score', 0)}/10"
    if llm_results:
        # Merge LLM insights into suggestions
        aggregated = llm_results.get('aggregated_analysis', {})
        if aggregated.get('description'):
            sug.description = aggregated['description']
        if aggregated.get('problem_solved'):
            sug.problem_solved = aggregated['problem_solved']
        if aggregated.get('monetization_potential'):
            sug.monetization_potential = aggregated['monetization_potential']

    if reporter:
        reporter.log_step("✅", f"Scan complete: Priority {prio}/20, Value {value}/10, Risk {risk}/10")

    # Store extended data in ProjectSummary for VibeSummary generation
    summary = ProjectSummary(facts=facts, scores=scores, suggestions=sug)

    # Attach raw analysis data as attributes (for VibeSummary)
    summary.code_analysis = code_analysis
    summary.deployment_analysis = deployment_analysis
    summary.doc_analysis = doc_analysis
    summary.llm_results = llm_results

    return summary


def main():
    ap = argparse.ArgumentParser(description='Borg Tools v2.0 – Advanced Project Scanner')
    ap.add_argument('--root', default='..', help='Root directory with projects (each subfolder = project)')

    # Legacy LLM options (deprecated but kept for compatibility)
    ap.add_argument('--use-llm', choices=['openai', 'openrouter'], help='Legacy: refine suggestions with an LLM provider (use --skip-llm to disable new pipeline)')
    ap.add_argument('--model', default='tngtech/deepseek-r1t2-chimera:free', help='LLM model id (OpenRouter or OpenAI)')

    # New v2.0 flags
    ap.add_argument('--deep-scan', action='store_true', help='Enable deep code/deployment/doc analysis (Tasks 1A-C)')
    ap.add_argument('--skip-llm', action='store_true', help='Fast mode: skip LLM pipeline entirely')
    ap.add_argument('--use-agent-zero', action='store_true', help='Enable Agent Zero integration for autonomous audits')
    ap.add_argument('--parallel-workers', type=int, default=4, help='LLM concurrency workers (default: 4)')
    ap.add_argument('--resume', action='store_true', help='Use cache for incremental scans')
    ap.add_argument('--output-format', choices=['json', 'yaml', 'markdown', 'all'], default='all', help='Output format (default: all)')
    ap.add_argument('--limit', type=int, default=0, help='Limit number of projects (0 = all)')
    ap.add_argument('--verbose', action='store_true', help='Enable verbose progress reporting')

    args = ap.parse_args()

    root = Path(os.path.expanduser(args.root)).resolve()
    if not root.exists():
        print(f"Root not found: {root}", file=sys.stderr)
        sys.exit(1)

    # Initialize v2.0 components
    reporter = ProgressReporter(verbose=args.verbose) if args.verbose else None
    cache_manager = get_cache_manager() if args.resume else None

    if reporter:
        reporter.log_step("🚀", f"Borg Tools v2.0 Scanner starting...")
        reporter.log_step("📁", f"Root directory: {root}")

    projects = list_projects(root)
    if args.limit:
        projects = projects[: args.limit]

    if reporter:
        reporter.log_step("🔍", f"Found {len(projects)} projects to scan")

    summaries: List[ProjectSummary] = []

    for idx, p in enumerate(projects, 1):
        if reporter:
            reporter.start_project(p.name, idx, len(projects))
        else:
            print(f"[{idx}/{len(projects)}] Scanning project: {p.name}")

        try:
            # v2.0 enhanced scan
            ps = scan_project(p, args=args, reporter=reporter, cache_manager=cache_manager)

            # Legacy LLM refinement (if using old --use-llm flag)
            if args.use_llm:
                chosen_model = args.model
                ps.suggestions = refine_with_llm(ps.suggestions, ps.facts, ps.scores, args.use_llm, chosen_model)

            # Write REPORT.md into project folder
            (p / 'REPORT.md').write_text(render_report_md(ps), encoding='utf-8')

            # Generate VibeSummary.md (NEW)
            if args.deep_scan and ps.code_analysis:
                try:
                    vibesummary_data = {
                        'project_name': ps.facts.name,
                        'project_path': ps.facts.path,
                        'languages': ps.facts.languages,
                        'code_analysis': ps.code_analysis or {},
                        'deployment_analysis': ps.deployment_analysis or {},
                        'documentation_analysis': ps.doc_analysis or {},
                        'llm_analysis': ps.llm_results or {}
                    }

                    vibesummary_path = p / 'VibeSummary.md'
                    success = generate_vibesummary(vibesummary_data, vibesummary_path)

                    if success and reporter:
                        reporter.log_step("📊", f"VibeSummary.md generated")
                except Exception as e:
                    if reporter:
                        reporter.log_step("⚠️", f"VibeSummary generation failed: {e}")

            if reporter:
                reporter.complete_project({
                    'value': ps.scores.value_score,
                    'risk': ps.scores.risk_score,
                    'priority': ps.scores.priority
                })

            summaries.append(ps)

        except Exception as e:
            error_msg = f"{p.name}: {e}"
            if reporter:
                reporter.log_step("❌", f"Scan failed: {e}")
            else:
                print(f"[WARN] {error_msg}")

    # Sort by priority desc, then value desc
    summaries.sort(key=lambda x: (x.scores.priority, x.scores.value_score), reverse=True)

    if reporter:
        reporter.log_step("📊", "Generating outputs...")

    # --- NEW: Find similar projects based on LLM tags ---
    if args.use_llm or (not args.skip_llm):
        for i, ps1 in enumerate(summaries):
            if not ps1.suggestions.functional_tags:
                continue
            tags1 = set(ps1.suggestions.functional_tags)
            similar = []
            for j, ps2 in enumerate(summaries):
                if i == j:
                    continue
                if ps2.suggestions.functional_tags:
                    tags2 = set(ps2.suggestions.functional_tags)
                    # Find projects with at least 2 common tags
                    if len(tags1.intersection(tags2)) >= 2:
                        similar.append(ps2.facts.name)
            ps1.suggestions.similar_projects = similar[:5] # Limit to 5

    # Write INDEX.md at root
    index_path = root / 'BORG_INDEX.md'
    index_path.write_text(render_index_md(summaries), encoding='utf-8')

    # Output format handling
    output_formats = ['all'] if args.output_format == 'all' else [args.output_format]

    if 'all' in output_formats or 'json' in output_formats:
        # CSV + JSON in current dir for quick dashboard imports
        import csv
        with open('borg_dashboard.csv', 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['name','path','stage','value','risk','priority','last_commit','fundamental_errors','languages'])
            for ps in summaries:
                fcts, sc = ps.facts, ps.scores
                w.writerow([
                    fcts.name,
                    fcts.path,
                    sc.stage,
                    sc.value_score,
                    sc.risk_score,
                    sc.priority,
                    fcts.last_commit_dt or '',
                    '; '.join(sc.fundamental_errors),
                    ','.join(fcts.languages),
                ])

        with open('borg_dashboard.json', 'w', encoding='utf-8') as f:
            json.dump([{
                'facts': dataclasses.asdict(ps.facts),
                'scores': dataclasses.asdict(ps.scores),
                'suggestions': dataclasses.asdict(ps.suggestions),
            } for ps in summaries], f, ensure_ascii=False, indent=2)

    # Show summary if using reporter
    if reporter:
        reporter.show_summary_table([{
            'name': ps.facts.name,
            'stage': ps.scores.stage,
            'value': ps.scores.value_score,
            'risk': ps.scores.risk_score,
            'priority': ps.scores.priority,
            'languages': ', '.join(ps.facts.languages[:2])
        } for ps in summaries[:10]])  # Top 10

    # Final output summary
    print(f"\n{'='*60}")
    print(f"Borg Tools v2.0 Scanner - Complete")
    print(f"{'='*60}")
    print(f"Projects scanned: {len(summaries)}")
    print(f"\nGenerated outputs:")
    print(f"  - {index_path} (master index)")
    print(f"  - borg_dashboard.csv (tabular data)")
    print(f"  - borg_dashboard.json (machine-readable)")
    print(f"\nPer-project outputs:")
    print(f"  - REPORT.md (detailed analysis)")
    if args.deep_scan:
        print(f"  - VibeSummary.md (comprehensive vibe report)")
    print(f"\nConfiguration:")
    print(f"  - Deep scan: {'✓' if args.deep_scan else '✗'}")
    print(f"  - LLM analysis: {'✓' if not args.skip_llm else '✗'}")
    print(f"  - Agent Zero: {'✓' if args.use_agent_zero else '✗'}")
    print(f"  - Cache: {'✓' if args.resume else '✗'}")
    print(f"\nTop 3 priority projects:")
    for i, ps in enumerate(summaries[:3], 1):
        print(f"  {i}. {ps.facts.name} - Priority {ps.scores.priority}/20 ({ps.scores.stage})")
    print()
if __name__ == '__main__':
    main()