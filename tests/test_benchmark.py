"""
Accuracy Evaluation Benchmark across multiple code samples.
Validates True Positives, False Positives, and detection performance.
"""
from pathlib import Path
from core.ast_inspector import ASTInspector
from core.scorer import CodeScorer

SAMPLES_DIR = Path(__file__).parent.parent / "samples"


def test_clean_code_sample_accuracy():
    sample_file = SAMPLES_DIR / "clean_code.py"
    with open(sample_file, "r", encoding="utf-8") as f:
        code = f.read()

    inspector = ASTInspector()
    valid, issues, _, _ = inspector.inspect(code)
    score_report = CodeScorer.evaluate(valid, issues, len(code.splitlines()))

    assert valid is True
    # Clean code should have 0 blocker/high issues and grade A+ or A
    blocker_or_high = [i for i in issues if i.severity in ("BLOCKER", "HIGH")]
    assert len(blocker_or_high) == 0
    assert score_report.score >= 90.0


def test_code_smells_sample_accuracy():
    sample_file = SAMPLES_DIR / "code_smells.py"
    with open(sample_file, "r", encoding="utf-8") as f:
        code = f.read()

    inspector = ASTInspector()
    valid, issues, _, _ = inspector.inspect(code)
    codes = {i.code for i in issues}

    # Verify expected code smells are caught accurately
    expected_codes = {"B001", "B002", "B004", "B005", "B006", "B007", "B008", "B009", "B010"}
    detected_expected = expected_codes.intersection(codes)
    assert len(detected_expected) >= 6, f"Expected at least 6 smells detected, got {detected_expected}"


def test_syntax_error_sample_accuracy():
    sample_file = SAMPLES_DIR / "syntax_error.py"
    with open(sample_file, "r", encoding="utf-8") as f:
        code = f.read()

    inspector = ASTInspector()
    valid, issues, _, _ = inspector.inspect(code)
    assert valid is False
    assert any(i.code == "E001" for i in issues)


def test_security_sample_accuracy():
    sample_file = SAMPLES_DIR / "security_issues.py"
    with open(sample_file, "r", encoding="utf-8") as f:
        code = f.read()

    inspector = ASTInspector()
    valid, issues, _, _ = inspector.inspect(code)
    codes = {i.code for i in issues}
    assert "SEC001" in codes  # eval()
    assert "SEC002" in codes  # hardcoded secret
    assert "SEC003" in codes  # assert (tuple)
