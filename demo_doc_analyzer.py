#!/usr/bin/env python3
"""
Demo script to analyze the Borg.tools_scan project documentation
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from doc_analyzer import analyze_documentation


def main():
    print("=" * 70)
    print("DOCUMENTATION ANALYSIS: Borg.tools_scan Project")
    print("=" * 70)

    project_path = Path(__file__).parent.absolute()

    # Simulated facts (would come from other analyzers)
    facts = {
        'deps': {
            'python': []  # No deps detected yet
        }
    }

    # Run analysis
    result = analyze_documentation(
        str(project_path),
        ['python', 'javascript'],
        facts,
        ['borg_tools_scan.py']
    )

    # Display results
    doc_data = result['documentation']

    print("\n📊 OVERALL RESULTS")
    print("-" * 70)
    print(f"Documentation Score: {doc_data['overall_score']}/10")
    print(f"Completeness:       {doc_data['completeness']:.1%}")
    print(f"Accuracy:           {doc_data['accuracy']:.1%}")

    print("\n📁 FOUND DOCUMENTATION")
    print("-" * 70)
    readme = doc_data['found_docs']['readme']
    if readme['exists']:
        print(f"✓ README.md found")
        print(f"  - Sections: {', '.join(readme['sections'])}")
        print(f"  - Missing: {', '.join(readme['missing_sections'])}")
        print(f"  - Word count: {readme['word_count']}")
        print(f"  - Code blocks: {readme['code_blocks']}")
    else:
        print("✗ No README found")

    api_docs = doc_data['found_docs']['api_docs']
    print(f"\n{'✓' if api_docs['exists'] else '✗'} API Documentation")
    print(f"  - Detected endpoints: {api_docs['detected_endpoints']}")
    print(f"  - Documented endpoints: {api_docs['documented_endpoints']}")

    print(f"\n{'✓' if doc_data['found_docs']['changelog']['exists'] else '✗'} CHANGELOG")
    print(f"{'✓' if doc_data['found_docs']['contributing']['exists'] else '✗'} CONTRIBUTING")
    print(f"{'✓' if doc_data['found_docs']['license']['exists'] else '✗'} LICENSE")

    if doc_data['accuracy_issues']:
        print("\n⚠️  ACCURACY ISSUES")
        print("-" * 70)
        for issue in doc_data['accuracy_issues']:
            print(f"[{issue['severity']}] {issue['type']}")
            print(f"  {issue['description']}")

    if doc_data['auto_generated_sections']:
        print("\n✨ AUTO-GENERATED CONTENT")
        print("-" * 70)
        for section, content in doc_data['auto_generated_sections'].items():
            print(f"\n### {section}")
            print(content[:300] + ('...' if len(content) > 300 else ''))

    # Save full results to JSON
    output_file = project_path / 'doc_analysis_result.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ Full results saved to: {output_file}")
    print("=" * 70)


if __name__ == '__main__':
    main()
