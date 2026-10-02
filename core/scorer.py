"""
Quality Scorer and Code Health Index Engine.
Calculates weighted scores, grades, category breakdowns, and technical debt estimations.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
from .rules import Issue, IssueSeverity, IssueCategory

SEVERITY_WEIGHTS = {
    IssueSeverity.BLOCKER: 30,
    IssueSeverity.HIGH: 10,
    IssueSeverity.MEDIUM: 5,
    IssueSeverity.LOW: 2,
    IssueSeverity.INFO: 1,
}

REMEDIATION_MINUTES = {
    IssueSeverity.BLOCKER: 30,
    IssueSeverity.HIGH: 15,
    IssueSeverity.MEDIUM: 10,
    IssueSeverity.LOW: 5,
    IssueSeverity.INFO: 2,
}


@dataclass
class ScoreReport:
    score: float
    grade: str
    grade_color: str
    status: str
    total_issues: int
    severity_counts: Dict[str, int]
    category_scores: Dict[str, float]
    estimated_debt_minutes: int
    feedback_summary: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "grade": self.grade,
            "grade_color": self.grade_color,
            "status": self.status,
            "total_issues": self.total_issues,
            "severity_counts": self.severity_counts,
            "category_scores": {k: round(v, 1) for k, v in self.category_scores.items()},
            "estimated_debt_minutes": self.estimated_debt_minutes,
            "feedback_summary": self.feedback_summary,
        }


class CodeScorer:
    @classmethod
    def evaluate(cls, syntax_valid: bool, issues: List[Issue], total_lines: int) -> ScoreReport:
        severity_counts = {
            IssueSeverity.BLOCKER.value: 0,
            IssueSeverity.HIGH.value: 0,
            IssueSeverity.MEDIUM.value: 0,
            IssueSeverity.LOW.value: 0,
            IssueSeverity.INFO.value: 0,
        }

        category_penalties: Dict[str, float] = {
            IssueCategory.SYNTAX.value: 0.0,
            IssueCategory.CODE_SMELL.value: 0.0,
            IssueCategory.SECURITY.value: 0.0,
            IssueCategory.COMPLEXITY.value: 0.0,
            IssueCategory.STYLE.value: 0.0,
        }

        total_penalty = 0.0
        total_debt_minutes = 0

        if not syntax_valid:
            total_penalty += 40.0
            category_penalties[IssueCategory.SYNTAX.value] += 40.0
            severity_counts[IssueSeverity.BLOCKER.value] += 1
            total_debt_minutes += 30

        for issue in issues:
            sev = issue.severity
            sev_key = sev.value if isinstance(sev, IssueSeverity) else str(sev)
            if sev_key in severity_counts:
                severity_counts[sev_key] += 1

            penalty = SEVERITY_WEIGHTS.get(sev, 2)
            total_penalty += penalty

            cat_key = issue.category.value if isinstance(issue.category, IssueCategory) else str(issue.category)
            category_penalties[cat_key] = category_penalties.get(cat_key, 0.0) + penalty
            total_debt_minutes += REMEDIATION_MINUTES.get(sev, 5)

        # Baseline score calculation normalized by code size
        raw_score = 100.0 - total_penalty
        score = max(0.0, min(100.0, raw_score))

        # Category scores (100 - localized penalties)
        category_scores = {}
        for cat, penalty in category_penalties.items():
            category_scores[cat] = max(0.0, min(100.0, 100.0 - (penalty * 2.0)))

        # Determine Letter Grade
        if not syntax_valid:
            grade = "F"
            grade_color = "#E53E3E"
            status = "Syntax Broken"
        elif score >= 95:
            grade = "A+"
            grade_color = "#38A169"
            status = "Outstanding (Production Ready)"
        elif score >= 85:
            grade = "A"
            grade_color = "#48BB78"
            status = "Excellent"
        elif score >= 75:
            grade = "B"
            grade_color = "#3182CE"
            status = "Good"
        elif score >= 60:
            grade = "C"
            grade_color = "#DD6B20"
            status = "Average / Needs Refactoring"
        elif score >= 40:
            grade = "D"
            grade_color = "#E53E3E"
            status = "Poor Quality"
        else:
            grade = "F"
            grade_color = "#9B2C2C"
            status = "Critical Issues Detected"

        # Summary bullet points
        feedback = []
        if not syntax_valid:
            feedback.append("Critical syntax errors prevent execution. Immediate correction required.")
        if severity_counts[IssueSeverity.BLOCKER.value] > 0:
            feedback.append(f"{severity_counts[IssueSeverity.BLOCKER.value]} Blocker issue(s) detected.")
        if severity_counts[IssueSeverity.HIGH.value] > 0:
            feedback.append(f"{severity_counts[IssueSeverity.HIGH.value]} High priority code smell(s) found.")
        if severity_counts[IssueSeverity.MEDIUM.value] > 0:
            feedback.append(f"{severity_counts[IssueSeverity.MEDIUM.value]} Medium maintainability warning(s).")
        if len(issues) == 0 and syntax_valid:
            feedback.append("Code passes all AST inspection checks with zero detected smells.")

        return ScoreReport(
            score=score,
            grade=grade,
            grade_color=grade_color,
            status=status,
            total_issues=len(issues),
            severity_counts=severity_counts,
            category_scores=category_scores,
            estimated_debt_minutes=total_debt_minutes,
            feedback_summary=feedback,
        )
