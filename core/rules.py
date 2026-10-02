"""
Rule definitions and categories for the AI-Assisted Static Code Analysis Tool.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class IssueSeverity(str, Enum):
    BLOCKER = "BLOCKER"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class IssueCategory(str, Enum):
    SYNTAX = "Syntax & Parsing"
    CODE_SMELL = "Code Smells"
    SECURITY = "Security & Safety"
    COMPLEXITY = "Complexity & Maintainability"
    STYLE = "Style & Conventions"
    PERFORMANCE = "Performance"


@dataclass
class Issue:
    code: str
    rule_name: str
    category: IssueCategory
    severity: IssueSeverity
    line: int
    column: int
    message: str
    suggestion: str
    code_snippet: Optional[str] = None
    ast_node: Optional[str] = None

    def to_dict(self):
        return {
            "code": self.code,
            "rule_name": self.rule_name,
            "category": self.category.value if isinstance(self.category, IssueCategory) else str(self.category),
            "severity": self.severity.value if isinstance(self.severity, IssueSeverity) else str(self.severity),
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet or "",
            "ast_node": self.ast_node or "",
        }


# Standard Rule Catalog
RULES = {
    # Syntax
    "E001": {
        "name": "SyntaxError",
        "category": IssueCategory.SYNTAX,
        "severity": IssueSeverity.BLOCKER,
        "description": "Source code contains invalid Python syntax and cannot be parsed into an AST.",
    },
    # Code Smells & Bugs
    "B001": {
        "name": "MutableDefaultArgument",
        "category": IssueCategory.CODE_SMELL,
        "severity": IssueSeverity.HIGH,
        "description": "Using mutable default arguments (list, dict, set) can lead to shared state across function calls.",
    },
    "B002": {
        "name": "BareExceptClause",
        "category": IssueCategory.CODE_SMELL,
        "severity": IssueSeverity.HIGH,
        "description": "Bare 'except:' clauses catch SystemExit and KeyboardInterrupt, obscuring crashes and interrupts.",
    },
    "B003": {
        "name": "BroadExceptionClause",
        "category": IssueCategory.CODE_SMELL,
        "severity": IssueSeverity.MEDIUM,
        "description": "Catching generic 'Exception' without re-raising or logging can mask unexpected bugs.",
    },
    "B004": {
        "name": "UnusedVariable",
        "category": IssueCategory.CODE_SMELL,
        "severity": IssueSeverity.LOW,
        "description": "Local variable is assigned but never referenced within its enclosing scope.",
    },
    "B005": {
        "name": "UnusedImport",
        "category": IssueCategory.CODE_SMELL,
        "severity": IssueSeverity.LOW,
        "description": "Imported module or symbol is never utilized within the source file.",
    },
    "B006": {
        "name": "ShadowedBuiltin",
        "category": IssueCategory.CODE_SMELL,
        "severity": IssueSeverity.MEDIUM,
        "description": "Variable or parameter name shadows a standard Python built-in function or type.",
    },
    "B007": {
        "name": "UnreachableCode",
        "category": IssueCategory.CODE_SMELL,
        "severity": IssueSeverity.HIGH,
        "description": "Statements located immediately after a return, raise, break, or continue will never execute.",
    },
    "B008": {
        "name": "DuplicateDictionaryKey",
        "category": IssueCategory.CODE_SMELL,
        "severity": IssueSeverity.HIGH,
        "description": "Dictionary literal contains duplicate keys; earlier values will be silently overwritten.",
    },
    "B009": {
        "name": "SingletonComparison",
        "category": IssueCategory.STYLE,
        "severity": IssueSeverity.LOW,
        "description": "Comparisons to None should use 'is' or 'is not' rather than equality operators ('==', '!=').",
    },
    "B010": {
        "name": "BooleanLiteralComparison",
        "category": IssueCategory.STYLE,
        "severity": IssueSeverity.LOW,
        "description": "Direct comparison to True or False is redundant. Use the expression directly or with 'not'.",
    },
    # Security
    "SEC001": {
        "name": "DangerousEvalExec",
        "category": IssueCategory.SECURITY,
        "severity": IssueSeverity.BLOCKER,
        "description": "Use of eval() or exec() poses severe arbitrary code execution vulnerabilities.",
    },
    "SEC002": {
        "name": "HardcodedSecret",
        "category": IssueCategory.SECURITY,
        "severity": IssueSeverity.HIGH,
        "description": "Variable name suggests hardcoded sensitive credential, token, or API key.",
    },
    "SEC003": {
        "name": "AssertOnTuple",
        "category": IssueCategory.SECURITY,
        "severity": IssueSeverity.HIGH,
        "description": "Asserting a non-empty tuple (assert (x, 'msg')) always evaluates to True in Python.",
    },
    # Complexity
    "C001": {
        "name": "HighCyclomaticComplexity",
        "category": IssueCategory.COMPLEXITY,
        "severity": IssueSeverity.HIGH,
        "description": "Function contains too many independent execution paths, making it hard to test and maintain.",
    },
    "C002": {
        "name": "DeepNesting",
        "category": IssueCategory.COMPLEXITY,
        "severity": IssueSeverity.MEDIUM,
        "description": "Excessive nesting depth increases cognitive load and degrades code readability.",
    },
    "C003": {
        "name": "LongFunction",
        "category": IssueCategory.COMPLEXITY,
        "severity": IssueSeverity.LOW,
        "description": "Function exceeds recommended line count (> 40 lines), violating Single Responsibility Principle.",
    },
    "C004": {
        "name": "TooManyArguments",
        "category": IssueCategory.COMPLEXITY,
        "severity": IssueSeverity.LOW,
        "description": "Function accepts too many arguments (> 5), suggesting need for a data class or parameter object.",
    },
    # Style
    "S001": {
        "name": "MissingDocstring",
        "category": IssueCategory.STYLE,
        "severity": IssueSeverity.INFO,
        "description": "Public module, class, or function is missing a docstring explanation.",
    },
    "S002": {
        "name": "SingleCharVariableName",
        "category": IssueCategory.STYLE,
        "severity": IssueSeverity.LOW,
        "description": "Single-character variable names outside standard loop counters reduce readability.",
    },
}
