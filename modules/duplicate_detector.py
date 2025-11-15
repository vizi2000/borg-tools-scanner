"""
Duplicate Project Detector - Borg Tools Scanner v2.0

Identifies duplicate and similar projects based on:
- Directory name similarity
- Language overlap
- Dependency similarity
- File structure patterns
- Functional tags (from LLM analysis)

Created by The Collective Borg.tools
"""

from typing import List, Dict, Tuple, Set
from pathlib import Path
import re
from difflib import SequenceMatcher


class DuplicateDetector:
    """Detects duplicate and similar projects"""

    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize duplicate detector

        Args:
            similarity_threshold: Minimum similarity score (0.0-1.0) to mark as duplicate
        """
        self.similarity_threshold = similarity_threshold

    def detect_duplicates(self, projects: List[Dict]) -> Dict[str, any]:
        """
        Detect duplicates across all projects

        Args:
            projects: List of project summaries with facts and scores

        Returns:
            Dictionary with duplicate groups and similarity scores
        """
        duplicates = []
        duplicate_groups = []
        processed = set()

        for i, p1 in enumerate(projects):
            if i in processed:
                continue

            group = [i]
            for j, p2 in enumerate(projects[i+1:], i+1):
                if j in processed:
                    continue

                similarity = self.calculate_similarity(p1, p2)
                
                if similarity >= self.similarity_threshold:
                    duplicates.append({
                        'project1': p1['facts']['name'],
                        'project2': p2['facts']['name'],
                        'similarity': round(similarity, 3),
                        'reasons': self._get_similarity_reasons(p1, p2)
                    })
                    group.append(j)
                    processed.add(j)

            if len(group) > 1:
                duplicate_groups.append({
                    'indices': group,
                    'projects': [projects[idx]['facts']['name'] for idx in group],
                    'primary': projects[group[0]]['facts']['name']  # First one is primary
                })
                processed.add(i)

        return {
            'duplicate_pairs': duplicates,
            'duplicate_groups': duplicate_groups,
            'total_duplicates': len(duplicates),
            'unique_projects': len(projects) - len(processed)
        }

    def calculate_similarity(self, p1: Dict, p2: Dict) -> float:
        """
        Calculate similarity score between two projects

        Args:
            p1, p2: Project dictionaries with facts and scores

        Returns:
            Similarity score (0.0-1.0)
        """
        scores = []
        weights = []

        # 1. Name similarity (weight: 0.3)
        name_sim = self._name_similarity(
            p1['facts']['name'],
            p2['facts']['name']
        )
        scores.append(name_sim)
        weights.append(0.3)

        # 2. Language overlap (weight: 0.25)
        lang_sim = self._language_similarity(
            p1['facts']['languages'],
            p2['facts']['languages']
        )
        scores.append(lang_sim)
        weights.append(0.25)

        # 3. Dependency similarity (weight: 0.2)
        dep_sim = self._dependency_similarity(
            p1['facts']['deps'],
            p2['facts']['deps']
        )
        scores.append(dep_sim)
        weights.append(0.2)

        # 4. Structure similarity (weight: 0.15)
        struct_sim = self._structure_similarity(p1['facts'], p2['facts'])
        scores.append(struct_sim)
        weights.append(0.15)

        # 5. Functional tag similarity (weight: 0.1) - if available
        if 'suggestions' in p1 and 'suggestions' in p2:
            tag_sim = self._tag_similarity(
                p1['suggestions'].get('functional_tags', []),
                p2['suggestions'].get('functional_tags', [])
            )
            scores.append(tag_sim)
            weights.append(0.1)

        # Weighted average
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity using sequence matching"""
        # Normalize names
        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)

        # Exact match
        if n1 == n2:
            return 1.0

        # Sequence matching
        return SequenceMatcher(None, n1, n2).ratio()

    def _normalize_name(self, name: str) -> str:
        """Normalize project name for comparison"""
        # Remove common suffixes/prefixes
        name = re.sub(r'[-_](old|new|v\d+|backup|copy|test|demo)$', '', name, flags=re.IGNORECASE)
        # Remove version numbers
        name = re.sub(r'[-_]?\d+(\.\d+)*$', '', name)
        # Lowercase and remove special chars
        name = re.sub(r'[^a-z0-9]', '', name.lower())
        return name

    def _language_similarity(self, langs1: List[str], langs2: List[str]) -> float:
        """Calculate language overlap similarity"""
        if not langs1 or not langs2:
            return 0.0

        set1 = set(langs1)
        set2 = set(langs2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _dependency_similarity(self, deps1: Dict, deps2: Dict) -> float:
        """Calculate dependency similarity"""
        if not deps1 or not deps2:
            return 0.0

        # Compare each ecosystem
        similarities = []
        all_ecosystems = set(deps1.keys()) | set(deps2.keys())

        for eco in all_ecosystems:
            d1 = set(deps1.get(eco, []))
            d2 = set(deps2.get(eco, []))

            if not d1 and not d2:
                continue

            intersection = len(d1 & d2)
            union = len(d1 | d2)

            if union > 0:
                similarities.append(intersection / union)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _structure_similarity(self, facts1: Dict, facts2: Dict) -> float:
        """Calculate structural similarity"""
        score = 0.0
        total = 5.0

        # Compare boolean features
        features = ['has_readme', 'has_license', 'has_tests', 'has_ci']
        for feat in features:
            if facts1.get(feat) == facts2.get(feat):
                score += 1.0

        # Compare commit count similarity (within 20%)
        c1 = facts1.get('commits_count', 0)
        c2 = facts2.get('commits_count', 0)
        
        if c1 > 0 and c2 > 0:
            ratio = min(c1, c2) / max(c1, c2)
            if ratio >= 0.8:  # Within 20%
                score += 1.0

        return score / total

    def _tag_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """Calculate functional tag similarity"""
        if not tags1 or not tags2:
            return 0.0

        set1 = set(tags1)
        set2 = set(tags2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _get_similarity_reasons(self, p1: Dict, p2: Dict) -> List[str]:
        """Get human-readable reasons for similarity"""
        reasons = []

        # Name similarity
        name_sim = self._name_similarity(p1['facts']['name'], p2['facts']['name'])
        if name_sim > 0.8:
            reasons.append(f"Similar names ({name_sim:.0%})")

        # Language overlap
        lang_sim = self._language_similarity(
            p1['facts']['languages'],
            p2['facts']['languages']
        )
        if lang_sim > 0.7:
            common_langs = set(p1['facts']['languages']) & set(p2['facts']['languages'])
            reasons.append(f"Same languages: {', '.join(common_langs)}")

        # Dependency overlap
        dep_sim = self._dependency_similarity(p1['facts']['deps'], p2['facts']['deps'])
        if dep_sim > 0.5:
            reasons.append(f"Similar dependencies ({dep_sim:.0%})")

        # Structure similarity
        struct_sim = self._structure_similarity(p1['facts'], p2['facts'])
        if struct_sim > 0.6:
            reasons.append(f"Similar structure ({struct_sim:.0%})")

        return reasons

    def mark_duplicates_in_summaries(
        self,
        projects: List[Dict],
        duplicate_info: Dict
    ) -> List[Dict]:
        """
        Mark projects as duplicates in their summaries

        Args:
            projects: List of project summaries
            duplicate_info: Output from detect_duplicates()

        Returns:
            Updated project list with duplicate markers
        """
        # Create index mapping
        name_to_idx = {p['facts']['name']: i for i, p in enumerate(projects)}

        # Mark duplicates
        for group in duplicate_info['duplicate_groups']:
            primary = group['primary']
            duplicates = [p for p in group['projects'] if p != primary]

            for proj_name in group['projects']:
                idx = name_to_idx.get(proj_name)
                if idx is not None:
                    if 'suggestions' not in projects[idx]:
                        projects[idx]['suggestions'] = {}
                    
                    projects[idx]['suggestions']['is_duplicate'] = (proj_name != primary)
                    projects[idx]['suggestions']['duplicate_of'] = primary if proj_name != primary else None
                    projects[idx]['suggestions']['duplicate_group'] = duplicates if proj_name == primary else []

        return projects


def detect_and_mark_duplicates(projects: List[Dict], threshold: float = 0.8) -> Tuple[List[Dict], Dict]:
    """
    Convenience function to detect and mark duplicates

    Args:
        projects: List of project summaries
        threshold: Similarity threshold (0.0-1.0)

    Returns:
        Tuple of (updated projects, duplicate info)
    """
    detector = DuplicateDetector(similarity_threshold=threshold)
    duplicate_info = detector.detect_duplicates(projects)
    updated_projects = detector.mark_duplicates_in_summaries(projects, duplicate_info)
    
    return updated_projects, duplicate_info


if __name__ == '__main__':
    # Test with mock data
    print("=" * 60)
    print("DUPLICATE DETECTOR - TEST")
    print("=" * 60)

    test_projects = [
        {
            'facts': {
                'name': 'my-app',
                'languages': ['python', 'javascript'],
                'deps': {'python': ['flask', 'requests'], 'node': ['react']},
                'has_readme': True,
                'has_tests': True,
                'has_ci': False,
                'commits_count': 50
            }
        },
        {
            'facts': {
                'name': 'my-app-v2',
                'languages': ['python', 'javascript'],
                'deps': {'python': ['flask', 'requests'], 'node': ['react', 'axios']},
                'has_readme': True,
                'has_tests': True,
                'has_ci': True,
                'commits_count': 55
            }
        },
        {
            'facts': {
                'name': 'other-project',
                'languages': ['rust'],
                'deps': {'rust': ['tokio', 'serde']},
                'has_readme': False,
                'has_tests': False,
                'has_ci': False,
                'commits_count': 10
            }
        }
    ]

    detector = DuplicateDetector(similarity_threshold=0.7)
    results = detector.detect_duplicates(test_projects)

    print(f"\nTotal duplicates found: {results['total_duplicates']}")
    print(f"Unique projects: {results['unique_projects']}")
    
    print("\nDuplicate pairs:")
    for dup in results['duplicate_pairs']:
        print(f"  - {dup['project1']} ↔ {dup['project2']}")
        print(f"    Similarity: {dup['similarity']:.1%}")
        print(f"    Reasons: {', '.join(dup['reasons'])}")

    print("\nDuplicate groups:")
    for group in results['duplicate_groups']:
        print(f"  - Primary: {group['primary']}")
        print(f"    Duplicates: {', '.join(group['projects'][1:])}")
