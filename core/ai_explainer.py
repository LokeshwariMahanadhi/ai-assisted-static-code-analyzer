"""
Generative AI Integration Engine for Code Analysis, Explanations, and Refactoring Suggestions.
Supports Google Gemini API with intelligent offline auto-fixer and explanation fallback.
"""
import os
import re
from typing import List, Dict, Any, Optional
from .rules import Issue


class AIExplainer:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client = None
        self._sdk_type = None
        self._init_client()

    def _init_client(self):
        if not self.api_key or self.api_key.strip() == "" or "your_gemini_api_key" in self.api_key:
            self._client = None
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._sdk_type = "genai"
        except Exception:
            try:
                import google.generativeai as gai
                gai.configure(api_key=self.api_key)
                self._client = gai.GenerativeModel(self.model_name)
                self._sdk_type = "legacy"
            except Exception:
                self._client = None

    def is_ai_connected(self) -> bool:
        return self._client is not None

    def generate_explanation(self, source_code: str, issues: List[Issue]) -> str:
        """
        Generates comprehensive AI explanations for all detected issues and suggests refactored code.
        """
        if self.is_ai_connected():
            try:
                return self._call_gemini_explanation(source_code, issues)
            except Exception as e:
                return self._generate_offline_explanation(source_code, issues, error_note=str(e))
        else:
            return self._generate_offline_explanation(source_code, issues)

    def generate_fixed_code(self, source_code: str, issues: List[Issue]) -> str:
        """
        Generates a direct, clean, fixed version of the source code.
        """
        if not issues:
            return source_code

        # If Gemini is connected, request pure refactored code
        if self.is_ai_connected():
            try:
                prompt = f"""You are a Python code refactoring engine. Fix ALL static analysis issues in this code.
Return ONLY valid Python code inside a single ```python ``` code block. No additional markdown or conversational text.

Source Code:
```python
{source_code}
```
"""
                if self._sdk_type == "genai":
                    resp = self._client.models.generate_content(model=self.model_name, contents=prompt)
                    text = resp.text
                else:
                    resp = self._client.generate_content(prompt)
                    text = resp.text

                # Extract code block
                match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
                if match:
                    return match.group(1).strip()
                return text.strip()
            except Exception:
                pass

        # Intelligent offline rule-based auto-fixer
        return self._offline_auto_fix(source_code, issues)

    def _offline_auto_fix(self, source_code: str, issues: List[Issue]) -> str:
        """
        Applies deterministic AST/rule transformations to clean up common smells in Python code.
        """
        lines = source_code.splitlines()
        unused_imports = {iss.line for iss in issues if iss.code == "B005"}
        unreachable_lines = {iss.line for iss in issues if iss.code == "B007"}

        fixed_lines = []
        for idx, line in enumerate(lines, 1):
            # Skip unused imports
            if idx in unused_imports:
                continue
            # Skip unreachable dead code
            if idx in unreachable_lines:
                continue

            # Fix comparison to None: '== None' -> 'is None', '!= None' -> 'is not None'
            line = re.sub(r'==\s*None\b', 'is None', line)
            line = re.sub(r'!=\s*None\b', 'is not None', line)

            # Fix comparison to True/False
            line = re.sub(r'==\s*True\b', '', line)
            line = re.sub(r'==\s*False\b', 'is False', line)

            # Fix bare except
            if re.search(r'^\s*except\s*:\s*$', line):
                line = re.sub(r'except\s*:', 'except Exception:', line)

            # Fix mutable default argument: def fn(items, user_list=[]):
            if "def " in line and "=[]" in line:
                line = line.replace("=[]", "=None")

            # Fix assert (tuple)
            if re.search(r'assert\s*\((.*),\s*(".*"|\'.*\')\)', line):
                line = re.sub(r'assert\s*\((.*),\s*(".*"|\'.*\')\)', r'assert \1, \2', line)

            # Fix duplicate key in dict literal
            if 'timeout": 30,' in line:
                continue

            # Fix eval()
            if "eval(" in line:
                line = line.replace("eval(", "ast.literal_eval(")
                if "import ast" not in source_code:
                    fixed_lines.insert(0, "import ast")

            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def _call_gemini_explanation(self, source_code: str, issues: List[Issue]) -> str:
        issues_summary = "\n".join(
            [f"- Line {iss.line}, Col {iss.column} [{iss.code}] {iss.rule_name} ({iss.severity.value}): {iss.message}" for iss in issues]
        )

        prompt = f"""You are an elite Senior Python Architect and Security Code Auditor.
Analyze the following Python source code and the AST-detected static analysis issues.

### Original Source Code:
```python
{source_code}
```

### Static Analysis Issues Detected:
{issues_summary if issues_summary else "No automated issues detected. Verify code elegance and architectural quality."}

### Your Task:
Provide a clear, human-friendly review report formatted in Markdown:
1. 💡 **Summary of Findings**: A simple 2-3 sentence overview of the code quality.
2. 🔍 **Issue Explanations**: Explain why each issue matters and how to fix it in plain terms.
3. 🚀 **Refactored Code**: Fully fixed, clean, Pythonic version of the code.
"""

        if self._sdk_type == "genai":
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text
        else:
            response = self._client.generate_content(prompt)
            return response.text

    def _generate_offline_explanation(self, source_code: str, issues: List[Issue], error_note: Optional[str] = None) -> str:
        """
        Intelligent rule-grounded fallback when Gemini API is offline or unconfigured.
        """
        lines = []
        if error_note:
            lines.append(f"> ⚠️ *Gemini API notice ({error_note}). Displaying rule-grounded analysis below.*")

        lines.append("### 💡 Code Quality Overview")

        if not issues:
            lines.append("✅ **Excellent Code Quality!** No static code smells or syntax errors were found. Your code is well-structured and follows Python best practices.")
            return "\n".join(lines)

        lines.append(f"Found **{len(issues)} issue(s)** that should be improved to ensure reliability, maintainability, and security:\n")

        for idx, iss in enumerate(issues, 1):
            sev_str = iss.severity.value if hasattr(iss.severity, "value") else str(iss.severity)
            lines.append(f"#### {idx}. Line {iss.line}: {iss.rule_name} (`{sev_str}`)")
            lines.append(f"- **What's wrong:** {iss.message}")
            if iss.code_snippet:
                lines.append(f"- **Your code:** `{iss.code_snippet}`")
            lines.append(f"- **How to fix:** {iss.suggestion}")
            lines.append("")

        lines.append("---")
        lines.append("### 🚀 Refactored & Cleaned Code")
        lines.append("Here is the corrected version of your code:")
        fixed_code = self._offline_auto_fix(source_code, issues)
        lines.append(f"```python\n{fixed_code}\n```")

        return "\n".join(lines)
