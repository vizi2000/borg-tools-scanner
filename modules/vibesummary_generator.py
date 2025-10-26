"""
VibeSummary Generator + Scoring Engine - Borg Tools Scanner v2.0

Generates comprehensive VibeSummary.md from aggregated analysis with:
- 6-category scoring system
- SMART task generation from LLM suggestions
- Jinja2 template rendering
- Portfolio suitability assessment

Created by The Collective Borg.tools
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import re


class ScoringEngine:
    """Computes 6 category scores from analysis data"""

    @staticmethod
    def compute_code_quality_score(code_analysis: Dict) -> Dict[str, Any]:
        """
        CODE_QUALITY_SCORE from Task 1A code analyzer results.

        Returns score, status emoji, and notes
        """
        if not code_analysis or 'code_quality' not in code_analysis:
            return {
                'score': 0,
                'status': '❌',
                'notes': 'No code analysis available'
            }

        score = code_analysis['code_quality'].get('overall_score', 0)

        if score >= 8:
            status = '✅'
            notes = 'Excellent code quality'
        elif score >= 6:
            status = '✅'
            notes = 'Good code quality'
        elif score >= 4:
            status = '⚠️'
            notes = 'Fair quality, needs improvement'
        else:
            status = '❌'
            notes = 'Poor quality, significant refactoring needed'

        return {
            'score': round(score, 1),
            'status': status,
            'notes': notes
        }

    @staticmethod
    def compute_deployment_readiness_score(deployment_analysis: Dict) -> Dict[str, Any]:
        """
        DEPLOYMENT_READINESS_SCORE from Task 1B deployment detector.

        Returns score, status emoji, and notes
        """
        if not deployment_analysis or 'deployment' not in deployment_analysis:
            return {
                'score': 0,
                'status': '❌',
                'notes': 'No deployment analysis available'
            }

        deployment = deployment_analysis['deployment']
        score = deployment.get('readiness_score', 0)
        is_deployable = deployment.get('is_deployable', False)

        blocker_count = len([b for b in deployment.get('blockers', [])
                            if b['severity'] in ['CRITICAL', 'HIGH']])

        if score >= 8 and is_deployable:
            status = '✅'
            notes = 'Ready for deployment'
        elif score >= 6:
            status = '⚠️'
            notes = f'Nearly ready, {blocker_count} blocker(s)'
        elif score >= 4:
            status = '⚠️'
            notes = 'Significant deployment work needed'
        else:
            status = '❌'
            notes = 'Not deployment ready'

        return {
            'score': round(score, 1),
            'status': status,
            'notes': notes
        }

    @staticmethod
    def compute_documentation_score(doc_analysis: Dict) -> Dict[str, Any]:
        """
        DOCUMENTATION_SCORE from Task 1C doc analyzer.

        Returns score, status emoji, and notes
        """
        if not doc_analysis or 'documentation' not in doc_analysis:
            return {
                'score': 0,
                'status': '❌',
                'notes': 'No documentation analysis available'
            }

        doc = doc_analysis['documentation']
        score = doc.get('overall_score', 0)
        completeness = doc.get('completeness', 0)

        if score >= 8:
            status = '✅'
            notes = 'Excellent documentation'
        elif score >= 6:
            status = '✅'
            notes = f'Good docs, {int(completeness*100)}% complete'
        elif score >= 4:
            status = '⚠️'
            notes = 'Documentation incomplete'
        else:
            status = '❌'
            notes = 'Minimal or missing documentation'

        return {
            'score': round(score, 1),
            'status': status,
            'notes': notes
        }

    @staticmethod
    def compute_borg_tools_fit_score(llm_analysis: Dict, deployment_analysis: Dict) -> Dict[str, Any]:
        """
        BORG_TOOLS_FIT_SCORE from LLM business analysis + deployment type.

        Factors:
        - LLM borg_tools_fit score
        - Docker/containerization readiness
        - Microservices architecture bonus
        - API-first design bonus

        Returns score, status emoji, and notes
        """
        base_score = 5  # Default neutral score
        notes_parts = []

        # Get LLM aggregator score if available
        if llm_analysis and 'aggregator' in llm_analysis:
            aggregator = llm_analysis['aggregator'].get('data', {})
            llm_fit = aggregator.get('borg_tools_fit', 5)
            base_score = llm_fit
            notes_parts.append(f'LLM assessment: {llm_fit}/10')

        # Check deployment readiness (Docker = good fit for borg.tools)
        if deployment_analysis and 'deployment' in deployment_analysis:
            deployment = deployment_analysis['deployment']
            deployment_type = deployment.get('deployment_type', 'unknown')
            target_platform = deployment.get('target_platform', 'unknown')

            if deployment_type == 'docker' or target_platform == 'borg.tools':
                base_score = min(10, base_score + 2)
                notes_parts.append('Docker-ready')

            # Check for services (microservices bonus)
            services = deployment.get('services', [])
            if len(services) > 1:
                base_score = min(10, base_score + 1)
                notes_parts.append(f'{len(services)} services')

        score = min(10, max(0, base_score))

        if score >= 8:
            status = '✅'
        elif score >= 6:
            status = '⚠️'
        else:
            status = '❌'

        notes = ', '.join(notes_parts) if notes_parts else 'Standard compatibility'

        return {
            'score': round(score, 1),
            'status': status,
            'notes': notes
        }

    @staticmethod
    def compute_mvp_proximity_score(deployment_analysis: Dict, doc_analysis: Dict,
                                     code_analysis: Dict, llm_analysis: Dict) -> Dict[str, Any]:
        """
        MVP_PROXIMITY_SCORE - Combined heuristic from all analyses.

        Factors:
        - Deployment readiness (30%)
        - Documentation completeness (20%)
        - Code quality (25%)
        - LLM vibecodibility assessment (25%)

        Returns score, status emoji, and notes
        """
        scores = []
        weights = []

        # Deployment readiness (30%)
        if deployment_analysis and 'deployment' in deployment_analysis:
            deploy_score = deployment_analysis['deployment'].get('readiness_score', 0)
            scores.append(deploy_score)
            weights.append(0.30)

        # Documentation completeness (20%)
        if doc_analysis and 'documentation' in doc_analysis:
            doc_score = doc_analysis['documentation'].get('overall_score', 0)
            scores.append(doc_score)
            weights.append(0.20)

        # Code quality (25%)
        if code_analysis and 'code_quality' in code_analysis:
            code_score = code_analysis['code_quality'].get('overall_score', 0)
            scores.append(code_score)
            weights.append(0.25)

        # LLM vibecodibility (25%)
        if llm_analysis and 'aggregator' in llm_analysis:
            aggregator = llm_analysis['aggregator'].get('data', {})
            vibe_score = aggregator.get('vibecodibility_score', 5)
            scores.append(vibe_score)
            weights.append(0.25)

        # Compute weighted average
        if scores:
            # Normalize weights
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]

            score = sum(s * w for s, w in zip(scores, normalized_weights))
        else:
            score = 0

        # Determine status and notes
        if score >= 8:
            status = '✅'
            notes = 'MVP-ready or very close'
        elif score >= 6:
            status = '⚠️'
            notes = 'MVP achievable with focused work'
        elif score >= 4:
            status = '⚠️'
            notes = 'Significant MVP work needed'
        else:
            status = '❌'
            notes = 'Far from MVP'

        return {
            'score': round(score, 1),
            'status': status,
            'notes': notes
        }

    @staticmethod
    def compute_monetization_viability_score(llm_analysis: Dict, code_analysis: Dict) -> Dict[str, Any]:
        """
        MONETIZATION_VIABILITY from LLM business analysis + code maturity.

        Factors:
        - LLM market_viability score
        - Code quality (readiness for production)
        - Architecture (scalability for paying customers)

        Returns score, status emoji, and notes
        """
        base_score = 5
        notes_parts = []

        # Get LLM business analysis
        if llm_analysis and 'business' in llm_analysis:
            business = llm_analysis['business'].get('data', {})
            market_viability = business.get('market_viability', 5)
            base_score = market_viability
            notes_parts.append(f'Market viability: {market_viability}/10')

        # Adjust based on code quality (can't monetize broken code)
        if code_analysis and 'code_quality' in code_analysis:
            code_score = code_analysis['code_quality'].get('overall_score', 0)
            if code_score < 4:
                base_score = min(base_score, 4)  # Cap at 4 if code is poor
                notes_parts.append('Code quality limits viability')
            elif code_score >= 7:
                base_score = min(10, base_score + 1)
                notes_parts.append('Production-ready quality')

        score = min(10, max(0, base_score))

        if score >= 7:
            status = '✅'
        elif score >= 5:
            status = '⚠️'
        else:
            status = '❌'

        notes = ', '.join(notes_parts) if notes_parts else 'Standard viability'

        return {
            'score': round(score, 1),
            'status': status,
            'notes': notes
        }

    @classmethod
    def compute_all_scores(cls, code_analysis: Dict, deployment_analysis: Dict,
                          doc_analysis: Dict, llm_analysis: Dict) -> Dict[str, Any]:
        """
        Compute all 6 category scores.

        Returns:
            Dictionary with all scores and overall vibecodibility
        """
        scores = {
            'code_quality': cls.compute_code_quality_score(code_analysis),
            'deployment_readiness': cls.compute_deployment_readiness_score(deployment_analysis),
            'documentation': cls.compute_documentation_score(doc_analysis),
            'borg_tools_fit': cls.compute_borg_tools_fit_score(llm_analysis, deployment_analysis),
            'mvp_proximity': cls.compute_mvp_proximity_score(
                deployment_analysis, doc_analysis, code_analysis, llm_analysis
            ),
            'monetization_viability': cls.compute_monetization_viability_score(
                llm_analysis, code_analysis
            )
        }

        # Compute overall vibecodibility (weighted average)
        # Equal weights for all categories
        overall = sum(s['score'] for s in scores.values()) / len(scores)

        if overall >= 8:
            emoji = '🌟'
        elif overall >= 6:
            emoji = '✅'
        elif overall >= 4:
            emoji = '⚠️'
        else:
            emoji = '❌'

        scores['overall_vibecodibility'] = round(overall, 1)
        scores['overall_emoji'] = emoji

        return scores


class TaskGenerator:
    """Generates SMART tasks from LLM suggestions and blocker analysis"""

    @staticmethod
    def parse_llm_priorities(llm_analysis: Dict) -> List[str]:
        """Extract priority tasks from LLM aggregator response"""
        priorities = []

        if llm_analysis and 'aggregator' in llm_analysis:
            aggregator = llm_analysis['aggregator'].get('data', {})
            top_priorities = aggregator.get('top_priorities', [])
            priorities.extend(top_priorities)

        return priorities

    @staticmethod
    def extract_mvp_roadmap(llm_analysis: Dict) -> List[str]:
        """Extract MVP roadmap items from deployment LLM response"""
        roadmap = []

        if llm_analysis and 'deployment' in llm_analysis:
            deployment_llm = llm_analysis['deployment'].get('data', {})
            mvp_roadmap = deployment_llm.get('mvp_roadmap', [])
            roadmap.extend(mvp_roadmap)

        return roadmap

    @staticmethod
    def estimate_task_time(task_description: str) -> float:
        """
        Heuristic time estimation based on task description.

        Returns hours estimate
        """
        task_lower = task_description.lower()

        # Quick fixes
        if any(word in task_lower for word in ['fix', 'update', 'add comment', 'rename']):
            return 0.5

        # Documentation
        if any(word in task_lower for word in ['document', 'readme', 'docs', 'write']):
            return 1.0

        # Testing
        if any(word in task_lower for word in ['test', 'unit test', 'integration']):
            return 2.0

        # Refactoring
        if any(word in task_lower for word in ['refactor', 'restructure', 'redesign']):
            return 4.0

        # New features
        if any(word in task_lower for word in ['implement', 'create', 'build', 'develop']):
            return 3.0

        # Default
        return 2.0

    @staticmethod
    def assess_impact(task_description: str, category: str) -> str:
        """
        Assess task impact level.

        Returns: HIGH, MEDIUM, or LOW
        """
        task_lower = task_description.lower()

        # High impact keywords
        if any(word in task_lower for word in [
            'critical', 'blocking', 'security', 'deploy', 'mvp', 'production'
        ]):
            return 'HIGH'

        # Category-based assessment
        if category in ['security', 'deployment', 'critical']:
            return 'HIGH'

        # Documentation and tests are medium impact
        if any(word in task_lower for word in ['document', 'test', 'readme']):
            return 'MEDIUM'

        return 'LOW'

    @staticmethod
    def assess_effort(time_estimate: float) -> str:
        """
        Assess effort level based on time estimate.

        Returns: LOW, MEDIUM, or HIGH
        """
        if time_estimate <= 1:
            return 'LOW'
        elif time_estimate <= 3:
            return 'MEDIUM'
        else:
            return 'HIGH'

    @classmethod
    def generate_smart_tasks(cls, deployment_analysis: Dict, doc_analysis: Dict,
                            code_analysis: Dict, llm_analysis: Dict) -> Dict[str, List[Dict]]:
        """
        Generate prioritized SMART task lists.

        Returns:
            Dictionary with critical_tasks, high_impact_tasks, quick_wins
        """
        all_tasks = []

        # 1. Deployment blockers (highest priority)
        if deployment_analysis and 'deployment' in deployment_analysis:
            blockers = deployment_analysis['deployment'].get('blockers', [])
            for blocker in blockers:
                task = {
                    'title': blocker.get('description', 'Unknown blocker'),
                    'description': blocker.get('suggestion', ''),
                    'time_estimate': blocker.get('estimated_fix_time_hours', 1),
                    'category': blocker.get('category', 'deployment'),
                    'severity': blocker.get('severity', 'MEDIUM'),
                    'source': 'deployment_blocker'
                }
                task['impact'] = cls.assess_impact(task['title'], task['category'])
                task['effort'] = cls.assess_effort(task['time_estimate'])
                all_tasks.append(task)

        # 2. Security issues (critical)
        if code_analysis and 'code_quality' in code_analysis:
            security_issues = code_analysis['code_quality'].get('fundamental_issues', [])
            for issue in security_issues[:5]:  # Limit to top 5
                task = {
                    'title': f"Fix security issue: {issue.get('type', issue.get('category', 'Unknown'))}",
                    'description': issue.get('description', 'Security vulnerability detected'),
                    'time_estimate': 1.0,
                    'category': 'security',
                    'severity': issue.get('severity', 'HIGH'),
                    'impact': 'HIGH',
                    'effort': 'LOW',
                    'source': 'security_scan'
                }
                all_tasks.append(task)

        # 3. Documentation gaps
        if doc_analysis and 'documentation' in doc_analysis:
            doc = doc_analysis['documentation']
            missing_sections = doc.get('found_docs', {}).get('readme', {}).get('missing_sections', [])
            for section in missing_sections[:3]:  # Top 3
                task = {
                    'title': f"Add README section: {section}",
                    'description': f"Document {section} in README for better project understanding",
                    'time_estimate': 1.0,
                    'category': 'documentation',
                    'severity': 'MEDIUM',
                    'impact': 'MEDIUM',
                    'effort': 'LOW',
                    'source': 'documentation_gap'
                }
                all_tasks.append(task)

        # 4. LLM-suggested priorities
        llm_priorities = cls.parse_llm_priorities(llm_analysis)
        for priority in llm_priorities[:5]:  # Top 5
            time_est = cls.estimate_task_time(priority)
            task = {
                'title': priority,
                'description': f"LLM-identified priority: {priority}",
                'time_estimate': time_est,
                'category': 'llm_priority',
                'severity': 'MEDIUM',
                'impact': cls.assess_impact(priority, 'llm_priority'),
                'effort': cls.assess_effort(time_est),
                'source': 'llm_aggregator'
            }
            all_tasks.append(task)

        # 5. MVP roadmap items
        mvp_items = cls.extract_mvp_roadmap(llm_analysis)
        for item in mvp_items[:5]:  # Top 5
            time_est = cls.estimate_task_time(item)
            task = {
                'title': item,
                'description': f"MVP milestone: {item}",
                'time_estimate': time_est,
                'category': 'mvp',
                'severity': 'MEDIUM',
                'impact': 'HIGH',
                'effort': cls.assess_effort(time_est),
                'source': 'mvp_roadmap'
            }
            all_tasks.append(task)

        # Categorize tasks
        critical_tasks = [t for t in all_tasks if t['severity'] == 'CRITICAL' or
                         (t['severity'] == 'HIGH' and t['category'] in ['security', 'deployment'])]

        high_impact_tasks = [t for t in all_tasks if t['impact'] == 'HIGH' and t not in critical_tasks]

        quick_wins = [t for t in all_tasks if t['effort'] == 'LOW' and
                     t['impact'] in ['MEDIUM', 'HIGH'] and t not in critical_tasks]

        # Sort by impact/effort ratio for high impact tasks
        high_impact_tasks.sort(key=lambda t: (t['impact'] == 'HIGH', t['time_estimate']))
        quick_wins.sort(key=lambda t: t['time_estimate'])

        return {
            'critical_tasks': critical_tasks[:5],
            'high_impact_tasks': high_impact_tasks[:5],
            'quick_wins': quick_wins[:5],
            'critical_hours': sum(t['time_estimate'] for t in critical_tasks[:5]),
            'high_impact_hours': sum(t['time_estimate'] for t in high_impact_tasks[:5]),
            'quick_wins_hours': sum(t['time_estimate'] for t in quick_wins[:5])
        }


class VibeSummaryGenerator:
    """Main VibeSummary generator orchestrator"""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize generator with Jinja2 template environment.

        Args:
            template_dir: Directory containing vibesummary.md.j2 template
        """
        if template_dir is None:
            # Default to templates/ directory in project root
            template_dir = Path(__file__).parent.parent / 'templates'

        self.template_dir = template_dir

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        self.scoring_engine = ScoringEngine()
        self.task_generator = TaskGenerator()

    def generate_vibesummary(self, project_summary: Dict, output_path: Path) -> bool:
        """
        Main entry point: Generate VibeSummary.md from project analysis.

        Args:
            project_summary: Aggregated analysis from all modules and LLM
            output_path: Path where VibeSummary.md will be written

        Returns:
            True if successful, False otherwise
        """
        print(f"🎨 [VIBESUMMARY] Generating VibeSummary for {project_summary.get('project_name', 'project')}...")

        try:
            # Extract analysis components
            code_analysis = project_summary.get('code_analysis', {})
            deployment_analysis = project_summary.get('deployment_analysis', {})
            doc_analysis = project_summary.get('documentation_analysis', {})
            llm_analysis = project_summary.get('llm_analysis', {})

            # Compute scores
            print("  📊 Computing 6-category scores...")
            scores = self.scoring_engine.compute_all_scores(
                code_analysis, deployment_analysis, doc_analysis, llm_analysis
            )

            # Generate SMART tasks
            print("  📝 Generating SMART task lists...")
            tasks = self.task_generator.generate_smart_tasks(
                deployment_analysis, doc_analysis, code_analysis, llm_analysis
            )

            # Generate AI opportunities
            print("  🤖 Generating AI acceleration opportunities...")
            ai_opportunities = self._generate_ai_opportunities(
                code_analysis, doc_analysis, deployment_analysis
            )

            # Prepare template context
            print("  🎨 Preparing template context...")
            context = self._prepare_template_context(
                project_summary, scores, tasks, ai_opportunities
            )

            # Render template
            print("  📄 Rendering Jinja2 template...")
            template = self.env.get_template('vibesummary.md.j2')
            rendered = template.render(**context)

            # Write output
            print(f"  💾 Writing VibeSummary to {output_path}...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding='utf-8')

            print(f"  ✅ VibeSummary generated successfully!")
            print(f"     Overall Vibecodibility: {scores['overall_vibecodibility']}/10 {scores['overall_emoji']}")

            return True

        except Exception as e:
            print(f"  ❌ Error generating VibeSummary: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _prepare_template_context(self, project_summary: Dict, scores: Dict,
                                  tasks: Dict, ai_opportunities: List[Dict]) -> Dict:
        """
        Prepare complete context dictionary for Jinja2 template.

        Returns:
            Dictionary with all template variables
        """
        # Extract analysis components
        code_analysis = project_summary.get('code_analysis', {})
        deployment_analysis = project_summary.get('deployment_analysis', {})
        doc_analysis = project_summary.get('documentation_analysis', {})
        llm_analysis = project_summary.get('llm_analysis', {})

        # Basic project info
        project_path = project_summary.get('project_path', 'unknown')
        project_name = project_summary.get('project_name', Path(project_path).name)

        # Get LLM responses
        business_data = llm_analysis.get('business', {}).get('data', {})
        aggregator_data = llm_analysis.get('aggregator', {}).get('data', {})
        architect_data = llm_analysis.get('architect', {}).get('data', {})
        deployment_llm_data = llm_analysis.get('deployment', {}).get('data', {})

        # Extract code quality data
        code_quality = code_analysis.get('code_quality', {})
        complexity_metrics = code_quality.get('complexity_metrics', {})
        readability = code_quality.get('readability', {})
        debt = code_quality.get('debt_indicators', {})

        # Extract deployment data
        deployment = deployment_analysis.get('deployment', {})

        # Extract documentation data
        documentation = doc_analysis.get('documentation', {})
        found_docs = documentation.get('found_docs', {})
        readme = found_docs.get('readme', {})
        api_docs = found_docs.get('api_docs', {})

        # Build context
        context = {
            # Basic info
            'project_name': project_name,
            'project_path': project_path,
            'generation_timestamp': datetime.now().isoformat(),
            'languages': project_summary.get('languages', []),

            # Scores
            'code_quality_score': scores['code_quality']['score'],
            'code_quality_status': scores['code_quality']['status'],
            'code_quality_notes': scores['code_quality']['notes'],

            'deployment_readiness_score': scores['deployment_readiness']['score'],
            'deployment_readiness_status': scores['deployment_readiness']['status'],
            'deployment_readiness_notes': scores['deployment_readiness']['notes'],

            'documentation_score': scores['documentation']['score'],
            'documentation_status': scores['documentation']['status'],
            'documentation_notes': scores['documentation']['notes'],

            'borg_tools_fit_score': scores['borg_tools_fit']['score'],
            'borg_tools_fit_status': scores['borg_tools_fit']['status'],
            'borg_tools_fit_notes': scores['borg_tools_fit']['notes'],

            'mvp_proximity_score': scores['mvp_proximity']['score'],
            'mvp_proximity_status': scores['mvp_proximity']['status'],
            'mvp_proximity_notes': scores['mvp_proximity']['notes'],

            'monetization_viability_score': scores['monetization_viability']['score'],
            'monetization_viability_status': scores['monetization_viability']['status'],
            'monetization_viability_notes': scores['monetization_viability']['notes'],

            'overall_vibecodibility': scores['overall_vibecodibility'],
            'overall_emoji': scores['overall_emoji'],

            # Project essence
            'project_description': aggregator_data.get('overall_assessment', business_data.get('problem_solved', 'No description available')),
            'target_audience': business_data.get('target_audience', 'Not specified'),
            'problem_solved': business_data.get('problem_solved', 'Not specified'),
            'project_stage': self._infer_project_stage(scores),

            # Architecture & Design
            'architecture_pattern': code_quality.get('architecture_pattern', 'Unknown'),
            'modularity_score': code_quality.get('modularity_score', 0),
            'design_patterns': architect_data.get('design_patterns', []),

            # Complexity
            'avg_cyclomatic': complexity_metrics.get('avg_cyclomatic', 0),
            'avg_cognitive': complexity_metrics.get('avg_cognitive', 0),
            'max_complexity': complexity_metrics.get('max_complexity_value', 0),
            'max_complexity_file': complexity_metrics.get('max_complexity_file'),

            # Code health
            'readability_score': readability.get('score', 0),
            'documentation_coverage': readability.get('documentation_coverage', 0) * 100,
            'avg_function_length': readability.get('avg_function_length', 0),
            'security_issues_count': len(code_quality.get('fundamental_issues', [])),
            'high_severity_count': len([i for i in code_quality.get('fundamental_issues', []) if i.get('severity') == 'HIGH']),

            # Technical debt
            'todo_count': debt.get('todo_count', 0),
            'fixme_count': debt.get('fixme_count', 0),
            'deprecated_apis_count': len(debt.get('deprecated_apis', [])),
            'fundamental_issues': code_quality.get('fundamental_issues', []),

            # Deployment
            'deployment_type': deployment.get('deployment_type', 'unknown'),
            'target_platform': deployment.get('target_platform', 'unknown'),
            'is_deployable': deployment.get('is_deployable', False),
            'detected_artifacts': deployment.get('detected_artifacts', {}),
            'environment_vars': deployment.get('environment_vars', []),
            'exposed_ports': deployment.get('ports', []),
            'deployment_blockers': deployment.get('blockers', []),
            'mvp_checklist': deployment.get('mvp_checklist', []),
            'estimated_hours_to_mvp': deployment.get('estimated_hours_to_mvp', 0),
            'deployment_instructions': deployment.get('deployment_instructions', 'No instructions available'),

            # Documentation
            'documentation_completeness': documentation.get('completeness', 0) * 100,
            'documentation_accuracy': documentation.get('accuracy', 0) * 100,
            'readme_exists': readme.get('exists', False),
            'readme_word_count': readme.get('word_count', 0),
            'readme_sections': readme.get('sections', []),
            'missing_sections': readme.get('missing_sections', []),
            'api_docs_exist': api_docs.get('exists', False),
            'detected_endpoints': api_docs.get('detected_endpoints', 0),
            'documented_endpoints': api_docs.get('documented_endpoints', 0),
            'changelog_exists': found_docs.get('changelog', {}).get('exists', False),
            'contributing_exists': found_docs.get('contributing', {}).get('exists', False),
            'license_exists': found_docs.get('license', {}).get('exists', False),
            'accuracy_issues': documentation.get('accuracy_issues', []),

            # Monetization
            'market_viability': business_data.get('market_viability', 5),
            'monetization_strategy': business_data.get('monetization_strategy', 'Not defined'),
            'monetization_potential_description': self._generate_monetization_description(business_data),
            'target_market_description': business_data.get('target_audience', 'Not specified'),
            'competitive_advantage': architect_data.get('scalability_notes', 'Not assessed'),

            # Portfolio
            'portfolio_suitable': business_data.get('portfolio_suitable', False),
            'portfolio_pitch': business_data.get('portfolio_pitch', ''),
            'portfolio_highlights': self._extract_portfolio_highlights(business_data, code_quality, deployment),
            'portfolio_blockers': self._identify_portfolio_blockers(scores, deployment, documentation),

            # Tasks
            'critical_tasks': tasks['critical_tasks'],
            'high_impact_tasks': tasks['high_impact_tasks'],
            'quick_wins': tasks['quick_wins'],
            'critical_hours': tasks['critical_hours'],
            'high_impact_hours': tasks['high_impact_hours'],
            'quick_wins_hours': tasks['quick_wins_hours'],

            # AI opportunities
            'ai_opportunities': ai_opportunities,

            # Borg.tools integration
            'borg_integration_opportunities': self._generate_borg_integrations(deployment, code_quality),

            # Raw data
            'code_quality_raw': code_quality,
            'deployment_analysis_raw': deployment,
            'documentation_analysis_raw': documentation,
            'llm_analysis_raw': {
                'business': business_data,
                'aggregator': aggregator_data,
                'architect': architect_data,
                'deployment': deployment_llm_data
            }
        }

        return context

    def _infer_project_stage(self, scores: Dict) -> str:
        """Infer project development stage from scores"""
        overall = scores['overall_vibecodibility']
        mvp_score = scores['mvp_proximity']['score']

        if overall >= 8 and mvp_score >= 8:
            return 'Production-ready'
        elif overall >= 6 and mvp_score >= 6:
            return 'MVP-stage'
        elif overall >= 4:
            return 'Active development'
        else:
            return 'Early stage / Prototype'

    def _generate_monetization_description(self, business_data: Dict) -> str:
        """Generate monetization potential description"""
        strategy = business_data.get('monetization_strategy', '')
        viability = business_data.get('market_viability', 5)

        if viability >= 7:
            return f"Strong revenue potential. {strategy}"
        elif viability >= 5:
            return f"Moderate revenue potential. {strategy}"
        else:
            return f"Limited monetization opportunity. {strategy}"

    def _extract_portfolio_highlights(self, business_data: Dict, code_quality: Dict,
                                     deployment: Dict) -> List[str]:
        """Extract key highlights for portfolio presentation"""
        highlights = []

        # Architecture
        pattern = code_quality.get('architecture_pattern', '')
        if pattern and pattern != 'Flat/Simple':
            highlights.append(f"Implements {pattern} architecture")

        # Deployment
        if deployment.get('is_deployable'):
            highlights.append("Production-ready deployment configuration")

        # Business value
        if business_data.get('market_viability', 0) >= 7:
            highlights.append("Strong market viability")

        # Code quality
        overall_score = code_quality.get('overall_score', 0)
        if overall_score >= 7:
            highlights.append("High code quality and best practices")

        return highlights or ["No standout features identified"]

    def _identify_portfolio_blockers(self, scores: Dict, deployment: Dict,
                                    documentation: Dict) -> str:
        """Identify reasons why project isn't portfolio-ready"""
        blockers = []

        if scores['code_quality']['score'] < 6:
            blockers.append("Code quality needs improvement")

        if scores['documentation']['score'] < 6:
            blockers.append("Documentation insufficient")

        if not deployment.get('is_deployable', False):
            blockers.append("Not deployment-ready")

        if scores['overall_vibecodibility'] < 6:
            blockers.append("Overall project maturity too low")

        return ', '.join(blockers) if blockers else "Project meets basic criteria"

    def _generate_ai_opportunities(self, code_analysis: Dict, doc_analysis: Dict,
                                  deployment_analysis: Dict) -> List[Dict]:
        """Generate AI-assisted improvement opportunities"""
        opportunities = []

        # Documentation generation
        doc = doc_analysis.get('documentation', {})
        missing_sections = doc.get('found_docs', {}).get('readme', {}).get('missing_sections', [])
        if missing_sections:
            opportunities.append({
                'category': 'Documentation Generation',
                'description': f"Auto-generate {len(missing_sections)} missing README sections",
                'prompt': f"Generate README sections for: {', '.join(missing_sections[:3])}",
                'expected_output': 'Markdown formatted documentation sections',
                'time_saved': f'{len(missing_sections) * 0.5}h'
            })

        # Test generation
        code_quality = code_analysis.get('code_quality', {})
        if code_quality.get('best_practices', {}).get('error_handling_coverage', 0) < 0.5:
            opportunities.append({
                'category': 'Test Generation',
                'description': 'Generate unit tests for core modules',
                'prompt': 'Generate pytest unit tests for the main modules with >80% coverage',
                'expected_output': 'Test files with fixtures and assertions',
                'time_saved': '4-6h'
            })

        # Refactoring suggestions
        complexity = code_quality.get('complexity_metrics', {})
        if complexity.get('avg_cyclomatic', 0) > 10:
            opportunities.append({
                'category': 'Code Refactoring',
                'description': 'Reduce complexity of high-complexity functions',
                'prompt': f'Refactor function in {complexity.get("max_complexity_file", "unknown")} to reduce cyclomatic complexity',
                'expected_output': 'Refactored code with lower complexity',
                'time_saved': '2-3h'
            })

        # Deployment automation
        deployment = deployment_analysis.get('deployment', {})
        if not deployment.get('detected_artifacts', {}).get('dockerfile', False):
            opportunities.append({
                'category': 'Deployment Setup',
                'description': 'Generate Dockerfile and deployment configuration',
                'prompt': f'Create production Dockerfile for {deployment.get("target_platform", "Docker")} deployment',
                'expected_output': 'Dockerfile with multi-stage build and best practices',
                'time_saved': '1-2h'
            })

        return opportunities

    def _generate_borg_integrations(self, deployment: Dict, code_quality: Dict) -> List[Dict]:
        """Generate Borg.tools integration opportunities"""
        integrations = []

        # MCP integration
        integrations.append({
            'service': 'MCP-VIBE Server',
            'description': 'Integrate with specs generation and validation',
            'effort': 'LOW'
        })

        # Docker deployment
        if deployment.get('deployment_type') == 'docker':
            integrations.append({
                'service': 'Borg.tools Hosting',
                'description': 'Deploy containerized app to borg.tools infrastructure',
                'effort': 'LOW'
            })

        # API integration
        if code_quality.get('best_practices', {}).get('security_patterns'):
            integrations.append({
                'service': 'Borg.tools API Gateway',
                'description': 'Integrate with centralized API management',
                'effort': 'MEDIUM'
            })

        return integrations


# ============================================================================
# ENTRY POINT
# ============================================================================

def generate_vibesummary(project_summary: Dict, output_path: Path) -> bool:
    """
    Main entry point for VibeSummary generation.

    Args:
        project_summary: Aggregated analysis from all modules
            {
                'project_name': str,
                'project_path': str,
                'languages': List[str],
                'code_analysis': Dict (from Task 1A),
                'deployment_analysis': Dict (from Task 1B),
                'documentation_analysis': Dict (from Task 1C),
                'llm_analysis': Dict (from Task 2A+2C)
            }
        output_path: Path where VibeSummary.md will be written

    Returns:
        True if successful, False otherwise
    """
    generator = VibeSummaryGenerator()
    return generator.generate_vibesummary(project_summary, output_path)


if __name__ == '__main__':
    # Simple test with mock data
    print("Testing VibeSummary Generator...\n")

    # Mock project summary
    mock_summary = {
        'project_name': 'Test Project',
        'project_path': '/path/to/test',
        'languages': ['python', 'javascript'],
        'code_analysis': {
            'code_quality': {
                'overall_score': 7.5,
                'architecture_pattern': 'MVC',
                'modularity_score': 8,
                'complexity_metrics': {
                    'avg_cyclomatic': 5,
                    'avg_cognitive': 3,
                    'max_complexity_value': 12,
                    'max_complexity_file': 'app/main.py'
                },
                'readability': {
                    'score': 7,
                    'documentation_coverage': 0.65,
                    'avg_function_length': 18
                },
                'debt_indicators': {
                    'todo_count': 5,
                    'fixme_count': 2,
                    'deprecated_apis': []
                },
                'fundamental_issues': []
            }
        },
        'deployment_analysis': {
            'deployment': {
                'readiness_score': 6,
                'is_deployable': True,
                'deployment_type': 'docker',
                'target_platform': 'borg.tools',
                'detected_artifacts': {
                    'dockerfile': True,
                    'docker_compose': False
                },
                'environment_vars': [],
                'ports': [8080],
                'blockers': [],
                'mvp_checklist': [
                    {'task': 'Create Dockerfile', 'status': 'done', 'time_hours': 0},
                    {'task': 'Add health check', 'status': 'pending', 'time_hours': 0.5}
                ],
                'estimated_hours_to_mvp': 2,
                'deployment_instructions': 'docker build -t test .'
            }
        },
        'documentation_analysis': {
            'documentation': {
                'overall_score': 5,
                'completeness': 0.6,
                'accuracy': 0.8,
                'found_docs': {
                    'readme': {
                        'exists': True,
                        'word_count': 500,
                        'sections': ['Installation', 'Usage'],
                        'missing_sections': ['Testing', 'Deployment']
                    },
                    'api_docs': {
                        'exists': False,
                        'detected_endpoints': 5,
                        'documented_endpoints': 2
                    },
                    'changelog': {'exists': False},
                    'contributing': {'exists': False},
                    'license': {'exists': True}
                },
                'accuracy_issues': []
            }
        },
        'llm_analysis': {
            'business': {
                'data': {
                    'problem_solved': 'Code analysis automation',
                    'target_audience': 'Developers',
                    'monetization_strategy': 'SaaS subscription',
                    'market_viability': 7,
                    'portfolio_suitable': True,
                    'portfolio_pitch': 'Automated code quality analysis tool'
                }
            },
            'aggregator': {
                'data': {
                    'overall_assessment': 'Solid project with good architecture',
                    'top_priorities': ['Add tests', 'Complete documentation', 'Deploy to staging'],
                    'vibecodibility_score': 7,
                    'borg_tools_fit': 8
                }
            },
            'architect': {
                'data': {
                    'design_patterns': ['MVC', 'Factory'],
                    'scalability_notes': 'Well-designed for horizontal scaling'
                }
            },
            'deployment': {
                'data': {
                    'mvp_roadmap': ['Setup CI/CD', 'Add monitoring', 'Configure staging']
                }
            }
        }
    }

    output_path = Path('/tmp/test_vibesummary.md')
    success = generate_vibesummary(mock_summary, output_path)

    if success:
        print(f"\n✅ Test VibeSummary generated at: {output_path}")
        print(f"\nPreview:")
        print("="*70)
        print(output_path.read_text()[:500])
        print("...")
    else:
        print("\n❌ Test failed")
