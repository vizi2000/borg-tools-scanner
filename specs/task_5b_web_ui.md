# Task 5B: Web UI Enhancements

## Objective
Display 6 category scores, VibeSummary viewer, deployment dashboard.

## Priority: 🟡 HIGH | Time: 3h | Dependencies: Task 5A

## New Features
1. **Scores Dashboard**: 6 category radial chart
2. **VibeSummary Tab**: Markdown viewer per project
3. **Deployment Status**: Traffic light (🔴🟡🟢) + blocker list
4. **Filter by Borg.tools Fit**: Show only fit_score >= 7

## UI Updates
- `templates/index.html` - add tabs, charts
- `/api/vibesummary/<project>` endpoint
- Chart.js for visualizations

## Test: Load 50 projects, verify UI renders all scores
