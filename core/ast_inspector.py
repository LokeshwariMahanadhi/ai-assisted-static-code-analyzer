"""
AST-based Static Code Inspector with Line-Level Issue Detection.
Performs AST parsing, visitor inspections, symbol usage analysis, and code smell identification.
"""
import ast
import re
from typing import List, Tuple, Optional, Set, Dict, Any
from .rules import Issue, IssueCategory, IssueSeverity
from .complexity import ComplexityAnalyzer, FunctionMetrics

PYTHON_BUILTINS = {
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes", "callable",
    "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod",
    "enumerate", "eval", "exec", "filter", "float", "format", "frozenset", "getattr",
    "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
    "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min",
    "next", "object", "oct", "open", "ord", "pow", "print", "property", "range",
    "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod",
    "str", "sum", "super", "tuple", "type", "vars", "zip"
}

SENSITIVE_KEYWORD_PATTERNS = [
    r"api[_-]?key",
    r"auth[_-]?token",
    r"secret[_-]?key",
    r"password",
    r"private[_-]?key",
    r"access[_-]?token",
]


class ScopeTracker(ast.NodeVisitor):
    """
    Collects defined and referenced identifiers across scopes to detect unused local variables and unused imports.
    """
    def __init__(self):
        self.scope_stack: List[Dict[str, Any]] = [{"definitions": {}, "references": set(), "type": "global"}]
        self.all_scopes: List[Dict[str, Any]] = []

    def push_scope(self, scope_type: str = "function"):
        scope = {"definitions": {}, "references": set(), "type": scope_type}
        self.scope_stack.append(scope)

    def pop_scope(self):
        scope = self.scope_stack.pop()
        self.all_scopes.append(scope)

    def add_definition(self, name: str, node: ast.AST, is_import: bool = False):
        if name.startswith("_"):
            return  # Conventionally ignored variable
        self.scope_stack[-1]["definitions"][name] = {"node": node, "is_import": is_import}

    def add_reference(self, name: str):
        # Reference applies to current scope and bubbles up
        for scope in reversed(self.scope_stack):
            scope["references"].add(name)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Function name belongs to enclosing scope
        self.add_definition(node.name, node)
        self.push_scope("function")
        for arg in node.args.args:
            if arg.arg not in ("self", "cls"):
                self.add_definition(arg.arg, arg)
        for arg in node.args.kwonlyargs:
            self.add_definition(arg.arg, arg)
        self.generic_visit(node)
        self.pop_scope()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.add_definition(node.name, node)
        self.push_scope("function")
        for arg in node.args.args:
            if arg.arg not in ("self", "cls"):
                self.add_definition(arg.arg, arg)
        self.generic_visit(node)
        self.pop_scope()

    def visit_ClassDef(self, node: ast.ClassDef):
        self.add_definition(node.name, node)
        self.push_scope("class")
        self.generic_visit(node)
        self.pop_scope()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            target_name = alias.asname if alias.asname else alias.name.split(".")[0]
            self.add_definition(target_name, alias, is_import=True)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":
                continue
            target_name = alias.asname if alias.asname else alias.name
            self.add_definition(target_name, alias, is_import=True)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.add_definition(node.id, node)
        elif isinstance(node.ctx, ast.Load):
            self.add_reference(node.id)
        self.generic_visit(node)


class CodeSmellVisitor(ast.NodeVisitor):
    """
    Main AST Visitor to inspect code smells, security risks, complexity, and style issues.
    """
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.issues: List[Issue] = []

    def _get_line_snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_mutable_defaults(node)
        self._check_function_naming_and_doc(node)
        self._check_unreachable_code(node.body)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_mutable_defaults(node)
        self._check_function_naming_and_doc(node)
        self._check_unreachable_code(node.body)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        if not ast.get_docstring(node):
            self.issues.append(
                Issue(
                    code="S001",
                    rule_name="MissingDocstring",
                    category=IssueCategory.STYLE,
                    severity=IssueSeverity.INFO,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Class '{node.name}' is missing a docstring.",
                    suggestion="Add a docstring detailing the class purpose and attributes.",
                    code_snippet=self._get_line_snippet(node.lineno),
                    ast_node="ClassDef",
                )
            )
        self._check_unreachable_code(node.body)
        self.generic_visit(node)

    def _check_mutable_defaults(self, node: (ast.FunctionDef, ast.AsyncFunctionDef)):
        all_defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
        for default in all_defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                type_name = "list" if isinstance(default, ast.List) else "dict" if isinstance(default, ast.Dict) else "set"
                self.issues.append(
                    Issue(
                        code="B001",
                        rule_name="MutableDefaultArgument",
                        category=IssueCategory.CODE_SMELL,
                        severity=IssueSeverity.HIGH,
                        line=default.lineno,
                        column=default.col_offset,
                        message=f"Function '{node.name}' uses a mutable {type_name} as default argument.",
                        suggestion=f"Use 'None' as default value and initialize with '{type_name}()' inside function body.",
                        code_snippet=self._get_line_snippet(default.lineno),
                        ast_node="arguments",
                    )
                )

    def _check_function_naming_and_doc(self, node: (ast.FunctionDef, ast.AsyncFunctionDef)):
        # Missing docstring check
        if not ast.get_docstring(node) and not node.name.startswith("__"):
            self.issues.append(
                Issue(
                    code="S001",
                    rule_name="MissingDocstring",
                    category=IssueCategory.STYLE,
                    severity=IssueSeverity.INFO,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Function '{node.name}' is missing a docstring.",
                    suggestion="Add a brief docstring explaining parameters, return value, and logic.",
                    code_snippet=self._get_line_snippet(node.lineno),
                    ast_node="FunctionDef",
                )
            )

        # Builtin shadowing in function name or args
        if node.name in PYTHON_BUILTINS and not node.name.startswith("__"):
            self.issues.append(
                Issue(
                    code="B006",
                    rule_name="ShadowedBuiltin",
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.MEDIUM,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Function name '{node.name}' shadows standard Python built-in function.",
                    suggestion=f"Rename '{node.name}' to something more specific (e.g. 'custom_{node.name}').",
                    code_snippet=self._get_line_snippet(node.lineno),
                    ast_node="FunctionDef",
                )
            )

        for arg in node.args.args:
            if arg.arg in PYTHON_BUILTINS and arg.arg not in ("self", "cls"):
                self.issues.append(
                    Issue(
                        code="B006",
                        rule_name="ShadowedBuiltin",
                        category=IssueCategory.CODE_SMELL,
                        severity=IssueSeverity.MEDIUM,
                        line=arg.lineno,
                        column=arg.col_offset,
                        message=f"Parameter '{arg.arg}' shadows Python built-in '{arg.arg}'.",
                        suggestion=f"Rename parameter to '{arg.arg}_val' or '{arg.arg}_item' to prevent shadowing.",
                        code_snippet=self._get_line_snippet(arg.lineno),
                        ast_node="arg",
                    )
                )

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.issues.append(
                Issue(
                    code="B002",
                    rule_name="BareExceptClause",
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.HIGH,
                    line=node.lineno,
                    column=node.col_offset,
                    message="Bare 'except:' clause caught. It catches KeyboardInterrupt and SystemExit.",
                    suggestion="Specify explicit exceptions, e.g. 'except Exception:' or 'except (ValueError, KeyError):'.",
                    code_snippet=self._get_line_snippet(node.lineno),
                    ast_node="ExceptHandler",
                )
            )
        elif isinstance(node.type, ast.Name) and node.type.id == "BaseException":
            self.issues.append(
                Issue(
                    code="B002",
                    rule_name="BareExceptClause",
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.HIGH,
                    line=node.lineno,
                    column=node.col_offset,
                    message="Catching 'BaseException' catches system-exiting exceptions.",
                    suggestion="Catch 'Exception' instead of 'BaseException' unless handling low-level process termination.",
                    code_snippet=self._get_line_snippet(node.lineno),
                    ast_node="ExceptHandler",
                )
            )
        self.generic_visit(node)

    def _check_unreachable_code(self, statements: List[ast.stmt]):
        terminal_types = (ast.Return, ast.Raise, ast.Break, ast.Continue)
        for i, stmt in enumerate(statements):
            if isinstance(stmt, terminal_types) and i < len(statements) - 1:
                next_stmt = statements[i + 1]
                self.issues.append(
                    Issue(
                        code="B007",
                        rule_name="UnreachableCode",
                        category=IssueCategory.CODE_SMELL,
                        severity=IssueSeverity.HIGH,
                        line=next_stmt.lineno,
                        column=next_stmt.col_offset,
                        message="Unreachable code detected immediately after a jump/return statement.",
                        suggestion="Remove dead code or adjust control flow logic before the terminal statement.",
                        code_snippet=self._get_line_snippet(next_stmt.lineno),
                        ast_node=next_stmt.__class__.__name__,
                    )
                )
                break

    def visit_Dict(self, node: ast.Dict):
        seen_keys = set()
        for key in node.keys:
            if key is None:
                continue
            if isinstance(key, ast.Constant):
                val = key.value
                if val in seen_keys:
                    self.issues.append(
                        Issue(
                            code="B008",
                            rule_name="DuplicateDictionaryKey",
                            category=IssueCategory.CODE_SMELL,
                            severity=IssueSeverity.HIGH,
                            line=key.lineno,
                            column=key.col_offset,
                            message=f"Duplicate dictionary key '{val}' detected in literal dictionary.",
                            suggestion="Remove or rename duplicate dictionary keys to prevent silent data overwrites.",
                            code_snippet=self._get_line_snippet(key.lineno),
                            ast_node="Dict",
                        )
                    )
                seen_keys.add(val)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        for op, comparator in zip(node.ops, node.comparators):
            # Check '== None' or '!= None'
            if isinstance(comparator, ast.Constant) and comparator.value is None:
                if isinstance(op, (ast.Eq, ast.NotEq)):
                    suggest_op = "is None" if isinstance(op, ast.Eq) else "is not None"
                    self.issues.append(
                        Issue(
                            code="B009",
                            rule_name="SingletonComparison",
                            category=IssueCategory.STYLE,
                            severity=IssueSeverity.LOW,
                            line=node.lineno,
                            column=node.col_offset,
                            message="Comparison to None using equality operator.",
                            suggestion=f"Use '{suggest_op}' according to PEP 8 standard.",
                            code_snippet=self._get_line_snippet(node.lineno),
                            ast_node="Compare",
                        )
                    )
            # Check '== True' or '== False'
            elif isinstance(comparator, ast.Constant) and isinstance(comparator.value, bool):
                if isinstance(op, (ast.Eq, ast.NotEq)):
                    self.issues.append(
                        Issue(
                            code="B010",
                            rule_name="BooleanLiteralComparison",
                            category=IssueCategory.STYLE,
                            severity=IssueSeverity.LOW,
                            line=node.lineno,
                            column=node.col_offset,
                            message=f"Explicit comparison to boolean literal '{comparator.value}'.",
                            suggestion="Use boolean expression directly (e.g. 'if cond:' or 'if not cond:').",
                            code_snippet=self._get_line_snippet(node.lineno),
                            ast_node="Compare",
                        )
                    )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Security: eval() or exec()
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ("eval", "exec"):
                self.issues.append(
                    Issue(
                        code="SEC001",
                        rule_name="DangerousEvalExec",
                        category=IssueCategory.SECURITY,
                        severity=IssueSeverity.BLOCKER,
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Use of dangerous dynamic execution function '{func_name}()'.",
                        suggestion=f"Avoid '{func_name}()'. Use 'ast.literal_eval()' or safe dispatch tables instead.",
                        code_snippet=self._get_line_snippet(node.lineno),
                        ast_node="Call",
                    )
                )
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert):
        if isinstance(node.test, ast.Tuple) and len(node.test.elts) > 0:
            self.issues.append(
                Issue(
                    code="SEC003",
                    rule_name="AssertOnTuple",
                    category=IssueCategory.SECURITY,
                    severity=IssueSeverity.HIGH,
                    line=node.lineno,
                    column=node.col_offset,
                    message="Asserting a non-empty tuple always evaluates to True.",
                    suggestion="Remove parentheses: 'assert condition, message' instead of 'assert (condition, message)'.",
                    code_snippet=self._get_line_snippet(node.lineno),
                    ast_node="Assert",
                )
            )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # Check hardcoded secrets
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                for pat in SENSITIVE_KEYWORD_PATTERNS:
                    if re.search(pat, var_name, re.IGNORECASE):
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and len(node.value.value) > 3:
                            self.issues.append(
                                Issue(
                                    code="SEC002",
                                    rule_name="HardcodedSecret",
                                    category=IssueCategory.SECURITY,
                                    severity=IssueSeverity.HIGH,
                                    line=node.lineno,
                                    column=node.col_offset,
                                    message=f"Possible hardcoded credential or token in variable '{var_name}'.",
                                    suggestion="Load sensitive secrets from environment variables (os.environ / python-dotenv).",
                                    code_snippet=self._get_line_snippet(node.lineno),
                                    ast_node="Assign",
                                )
                            )
                # Check single character variables (not in comprehension/loop counters)
                if len(var_name) == 1 and var_name not in ("_", "i", "j", "k", "x", "y", "z", "e", "f"):
                    self.issues.append(
                        Issue(
                            code="S002",
                            rule_name="SingleCharVariableName",
                            category=IssueCategory.STYLE,
                            severity=IssueSeverity.LOW,
                            line=node.lineno,
                            column=node.col_offset,
                            message=f"Single-character variable name '{var_name}' detected.",
                            suggestion=f"Use descriptive names reflecting the variable's intent.",
                            code_snippet=self._get_line_snippet(node.lineno),
                            ast_node="Assign",
                        )
                    )
        self.generic_visit(node)


class ASTInspector:
    """
    Orchestrates AST parsing, line-level inspection, complexity metrics, and unused symbol identification.
    """
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()

    def inspect(self, source_code: str) -> Tuple[bool, List[Issue], List[FunctionMetrics], Dict[str, Any]]:
        source_lines = source_code.splitlines()
        stats = self.complexity_analyzer.get_code_stats(source_code)
        issues: List[Issue] = []
        function_metrics: List[FunctionMetrics] = []

        # 1. Parse AST
        try:
            tree = ast.parse(source_code)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            line = e.lineno or 1
            col = e.offset or 0
            snippet = source_lines[line - 1].strip() if 1 <= line <= len(source_lines) else (e.text or "").strip()
            issues.append(
                Issue(
                    code="E001",
                    rule_name="SyntaxError",
                    category=IssueCategory.SYNTAX,
                    severity=IssueSeverity.BLOCKER,
                    line=line,
                    column=col,
                    message=f"Syntax Error: {e.msg}",
                    suggestion="Fix Python syntax at the specified line and column before further static analysis.",
                    code_snippet=snippet,
                    ast_node="SyntaxError",
                )
            )
            return syntax_valid, issues, function_metrics, stats

        # 2. Node Visitor Code Smell Checks
        smell_visitor = CodeSmellVisitor(source_lines)
        smell_visitor.visit(tree)
        issues.extend(smell_visitor.issues)

        # 3. Scope & Unused Symbol Analysis
        scope_tracker = ScopeTracker()
        scope_tracker.visit(tree)
        # Pop remaining root scope
        while scope_tracker.scope_stack:
            scope_tracker.pop_scope()

        for scope in scope_tracker.all_scopes:
            defs = scope["definitions"]
            refs = scope["references"]
            for name, meta in defs.items():
                if name not in refs:
                    node = meta["node"]
                    is_import = meta["is_import"]
                    lineno = getattr(node, "lineno", 1)
                    col = getattr(node, "col_offset", 0)
                    snippet = source_lines[lineno - 1].strip() if 1 <= lineno <= len(source_lines) else ""
                    
                    if is_import:
                        issues.append(
                            Issue(
                                code="B005",
                                rule_name="UnusedImport",
                                category=IssueCategory.CODE_SMELL,
                                severity=IssueSeverity.LOW,
                                line=lineno,
                                column=col,
                                message=f"Imported symbol '{name}' is never used in this file.",
                                suggestion=f"Remove 'import {name}' to optimize module load time and keep imports clean.",
                                code_snippet=snippet,
                                ast_node="Import",
                            )
                        )
                    elif scope["type"] == "function" and not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.arg)):
                        issues.append(
                            Issue(
                                code="B004",
                                rule_name="UnusedVariable",
                                category=IssueCategory.CODE_SMELL,
                                severity=IssueSeverity.LOW,
                                line=lineno,
                                column=col,
                                message=f"Local variable '{name}' is assigned but never referenced.",
                                suggestion=f"Remove variable '{name}' or prefix with an underscore if unused by design.",
                                code_snippet=snippet,
                                ast_node="Name",
                            )
                        )

        # 4. Complexity & Function Metrics Analysis
        function_metrics = self.complexity_analyzer.analyze_functions(tree, source_lines)
        for fn in function_metrics:
            if fn.cyclomatic_complexity > 10:
                snippet = source_lines[fn.line - 1].strip() if 1 <= fn.line <= len(source_lines) else ""
                issues.append(
                    Issue(
                        code="C001",
                        rule_name="HighCyclomaticComplexity",
                        category=IssueCategory.COMPLEXITY,
                        severity=IssueSeverity.HIGH,
                        line=fn.line,
                        column=0,
                        message=f"Function '{fn.name}' has high cyclomatic complexity ({fn.cyclomatic_complexity} > 10).",
                        suggestion="Refactor branching logic into smaller helper functions or lookup tables.",
                        code_snippet=snippet,
                        ast_node="FunctionDef",
                    )
                )
            if fn.max_nesting_depth > 4:
                snippet = source_lines[fn.line - 1].strip() if 1 <= fn.line <= len(source_lines) else ""
                issues.append(
                    Issue(
                        code="C002",
                        rule_name="DeepNesting",
                        category=IssueCategory.COMPLEXITY,
                        severity=IssueSeverity.MEDIUM,
                        line=fn.line,
                        column=0,
                        message=f"Function '{fn.name}' exceeds nesting depth threshold (depth: {fn.max_nesting_depth} > 4).",
                        suggestion="Use guard clauses with early returns or extract nested logic into sub-functions.",
                        code_snippet=snippet,
                        ast_node="FunctionDef",
                    )
                )
            if fn.lines_count > 40:
                snippet = source_lines[fn.line - 1].strip() if 1 <= fn.line <= len(source_lines) else ""
                issues.append(
                    Issue(
                        code="C003",
                        rule_name="LongFunction",
                        category=IssueCategory.COMPLEXITY,
                        severity=IssueSeverity.LOW,
                        line=fn.line,
                        column=0,
                        message=f"Function '{fn.name}' is too long ({fn.lines_count} lines > 40).",
                        suggestion="Split this function into focused single-responsibility routines.",
                        code_snippet=snippet,
                        ast_node="FunctionDef",
                    )
                )
            if fn.arg_count > 5:
                snippet = source_lines[fn.line - 1].strip() if 1 <= fn.line <= len(source_lines) else ""
                issues.append(
                    Issue(
                        code="C004",
                        rule_name="TooManyArguments",
                        category=IssueCategory.COMPLEXITY,
                        severity=IssueSeverity.LOW,
                        line=fn.line,
                        column=0,
                        message=f"Function '{fn.name}' has {fn.arg_count} parameters (limit: 5).",
                        suggestion="Encapsulate parameters into a dataclass, dictionary, or config object.",
                        code_snippet=snippet,
                        ast_node="FunctionDef",
                    )
                )

        # Sort issues primarily by line number and column
        issues.sort(key=lambda x: (x.line, x.column))

        return syntax_valid, issues, function_metrics, stats
