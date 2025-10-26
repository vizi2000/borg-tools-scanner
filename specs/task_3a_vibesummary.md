# Task 3A: VibeSummary Generator + Scoring

## Objective
Generate VibeSummary.md from aggregated analysis.

## Priority: 🔴 CRITICAL | Time: 6h | Dependencies: Task 2A, 2C

## Output
```python
# vibesummary_generator.py
def generate_vibesummary(project_summary: Dict, output_path: Path):
    # Jinja2 rendering
    # Compute 6 category scores
    # Generate SMART task lists
    # Write VibeSummary.md
```

## Template Sections (see full spec in plan)
- Project Essence
- 6 Category Scores (table)
- Deployment Status + MVP Checklist
- Monetization Analysis
- Portfolio Suitability
- Actionable Next Steps

## Test: Generated VibeSummary passes markdown linting
