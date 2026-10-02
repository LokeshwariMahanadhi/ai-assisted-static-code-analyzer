"""
Legacy compatibility wrapper routing to the advanced core AST inspector.
"""
from core.ast_inspector import ASTInspector


def analyze_code(code: str):
    """
    Legacy wrapper function for backward compatibility.
    Returns (syntax_status, issues_list).
    """
    inspector = ASTInspector()
    valid, issues, _, _ = inspector.inspect(code)
    issue_strings = [f"Line {iss.line}: [{iss.code}] {iss.message}" for iss in issues]
    return valid, issue_strings
