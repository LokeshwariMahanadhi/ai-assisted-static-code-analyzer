"""
Unit tests for CodeScorer health index and grading.
"""
from core.scorer import CodeScorer
from core.rules import Issue, IssueCategory, IssueSeverity


def test_clean_code_score():
    report = CodeScorer.evaluate(syntax_valid=True, issues=[], total_lines=50)
    assert report.score == 100.0
    assert report.grade == "A+"
    assert report.total_issues == 0
    assert report.estimated_debt_minutes == 0


def test_syntax_error_score():
    report = CodeScorer.evaluate(syntax_valid=False, issues=[], total_lines=10)
    assert report.grade == "F"
    assert report.status == "Syntax Broken"
    assert report.score <= 60.0


def test_weighted_issue_penalties():
    issues = [
        Issue("SEC001", "DangerousEvalExec", IssueCategory.SECURITY, IssueSeverity.BLOCKER, 1, 0, "msg", "sug"),
        Issue("B001", "MutableDefaultArgument", IssueCategory.CODE_SMELL, IssueSeverity.HIGH, 2, 0, "msg", "sug"),
        Issue("B004", "UnusedVariable", IssueCategory.CODE_SMELL, IssueSeverity.LOW, 3, 0, "msg", "sug"),
    ]
    report = CodeScorer.evaluate(syntax_valid=True, issues=issues, total_lines=30)
    assert report.total_issues == 3
    # Blocker (30) + High (10) + Low (2) = 42 penalty -> Score = 58 -> Grade D
    assert report.score == 58.0
    assert report.grade == "D"
