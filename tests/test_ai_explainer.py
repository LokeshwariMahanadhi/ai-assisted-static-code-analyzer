"""
Unit tests for AIExplainer fallback and prompt formatting.
"""
from core.ai_explainer import AIExplainer
from core.rules import Issue, IssueCategory, IssueSeverity


def test_default_gemini_model(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert AIExplainer().model_name == "gemini-3.8-flash"


def test_gemini_model_environment_override(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "custom-gemini-model")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert AIExplainer().model_name == "custom-gemini-model"


def test_offline_ai_explanation_generation():
    explainer = AIExplainer(api_key=None)
    assert not explainer.is_ai_connected()

    issues = [
        Issue(
            code="B001",
            rule_name="MutableDefaultArgument",
            category=IssueCategory.CODE_SMELL,
            severity=IssueSeverity.HIGH,
            line=2,
            column=4,
            message="Mutable default list argument",
            suggestion="Use None as default",
            code_snippet="def foo(x=[])",
        )
    ]
    explanation = explainer.generate_explanation("def foo(x=[]):\n    pass", issues)
    assert "MutableDefaultArgument" in explanation
    assert "Line 2" in explanation
    assert "Refactored & Cleaned Code" in explanation


def test_generate_fixed_code():
    explainer = AIExplainer(api_key=None)
    code = "def foo(items, user_list=[]):\n    if items == None:\n        return None\n"
    issues = [
        Issue("B001", "MutableDefaultArgument", IssueCategory.CODE_SMELL, IssueSeverity.HIGH, 1, 0, "Mutable default", "Use None"),
        Issue("B009", "SingletonComparison", IssueCategory.STYLE, IssueSeverity.LOW, 2, 0, "== None", "is None"),
    ]
    fixed = explainer.generate_fixed_code(code, issues)
    assert "user_list=None" in fixed
    assert "is None" in fixed
