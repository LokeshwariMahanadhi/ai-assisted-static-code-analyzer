"""
Automated Reporting Generator.
Exports analysis results in JSON, Markdown, and HTML formats.
"""
import json
import datetime
from typing import List, Dict, Any
from .rules import Issue
from .scorer import ScoreReport
from .complexity import FunctionMetrics


class ReportGenerator:
    @staticmethod
    def to_json(
        syntax_valid: bool,
        issues: List[Issue],
        score_report: ScoreReport,
        function_metrics: List[FunctionMetrics],
        stats: Dict[str, Any],
        ai_explanation: str = "",
    ) -> str:
        payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "syntax_valid": syntax_valid,
            "score": score_report.to_dict(),
            "code_stats": stats,
            "issues": [issue.to_dict() for issue in issues],
            "functions": [
                {
                    "name": fn.name,
                    "line": fn.line,
                    "lines_count": fn.lines_count,
                    "cyclomatic_complexity": fn.cyclomatic_complexity,
                    "max_nesting_depth": fn.max_nesting_depth,
                    "arg_count": fn.arg_count,
                    "has_docstring": fn.has_docstring,
                }
                for fn in function_metrics
            ],
            "ai_explanation": ai_explanation,
        }
        return json.dumps(payload, indent=2)

    @staticmethod
    def to_markdown(
        source_name: str,
        syntax_valid: bool,
        issues: List[Issue],
        score_report: ScoreReport,
        stats: Dict[str, Any],
        ai_explanation: str = "",
    ) -> str:
        lines = [
            f"# 🛡️ Static Code Analysis Report: `{source_name}`",
            f"*Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## 📊 Executive Summary",
            f"- **Overall Score**: **{score_report.score}/100** (Grade: `{score_report.grade}` - {score_report.status})",
            f"- **Total Lines of Code**: {stats.get('total_lines', 0)} ({stats.get('code_lines', 0)} SLOC, {stats.get('comment_lines', 0)} comments)",
            f"- **Total Issues Identified**: {len(issues)}",
            f"- **Estimated Remediation Debt**: ~{score_report.estimated_debt_minutes} mins",
            "",
            "### Severity Breakdown",
        ]

        for sev, count in score_report.severity_counts.items():
            lines.append(f"- **{sev}**: {count}")

        lines.extend([
            "",
            "## 🔍 Detailed Line-by-Line Findings",
        ])

        if not issues:
            lines.append("✅ No issues found. Code passed all static analysis checks!")
        else:
            lines.append("| Line | Severity | Code | Category | Description | Suggestion |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for iss in issues:
                desc = iss.message.replace("|", "\\|")
                sug = iss.suggestion.replace("|", "\\|")
                lines.append(f"| L{iss.line} | `{iss.severity}` | `{iss.code}` | {iss.category} | {desc} | {sug} |")

        if ai_explanation:
            lines.extend([
                "",
                "## 🤖 Generative AI Analysis & Recommendations",
                ai_explanation,
            ])

        return "\n".join(lines)
