"""
Command-Line Interface (CLI) for AI-Assisted Static Code Analysis.
Usage:
    python cli.py --file samples/code_smells.py
    python cli.py --dir samples/
    python cli.py --benchmark
"""
import sys
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from core.ast_inspector import ASTInspector
from core.scorer import CodeScorer
from core.ai_explainer import AIExplainer
from core.reporter import ReportGenerator

console = Console(force_terminal=True, legacy_windows=False)


def analyze_file(filepath: Path, run_ai: bool = False, api_key: str = None):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading file {filepath}: {e}[/bold red]")
        return

    inspector = ASTInspector()
    valid, issues, functions, stats = inspector.inspect(code)
    score_report = CodeScorer.evaluate(valid, issues, stats.get("total_lines", 0))

    # Header Panel
    console.print(
        Panel(
            f"[bold cyan]AI-Assisted Static Code Analysis[/bold cyan]\n"
            f"File: [yellow]{filepath.resolve()}[/yellow] | Lines: [white]{stats.get('total_lines')}[/white] | "
            f"Score: [bold {score_report.grade_color}]{score_report.score}/100 ({score_report.grade})[/bold {score_report.grade_color}]",
            expand=False,
        )
    )

    # Issues Table
    if issues:
        table = Table(title="Line-Level Findings", show_header=True, header_style="bold magenta")
        table.add_column("Line", style="dim", width=6)
        table.add_column("Sev", width=8)
        table.add_column("Rule", width=22)
        table.add_column("Description", width=40)
        table.add_column("Remediation", style="green")

        sev_colors = {
            "BLOCKER": "bold red",
            "HIGH": "red",
            "MEDIUM": "yellow",
            "LOW": "blue",
            "INFO": "dim cyan",
        }

        for iss in issues:
            sev_val = iss.severity.value if hasattr(iss.severity, "value") else str(iss.severity)
            c = sev_colors.get(sev_val, "white")
            table.add_row(
                f"L{iss.line}",
                f"[{c}]{sev_val}[/{c}]",
                iss.rule_name,
                iss.message,
                iss.suggestion,
            )
        console.print(table)
    else:
        console.print("[bold green]✅ No issues detected. Clean and conformant code![/bold green]")

    # Function Metrics
    if functions:
        fn_table = Table(title="Function Complexity Metrics", show_header=True, header_style="bold blue")
        fn_table.add_column("Function", style="cyan")
        fn_table.add_column("Line", width=6)
        fn_table.add_column("SLOC", width=6)
        fn_table.add_column("Complexity (CC)", width=15)
        fn_table.add_column("Nesting Depth", width=15)
        fn_table.add_column("Args", width=6)

        for fn in functions:
            cc_style = "red" if fn.cyclomatic_complexity > 10 else "green"
            fn_table.add_row(
                fn.name,
                str(fn.line),
                str(fn.lines_count),
                f"[{cc_style}]{fn.cyclomatic_complexity}[/{cc_style}]",
                str(fn.max_nesting_depth),
                str(fn.arg_count),
            )
        console.print(fn_table)

    if run_ai:
        console.print("\n[bold purple]🤖 Generating AI Explanation & Recommendations...[/bold purple]")
        explainer = AIExplainer(api_key=api_key)
        explanation = explainer.generate_explanation(code, issues)
        console.print(Panel(explanation, title="Generative AI Review", border_style="purple"))


def run_benchmark():
    samples_dir = Path(__file__).parent / "samples"
    files = list(samples_dir.glob("*.py"))
    console.print(f"[bold green]Running Accuracy Benchmark on {len(files)} Samples...[/bold green]\n")

    table = Table(title="Benchmark Evaluation Matrix", show_header=True, header_style="bold yellow")
    table.add_column("Sample File", style="cyan")
    table.add_column("Syntax", width=10)
    table.add_column("Score", width=10)
    table.add_column("Grade", width=8)
    table.add_column("Issues Count", width=14)
    table.add_column("Primary Categories")

    inspector = ASTInspector()
    for f in sorted(files):
        with open(f, "r", encoding="utf-8") as fh:
            code = fh.read()
        valid, issues, _, stats = inspector.inspect(code)
        report = CodeScorer.evaluate(valid, issues, stats.get("total_lines", 0))
        cats = ", ".join(sorted(set(iss.category.value for iss in issues))) if issues else "Clean"
        table.add_row(
            f.name,
            "[green]Valid[/green]" if valid else "[red]Error[/red]",
            f"{report.score}/100",
            report.grade,
            str(len(issues)),
            cats,
        )
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="AI-Assisted Static Code Analysis Tool")
    parser.add_argument("--file", "-f", type=str, help="Path to Python file to analyze")
    parser.add_argument("--dir", "-d", type=str, help="Directory containing Python files to scan")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Run benchmark across sample test cases")
    parser.add_argument("--ai", action="store_true", help="Include Generative AI explanations")
    parser.add_argument("--api-key", type=str, help="Gemini API Key")

    args = parser.parse_args()

    if args.benchmark:
        run_benchmark()
    elif args.file:
        analyze_file(Path(args.file), run_ai=args.ai, api_key=args.api_key)
    elif args.dir:
        target_dir = Path(args.dir)
        for p in target_dir.rglob("*.py"):
            analyze_file(p, run_ai=args.ai, api_key=args.api_key)
            console.print("=" * 60)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
