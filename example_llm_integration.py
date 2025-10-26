"""
Example: Full Pipeline Integration with LLM Orchestrator

This demonstrates how to integrate all analysis modules:
- Task 1A: Code Analyzer
- Task 1B: Deployment Detector
- Task 1C: Documentation Analyzer
- Task 2A: LLM Orchestrator

Created by The Collective Borg.tools
"""

import asyncio
import json
from pathlib import Path
from modules.code_analyzer import analyze_code
from modules.deployment_detector import detect_deployment
from modules.doc_analyzer import analyze_documentation
from modules.llm_orchestrator import analyze_with_llm


async def analyze_project_full(project_path: str, dry_run: bool = True):
    """
    Run complete project analysis with all modules

    Args:
        project_path: Path to the project directory
        dry_run: If True, use mock LLM responses (no API calls)

    Returns:
        Complete analysis results
    """
    project_path = Path(project_path)
    project_name = project_path.name

    print("=" * 70)
    print(f"FULL PROJECT ANALYSIS: {project_name}")
    print("=" * 70)
    print()

    # Step 1: Detect languages (basic implementation)
    print("🔍 Step 1/4: Detecting languages...")
    languages = detect_languages(project_path)
    print(f"  Languages: {', '.join(languages)}")
    print()

    # Step 2: Code Analysis (Task 1A)
    print("🔍 Step 2/4: Analyzing code quality...")
    code_analysis = analyze_code(str(project_path), languages)
    overall_score = code_analysis.get('code_quality', {}).get('overall_score', 0)
    print(f"  Code Quality Score: {overall_score}/10")
    print()

    # Step 3: Deployment Analysis (Task 1B)
    print("🔍 Step 3/4: Analyzing deployment readiness...")
    # Note: deployment detector needs facts dict, we'll pass basic info
    basic_facts = {'languages': languages}
    deployment_analysis = detect_deployment(str(project_path), languages, basic_facts)
    deploy_confidence = deployment_analysis.get('deployment_readiness', {}).get('overall_confidence', 0)
    print(f"  Deployment Confidence: {deploy_confidence * 100:.0f}%")
    print()

    # Step 4: Documentation Analysis (Task 1C)
    print("🔍 Step 4/4: Analyzing documentation...")
    # Note: doc analyzer needs facts dict
    doc_analysis = analyze_documentation(str(project_path), languages, basic_facts)
    doc_quality = doc_analysis.get('documentation', {}).get('quality_score', 0)
    print(f"  Documentation Quality: {doc_quality * 100:.0f}%")
    print()

    # Step 5: LLM Analysis (Task 2A)
    print("🤖 Step 5/5: Running LLM analysis...")
    if dry_run:
        print("  (Dry run mode - using mock responses)")

    project_data = {
        'name': project_name,
        'path': str(project_path),
        'languages': languages,
        'code_analysis': code_analysis,
        'deployment_analysis': deployment_analysis,
        'doc_analysis': doc_analysis
    }

    llm_results = await analyze_with_llm(project_data, dry_run=dry_run)
    print()

    # Combine all results
    full_results = {
        'project': {
            'name': project_name,
            'path': str(project_path),
            'languages': languages
        },
        'static_analysis': {
            'code': code_analysis,
            'deployment': deployment_analysis,
            'documentation': doc_analysis
        },
        'llm_analysis': llm_results
    }

    # Print summary
    print("=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print()

    print(f"📊 Project: {project_name}")
    print(f"   Languages: {', '.join(languages)}")
    print()

    print("📈 Static Analysis Scores:")
    print(f"   Code Quality:          {overall_score}/10")
    print(f"   Deployment Readiness:  {deploy_confidence * 100:.0f}%")
    print(f"   Documentation Quality: {doc_quality * 100:.0f}%")
    print()

    if 'llm_results' in llm_results:
        llm_data = llm_results['llm_results']

        print("🤖 LLM Analysis:")

        # Architect insights
        arch = llm_data.get('architect_analysis', {})
        if 'architecture_assessment' in arch:
            print(f"   Architecture: {arch.get('technical_debt_priority', 'N/A')} technical debt")

        # Business insights
        business = llm_data.get('business_analysis', {})
        if 'market_viability' in business:
            print(f"   Market Viability: {business['market_viability']}/10")
            print(f"   Portfolio Fit: {'Yes' if business.get('portfolio_suitable') else 'No'}")

        # Aggregated insights
        insights = llm_data.get('aggregated_insights', {})
        if 'vibecodibility_score' in insights:
            print(f"   Vibecodibility:  {insights['vibecodibility_score']}/10")
            print(f"   Borg.tools Fit:  {insights['borg_tools_fit']}/10")

        # Metadata
        metadata = llm_data.get('metadata', {})
        if metadata:
            print()
            print(f"⚡ Performance:")
            print(f"   Total Time:  {metadata.get('total_time_seconds', 0):.1f}s")
            print(f"   API Calls:   {metadata.get('api_calls', 0)}")
            print(f"   Cache Hits:  {metadata.get('cache_hits', 0)}")

    print()
    print("=" * 70)

    return full_results


def detect_languages(project_path: Path) -> list:
    """
    Simple language detection based on file extensions

    Args:
        project_path: Path to project directory

    Returns:
        List of detected languages
    """
    languages = set()

    # Python
    if list(project_path.rglob('*.py')):
        languages.add('python')

    # JavaScript/TypeScript
    if list(project_path.rglob('*.js')) or list(project_path.rglob('*.ts')):
        languages.add('javascript')

    # Go
    if list(project_path.rglob('*.go')):
        languages.add('go')

    # Rust
    if list(project_path.rglob('*.rs')):
        languages.add('rust')

    # Java
    if list(project_path.rglob('*.java')):
        languages.add('java')

    return list(languages) if languages else ['unknown']


async def main():
    """Run example analysis"""
    import sys

    # Use current project if no argument provided
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = str(Path.cwd())

    # Check for dry run mode
    dry_run = True
    if len(sys.argv) > 2 and sys.argv[2].lower() in ['--real', '--api']:
        dry_run = False
        print("⚠️  Running with REAL API calls")
        print()

    # Run analysis
    results = await analyze_project_full(project_path, dry_run=dry_run)

    # Save results
    output_file = Path('full_analysis_results.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"💾 Full results saved to: {output_file}")
    print()


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║         Borg.tools Scanner V2 - Full Pipeline Demo               ║
║                                                                   ║
║  Usage:                                                           ║
║    python3 example_llm_integration.py [path] [--real]            ║
║                                                                   ║
║  Examples:                                                        ║
║    python3 example_llm_integration.py                            ║
║    python3 example_llm_integration.py /path/to/project           ║
║    python3 example_llm_integration.py . --real                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())
