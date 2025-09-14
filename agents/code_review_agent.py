import ast
import re
import difflib
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseAgent, AgentCapability, TaskResult
from .utils.file_analyzer import FileAnalyzer

logger = logging.getLogger(__name__)

class ReviewSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass 
class CodeIssue:
    """Represents a code review issue"""
    file_path: str
    line_number: int
    column: Optional[int]
    severity: ReviewSeverity
    category: str
    title: str
    description: str
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None

@dataclass
class CodeReviewResult:
    """Result of a code review"""
    issues: List[CodeIssue]
    metrics: Dict[str, Any]
    suggestions: List[str]
    score: float  # 0-100 quality score

class CodeReviewAgent(BaseAgent):
    """Agent responsible for reviewing code changes and suggesting improvements"""
    
    def __init__(self):
        super().__init__(
            agent_id="code_reviewer",
            name="Code Review Agent", 
            description="Analyzes code changes, suggests improvements, and flags potential issues"
        )
        self.file_analyzer = FileAnalyzer()
        self.coding_standards = {}
        self.custom_rules = []
        
        # Initialize built-in rules
        self._setup_built_in_rules()
    
    async def initialize(self):
        """Initialize the code review agent"""
        logger.info("Code Review Agent initialized")
        
    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities"""
        return [
            AgentCapability(
                name="review_code_changes",
                description="Review code changes and provide feedback",
                input_schema={
                    "type": "object",
                    "properties": {
                        "changes": {"type": "array"},
                        "context": {"type": "object"},
                        "standards": {"type": "object", "optional": True}
                    },
                    "required": ["changes"]
                },
                output_schema={
                    "type": "object", 
                    "properties": {
                        "issues": {"type": "array"},
                        "suggestions": {"type": "array"},
                        "score": {"type": "number"}
                    }
                }
            ),
            AgentCapability(
                name="analyze_file_quality",
                description="Analyze code quality of individual files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                        "language": {"type": "string"}
                    },
                    "required": ["file_path", "content"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "quality_score": {"type": "number"},
                        "issues": {"type": "array"},
                        "metrics": {"type": "object"}
                    }
                }
            ),
            AgentCapability(
                name="suggest_best_practices",
                description="Suggest best practices based on language and framework",
                input_schema={
                    "type": "object",
                    "properties": {
                        "language": {"type": "string"},
                        "framework": {"type": "string", "optional": True},
                        "code_sample": {"type": "string"}
                    },
                    "required": ["language", "code_sample"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "recommendations": {"type": "array"},
                        "examples": {"type": "array"}
                    }
                }
            )
        ]
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process code review tasks"""
        task_type = task.get("type")
        
        if task_type == "review_code_changes":
            return await self._review_code_changes(
                task["changes"], 
                task.get("context", {}),
                task.get("standards", {})
            )
        elif task_type == "analyze_file_quality":
            return await self._analyze_file_quality(
                task["file_path"],
                task["content"], 
                task.get("language")
            )
        elif task_type == "suggest_best_practices":
            return await self._suggest_best_practices(
                task["language"],
                task["code_sample"],
                task.get("framework")
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _review_code_changes(self, changes: List[Dict], context: Dict, standards: Dict) -> Dict[str, Any]:
        """Review a set of code changes"""
        all_issues = []
        all_suggestions = []
        total_score = 0
        files_reviewed = 0
        
        for change in changes:
            file_path = change.get("file_path")
            if not file_path:
                continue
                
            old_content = change.get("old_content", "")
            new_content = change.get("new_content", "")
            change_type = change.get("type", "modified")  # added, modified, deleted
            
            if change_type == "deleted":
                continue  # Skip deleted files
            
            # Analyze the new content
            language = self._detect_language(file_path)
            if language:
                file_result = await self._analyze_file_quality(file_path, new_content, language)
                all_issues.extend(file_result["issues"])
                total_score += file_result["quality_score"]
                files_reviewed += 1
            
            # Analyze the diff if it's a modification
            if change_type == "modified" and old_content:
                diff_issues = self._analyze_diff(file_path, old_content, new_content)
                all_issues.extend(diff_issues)
            
            # Check against coding standards
            if standards:
                standard_issues = self._check_coding_standards(file_path, new_content, standards)
                all_issues.extend(standard_issues)
        
        # Calculate overall score
        average_score = total_score / files_reviewed if files_reviewed > 0 else 0
        
        # Generate high-level suggestions
        all_suggestions = self._generate_review_suggestions(all_issues, context)
        
        return {
            "issues": [self._issue_to_dict(issue) for issue in all_issues],
            "suggestions": all_suggestions,
            "score": average_score,
            "metrics": {
                "files_reviewed": files_reviewed,
                "total_issues": len(all_issues),
                "critical_issues": len([i for i in all_issues if i.severity == ReviewSeverity.CRITICAL]),
                "error_issues": len([i for i in all_issues if i.severity == ReviewSeverity.ERROR]),
                "warning_issues": len([i for i in all_issues if i.severity == ReviewSeverity.WARNING])
            }
        }
    
    async def _analyze_file_quality(self, file_path: str, content: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Analyze the quality of a single file"""
        if not language:
            language = self._detect_language(file_path)
        
        issues = []
        metrics = {}
        
        if language == "python":
            issues, metrics = self._analyze_python_file(file_path, content)
        elif language in ["javascript", "typescript"]:
            issues, metrics = self._analyze_javascript_file(file_path, content, language)
        elif language == "java":
            issues, metrics = self._analyze_java_file(file_path, content)
        else:
            # Generic analysis
            issues, metrics = self._analyze_generic_file(file_path, content)
        
        # Calculate quality score based on issues
        quality_score = self._calculate_quality_score(issues, metrics)
        
        return {
            "quality_score": quality_score,
            "issues": [self._issue_to_dict(issue) for issue in issues],
            "metrics": metrics
        }
    
    def _analyze_python_file(self, file_path: str, content: str) -> Tuple[List[CodeIssue], Dict[str, Any]]:
        """Analyze Python file for code quality issues"""
        issues = []
        metrics = {
            "lines_of_code": len([line for line in content.split('\n') if line.strip()]),
            "complexity": 0,
            "functions": 0,
            "classes": 0,
            "docstring_coverage": 0
        }
        
        try:
            tree = ast.parse(content)
            
            # Count functions and classes
            functions_with_docstrings = 0
            classes_with_docstrings = 0
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics["functions"] += 1
                    
                    # Check for docstrings
                    if ast.get_docstring(node):
                        functions_with_docstrings += 1
                    else:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            severity=ReviewSeverity.WARNING,
                            category="documentation",
                            title="Missing docstring",
                            description=f"Function '{node.name}' is missing a docstring",
                            suggestion=f"Add a docstring to explain what '{node.name}' does",
                            rule_id="PY001"
                        ))
                    
                    # Check function length
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        func_length = node.end_lineno - node.lineno
                        if func_length > 50:
                            issues.append(CodeIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                column=node.col_offset,
                                severity=ReviewSeverity.WARNING,
                                category="maintainability",
                                title="Long function",
                                description=f"Function '{node.name}' is {func_length} lines long, consider breaking it down",
                                suggestion="Split this function into smaller, more focused functions",
                                rule_id="PY002"
                            ))
                
                elif isinstance(node, ast.ClassDef):
                    metrics["classes"] += 1
                    
                    # Check for class docstrings
                    if ast.get_docstring(node):
                        classes_with_docstrings += 1
                    else:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            severity=ReviewSeverity.WARNING,
                            category="documentation", 
                            title="Missing class docstring",
                            description=f"Class '{node.name}' is missing a docstring",
                            suggestion=f"Add a docstring to explain the purpose of class '{node.name}'",
                            rule_id="PY003"
                        ))
                
                # Count complexity (simplified)
                elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                    metrics["complexity"] += 1
            
            # Calculate docstring coverage
            total_items = metrics["functions"] + metrics["classes"]
            if total_items > 0:
                metrics["docstring_coverage"] = int((functions_with_docstrings + classes_with_docstrings) / total_items * 100)
        
        except SyntaxError as e:
            issues.append(CodeIssue(
                file_path=file_path,
                line_number=e.lineno or 1,
                column=e.offset,
                severity=ReviewSeverity.ERROR,
                category="syntax",
                title="Syntax Error",
                description=f"Syntax error: {e.msg}",
                rule_id="PY000"
            ))
        
        # Check for common Python issues
        issues.extend(self._check_python_best_practices(file_path, content))
        
        return issues, metrics
    
    def _analyze_javascript_file(self, file_path: str, content: str, language: str) -> Tuple[List[CodeIssue], Dict[str, Any]]:
        """Analyze JavaScript/TypeScript file for code quality issues"""
        issues = []
        metrics = {
            "lines_of_code": len([line for line in content.split('\n') if line.strip()]),
            "functions": 0,
            "classes": 0,
            "complexity": 0
        }
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for console.log statements
            if 'console.log' in line_stripped:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    column=line.find('console.log'),
                    severity=ReviewSeverity.WARNING,
                    category="debugging",
                    title="Console statement found",
                    description="Remove console.log statements before committing",
                    suggestion="Use proper logging framework or remove debugging statements",
                    rule_id="JS001"
                ))
            
            # Check for == instead of ===
            if re.search(r'[^=!]==[^=]', line_stripped):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    column=line_stripped.find('=='),
                    severity=ReviewSeverity.WARNING,
                    category="best_practices",
                    title="Use strict equality",
                    description="Use === instead of == for strict equality comparison",
                    suggestion="Replace == with === for type-safe comparison",
                    rule_id="JS002"
                ))
            
            # Count functions
            if re.search(r'function\s+\w+|const\s+\w+\s*=.*=>', line_stripped):
                metrics["functions"] += 1
            
            # Count classes
            if line_stripped.startswith('class '):
                metrics["classes"] += 1
            
            # Count complexity
            if any(keyword in line_stripped for keyword in ['if', 'for', 'while', 'switch', 'try']):
                metrics["complexity"] += 1
        
        return issues, metrics
    
    def _analyze_java_file(self, file_path: str, content: str) -> Tuple[List[CodeIssue], Dict[str, Any]]:
        """Analyze Java file for code quality issues"""
        issues = []
        metrics = {
            "lines_of_code": len([line for line in content.split('\n') if line.strip()]),
            "methods": 0,
            "classes": 0,
            "complexity": 0
        }
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for System.out.println
            if 'System.out.println' in line_stripped:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    column=line.find('System.out.println'),
                    severity=ReviewSeverity.WARNING,
                    category="debugging",
                    title="Debug statement found",
                    description="Remove System.out.println statements before committing",
                    suggestion="Use proper logging framework instead of System.out.println",
                    rule_id="JAVA001"
                ))
            
            # Count methods
            if re.search(r'(public|private|protected).*\s+\w+\s*\(.*\)\s*{', line_stripped):
                metrics["methods"] += 1
            
            # Count classes
            if re.search(r'(public\s+)?class\s+\w+', line_stripped):
                metrics["classes"] += 1
            
            # Count complexity
            if any(keyword in line_stripped for keyword in ['if', 'for', 'while', 'switch', 'try']):
                metrics["complexity"] += 1
        
        return issues, metrics
    
    def _analyze_generic_file(self, file_path: str, content: str) -> Tuple[List[CodeIssue], Dict[str, Any]]:
        """Generic file analysis for unsupported languages"""
        issues = []
        metrics = {
            "lines_of_code": len([line for line in content.split('\n') if line.strip()]),
            "file_size": len(content)
        }
        
        # Check file size
        if len(content) > 100000:  # 100KB
            issues.append(CodeIssue(
                file_path=file_path,
                line_number=1,
                column=0,
                severity=ReviewSeverity.WARNING,
                category="maintainability",
                title="Large file",
                description=f"File is {len(content)} bytes, consider breaking it down",
                suggestion="Split large files into smaller, more manageable pieces",
                rule_id="GEN001"
            ))
        
        return issues, metrics
    
    def _check_python_best_practices(self, file_path: str, content: str) -> List[CodeIssue]:
        """Check Python-specific best practices"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for bare except clauses
            if line_stripped == 'except:':
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    column=0,
                    severity=ReviewSeverity.WARNING,
                    category="error_handling",
                    title="Bare except clause",
                    description="Avoid bare 'except:' clauses, specify exception type",
                    suggestion="Use 'except Exception:' or specific exception types",
                    rule_id="PY004"
                ))
            
            # Check for mutable default arguments
            if re.search(r'def\s+\w+\([^)]*=\s*(\[\]|\{\})', line_stripped):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    column=0,
                    severity=ReviewSeverity.ERROR,
                    category="bugs",
                    title="Mutable default argument",
                    description="Mutable default arguments can cause unexpected behavior",
                    suggestion="Use None as default and create mutable object inside function",
                    rule_id="PY005"
                ))
        
        return issues
    
    def _analyze_diff(self, file_path: str, old_content: str, new_content: str) -> List[CodeIssue]:
        """Analyze the differences between old and new content"""
        issues = []
        
        # Get the diff
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        
        # Analyze added/modified lines
        line_number = 0
        for line in diff:
            if line.startswith('@@'):
                # Parse line number from diff header
                match = re.search(r'\+(\d+)', line)
                if match:
                    line_number = int(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                # This is an added line
                added_line = line[1:]  # Remove the '+' prefix
                
                # Check for potential issues in added lines
                if 'TODO' in added_line or 'FIXME' in added_line:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=line_number,
                        column=0,
                        severity=ReviewSeverity.INFO,
                        category="maintainability",
                        title="TODO/FIXME comment",
                        description="TODO or FIXME comment found in new code",
                        suggestion="Address TODO/FIXME comments before committing",
                        rule_id="DIFF001"
                    ))
                
                line_number += 1
        
        return issues
    
    def _check_coding_standards(self, file_path: str, content: str, standards: Dict) -> List[CodeIssue]:
        """Check code against provided coding standards"""
        issues = []
        
        # This would check against project-specific coding standards
        # For now, implement basic checks
        
        max_line_length = standards.get('max_line_length', 120)
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if len(line) > max_line_length:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    column=max_line_length,
                    severity=ReviewSeverity.WARNING,
                    category="style",
                    title="Line too long",
                    description=f"Line exceeds {max_line_length} characters",
                    suggestion=f"Break long lines into multiple lines",
                    rule_id="STD001"
                ))
        
        return issues
    
    async def _suggest_best_practices(self, language: str, code_sample: str, framework: Optional[str] = None) -> Dict[str, Any]:
        """Suggest best practices for given language and framework"""
        recommendations = []
        examples = []
        
        if language.lower() == "python":
            recommendations.extend([
                "Follow PEP 8 style guidelines",
                "Use type hints for better code documentation",
                "Write comprehensive docstrings",
                "Use list comprehensions when appropriate",
                "Handle exceptions explicitly"
            ])
            
            examples.extend([
                {
                    "title": "Type hints example",
                    "code": "def calculate_area(width: float, height: float) -> float:\n    return width * height"
                },
                {
                    "title": "Docstring example", 
                    "code": 'def greet(name: str) -> str:\n    """Return a greeting message.\n    \n    Args:\n        name: The person\'s name\n        \n    Returns:\n        A greeting message\n    """\n    return f"Hello, {name}!"'
                }
            ])
        
        elif language.lower() in ["javascript", "typescript"]:
            recommendations.extend([
                "Use const and let instead of var",
                "Use strict equality (===) comparisons", 
                "Handle promises with async/await",
                "Use meaningful variable names",
                "Avoid console.log in production code"
            ])
            
            examples.extend([
                {
                    "title": "Async/await example",
                    "code": "async function fetchData() {\n  try {\n    const response = await fetch('/api/data');\n    return await response.json();\n  } catch (error) {\n    console.error('Error fetching data:', error);\n  }\n}"
                }
            ])
        
        return {
            "recommendations": recommendations,
            "examples": examples
        }
    
    def _calculate_quality_score(self, issues: List[CodeIssue], metrics: Dict[str, Any]) -> float:
        """Calculate a quality score based on issues and metrics"""
        base_score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == ReviewSeverity.CRITICAL:
                base_score -= 20
            elif issue.severity == ReviewSeverity.ERROR:
                base_score -= 10
            elif issue.severity == ReviewSeverity.WARNING:
                base_score -= 5
            elif issue.severity == ReviewSeverity.INFO:
                base_score -= 1
        
        # Bonus for good metrics
        if metrics.get("docstring_coverage", 0) > 80:
            base_score += 5
        
        if metrics.get("complexity", 0) < 10:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _generate_review_suggestions(self, issues: List[CodeIssue], context: Dict) -> List[str]:
        """Generate high-level suggestions based on issues"""
        suggestions = []
        
        issue_counts = {}
        for issue in issues:
            issue_counts[issue.category] = issue_counts.get(issue.category, 0) + 1
        
        # Generate suggestions based on issue patterns
        if issue_counts.get("documentation", 0) > 3:
            suggestions.append("Consider improving code documentation with more docstrings and comments")
        
        if issue_counts.get("debugging", 0) > 0:
            suggestions.append("Remove debugging statements (console.log, print, etc.) before committing")
        
        if issue_counts.get("maintainability", 0) > 2:
            suggestions.append("Focus on code maintainability by breaking down large functions and files")
        
        if issue_counts.get("security", 0) > 0:
            suggestions.append("Address security-related issues before deployment")
        
        return suggestions
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.kt': 'kotlin',
            '.swift': 'swift'
        }
        
        return language_map.get(ext)
    
    def _issue_to_dict(self, issue: CodeIssue) -> Dict[str, Any]:
        """Convert CodeIssue to dictionary for JSON serialization"""
        return {
            "file_path": issue.file_path,
            "line_number": issue.line_number,
            "column": issue.column,
            "severity": issue.severity.value,
            "category": issue.category,
            "title": issue.title,
            "description": issue.description,
            "suggestion": issue.suggestion,
            "rule_id": issue.rule_id
        }
    
    def _setup_built_in_rules(self):
        """Setup built-in code review rules"""
        # This would be expanded with comprehensive rule definitions
        self.custom_rules = [
            {
                "id": "SECURITY001",
                "category": "security",
                "severity": "critical",
                "description": "Hardcoded passwords or API keys detected",
                "pattern": r"(password|api_key|secret_key)\s*=\s*['\"].*['\"]"
            },
            {
                "id": "PERF001", 
                "category": "performance",
                "severity": "warning",
                "description": "Inefficient loop detected",
                "pattern": r"for.*in.*len\("
            }
        ]