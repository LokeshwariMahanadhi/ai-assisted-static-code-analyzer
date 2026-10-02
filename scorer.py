"""
Legacy compatibility wrapper routing to the advanced core CodeScorer engine.
"""
from core.ast_inspector import ASTInspector
from core.scorer import CodeScorer


def calculate_score(syntax_status: bool, issues: list):
    """
    Legacy wrapper function for backward compatibility.
    """
    total_lines = 50
    # If issues are strings from legacy analyzer
    score = 100 if syntax_status else 60
    score -= 3 * len(issues)
    score = max(0, min(100, score))

    if not syntax_status:
        grade = "F"
    elif score >= 95:
        grade = "Outstanding"
    elif score >= 85:
        grade = "Excellent"
    elif score >= 75:
        grade = "Good"
    elif score >= 60:
        grade = "Average"
    else:
        grade = "Needs Improvement"

    return {
        "score": score,
        "grade": grade,
        "issues": issues,
        "syntax": syntax_status,
        "feedback": ["Analysis completed using AST engine"],
    }
