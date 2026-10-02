# 🛡️ AI-Assisted Static Code Analysis Tool

**Timeline:** Jun 2026 – Aug 2026  
**Tech Stack:** Python 3.10+, AST (Abstract Syntax Tree), Generative AI (Google Gemini), Streamlit, Plotly, Pytest

---

## 📌 Project Overview

**AI-Assisted Static Code Analysis Tool** is an automated code inspection and quality assurance platform designed to parse Python source code, perform line-level code smell detection, calculate cyclomatic complexity, evaluate architectural health scores, and synthesize LLM-powered refactoring suggestions using Generative AI.

---

## 🚀 Key Highlights & Resume Summary

- **AST-Based Static Analysis Engine**: Developed a Python-based static analysis tool to parse source code into an Abstract Syntax Tree (AST) and identify common code smells, bug patterns, and security vulnerabilities.
- **Line-Level Issue Detection & Automated Reporting**: Implemented visitor-based AST node inspection and automated reporting with precise line numbers, columns, severity classification, and remediation advice.
- **Generative AI Integration**: Integrated Google Gemini API to provide deep-dive root cause explanations, security impact evaluations, and complete production-ready refactored code (with built-in offline intelligent fallback).
- **Comprehensive Benchmark & Evaluation Matrix**: Created standardized test cases and benchmark suites (`clean_code.py`, `code_smells.py`, `syntax_error.py`, `security_issues.py`, `complex_algorithm.py`) to evaluate detection accuracy across multiple code samples.
- **Interactive Web Dashboard & CLI**: Built a modern Streamlit web dashboard featuring interactive metric cards, complexity visualizations, AST tree explorer, and one-click JSON/Markdown report exports.

---

## 📂 Project Architecture

```
AI_Code_Reviewer/
│
├── core/
│   ├── __init__.py              # Core package entrypoint
│   ├── ast_inspector.py         # Advanced AST Visitor & line-level smell detector
│   ├── rules.py                 # Rule definitions, severities & categories
│   ├── complexity.py            # Cyclomatic complexity (McCabe) & nesting analyzer
│   ├── scorer.py                # Health index & weighted grading algorithm
│   ├── ai_explainer.py          # Gemini API integration & offline explanation fallback
│   └── reporter.py              # JSON & Markdown report generation
│
├── samples/                     # Standardized evaluation test samples
│   ├── clean_code.py            # Production-ready, fully compliant code
│   ├── code_smells.py           # Mutable defaults, bare excepts, dead code, etc.
│   ├── syntax_error.py          # Syntax broken code
│   ├── security_issues.py       # eval(), hardcoded secrets, tuple assertions
│   └── complex_algorithm.py     # High cyclomatic complexity & deep nesting
│
├── tests/                       # Pytest test suite & accuracy benchmarks
│   ├── __init__.py
│   ├── test_ast_inspector.py    # Unit tests for AST inspections
│   ├── test_scorer.py           # Unit tests for scoring & health index
│   ├── test_ai_explainer.py     # Unit tests for AI reasoning
│   └── test_benchmark.py        # Benchmark accuracy evaluation
│
├── app.py                       # Modern Streamlit Web Application
├── cli.py                       # Command-line interface for terminal / CI/CD
├── requirements.txt             # Pinned package dependencies
├── .env.example                 # Environment variables template
└── README.md                    # Project documentation
```

---

## 🔍 Supported Static Analysis Rules

| Code | Rule Name | Category | Severity | Description |
| :--- | :--- | :--- | :--- | :--- |
| `E001` | `SyntaxError` | Syntax | **BLOCKER** | Syntax errors preventing AST tree construction |
| `B001` | `MutableDefaultArgument` | Code Smells | **HIGH** | Mutable defaults (`[]`, `{}`) causing shared state |
| `B002` | `BareExceptClause` | Code Smells | **HIGH** | Bare `except:` catching `KeyboardInterrupt` / `SystemExit` |
| `B003` | `BroadExceptionClause` | Code Smells | **MEDIUM** | Catching generic `Exception` without re-raise |
| `B004` | `UnusedVariable` | Code Smells | **LOW** | Assigned local variable never referenced |
| `B005` | `UnusedImport` | Code Smells | **LOW** | Imported module or symbol not referenced |
| `B006` | `ShadowedBuiltin` | Code Smells | **MEDIUM** | Variable or param shadowing built-in (`id`, `list`, etc.) |
| `B007` | `UnreachableCode` | Code Smells | **HIGH** | Dead code immediately following `return` or `raise` |
| `B008` | `DuplicateDictionaryKey` | Code Smells | **HIGH** | Duplicate dictionary keys silently overwritten |
| `B009` | `SingletonComparison` | Style | **LOW** | Comparison to `None` using `==` instead of `is` |
| `B010` | `BooleanLiteralComparison` | Style | **LOW** | Redundant comparison to `True` or `False` |
| `SEC001`| `DangerousEvalExec` | Security | **BLOCKER** | Dynamic code execution (`eval`, `exec`) |
| `SEC002`| `HardcodedSecret` | Security | **HIGH** | Hardcoded tokens or API credentials |
| `SEC003`| `AssertOnTuple` | Security | **HIGH** | Tuple assertion `assert (x, msg)` always True |
| `C001` | `HighCyclomaticComplexity`| Complexity | **HIGH** | McCabe complexity > 10 |
| `C002` | `DeepNesting` | Complexity | **MEDIUM** | Block nesting depth > 4 levels |
| `C003` | `LongFunction` | Complexity | **LOW** | Function length > 40 lines |
| `C004` | `TooManyArguments` | Complexity | **LOW** | Parameter count > 5 |
| `S001` | `MissingDocstring` | Style | **INFO** | Public class/function missing docstring |
| `S002` | `SingleCharVariableName` | Style | **LOW** | Ambiguous single-letter variables |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository & Activate Environment

```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ (Optional) Configure Gemini API Key

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Add your API key from [Google AI Studio](https://aistudio.google.com/):
```env
GEMINI_API_KEY=your_actual_gemini_api_key
```
*(Note: If no API key is supplied, the tool automatically uses its built-in Intelligent Rule-Grounded Explanations engine)*.

---

## 🖥️ Running the Application

### 🌐 Web Dashboard (Streamlit)

```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 💻 Command-Line Interface (CLI)

```bash
# Analyze a single file
python cli.py --file samples/code_smells.py

# Analyze a directory
python cli.py --dir samples/

# Run analysis with Generative AI
python cli.py --file samples/security_issues.py --ai

# Run accuracy benchmark across test samples
python cli.py --benchmark
```

---

## 🧪 Running Automated Tests & Benchmarks

Run the full pytest suite:

```bash
pytest -v
```

---

## 📊 Scoring & Health Index Formula

- **Base Score:** 100.0
- **Penalties:**
  - `BLOCKER`: -30 pts
  - `HIGH`: -10 pts
  - `MEDIUM`: -5 pts
  - `LOW`: -2 pts
  - `INFO`: -1 pt
- **Grades:**
  - `A+` (95 - 100): Outstanding (Production Ready)
  - `A` (85 - 94): Excellent
  - `B` (75 - 84): Good
  - `C` (60 - 74): Average / Needs Refactoring
  - `D` (40 - 59): Poor Quality
  - `F` (< 40 or Syntax Error): Critical Remediation Required

---

## 📜 License
MIT License. Developed for static code analysis and AI-assisted software quality engineering.
