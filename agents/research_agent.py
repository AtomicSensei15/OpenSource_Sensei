"""
Research Agent for OpenSource Sensei

This agent searches and retrieves relevant programming resources, examples,
and documentation based on user queries and project context.
"""

import os
import re
import json
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from .base_agent import BaseAgent, AgentCapability, TaskResult

logger = logging.getLogger(__name__)

class ResearchAgent(BaseAgent):
    """
    Agent responsible for researching programming topics, finding relevant resources,
    examples, and documentation based on user queries and project context.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="research_agent",
            name="Research Agent",
            description="Researches programming topics and finds relevant resources, examples, and documentation"
        )
        self.api_keys = {}
        self.search_cache = {}
        self.documentation_sources = {
            "python": ["docs.python.org", "pypi.org", "realpython.com"],
            "javascript": ["developer.mozilla.org", "nodejs.org", "npmjs.com"],
            "java": ["docs.oracle.com/javase", "docs.spring.io"],
            "csharp": ["docs.microsoft.com/dotnet", "learn.microsoft.com/dotnet"],
            "go": ["golang.org/doc", "pkg.go.dev"],
            "rust": ["doc.rust-lang.org", "crates.io"],
            "typescript": ["www.typescriptlang.org/docs", "typescript-lang.org"],
            "cpp": ["en.cppreference.com", "isocpp.org"],
            "php": ["php.net/docs", "laravel.com/docs"],
            "ruby": ["ruby-doc.org", "rubygems.org"],
            "swift": ["swift.org/documentation", "developer.apple.com"],
            "kotlin": ["kotlinlang.org/docs", "developer.android.com"]
        }
        # Maximum age of cached results in seconds (1 hour)
        self.cache_expiry = 3600
    
    async def initialize(self):
        """Initialize the research agent with necessary resources"""
        # Load API keys from environment or config
        self._load_api_keys()
        logger.info("Research Agent initialized")
    
    def _load_api_keys(self):
        """Load API keys for various search and documentation services"""
        # GitHub API
        self.api_keys["github"] = os.environ.get("GITHUB_API_KEY", "")
        # Stack Overflow API
        self.api_keys["stackoverflow"] = os.environ.get("STACKOVERFLOW_API_KEY", "")
        # Google Custom Search API
        self.api_keys["google_cse"] = os.environ.get("GOOGLE_CSE_API_KEY", "")
        self.api_keys["google_cse_id"] = os.environ.get("GOOGLE_CSE_ID", "")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        return [
            AgentCapability(
                name="search_documentation",
                description="Search official documentation for a programming language or library",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "language": {"type": "string"},
                        "library": {"type": "string", "optional": True},
                        "max_results": {"type": "integer", "optional": True}
                    },
                    "required": ["query", "language"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "results": {"type": "array"},
                        "language": {"type": "string"},
                        "documentation_sources": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="find_code_examples",
                description="Find code examples for a programming task or concept",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "language": {"type": "string"},
                        "complexity": {"type": "string", "optional": True},
                        "max_results": {"type": "integer", "optional": True}
                    },
                    "required": ["query", "language"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "examples": {"type": "array"},
                        "language": {"type": "string"},
                        "sources": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="research_best_practices",
                description="Research best practices for a programming task or concept",
                input_schema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "language": {"type": "string", "optional": True},
                        "context": {"type": "string", "optional": True},
                        "max_results": {"type": "integer", "optional": True}
                    },
                    "required": ["topic"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "best_practices": {"type": "array"},
                        "references": {"type": "array"},
                        "related_topics": {"type": "array"}
                    }
                }
            ),
            AgentCapability(
                name="find_libraries",
                description="Find popular libraries or tools for a specific task",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "language": {"type": "string"},
                        "criteria": {"type": "array", "optional": True},
                        "max_results": {"type": "integer", "optional": True}
                    },
                    "required": ["task", "language"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "libraries": {"type": "array"},
                        "comparison": {"type": "object"},
                        "recommendations": {"type": "array"}
                    }
                }
            )
        ]
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process research tasks"""
        # Accept both 'type' and legacy 'task_type' keys
        task_type = task.get("type") or task.get("task_type")
        
        if task_type == "search_documentation":
            return await self._search_documentation(
                query=task["query"],
                language=task["language"],
                library=task.get("library"),
                max_results=task.get("max_results", 5)
            )
        elif task_type == "find_code_examples":
            return await self._find_code_examples(
                query=task["query"],
                language=task["language"],
                complexity=task.get("complexity", "medium"),
                max_results=task.get("max_results", 3)
            )
        elif task_type == "research_best_practices":
            return await self._research_best_practices(
                topic=task["topic"],
                language=task.get("language"),
                context=task.get("context"),
                max_results=task.get("max_results", 5)
            )
        elif task_type == "find_libraries":
            return await self._find_libraries(
                task=task["task"],
                language=task["language"],
                criteria=task.get("criteria", []),
                max_results=task.get("max_results", 5)
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _search_documentation(
        self, query: str, language: str, library: Optional[str] = None, 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Search official documentation for a programming language or library"""
        cache_key = f"doc_{language}_{library}_{query}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        results = []
        sources = []
        
        # Add language-specific documentation sources
        lang_sources = self.documentation_sources.get(language.lower(), [])
        if lang_sources:
            sources.extend(lang_sources)
        
        # Add library-specific documentation source if available
        if library:
            sources.append(f"{library.lower()}.org")
            sources.append(f"docs.{library.lower()}.org")
        
        # Placeholder for actual API calls to search engines or documentation sites
        # In a real implementation, this would use specific APIs for documentation sites
        
        # Simulate results for demonstration
        results = [
            {
                "title": f"{language} Documentation: {query}",
                "url": f"https://docs.{language.lower()}.org/search?q={query}",
                "description": f"Official {language} documentation about {query}",
                "source": f"docs.{language.lower()}.org"
            },
            {
                "title": f"{query} - {language} Examples",
                "url": f"https://www.{language.lower()}.org/examples/{query.lower().replace(' ', '-')}",
                "description": f"Examples of {query} in {language}",
                "source": f"www.{language.lower()}.org"
            }
        ]
        
        if library:
            results.append({
                "title": f"{library} {query} Documentation",
                "url": f"https://docs.{library.lower()}.org/{query.lower().replace(' ', '-')}",
                "description": f"{library} documentation for {query}",
                "source": f"docs.{library.lower()}.org"
            })
        
        # In a real implementation, we would filter and rank results based on relevance
        
        result = {
            "results": results[:max_results],
            "language": language,
            "documentation_sources": sources,
            "query": query
        }
        
        # Cache the result
        self._add_to_cache(cache_key, result)
        
        return result
    
    async def _find_code_examples(
        self, query: str, language: str, complexity: str = "medium", 
        max_results: int = 3
    ) -> Dict[str, Any]:
        """Find code examples for a programming task or concept"""
        cache_key = f"example_{language}_{complexity}_{query}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        examples = []
        sources = []
        
        # Placeholder for actual API calls to GitHub, Stack Overflow, etc.
        # In a real implementation, this would use specific APIs like GitHub Search API
        
        # Simulate results for demonstration
        examples = [
            {
                "title": f"{query} implementation in {language}",
                "code": f"# Example {complexity} complexity {language} code for {query}\n# This is a placeholder for actual code example",
                "explanation": f"This example shows how to implement {query} in {language} with {complexity} complexity.",
                "source": "github.com",
                "url": f"https://github.com/example/{language.lower()}-{query.lower().replace(' ', '-')}"
            },
            {
                "title": f"Simple {query} example - {language}",
                "code": f"# Another {language} example for {query}\n# This is a placeholder for actual code example",
                "explanation": f"A simpler approach to {query} in {language}.",
                "source": "stackoverflow.com",
                "url": f"https://stackoverflow.com/questions/tagged/{language.lower()}+{query.lower().replace(' ', '-')}"
            }
        ]
        
        sources = ["github.com", "stackoverflow.com", f"{language.lower()}.org"]
        
        result = {
            "examples": examples[:max_results],
            "language": language,
            "sources": sources,
            "query": query,
            "complexity": complexity
        }
        
        # Cache the result
        self._add_to_cache(cache_key, result)
        
        return result
    
    async def _research_best_practices(
        self, topic: str, language: Optional[str] = None, 
        context: Optional[str] = None, max_results: int = 5
    ) -> Dict[str, Any]:
        """Research best practices for a programming task or concept"""
        lang_param = f"_{language}" if language else ""
        cache_key = f"best_practices{lang_param}_{topic}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        best_practices = []
        references = []
        related_topics = []
        
        # Placeholder for actual API calls to search engines, blogs, etc.
        # In a real implementation, this would use specific APIs
        
        # Simulate results for demonstration
        language_text = f" in {language}" if language else ""
        context_text = f" for {context}" if context else ""
        
        best_practices = [
            {
                "title": f"Always use proper error handling{language_text}",
                "description": f"When working with {topic}{language_text}{context_text}, make sure to implement proper error handling to improve code robustness.",
                "example": "# Example of proper error handling\ntry:\n    # Your code here\nexcept Exception as e:\n    # Handle error",
                "source": "best-practices.dev"
            },
            {
                "title": f"Follow the principle of least privilege{language_text}",
                "description": f"When implementing {topic}{language_text}{context_text}, always follow the principle of least privilege to improve security.",
                "example": "# Example of principle of least privilege\n# Limit access to only what's necessary",
                "source": "secure-coding.org"
            },
            {
                "title": f"Write comprehensive tests{language_text}",
                "description": f"For {topic}{language_text}{context_text}, ensure you have good test coverage to catch bugs early.",
                "example": "# Example of comprehensive testing\n# Unit tests, integration tests, etc.",
                "source": "testing-best-practices.com"
            }
        ]
        
        references = [
            {"title": f"Best Practices for {topic}{language_text}", "url": f"https://best-practices.dev/{topic.lower().replace(' ', '-')}"},
            {"title": f"Industry Standards for {topic}", "url": f"https://industry-standards.org/{topic.lower().replace(' ', '-')}"}
        ]
        
        related_topics = [
            f"{topic} security concerns",
            f"{topic} performance optimization",
            f"{topic} scalability"
        ]
        
        result = {
            "best_practices": best_practices[:max_results],
            "references": references,
            "related_topics": related_topics,
            "topic": topic,
            "language": language
        }
        
        # Cache the result
        self._add_to_cache(cache_key, result)
        
        return result
    
    async def _find_libraries(
        self, task: str, language: str, criteria: List[str] = [], 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Find popular libraries or tools for a specific task"""
        criteria_str = "_".join(criteria) if criteria else ""
        cache_key = f"libraries_{language}_{task}_{criteria_str}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        libraries = []
        comparison = {}
        recommendations = []
        
        # Placeholder for actual API calls to GitHub, package repositories, etc.
        # In a real implementation, this would use specific APIs
        
        # Simulate results for demonstration
        criteria = criteria or ["popularity", "maintenance", "features"]
        
        # Populate comparison categories
        comparison = {criterion: {} for criterion in criteria}
        
        # Example libraries based on language
        if language.lower() == "python":
            libraries = [
                {"name": "Library1", "stars": 15000, "last_update": "2023-06-15", "description": f"A popular Python library for {task}"},
                {"name": "Library2", "stars": 8000, "last_update": "2023-08-01", "description": f"Another Python solution for {task}"},
                {"name": "Library3", "stars": 5000, "last_update": "2023-09-01", "description": f"A newer Python library for {task} with modern features"}
            ]
            
            # Populate comparison data
            for lib in libraries:
                for criterion in criteria:
                    if criterion == "popularity":
                        comparison[criterion][lib["name"]] = lib["stars"]
                    elif criterion == "maintenance":
                        comparison[criterion][lib["name"]] = lib["last_update"]
                    elif criterion == "features":
                        comparison[criterion][lib["name"]] = ["Feature A", "Feature B"] if lib["name"] == "Library1" else ["Feature A"]
        
        elif language.lower() == "javascript":
            libraries = [
                {"name": "npm-package1", "stars": 25000, "last_update": "2023-07-10", "description": f"A popular JavaScript library for {task}"},
                {"name": "npm-package2", "stars": 12000, "last_update": "2023-08-20", "description": f"Another JavaScript solution for {task}"},
                {"name": "npm-package3", "stars": 7000, "last_update": "2023-09-05", "description": f"A newer JavaScript library for {task}"}
            ]
            
            # Populate comparison data
            for lib in libraries:
                for criterion in criteria:
                    if criterion == "popularity":
                        comparison[criterion][lib["name"]] = lib["stars"]
                    elif criterion == "maintenance":
                        comparison[criterion][lib["name"]] = lib["last_update"]
                    elif criterion == "features":
                        comparison[criterion][lib["name"]] = ["Feature X", "Feature Y"] if lib["name"] == "npm-package1" else ["Feature X"]
        
        else:
            libraries = [
                {"name": f"{language}-lib1", "stars": 10000, "last_update": "2023-06-01", "description": f"A popular {language} library for {task}"},
                {"name": f"{language}-lib2", "stars": 6000, "last_update": "2023-07-15", "description": f"Another {language} solution for {task}"}
            ]
            
            # Populate comparison data
            for lib in libraries:
                for criterion in criteria:
                    if criterion == "popularity":
                        comparison[criterion][lib["name"]] = lib["stars"]
                    elif criterion == "maintenance":
                        comparison[criterion][lib["name"]] = lib["last_update"]
                    elif criterion == "features":
                        comparison[criterion][lib["name"]] = ["Feature 1", "Feature 2"] if lib["name"] == f"{language}-lib1" else ["Feature 1"]
        
        # Generate recommendations
        for lib in libraries[:2]:  # Just recommend top 2 libraries
            recommendations.append({
                "library": lib["name"],
                "reason": f"Recommended for {task} due to its {lib['stars']} GitHub stars and active maintenance (last updated {lib['last_update']}).",
                "use_case": f"Best suited for projects requiring {task} functionality with emphasis on reliability."
            })
        
        result = {
            "libraries": libraries[:max_results],
            "comparison": comparison,
            "recommendations": recommendations,
            "task": task,
            "language": language,
            "criteria": criteria
        }
        
        # Cache the result
        self._add_to_cache(cache_key, result)
        
        return result
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache if it exists and is not expired"""
        if key in self.search_cache:
            cached_item = self.search_cache[key]
            cache_time = cached_item["timestamp"]
            current_time = datetime.now().timestamp()
            
            # Check if cache is still valid
            if current_time - cache_time < self.cache_expiry:
                return cached_item["data"]
        
        return None
    
    def _add_to_cache(self, key: str, data: Dict[str, Any]):
        """Add result to cache with current timestamp"""
        self.search_cache[key] = {
            "data": data,
            "timestamp": datetime.now().timestamp()
        }
        
        # Prune cache if it gets too large (simple implementation)
        if len(self.search_cache) > 1000:
            # Remove oldest items
            oldest_keys = sorted(
                self.search_cache.keys(), 
                key=lambda k: self.search_cache[k]["timestamp"]
            )[:100]
            
            for old_key in oldest_keys:
                del self.search_cache[old_key]

    async def _search_github(self, query: str, language: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search GitHub for code examples and repositories"""
        # This would be implemented with GitHub API in a real system
        # For now, return placeholder data
        return [
            {
                "repo": f"example/{language.lower()}-{query.lower().replace(' ', '-')}",
                "description": f"A {language} implementation of {query}",
                "stars": 1200,
                "url": f"https://github.com/example/{language.lower()}-{query.lower().replace(' ', '-')}"
            },
            {
                "repo": f"another-example/{query.lower().replace(' ', '-')}",
                "description": f"Another approach to {query} in {language}",
                "stars": 800,
                "url": f"https://github.com/another-example/{query.lower().replace(' ', '-')}"
            }
        ][:max_results]
    
    async def _search_stackoverflow(self, query: str, language: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search Stack Overflow for questions and answers"""
        # This would be implemented with Stack Overflow API in a real system
        # For now, return placeholder data
        return [
            {
                "title": f"How to implement {query} in {language}?",
                "url": f"https://stackoverflow.com/questions/123456/{query.lower().replace(' ', '-')}-in-{language.lower()}",
                "score": 25,
                "answer_count": 3
            },
            {
                "title": f"Best practices for {query} using {language}",
                "url": f"https://stackoverflow.com/questions/654321/best-practices-{query.lower().replace(' ', '-')}-{language.lower()}",
                "score": 42,
                "answer_count": 5
            }
        ][:max_results]
