"""
AST-based Complexity and Metrics Analyzer.
Computes Cyclomatic Complexity (McCabe), Nesting Depth, and Function Metrics.
"""
import ast
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class FunctionMetrics:
    name: str
    line: int
    end_line: int
    lines_count: int
    arg_count: int
    return_count: int
    cyclomatic_complexity: int
    max_nesting_depth: int
    has_docstring: bool


class ComplexityVisitor(ast.NodeVisitor):
    """
    Computes McCabe cyclomatic complexity:
    Base complexity = 1 + number of branching points (if, while, for, except, with, boolean ops, comprehensions).
    """
    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # 'a and b and c' adds 1 for each extra condition
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_Match(self, node):
        # Python 3.10+ pattern matching
        self.complexity += len(node.cases)
        self.generic_visit(node)


class ComplexityAnalyzer:
    @staticmethod
    def calculate_cyclomatic_complexity(node: ast.AST) -> int:
        visitor = ComplexityVisitor()
        visitor.visit(node)
        return visitor.complexity

    @staticmethod
    def calculate_max_nesting_depth(node: ast.AST) -> int:
        max_depth = 0

        def traverse(current_node: ast.AST, current_depth: int):
            nonlocal max_depth
            nesting_nodes = (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.Try,
                ast.With,
                ast.AsyncWith,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            )
            is_nesting = isinstance(current_node, nesting_nodes)
            next_depth = current_depth + 1 if is_nesting else current_depth
            if next_depth > max_depth:
                max_depth = next_depth

            for child in ast.iter_child_nodes(current_node):
                traverse(child, next_depth)

        # Do not count the function itself as nesting level 1 if analyzing function body
        traverse(node, 0)
        return max_depth

    @classmethod
    def analyze_functions(cls, tree: ast.AST, source_lines: List[str]) -> List[FunctionMetrics]:
        results: List[FunctionMetrics] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line)
                lines_count = end_line - start_line + 1

                # Count arguments
                pos_args = len(node.args.args)
                kwonly_args = len(node.args.kwonlyargs)
                var_arg = 1 if node.args.vararg else 0
                kw_arg = 1 if node.args.kwarg else 0
                total_args = pos_args + kwonly_args + var_arg + kw_arg
                # Deduct self or cls if method
                if pos_args > 0 and node.args.args[0].arg in ("self", "cls"):
                    total_args -= 1

                # Count return statements
                return_count = sum(
                    1 for child in ast.walk(node) if isinstance(child, ast.Return)
                )

                # Cyclomatic complexity
                cc = cls.calculate_cyclomatic_complexity(node)

                # Nesting depth inside function
                max_nesting = 0
                for child in node.body:
                    depth = cls.calculate_max_nesting_depth(child)
                    if depth > max_nesting:
                        max_nesting = depth

                # Docstring
                has_doc = (
                    len(node.body) > 0
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                )

                metrics = FunctionMetrics(
                    name=node.name,
                    line=start_line,
                    end_line=end_line,
                    lines_count=lines_count,
                    arg_count=max(0, total_args),
                    return_count=return_count,
                    cyclomatic_complexity=cc,
                    max_nesting_depth=max_nesting,
                    has_docstring=has_doc,
                )
                results.append(metrics)

        return results

    @staticmethod
    def get_code_stats(source_code: str) -> Dict[str, Any]:
        lines = source_code.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        code_lines = total_lines - blank_lines - comment_lines

        return {
            "total_lines": total_lines,
            "code_lines": max(0, code_lines),
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "comment_ratio": round(comment_lines / max(1, total_lines) * 100, 1),
        }
