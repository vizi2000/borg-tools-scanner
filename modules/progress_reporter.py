#!/usr/bin/env python3
"""
Progress Reporter - Rich Console UI for Borg Tools Scanner

Provides beautiful terminal output with:
- Emoji indicators
- Color-coded severity
- Progress bars
- Styled tables

Created by The Collective Borg.tools
"""

from typing import Dict, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box


class ProgressReporter:
    """
    Rich console UI for real-time progress reporting during project scanning.

    Features:
    - Emoji-based status indicators (🔍 📄 🏗️ 🔒 ✅)
    - Color-coded severity levels (🔴🟡🟢)
    - Progress bars for file scanning
    - Summary tables with project scores

    Example:
        reporter = ProgressReporter()
        reporter.start_project("my-project", 1, 5)
        reporter.log_step("📄", "Scanning 142 Python files...")
        reporter.show_progress_bar(current=50, total=142, description="Files")
        reporter.complete_project({"value": 7.5, "risk": 3.2, "priority": 14})
        reporter.show_summary_table(projects)
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the progress reporter.

        Args:
            verbose: If True, show detailed progress. If False, minimal output.
        """
        self.console = Console()
        self.verbose = verbose
        self.current_project = None
        self.project_count = 0
        self.total_projects = 0

    def start_project(self, name: str, current: int = 1, total: int = 1):
        """
        Signal the start of a new project analysis.

        Args:
            name: Project name
            current: Current project number (1-indexed)
            total: Total number of projects
        """
        self.current_project = name
        self.project_count = current
        self.total_projects = total

        # Create a styled header
        header = Text()
        header.append(f"\n🔍 [{current}/{total}] ", style="bold cyan")
        header.append(f"Analyzing project: ", style="bold white")
        header.append(f"{name}", style="bold yellow")

        self.console.print(header)

    def log_step(self, emoji: str, message: str, style: str = "white"):
        """
        Log a step in the analysis process.

        Args:
            emoji: Emoji indicator (e.g., "📄", "🏗️", "🔒")
            message: Step description
            style: Rich style name (e.g., "white", "green", "red", "yellow")
        """
        if not self.verbose:
            return

        text = Text()
        text.append(f"  {emoji} ", style="bold")
        text.append(message, style=style)
        self.console.print(text)

    def show_progress_bar(
        self,
        current: int,
        total: int,
        description: str = "Processing"
    ):
        """
        Display a progress bar for the current operation.

        Args:
            current: Current progress value
            total: Total value
            description: Description of what's being processed
        """
        if not self.verbose or total == 0:
            return

        percentage = (current / total) * 100
        bar_length = 30
        filled = int((current / total) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        text = Text()
        text.append(f"  📊 {description}: ", style="cyan")
        text.append(f"[{bar}] ", style="blue")
        text.append(f"{current}/{total} ({percentage:.0f}%)", style="yellow")

        self.console.print(text)

    def complete_project(self, scores: Dict[str, float]):
        """
        Signal project analysis completion and display scores.

        Args:
            scores: Dictionary with keys like "value_score", "risk_score", "priority"
        """
        value = scores.get("value_score", scores.get("value", 0))
        risk = scores.get("risk_score", scores.get("risk", 0))
        priority = scores.get("priority", 0)
        stage = scores.get("stage", "unknown")

        # Determine color based on value score
        if value >= 7:
            value_color = "green"
            emoji_quality = "🟢"
        elif value >= 5:
            value_color = "yellow"
            emoji_quality = "🟡"
        else:
            value_color = "red"
            emoji_quality = "🔴"

        # Risk color (inverted logic - lower is better)
        if risk <= 3:
            risk_color = "green"
        elif risk <= 6:
            risk_color = "yellow"
        else:
            risk_color = "red"

        text = Text()
        text.append(f"  ✅ ", style="bold green")
        text.append(f"Complete - Stage: ", style="white")
        text.append(f"{stage}", style="bold cyan")
        text.append(f" | Quality: ", style="white")
        text.append(f"{emoji_quality} {value:.1f}/10", style=f"bold {value_color}")
        text.append(f" | Risk: ", style="white")
        text.append(f"{risk:.1f}/10", style=f"bold {risk_color}")
        text.append(f" | Priority: ", style="white")
        text.append(f"{priority:.0f}/20", style="bold magenta")

        self.console.print(text)
        self.console.print()  # Empty line for spacing

    def show_error(self, message: str):
        """
        Display an error message.

        Args:
            message: Error description
        """
        text = Text()
        text.append("  ❌ ERROR: ", style="bold red")
        text.append(message, style="red")
        self.console.print(text)

    def show_warning(self, message: str):
        """
        Display a warning message.

        Args:
            message: Warning description
        """
        text = Text()
        text.append("  ⚠️  WARNING: ", style="bold yellow")
        text.append(message, style="yellow")
        self.console.print(text)

    def show_summary_table(self, projects: List[Dict]):
        """
        Display a summary table of all analyzed projects.

        Args:
            projects: List of project dictionaries with keys:
                - name: Project name
                - stage: Development stage
                - value_score: Value score (0-10)
                - risk_score: Risk score (0-10)
                - priority: Priority score (0-20)
                - languages: List of languages
                - fundamental_errors: List of errors
        """
        if not projects:
            self.console.print("\n[yellow]No projects to display[/yellow]")
            return

        # Create table
        table = Table(
            title="\n📊 Project Portfolio Summary",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            title_style="bold magenta",
        )

        # Add columns
        table.add_column("Project", style="bold yellow", no_wrap=False)
        table.add_column("Stage", style="cyan", justify="center")
        table.add_column("Quality", justify="center")
        table.add_column("Risk", justify="center")
        table.add_column("Priority", justify="center")
        table.add_column("Languages", style="dim")
        table.add_column("Issues", style="red", no_wrap=False)

        # Add rows
        for project in projects:
            name = project.get("name", "Unknown")
            stage = project.get("stage", "unknown")
            value = project.get("value_score", project.get("value", 0))
            risk = project.get("risk_score", project.get("risk", 0))
            priority = project.get("priority", 0)
            languages = ", ".join(project.get("languages", []))[:30]
            errors = project.get("fundamental_errors", [])

            # Format value with color emoji
            if value >= 7:
                value_str = f"🟢 {value:.1f}"
            elif value >= 5:
                value_str = f"🟡 {value:.1f}"
            else:
                value_str = f"🔴 {value:.1f}"

            # Format risk with color
            if risk <= 3:
                risk_str = f"[green]{risk:.1f}[/green]"
            elif risk <= 6:
                risk_str = f"[yellow]{risk:.1f}[/yellow]"
            else:
                risk_str = f"[red]{risk:.1f}[/red]"

            # Format priority
            priority_str = f"[magenta]{priority:.0f}[/magenta]"

            # Format errors
            error_count = len(errors)
            if error_count == 0:
                error_str = "[green]None[/green]"
            else:
                error_str = f"[red]{error_count} issue(s)[/red]"

            table.add_row(
                name,
                stage,
                value_str,
                risk_str,
                priority_str,
                languages,
                error_str
            )

        self.console.print(table)
        self.console.print()

    def show_header(self, title: str = "Borg Tools Scanner"):
        """
        Display a styled header banner.

        Args:
            title: Header title text
        """
        panel = Panel(
            Text(title, justify="center", style="bold cyan"),
            box=box.DOUBLE,
            style="cyan",
            padding=(1, 2)
        )
        self.console.print(panel)

    def show_footer(self, stats: Dict[str, int]):
        """
        Display summary statistics footer.

        Args:
            stats: Dictionary with keys like "total", "high_value", "high_risk"
        """
        total = stats.get("total", 0)
        high_value = stats.get("high_value", 0)
        high_risk = stats.get("high_risk", 0)

        text = Text()
        text.append("\n" + "="*60 + "\n", style="dim")
        text.append("📈 Summary: ", style="bold cyan")
        text.append(f"{total} projects scanned", style="white")

        if high_value > 0:
            text.append(f" | 🟢 {high_value} high-value", style="green")
        if high_risk > 0:
            text.append(f" | 🔴 {high_risk} high-risk", style="red")

        text.append("\n" + "="*60 + "\n", style="dim")

        self.console.print(text)

    def show_spinner_context(self, description: str = "Processing"):
        """
        Return a context manager for showing a spinner during long operations.

        Args:
            description: Description of the operation

        Returns:
            Progress context manager

        Example:
            with reporter.show_spinner_context("Scanning files"):
                # Long operation here
                pass
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=self.console
        )


# Example usage demonstration
if __name__ == "__main__":
    # Create reporter
    reporter = ProgressReporter()

    # Show header
    reporter.show_header("Borg Tools Scanner - Demo")

    # Simulate scanning 3 projects
    projects_data = []

    for i in range(1, 4):
        # Start project
        reporter.start_project(f"project-{i}", i, 3)

        # Log steps
        reporter.log_step("📄", f"Scanning {50 + i*30} Python files...", "cyan")
        reporter.show_progress_bar(current=50 + i*30, total=50 + i*30, description="Files")

        reporter.log_step("🏗️", f"Architecture: {'Hexagonal (DDD)' if i == 1 else 'MVC'}", "blue")
        reporter.log_step("🔒", f"Security scan: {i} issues found", "yellow" if i > 1 else "green")

        # Complete with scores
        scores = {
            "stage": "mvp" if i == 1 else "prototype",
            "value_score": 7.5 - i * 0.5,
            "risk_score": 2.0 + i * 1.5,
            "priority": 15 - i * 2
        }
        reporter.complete_project(scores)

        # Collect for summary
        projects_data.append({
            "name": f"project-{i}",
            "stage": scores["stage"],
            "value_score": scores["value_score"],
            "risk_score": scores["risk_score"],
            "priority": scores["priority"],
            "languages": ["python", "typescript"] if i == 1 else ["python"],
            "fundamental_errors": ["brak testów", "brak CI"] if i > 1 else []
        })

    # Show summary table
    reporter.show_summary_table(projects_data)

    # Show footer
    reporter.show_footer({
        "total": 3,
        "high_value": 2,
        "high_risk": 1
    })
