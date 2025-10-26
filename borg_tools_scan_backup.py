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

@dataclasses.dataclass
class ProjectSummary:
    facts: Facts
    scores: Scores
    suggestions: Suggestions

# ----------------------------- Detection -----------------------------

def list_projects(root: Path) -> List[Path]:
    return [p for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith((".", "_"))]


def detect_languages(p: Path) -> List[str]:
    langs = set()
    names = {f.name for f in p.glob("*.*")} | {f.name for f in p.glob("**/*.*")}
    if any(n in names for n in PY_FILES) or any(str(f).endswith(".py") for f in p.rglob("*.py")):
        langs.add("python")
    if any(n in names for n in JS_FILES) or any(str(f).endswith((".js", ".ts", ".tsx")) for f in p.rglob("*")):
        # don't double-count from random assets; presence of package.json is strongest
        if "package.json" in names:
            langs.add("nodejs")
        else:
            langs.add("javascript-typescript")
    if any(n in names for n in RUST_FILES) or any(str(f).endswith(".rs") for f in p.rglob("*.rs")):
        langs.add("rust")
    if any(n in names for n in GO_FILES) or any(str(f).endswith(".go") for f in p.rglob("*.go")):
        langs.add("go")
    if any(str(f).endswith(('.java',)) for f in p.rglob('*.java')):
        langs.add('java')
    if any(str(f).endswith(('.swift',)) for f in p.rglob('*.swift')):
        langs.add('swift')
    if not langs:
        # fallback heuristic by file mix
        if any(str(f).endswith(('.sh',)) for f in p.rglob('*.sh')):
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
    for file in p.rglob("*.*"):
        rel = file.relative_to(p)
        if SAFE_IGNORE_RE.search(str(rel)):
            continue
        try:
            text = file.read_text(errors="ignore")
        except Exception:
            continue
        items = TODO_FIXME_RE.findall(text)
        if not items:
            continue
        # Extract full lines containing matches
        for m in re.finditer(r".*(?i)(TODO|FIXME|BUG|HACK)[^\n\r]*", text):
            line = m.group(0).strip()
            if line:
                todos.append(f"{rel}: {line[:200]}")
                if len(todos) >= max_total:
                    return todos
        if len(items) >= max_per_file and len(todos) >= max_total:
            break
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
                    if not ln or ln.startswith(('#', '[', 'url', 'path')):
                        continue
                    if '=' in ln and fname == 'pyproject.toml':
                        # ignore toml sections
                        continue
                    # crude split
                    pkg = re.split(r"[<>=~!;\[\] ]", ln)[0]
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

def scan_project(p: Path) -> ProjectSummary:
    name = p.name
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

    stage = classify_stage(facts)
    value = score_value(facts)
    risk = score_risk(facts)
    prio = compute_priority(value, risk, facts.last_commit_dt)
    errs = fundamental_errors(facts)

    scores = Scores(stage=stage, value_score=value, risk_score=risk, priority=prio, fundamental_errors=errs)

    sug = heuristic_suggestions(facts, scores)
    # LLM refinement optionally added by caller

    return ProjectSummary(facts=facts, scores=scores, suggestions=sug)


def main():
    ap = argparse.ArgumentParser(description='Borg Tools – scan & score your projects')
    ap.add_argument('--root', required=True, help='Root directory with projects (each subfolder = project)')
    ap.add_argument('--use-llm', choices=['openai','openrouter'], help='Optional: refine suggestions with an LLM provider')
    ap.add_argument('--model', default='anthropic/claude-3.7-sonnet', help='LLM model id (OpenRouter or OpenAI)')
    ap.add_argument('--limit', type=int, default=0, help='Limit number of projects (0 = all)')
    args = ap.parse_args()

    root = Path(os.path.expanduser(args.root)).resolve()
    if not root.exists():
        print(f"Root not found: {root}", file=sys.stderr)
        sys.exit(1)

    projects = list_projects(root)
    if args.limit:
        projects = projects[: args.limit]

    summaries: List[ProjectSummary] = []

    for p in projects:
        try:
            ps = scan_project(p)
            # Auto-routing per project if requested
            chosen_model = args.model
            if args.auto_route and args.use_llm == 'openrouter':
                size = args.repo_size
                density = args.code_heavy
                if size == 'auto' or density == 'auto':
                    est_size, est_density = estimate_repo_profile(p)
                    size = est_size if size == 'auto' else size
                    density = est_density if density == 'auto' else density
                chosen_model = route_model(args.task, size, density, args.budget, args.enterprise)
                print(f"[ROUTE] {p.name}: size={size} density={density} → model={chosen_model}")
            if args.use_llm:
                ps.suggestions = refine_with_llm(ps.suggestions, ps.facts, ps.scores, args.use_llm, chosen_model)
            # write REPORT.md into project folder
            (p / 'REPORT.md').write_text(render_report_md(ps), encoding='utf-8')
            summaries.append(ps)
        except Exception as e:
            print(f"[WARN] {p.name}: {e}")

    # Sort by priority desc, then value desc
    summaries.sort(key=lambda x: (x.scores.priority, x.scores.value_score), reverse=True)

    # Write INDEX.md at root
    (root / 'BORG_INDEX.md').write_text(render_index_md(summaries), encoding='utf-8')

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

    print(f"
Done. Projects scanned: {len(summaries)}")
    print(f"- Wygenerowano: {root / 'BORG_INDEX.md'}")
    print(f"- Wygenerowano: borg_dashboard.csv, borg_dashboard.json (tu, gdzie uruchomiłeś)")
    print(f"- Każdy projekt ma: REPORT.md z TODO/AI Accel/Skills\n")

if __name__ == '__main__':
    main()
