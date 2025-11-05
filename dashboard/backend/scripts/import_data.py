"""
Import script for populating database with projects from borg_dashboard.json

Usage:
    cd /Users/wojciechwiesner/ai/_Borg.tools_scan/dashboard/backend
    python -m scripts.import_data
"""

import json
import re
import sys
from pathlib import Path

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import engine, Base, SessionLocal
from models.project import Project


def extract_code_quality(vibe_notes: str) -> float:
    """Extract code quality score from vibe_notes string.

    Expected format: "Code Quality: 8.3/10"
    Returns: float between 0-10, or 0.0 if not found
    """
    if not vibe_notes:
        return 0.0

    match = re.search(r'Code Quality:\s*([\d.]+)/10', vibe_notes)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0
    return 0.0


def import_projects():
    """Import all projects from borg_dashboard.json into database."""

    # Path to source data
    data_path = Path("/Users/wojciechwiesner/ai/_Borg.tools_scan/borg_dashboard.json")

    if not data_path.exists():
        print(f"❌ Error: {data_path} not found")
        return

    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(engine)

    # Load JSON data
    print(f"Loading data from {data_path}...")
    with open(data_path) as f:
        data = json.load(f)

    print(f"Found {len(data)} projects to import")

    # Create database session
    db = SessionLocal()

    try:
        imported_count = 0
        skipped_count = 0

        for item in data:
            facts = item['facts']
            scores = item['scores']
            suggestions = item['suggestions']

            # Check if project already exists
            existing = db.query(Project).filter(Project.path == facts['path']).first()
            if existing:
                print(f"⏭️  Skipping {facts['name']} (already exists)")
                skipped_count += 1
                continue

            # Extract code quality score
            vibe_notes = suggestions.get('vibe_notes', '')
            code_quality = extract_code_quality(vibe_notes)

            # Create Project instance
            project = Project(
                name=facts['name'],
                path=facts['path'],
                stage=scores['stage'],
                priority=scores['priority'],
                value_score=scores['value_score'],
                risk_score=scores['risk_score'],
                code_quality_score=code_quality,
                languages=facts['languages'],
                has_readme=facts['has_readme'],
                has_license=facts['has_license'],
                has_tests=facts['has_tests'],
                has_ci=facts['has_ci'],
                commits_count=facts.get('commits_count'),
                branches_count=facts.get('branches_count'),
                last_commit_dt=facts.get('last_commit_dt'),
                todos=facts['todos'],
                deps=facts['deps'],
                fundamental_errors=scores['fundamental_errors'],
                todo_now=suggestions['todo_now'],
                todo_next=suggestions['todo_next'],
                raw_data=item
            )

            db.add(project)
            imported_count += 1
            print(f"✅ Imported: {facts['name']} (quality: {code_quality}/10)")

        # Commit all changes
        db.commit()

        print(f"\n🎉 Import complete!")
        print(f"   ✅ Imported: {imported_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        print(f"   📊 Total in DB: {db.query(Project).count()}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during import: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_projects()
