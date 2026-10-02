"""
Unit tests for ASTInspector line-level issue detection and code smells.
"""
import pytest
from core.ast_inspector import ASTInspector
from core.rules import IssueCategory, IssueSeverity


@pytest.fixture
def inspector():
    return ASTInspector()


def test_syntax_error_detection(inspector):
    code = "def broken(\n    return 1"
    valid, issues, _, _ = inspector.inspect(code)
    assert not valid
    assert len(issues) >= 1
    assert issues[0].code == "E001"
    assert issues[0].category == IssueCategory.SYNTAX
    assert issues[0].severity == IssueSeverity.BLOCKER


def test_mutable_default_argument(inspector):
    code = "def append_val(item, target_list=[]):\n    target_list.append(item)\n    return target_list"
    valid, issues, _, _ = inspector.inspect(code)
    assert valid
    codes = [iss.code for iss in issues]
    assert "B001" in codes
    issue = next(i for i in issues if i.code == "B001")
    assert issue.line == 1
    assert issue.category == IssueCategory.CODE_SMELL


def test_bare_except_clause(inspector):
    code = "try:\n    x = 1 / 0\nexcept:\n    pass"
    valid, issues, _, _ = inspector.inspect(code)
    assert valid
    codes = [iss.code for iss in issues]
    assert "B002" in codes
    issue = next(i for i in issues if i.code == "B002")
    assert issue.line == 3


def test_unused_variable_and_import(inspector):
    code = "import os\ndef test_fn():\n    unused_val = 42\n    return 1"
    valid, issues, _, _ = inspector.inspect(code)
    assert valid
    codes = [iss.code for iss in issues]
    assert "B004" in codes  # Unused variable
    assert "B005" in codes  # Unused import


def test_shadowed_builtin(inspector):
    code = "def process(list, id):\n    return len(list) + id"
    valid, issues, _, _ = inspector.inspect(code)
    assert valid
    codes = [iss.code for iss in issues]
    assert "B006" in codes


def test_unreachable_code(inspector):
    code = "def jump_test():\n    return 1\n    x = 2\n    print(x)"
    valid, issues, _, _ = inspector.inspect(code)
    assert valid
    codes = [iss.code for iss in issues]
    assert "B007" in codes
    issue = next(i for i in issues if i.code == "B007")
    assert issue.line == 3


def test_duplicate_dict_key(inspector):
    code = "config = {'key': 1, 'key': 2}"
    valid, issues, _, _ = inspector.inspect(code)
    assert valid
    codes = [iss.code for iss in issues]
    assert "B008" in codes


def test_dangerous_eval_security(inspector):
    code = "def execute_code(user_str):\n    return eval(user_str)"
    valid, issues, _, _ = inspector.inspect(code)
    assert valid
    codes = [iss.code for iss in issues]
    assert "SEC001" in codes
    issue = next(i for i in issues if i.code == "SEC001")
    assert issue.severity == IssueSeverity.BLOCKER
