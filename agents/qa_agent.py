"""
Real-Time Q&A Agent for OpenSource Sensei

This agent provides contextual assistance and coaching to users based on their
questions, project context, and specific programming inquiries.
"""

import os
import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import logging
from collections import deque

from .base_agent import BaseAgent, AgentCapability, TaskResult

logger = logging.getLogger(__name__)

class QAAgent(BaseAgent):
    """
    Agent responsible for answering user questions in real-time, providing
    contextual assistance, coaching, and programming guidance.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="qa_agent",
            name="Q&A Agent",
            description="Provides real-time answers to programming questions with contextual awareness"
        )
        # Store recent conversation history for context
        self.conversation_history = deque(maxlen=20)
        # Store project context information
        self.project_context = {}
        # Track user preferences
        self.user_preferences = {}
        # Track active learning topics
        self.learning_topics = set()
        # Maximum age of cached results in seconds (30 minutes)
        self.cache_expiry = 1800
        # Cache for previous answers to similar questions
        self.answer_cache = {}
    
    async def initialize(self):
        """Initialize the Q&A agent with necessary resources"""
        logger.info("Q&A Agent initialized")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        return [
            AgentCapability(
                name="answer_question",
                description="Answer a programming question with context awareness",
                input_schema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "context": {"type": "object", "optional": True},
                        "language": {"type": "string", "optional": True},
                        "code_snippet": {"type": "string", "optional": True}
                    },
                    "required": ["question"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "answer": {"type": "string"},
                        "code_examples": {"type": "array", "optional": True},
                        "references": {"type": "array", "optional": True},
                        "follow_up_questions": {"type": "array", "optional": True}
                    }
                }
            ),
            AgentCapability(
                name="explain_code",
                description="Explain what a code snippet does",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "language": {"type": "string"},
                        "detail_level": {"type": "string", "optional": True},
                        "focus_area": {"type": "string", "optional": True}
                    },
                    "required": ["code", "language"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "explanation": {"type": "string"},
                        "highlighted_sections": {"type": "array", "optional": True},
                        "potential_issues": {"type": "array", "optional": True},
                        "learning_resources": {"type": "array", "optional": True}
                    }
                }
            ),
            AgentCapability(
                name="debug_code",
                description="Help debug a code snippet with errors",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "language": {"type": "string"},
                        "error_message": {"type": "string", "optional": True},
                        "expected_behavior": {"type": "string", "optional": True}
                    },
                    "required": ["code", "language"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "issues": {"type": "array"},
                        "fixes": {"type": "array"},
                        "explanation": {"type": "string"},
                        "improved_code": {"type": "string", "optional": True}
                    }
                }
            ),
            AgentCapability(
                name="suggest_improvements",
                description="Suggest improvements for a code snippet",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "language": {"type": "string"},
                        "focus_areas": {"type": "array", "optional": True}
                    },
                    "required": ["code", "language"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "suggestions": {"type": "array"},
                        "improved_code": {"type": "string", "optional": True},
                        "best_practices": {"type": "array", "optional": True},
                        "learning_resources": {"type": "array", "optional": True}
                    }
                }
            ),
            AgentCapability(
                name="learning_path",
                description="Generate a learning path for a programming topic",
                input_schema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "current_level": {"type": "string", "optional": True},
                        "goal": {"type": "string", "optional": True},
                        "timeframe": {"type": "string", "optional": True}
                    },
                    "required": ["topic"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "steps": {"type": "array"},
                        "resources": {"type": "array"},
                        "projects": {"type": "array", "optional": True},
                        "estimated_timeframes": {"type": "object", "optional": True}
                    }
                }
            )
        ]
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process Q&A tasks"""
        task_type = task.get("type")
        
        # Update conversation history
        self._update_conversation(task)
        
        if task_type == "answer_question":
            return await self._answer_question(
                question=task["question"],
                context=task.get("context", {}),
                language=task.get("language"),
                code_snippet=task.get("code_snippet")
            )
        elif task_type == "explain_code":
            return await self._explain_code(
                code=task["code"],
                language=task["language"],
                detail_level=task.get("detail_level", "medium"),
                focus_area=task.get("focus_area")
            )
        elif task_type == "debug_code":
            return await self._debug_code(
                code=task["code"],
                language=task["language"],
                error_message=task.get("error_message"),
                expected_behavior=task.get("expected_behavior")
            )
        elif task_type == "suggest_improvements":
            return await self._suggest_improvements(
                code=task["code"],
                language=task["language"],
                focus_areas=task.get("focus_areas", [])
            )
        elif task_type == "learning_path":
            return await self._create_learning_path(
                topic=task["topic"],
                current_level=task.get("current_level", "beginner"),
                goal=task.get("goal"),
                timeframe=task.get("timeframe")
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _update_conversation(self, task: Dict[str, Any]):
        """Update conversation history with new task"""
        self.conversation_history.append({
            "timestamp": asyncio.get_event_loop().time(),
            "task_type": task.get("type"),
            "content": task
        })
    
    async def _answer_question(
        self, question: str, context: Optional[Dict[str, Any]] = None, 
        language: Optional[str] = None, code_snippet: Optional[str] = None
    ) -> Dict[str, Any]:
        """Answer a programming question with context awareness"""
        # Check if we have a cached answer for a similar question
        cached_answer = self._check_similar_questions(question, language)
        if cached_answer:
            return cached_answer
        
        # Prepare context for better answering
        contextualized_answer = self._contextualize_answer(
            question, context or {}, language, code_snippet
        )
        
        # In a real implementation, this would use an LLM or knowledge base
        # For now, generate a placeholder answer
        
        # Simulate answer generation
        answer = f"To address your question about '{question}':\n\n"
        
        if language:
            answer += f"In {language}, "
        
        # Add language-specific details if available
        if language == "python":
            answer += "Python provides several ways to solve this problem. "
            answer += "The most Pythonic approach would be to use list comprehensions or built-in functions.\n\n"
        elif language == "javascript":
            answer += "In JavaScript, you can leverage modern ES6+ features to handle this elegantly. "
            answer += "Consider using arrow functions and array methods like map/filter/reduce.\n\n"
        
        # Add generic answer content
        answer += "Here's an explanation of the core concepts involved:\n\n"
        answer += "1. First, understand the problem domain clearly\n"
        answer += "2. Break down the solution into manageable steps\n"
        answer += "3. Implement each step with appropriate error handling\n"
        answer += "4. Test your implementation thoroughly\n\n"
        
        if code_snippet:
            answer += "Regarding your code snippet, here are some observations:\n"
            answer += "- The approach looks generally sound\n"
            answer += "- Consider improving error handling\n"
            answer += "- The logic could be optimized for better performance\n\n"
        
        # Generate code examples
        code_examples = []
        if language:
            if language.lower() == "python":
                code_examples.append({
                    "description": "Basic implementation example",
                    "code": "def example_function(param):\n    # Process the input\n    result = [item for item in param if condition(item)]\n    return result",
                    "explanation": "This example shows a simple implementation using list comprehension."
                })
            elif language.lower() == "javascript":
                code_examples.append({
                    "description": "Basic implementation example",
                    "code": "function exampleFunction(param) {\n  // Process the input\n  const result = param.filter(item => condition(item));\n  return result;\n}",
                    "explanation": "This example shows a simple implementation using array filter method."
                })
            else:
                code_examples.append({
                    "description": "Basic implementation example",
                    "code": f"// {language} implementation\n// Example code would go here",
                    "explanation": f"A basic example in {language}."
                })
        
        # Generate references
        references = [
            {
                "title": "Official Documentation",
                "url": f"https://docs.example.org/{language.lower() if language else 'programming'}/guide"
            },
            {
                "title": "Related Tutorial",
                "url": "https://tutorials.example.org/best-practices"
            }
        ]
        
        # Generate follow-up questions
        follow_up_questions = [
            f"How can I optimize this solution for performance?",
            f"What are common pitfalls when implementing this in {language if language else 'different languages'}?",
            f"Are there any libraries that can simplify this task?"
        ]
        
        result = {
            "answer": answer,
            "code_examples": code_examples,
            "references": references,
            "follow_up_questions": follow_up_questions
        }
        
        # Cache this answer for future reference
        self._cache_answer(question, language, result)
        
        return result
    
    def _contextualize_answer(
        self, question: str, context: Dict[str, Any], 
        language: Optional[str], code_snippet: Optional[str]
    ) -> Dict[str, Any]:
        """Add context to improve answer quality"""
        # This would be implemented with advanced context processing in a real system
        # For now, return a simple context dictionary
        return {
            "question_type": self._classify_question(question),
            "complexity_level": "intermediate",
            "related_topics": self._extract_topics(question),
            "language_context": language,
            "code_context": "present" if code_snippet else "absent"
        }
    
    def _classify_question(self, question: str) -> str:
        """Classify question type for better handling"""
        # Simple rule-based classification
        question_lower = question.lower()
        
        if "how" in question_lower and "to" in question_lower:
            return "how-to"
        elif "what" in question_lower and ("is" in question_lower or "are" in question_lower):
            return "definition"
        elif "why" in question_lower:
            return "explanation"
        elif "difference" in question_lower or "compare" in question_lower:
            return "comparison"
        elif "best" in question_lower or "recommended" in question_lower:
            return "recommendation"
        elif "debug" in question_lower or "error" in question_lower or "not working" in question_lower:
            return "troubleshooting"
        else:
            return "general"
    
    def _extract_topics(self, question: str) -> List[str]:
        """Extract programming topics from question"""
        # Simple keyword-based topic extraction
        # In a real system, this would use NLP and topic modeling
        topics = []
        
        # Check for programming languages
        for lang in ["python", "javascript", "java", "c++", "typescript", "ruby", "go"]:
            if lang in question.lower():
                topics.append(lang)
        
        # Check for common programming topics
        for topic in ["api", "database", "web", "algorithm", "function", "class", 
                     "object", "variable", "debugging", "testing", "framework"]:
            if topic in question.lower():
                topics.append(topic)
        
        return topics
    
    def _check_similar_questions(
        self, question: str, language: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Check if we've answered a similar question before"""
        # Simple similarity check based on keywords
        # In a real system, this would use semantic similarity
        
        # Extract key terms
        terms = set(re.findall(r'\b\w+\b', question.lower()))
        
        # Check cached questions for similarity
        for cached_q, cached_data in self.answer_cache.items():
            cached_terms = set(re.findall(r'\b\w+\b', cached_q.lower()))
            
            # Check if languages match and if there's significant term overlap
            if (not language or cached_data.get("language") == language) and \
               len(terms.intersection(cached_terms)) >= min(len(terms), len(cached_terms)) * 0.7:
                
                # Check if cache is still valid
                if asyncio.get_event_loop().time() - cached_data["timestamp"] < self.cache_expiry:
                    # Clone the result to avoid modifying the cache
                    result = cached_data["data"].copy()
                    result["answer"] = "Based on a similar question you asked earlier:\n\n" + result["answer"]
                    return result
        
        return None
    
    def _cache_answer(
        self, question: str, language: Optional[str], result: Dict[str, Any]
    ):
        """Cache an answer for future reference"""
        self.answer_cache[question] = {
            "data": result,
            "language": language,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Prune cache if it gets too large
        if len(self.answer_cache) > 100:
            # Remove oldest items
            oldest_questions = sorted(
                self.answer_cache.keys(),
                key=lambda q: self.answer_cache[q]["timestamp"]
            )[:20]
            
            for old_q in oldest_questions:
                del self.answer_cache[old_q]
    
    async def _explain_code(
        self, code: str, language: str, 
        detail_level: str = "medium", focus_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """Explain what a code snippet does"""
        # In a real implementation, this would use an LLM or code analysis tool
        # For now, generate a placeholder explanation
        
        # Adjust explanation based on detail level
        if detail_level.lower() == "high":
            detail_multiplier = 2
            detail_prefix = "Detailed explanation"
        elif detail_level.lower() == "low":
            detail_multiplier = 0.5
            detail_prefix = "Brief overview"
        else:  # medium
            detail_multiplier = 1
            detail_prefix = "Explanation"
        
        # Generate basic explanation
        explanation = f"{detail_prefix} of the {language} code:\n\n"
        explanation += "This code appears to be "
        
        # Language-specific details
        if language.lower() == "python":
            explanation += "a Python function that processes some data. "
            explanation += "It likely uses common Python patterns such as list comprehensions, "
            explanation += "conditional statements, and possibly some library functions.\n\n"
        elif language.lower() == "javascript":
            explanation += "a JavaScript function that handles data manipulation. "
            explanation += "It appears to use modern JavaScript features like arrow functions, "
            explanation += "array methods, and possibly ES6+ syntax.\n\n"
        else:
            explanation += f"a {language} code snippet with typical {language} patterns and structures.\n\n"
        
        # Add structure overview
        explanation += "The code structure consists of:\n"
        explanation += "1. Initialization of variables\n"
        explanation += "2. Processing of input data\n"
        explanation += "3. Conditional logic to handle different cases\n"
        explanation += "4. Return of processed results\n\n"
        
        # Add focus area details if specified
        if focus_area:
            explanation += f"Focusing specifically on the {focus_area} aspect:\n"
            explanation += f"The code handles {focus_area} by implementing specialized logic "
            explanation += f"that ensures proper handling of {focus_area}-related concerns.\n\n"
        
        # Add algorithm explanation based on detail level
        if detail_multiplier > 1:
            explanation += "The algorithm works as follows:\n"
            explanation += "1. First, it validates the input data\n"
            explanation += "2. Then, it transforms the data through several processing steps\n"
            explanation += "3. Next, it applies specific business logic rules\n"
            explanation += "4. Finally, it formats the output for the caller\n\n"
            explanation += "Each step includes proper error handling and edge case management.\n\n"
        
        # Add highlighted sections
        highlighted_sections = [
            {
                "line_range": "1-3",
                "description": "Initialization and input validation",
                "importance": "high"
            },
            {
                "line_range": "5-10",
                "description": "Core processing logic",
                "importance": "critical"
            },
            {
                "line_range": "12-15",
                "description": "Result formatting and return",
                "importance": "medium"
            }
        ]
        
        # Add potential issues
        potential_issues = [
            {
                "description": "Lack of comprehensive error handling",
                "impact": "Could lead to unexpected crashes with invalid input",
                "fix": "Add try-except blocks around critical operations"
            },
            {
                "description": "Possible performance bottleneck in data processing",
                "impact": "May slow down with large datasets",
                "fix": "Consider optimizing the algorithm or using more efficient data structures"
            }
        ]
        
        # Add learning resources
        learning_resources = [
            {
                "title": f"Official {language} Documentation",
                "url": f"https://docs.{language.lower()}.org/",
                "type": "documentation"
            },
            {
                "title": f"Advanced {language} Techniques",
                "url": f"https://tutorials.example.org/{language.lower()}/advanced",
                "type": "tutorial"
            }
        ]
        
        return {
            "explanation": explanation,
            "highlighted_sections": highlighted_sections,
            "potential_issues": potential_issues,
            "learning_resources": learning_resources
        }
    
    async def _debug_code(
        self, code: str, language: str, 
        error_message: Optional[str] = None, 
        expected_behavior: Optional[str] = None
    ) -> Dict[str, Any]:
        """Help debug a code snippet with errors"""
        # In a real implementation, this would use code analysis tools
        # For now, generate placeholder debugging help
        
        # Basic debug analysis
        issues = []
        fixes = []
        
        # Add language-specific common issues
        if language.lower() == "python":
            issues = [
                {
                    "type": "syntax",
                    "description": "Potential indentation error in the code",
                    "line_numbers": "5-7",
                    "severity": "high"
                },
                {
                    "type": "logical",
                    "description": "Possible off-by-one error in loop condition",
                    "line_numbers": "10",
                    "severity": "medium"
                },
                {
                    "type": "runtime",
                    "description": "Potential None/null reference when accessing attribute",
                    "line_numbers": "12",
                    "severity": "high"
                }
            ]
            
            fixes = [
                {
                    "issue_type": "syntax",
                    "description": "Fix indentation to be consistent (4 spaces per level)",
                    "line_numbers": "5-7",
                    "code_change": "    # Properly indented code\n    for item in items:\n        process(item)"
                },
                {
                    "issue_type": "logical",
                    "description": "Adjust loop bounds to include the last element",
                    "line_numbers": "10",
                    "code_change": "for i in range(len(items)):  # or for i in range(len(items) - 1):"
                },
                {
                    "issue_type": "runtime",
                    "description": "Add null check before accessing attribute",
                    "line_numbers": "12",
                    "code_change": "if obj is not None and hasattr(obj, 'attribute'):\n    result = obj.attribute"
                }
            ]
        elif language.lower() == "javascript":
            issues = [
                {
                    "type": "syntax",
                    "description": "Missing semicolon or bracket",
                    "line_numbers": "3",
                    "severity": "medium"
                },
                {
                    "type": "logical",
                    "description": "Variable scope issue with closures",
                    "line_numbers": "8-15",
                    "severity": "high"
                },
                {
                    "type": "runtime",
                    "description": "Potential undefined property access",
                    "line_numbers": "12",
                    "severity": "high"
                }
            ]
            
            fixes = [
                {
                    "issue_type": "syntax",
                    "description": "Add missing semicolon or bracket",
                    "line_numbers": "3",
                    "code_change": "const value = calculateValue();"
                },
                {
                    "issue_type": "logical",
                    "description": "Fix variable scope with proper closure handling",
                    "line_numbers": "8-15",
                    "code_change": "items.forEach((item) => {\n  // Use arrow function to preserve 'this' context\n});"
                },
                {
                    "issue_type": "runtime",
                    "description": "Add null/undefined check before property access",
                    "line_numbers": "12",
                    "code_change": "if (obj && obj.property) {\n  result = obj.property;\n}"
                }
            ]
        else:
            # Generic issues for other languages
            issues = [
                {
                    "type": "syntax",
                    "description": f"Possible syntax error in {language} code",
                    "line_numbers": "3-5",
                    "severity": "high"
                },
                {
                    "type": "logical",
                    "description": "Logic flow issue in conditional statements",
                    "line_numbers": "8-10",
                    "severity": "medium"
                }
            ]
            
            fixes = [
                {
                    "issue_type": "syntax",
                    "description": f"Check {language} syntax for this section",
                    "line_numbers": "3-5",
                    "code_change": "// Correct syntax would depend on specific language rules"
                },
                {
                    "issue_type": "logical",
                    "description": "Review conditional logic flow",
                    "line_numbers": "8-10",
                    "code_change": "// Consider restructuring conditions to handle all cases properly"
                }
            ]
        
        # If error message provided, add specific issue
        if error_message:
            error_type = "unknown"
            if "syntax" in error_message.lower():
                error_type = "syntax"
            elif "type" in error_message.lower():
                error_type = "type"
            elif "reference" in error_message.lower():
                error_type = "reference"
            
            issues.append({
                "type": error_type,
                "description": f"Error message indicates a {error_type} issue",
                "line_numbers": "unknown",
                "severity": "high",
                "error_message": error_message
            })
            
            fixes.append({
                "issue_type": error_type,
                "description": f"Address the specific {error_type} error in the message",
                "line_numbers": "unknown",
                "code_change": "// Specific fix would depend on exact error details"
            })
        
        # Generate explanation
        explanation = f"Analysis of the {language} code reveals several potential issues:\n\n"
        
        for issue in issues:
            explanation += f"- {issue['type'].capitalize()} issue: {issue['description']} (line(s) {issue['line_numbers']})\n"
        
        explanation += "\nRecommended fixes:\n\n"
        
        for fix in fixes:
            explanation += f"- For the {fix['issue_type']} issue: {fix['description']} (line(s) {fix['line_numbers']})\n"
        
        # Generate improved code (placeholder)
        improved_code = "// Improved code would replace problematic sections with fixes\n"
        improved_code += "// This would be a complete corrected version in a real implementation"
        
        return {
            "issues": issues,
            "fixes": fixes,
            "explanation": explanation,
            "improved_code": improved_code
        }
    
    async def _suggest_improvements(
        self, code: str, language: str, focus_areas: List[str] = []
    ) -> Dict[str, Any]:
        """Suggest improvements for a code snippet"""
        # In a real implementation, this would use code quality tools and LLMs
        # For now, generate placeholder improvement suggestions
        
        # Default focus areas if none provided
        if not focus_areas:
            focus_areas = ["readability", "performance", "maintainability"]
        
        suggestions = []
        best_practices = []
        
        # Generate language-specific suggestions
        if language.lower() == "python":
            if "readability" in focus_areas:
                suggestions.append({
                    "category": "readability",
                    "description": "Use more descriptive variable names",
                    "line_numbers": "3-10",
                    "example": "# Instead of:\nx = process(y)\n\n# Use:\nprocessed_result = process_data(input_value)"
                })
                
                best_practices.append({
                    "title": "Follow PEP 8 style guide",
                    "description": "PEP 8 provides conventions for Python code layout, naming, etc.",
                    "url": "https://peps.python.org/pep-0008/"
                })
            
            if "performance" in focus_areas:
                suggestions.append({
                    "category": "performance",
                    "description": "Use list comprehensions instead of explicit loops for better performance",
                    "line_numbers": "12-15",
                    "example": "# Instead of:\nresult = []\nfor item in items:\n    if condition(item):\n        result.append(process(item))\n\n# Use:\nresult = [process(item) for item in items if condition(item)]"
                })
                
                best_practices.append({
                    "title": "Prefer built-in functions and libraries",
                    "description": "Python's built-in functions are optimized and often faster than custom implementations",
                    "url": "https://docs.python.org/3/library/functions.html"
                })
            
            if "maintainability" in focus_areas:
                suggestions.append({
                    "category": "maintainability",
                    "description": "Add docstrings to functions and classes",
                    "line_numbers": "1-5",
                    "example": "def process_data(input_value):\n    \"\"\"\n    Process the input data and return the transformed result.\n    \n    Args:\n        input_value: The input data to process\n        \n    Returns:\n        The processed result\n    \"\"\"\n    # Function implementation"
                })
                
                best_practices.append({
                    "title": "Write comprehensive tests",
                    "description": "Use pytest or unittest to ensure code correctness",
                    "url": "https://docs.pytest.org/en/latest/"
                })
        
        elif language.lower() == "javascript":
            if "readability" in focus_areas:
                suggestions.append({
                    "category": "readability",
                    "description": "Use destructuring for cleaner object property access",
                    "line_numbers": "5-8",
                    "example": "// Instead of:\nconst name = user.name;\nconst age = user.age;\n\n// Use:\nconst { name, age } = user;"
                })
                
                best_practices.append({
                    "title": "Follow Airbnb JavaScript Style Guide",
                    "description": "A widely-used style guide for modern JavaScript",
                    "url": "https://github.com/airbnb/javascript"
                })
            
            if "performance" in focus_areas:
                suggestions.append({
                    "category": "performance",
                    "description": "Use map/filter/reduce instead of traditional loops",
                    "line_numbers": "10-15",
                    "example": "// Instead of:\nconst results = [];\nfor (let i = 0; i < items.length; i++) {\n  if (condition(items[i])) {\n    results.push(process(items[i]));\n  }\n}\n\n// Use:\nconst results = items.filter(condition).map(process);"
                })
                
                best_practices.append({
                    "title": "Avoid unnecessary DOM manipulations",
                    "description": "Batch DOM updates for better performance",
                    "url": "https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Introduction"
                })
            
            if "maintainability" in focus_areas:
                suggestions.append({
                    "category": "maintainability",
                    "description": "Use modules to organize code",
                    "line_numbers": "1-20",
                    "example": "// Split code into modules\n// file: data-processing.js\nexport function processData(data) {\n  // Implementation\n}\n\n// file: main.js\nimport { processData } from './data-processing.js';"
                })
                
                best_practices.append({
                    "title": "Write unit tests with Jest",
                    "description": "Jest is a popular testing framework for JavaScript",
                    "url": "https://jestjs.io/"
                })
        
        else:
            # Generic suggestions for other languages
            if "readability" in focus_areas:
                suggestions.append({
                    "category": "readability",
                    "description": "Use clear and descriptive naming",
                    "line_numbers": "all",
                    "example": "// Use descriptive names for variables, functions, and classes"
                })
            
            if "performance" in focus_areas:
                suggestions.append({
                    "category": "performance",
                    "description": "Optimize resource usage",
                    "line_numbers": "all",
                    "example": "// Look for opportunities to reduce memory usage and improve algorithm efficiency"
                })
            
            if "maintainability" in focus_areas:
                suggestions.append({
                    "category": "maintainability",
                    "description": "Add comprehensive comments and documentation",
                    "line_numbers": "all",
                    "example": "// Document the purpose and usage of important code sections"
                })
        
        # Generate learning resources
        learning_resources = [
            {
                "title": f"{language} Best Practices",
                "url": f"https://best-practices.dev/{language.lower()}",
                "type": "guide"
            },
            {
                "title": f"Clean Code in {language}",
                "url": f"https://cleancode.example.org/{language.lower()}",
                "type": "book"
            }
        ]
        
        # Generate improved code (placeholder)
        improved_code = "// An improved version would apply all the suggestions\n"
        improved_code += "// This would be a complete improved version in a real implementation"
        
        return {
            "suggestions": suggestions,
            "improved_code": improved_code,
            "best_practices": best_practices,
            "learning_resources": learning_resources
        }
    
    async def _create_learning_path(
        self, topic: str, current_level: str = "beginner", 
        goal: Optional[str] = None, timeframe: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a learning path for a programming topic"""
        # In a real implementation, this would use educational content APIs and LLMs
        # For now, generate a placeholder learning path
        
        steps = []
        resources = []
        projects = []
        estimated_timeframes = {}
        
        # Normalize level
        level = current_level.lower()
        if level not in ["beginner", "intermediate", "advanced"]:
            level = "beginner"
        
        # Set goal if not provided
        if not goal:
            if level == "beginner":
                goal = f"Achieve intermediate proficiency in {topic}"
            elif level == "intermediate":
                goal = f"Achieve advanced proficiency in {topic}"
            else:
                goal = f"Master {topic} and be able to teach others"
        
        # Set default timeframe if not provided
        if not timeframe:
            timeframe = "3 months"
        
        # Track this as an active learning topic
        self.learning_topics.add(topic)
        
        # Generate steps based on current level
        if level == "beginner":
            steps = [
                {
                    "name": f"Learn {topic} fundamentals",
                    "description": f"Understand the basic concepts and syntax of {topic}",
                    "estimated_duration": "2 weeks",
                    "resources": ["resource1", "resource2"]
                },
                {
                    "name": "Complete basic exercises",
                    "description": f"Practice with simple {topic} exercises to reinforce learning",
                    "estimated_duration": "2 weeks",
                    "resources": ["resource3"]
                },
                {
                    "name": "Build a simple project",
                    "description": f"Apply your knowledge by building a basic {topic} project",
                    "estimated_duration": "2 weeks",
                    "resources": ["resource4", "project1"]
                },
                {
                    "name": "Review and solidify knowledge",
                    "description": "Review what you've learned and identify gaps",
                    "estimated_duration": "1 week",
                    "resources": ["resource5"]
                }
            ]
            
            resources = [
                {
                    "id": "resource1",
                    "title": f"{topic} for Beginners",
                    "type": "course",
                    "url": f"https://beginners-guide.example.org/{topic.lower().replace(' ', '-')}",
                    "description": f"A comprehensive introduction to {topic} for beginners"
                },
                {
                    "id": "resource2",
                    "title": f"{topic} Fundamentals",
                    "type": "documentation",
                    "url": f"https://docs.example.org/{topic.lower().replace(' ', '-')}/fundamentals",
                    "description": f"Official documentation covering {topic} fundamentals"
                },
                {
                    "id": "resource3",
                    "title": f"{topic} Practice Exercises",
                    "type": "exercises",
                    "url": f"https://exercises.example.org/{topic.lower().replace(' ', '-')}/beginner",
                    "description": f"A collection of beginner-level exercises for practicing {topic}"
                },
                {
                    "id": "resource4",
                    "title": f"Building Your First {topic} Project",
                    "type": "tutorial",
                    "url": f"https://tutorials.example.org/{topic.lower().replace(' ', '-')}/first-project",
                    "description": f"Step-by-step guide to building your first {topic} project"
                },
                {
                    "id": "resource5",
                    "title": f"{topic} Knowledge Check",
                    "type": "quiz",
                    "url": f"https://quiz.example.org/{topic.lower().replace(' ', '-')}/beginner",
                    "description": f"Test your knowledge of {topic} fundamentals"
                }
            ]
            
            projects = [
                {
                    "id": "project1",
                    "title": f"Simple {topic} Application",
                    "description": f"Build a simple application using {topic}",
                    "difficulty": "beginner",
                    "estimated_duration": "1-2 weeks",
                    "requirements": [f"Basic {topic} knowledge"],
                    "learning_outcomes": [f"Apply {topic} fundamentals in a real project", "Understand basic project structure"]
                }
            ]
            
            estimated_timeframes = {
                "total": "7 weeks",
                "study_time": "10-15 hours/week",
                "milestones": {
                    "fundamentals": "2 weeks",
                    "basic_exercises": "4 weeks",
                    "first_project": "6 weeks",
                    "knowledge_review": "7 weeks"
                }
            }
        
        elif level == "intermediate":
            steps = [
                {
                    "name": f"Deepen {topic} knowledge",
                    "description": f"Explore advanced concepts and patterns in {topic}",
                    "estimated_duration": "3 weeks",
                    "resources": ["resource1", "resource2"]
                },
                {
                    "name": "Study best practices",
                    "description": f"Learn and apply {topic} best practices and design patterns",
                    "estimated_duration": "2 weeks",
                    "resources": ["resource3"]
                },
                {
                    "name": "Build a complex project",
                    "description": f"Apply your knowledge by building a more complex {topic} project",
                    "estimated_duration": "4 weeks",
                    "resources": ["resource4", "project1"]
                },
                {
                    "name": "Explore related technologies",
                    "description": f"Learn about technologies that complement {topic}",
                    "estimated_duration": "2 weeks",
                    "resources": ["resource5"]
                },
                {
                    "name": "Contribute to open source",
                    "description": f"Make contributions to {topic}-related open source projects",
                    "estimated_duration": "3 weeks",
                    "resources": ["resource6"]
                }
            ]
            
            # Resources would be populated similar to beginner level but with intermediate content
            
            projects = [
                {
                    "id": "project1",
                    "title": f"Advanced {topic} Application",
                    "description": f"Build a more complex application using {topic} and related technologies",
                    "difficulty": "intermediate",
                    "estimated_duration": "3-4 weeks",
                    "requirements": [f"Intermediate {topic} knowledge"],
                    "learning_outcomes": [f"Apply advanced {topic} concepts", "Integrate with related technologies", "Implement best practices"]
                }
            ]
            
            estimated_timeframes = {
                "total": "14 weeks",
                "study_time": "15-20 hours/week",
                "milestones": {
                    "advanced_concepts": "3 weeks",
                    "best_practices": "5 weeks",
                    "complex_project": "9 weeks",
                    "related_tech": "11 weeks",
                    "open_source": "14 weeks"
                }
            }
        
        else:  # advanced
            steps = [
                {
                    "name": f"Master advanced {topic} concepts",
                    "description": f"Dive deep into the most advanced aspects of {topic}",
                    "estimated_duration": "4 weeks",
                    "resources": ["resource1", "resource2"]
                },
                {
                    "name": "Study internals and implementation details",
                    "description": f"Understand how {topic} works under the hood",
                    "estimated_duration": "3 weeks",
                    "resources": ["resource3"]
                },
                {
                    "name": "Build an expert-level project",
                    "description": f"Design and implement a complex, production-quality {topic} project",
                    "estimated_duration": "6 weeks",
                    "resources": ["resource4", "project1"]
                },
                {
                    "name": "Teach and mentor others",
                    "description": f"Solidify your knowledge by teaching {topic} to others",
                    "estimated_duration": "ongoing",
                    "resources": ["resource5"]
                },
                {
                    "name": "Contribute to the {topic} ecosystem",
                    "description": f"Make significant contributions to {topic} or related technologies",
                    "estimated_duration": "ongoing",
                    "resources": ["resource6"]
                }
            ]
            
            # Resources would be populated similar to other levels but with advanced content
            
            projects = [
                {
                    "id": "project1",
                    "title": f"Expert-level {topic} System",
                    "description": f"Design and build a production-quality system using {topic} and related technologies",
                    "difficulty": "advanced",
                    "estimated_duration": "5-6 weeks",
                    "requirements": [f"Advanced {topic} knowledge", "Experience with related technologies"],
                    "learning_outcomes": [f"Master all aspects of {topic}", "Design complex systems", "Implement advanced patterns and techniques"]
                }
            ]
            
            estimated_timeframes = {
                "total": "13+ weeks",
                "study_time": "20+ hours/week",
                "milestones": {
                    "advanced_mastery": "4 weeks",
                    "internals": "7 weeks",
                    "expert_project": "13 weeks",
                    "teaching": "ongoing",
                    "ecosystem_contribution": "ongoing"
                }
            }
        
        return {
            "steps": steps,
            "resources": resources,
            "projects": projects,
            "estimated_timeframes": estimated_timeframes,
            "topic": topic,
            "current_level": current_level,
            "goal": goal,
            "timeframe": timeframe
        }
