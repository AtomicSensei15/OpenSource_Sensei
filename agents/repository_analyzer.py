import os
import json
import zipfile
import rarfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from git import Repo, GitCommandError
from github import Github
import requests
from collections import defaultdict
import ast
import logging
from itertools import islice

from .base_agent import BaseAgent, AgentCapability, TaskResult
from .utils.file_analyzer import FileAnalyzer
from .utils.dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)

class RepositoryAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing repository structure, dependencies, and codebase"""
    
    def __init__(self):
        super().__init__(
            agent_id="repo_analyzer",
            name="Repository Analysis Agent",
            description="Analyzes repository structure, dependencies, and codebase characteristics"
        )
        self.file_analyzer = FileAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.supported_archives = {'.zip', '.rar', '.tar', '.tar.gz', '.tgz'}
        self.programming_languages = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.kt': 'Kotlin',
            '.swift': 'Swift',
            '.scala': 'Scala'
        }
    
    async def initialize(self):
        """Initialize the repository analysis agent"""
        logger.info("Repository Analysis Agent initialized")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities"""
        return [
            AgentCapability(
                name="analyze_github_repo",
                description="Analyze a GitHub repository from URL",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string"},
                        "access_token": {"type": "string", "optional": True}
                    },
                    "required": ["repo_url"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "structure": {"type": "object"},
                        "languages": {"type": "object"},
                        "dependencies": {"type": "object"},
                        "metadata": {"type": "object"}
                    }
                }
            ),
            AgentCapability(
                name="analyze_archive",
                description="Analyze uploaded ZIP or RAR archive",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "archive_type": {"type": "string"}
                    },
                    "required": ["file_path", "archive_type"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "structure": {"type": "object"},
                        "languages": {"type": "object"},
                        "dependencies": {"type": "object"},
                        "metadata": {"type": "object"}
                    }
                }
            ),
            AgentCapability(
                name="extract_project_structure",
                description="Extract detailed project structure and organization",
                input_schema={
                    "type": "object",
                    "properties": {
                        "project_path": {"type": "string"}
                    },
                    "required": ["project_path"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "directory_tree": {"type": "object"},
                        "file_summary": {"type": "object"},
                        "architecture_patterns": {"type": "array"}
                    }
                }
            )
        ]
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process repository analysis tasks"""
        task_type = task.get("type")
        
        if task_type == "analyze_github_repo":
            return await self._analyze_github_repo(task["repo_url"], task.get("access_token"))
        elif task_type == "analyze_archive":
            return await self._analyze_archive(task["file_path"], task["archive_type"])
        elif task_type == "extract_project_structure":
            return await self._extract_project_structure(task["project_path"])
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _analyze_github_repo(self, repo_url: str, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a GitHub repository"""
        try:
            # Parse repository URL
            if "github.com" not in repo_url:
                raise ValueError("Invalid GitHub repository URL")
            
            parts = repo_url.rstrip('/').split('/')
            owner = parts[-2]
            repo_name = parts[-1].replace('.git', '')
            
            # Initialize GitHub client
            github_client = Github(access_token) if access_token else Github()
            repo = github_client.get_repo(f"{owner}/{repo_name}")
            
            # Clone repository to temporary directory
            temp_dir = tempfile.mkdtemp()
            try:
                git_repo = Repo.clone_from(repo_url, temp_dir)
                
                # Analyze the cloned repository
                analysis_result = await self._analyze_local_repository(temp_dir)
                # Add GitHub-specific metadata
                analysis_result["metadata"].update({
                    "github_stats": {
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "watchers": repo.watchers_count,
                        "open_issues": repo.open_issues_count,
                        "language": repo.language,
                        "size": repo.size,
                        "created_at": repo.created_at.isoformat(),
                        "updated_at": repo.updated_at.isoformat(),
                        "default_branch": repo.default_branch
                    },
                    "contributors": [
                        name for name in (
                            getattr(c, "login", getattr(c, "name", None))
                            for c in islice(repo.get_contributors(), 10)
                        ) if name
                    ],
                    "topics": repo.get_topics(),
                    "license": repo.license.name if repo.license else None
                })
                
                return analysis_result
                
            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Error analyzing GitHub repository: {e}")
            raise
    
    async def _analyze_archive(self, file_path: str, archive_type: str) -> Dict[str, Any]:
        """Analyze an uploaded archive file"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Extract archive
            if archive_type.lower() in ['.zip']:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif archive_type.lower() in ['.rar']:
                with rarfile.RarFile(file_path, 'r') as rar_ref:
                    rar_ref.extractall(temp_dir)
            else:
                raise ValueError(f"Unsupported archive type: {archive_type}")
            
            # Find the root directory of the extracted files
            extracted_items = os.listdir(temp_dir)
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
                project_root = os.path.join(temp_dir, extracted_items[0])
            else:
                project_root = temp_dir
            
            # Analyze the extracted repository
            return await self._analyze_local_repository(project_root)
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _analyze_local_repository(self, repo_path: str) -> Dict[str, Any]:
        """Analyze a local repository"""
        analysis = {
            "structure": {},
            "languages": {},
            "dependencies": {},
            "metadata": {}
        }
        
        # Extract project structure
        structure_data = await self._extract_project_structure(repo_path)
        analysis["structure"] = structure_data

        # Analyze programming languages (includes code size)
        analysis["languages"] = self._analyze_languages(repo_path)

        # Count total lines of code across recognized source files
        loc_stats = self._count_lines_of_code(repo_path)
        analysis["languages"].update(loc_stats)  # adds total_lines and per-language lines if available

        # Analyze dependencies
        analysis["dependencies"] = await self._analyze_dependencies(repo_path)

        # Extract metadata
        analysis["metadata"] = self._extract_metadata(repo_path)

        # Detect project type (Python vs Node.js vs Mixed etc.)
        analysis["metadata"]["project_type"] = self._detect_project_type(repo_path)

        return analysis
    
    async def _extract_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Extract detailed project structure"""
        structure = {
            "directory_tree": {},
            "file_summary": {
                "total_files": 0,
                "total_directories": 0,
                "file_types": defaultdict(int),
                "largest_files": []
            },
            "architecture_patterns": []
        }
        
        # Build directory tree
        def build_tree(path: str, max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {"...": "truncated"}
            
            tree = {}
            try:
                for item in sorted(os.listdir(path)):
                    if item.startswith('.') and item not in ['.gitignore', '.env.example']:
                        continue
                    
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        tree[f"{item}/"] = build_tree(item_path, max_depth, current_depth + 1)
                        structure["file_summary"]["total_directories"] += 1
                    else:
                        tree[item] = {"type": "file", "size": os.path.getsize(item_path)}
                        structure["file_summary"]["total_files"] += 1
                        
                        # Track file types
                        ext = Path(item).suffix.lower()
                        structure["file_summary"]["file_types"][ext] += 1
                        
                        # Track largest files
                        file_size = os.path.getsize(item_path)
                        structure["file_summary"]["largest_files"].append({
                            "name": item,
                            "size": file_size,
                            "path": os.path.relpath(item_path, project_path)
                        })
            except PermissionError:
                tree["<access_denied>"] = "Permission denied"
            
            return tree
        
        structure["directory_tree"] = build_tree(project_path)
        
        # Sort largest files
        structure["file_summary"]["largest_files"] = sorted(
            structure["file_summary"]["largest_files"],
            key=lambda x: x["size"],
            reverse=True
        )[:10]
        
        # Detect architecture patterns
        structure["architecture_patterns"] = self._detect_architecture_patterns(project_path)
        
        return structure
    
    def _analyze_languages(self, repo_path: str) -> Dict[str, Any]:
        """Analyze programming languages used in the repository"""
        language_stats = defaultdict(int)
        file_count_by_lang = defaultdict(int)
        
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common build/cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.git']]
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = Path(file).suffix.lower()
                
                if ext in self.programming_languages:
                    try:
                        file_size = os.path.getsize(file_path)
                        lang = self.programming_languages[ext]
                        language_stats[lang] += file_size
                        file_count_by_lang[lang] += 1
                    except OSError:
                        continue
        
        # Calculate percentages
        total_size = sum(language_stats.values())
        language_breakdown = {}
        
        for lang, size in language_stats.items():
            percentage = (size / total_size * 100) if total_size > 0 else 0
            language_breakdown[lang] = {
                "bytes": size,
                "percentage": round(percentage, 2),
                "file_count": file_count_by_lang[lang]
            }
        
        return {
            "primary_language": max(language_breakdown.keys(), key=lambda x: language_breakdown[x]["percentage"]) if language_breakdown else None,
            "languages": dict(sorted(language_breakdown.items(), key=lambda x: x[1]["percentage"], reverse=True)),
            "total_code_size": total_size
        }

    def _count_lines_of_code(self, repo_path: str) -> Dict[str, Any]:
        """Count lines of code per language (simple heuristic)"""
        line_counts: Dict[str, int] = defaultdict(int)
        total_lines = 0
        extensions_map = {ext: lang for ext, lang in self.programming_languages.items()}

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.git']]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in extensions_map:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            # Basic line counting ignoring very long binary-looking lines
                            lines = [ln for ln in f.readlines() if ln.strip() and len(ln) < 10000]
                            count = len(lines)
                            line_counts[extensions_map[ext]] += count
                            total_lines += count
                    except Exception:
                        continue

        return {
            "total_lines": total_lines,
            "lines_per_language": dict(sorted(line_counts.items(), key=lambda x: x[1], reverse=True))
        }

    def _detect_project_type(self, repo_path: str) -> str:
        """Detect high-level project type based on sentinel files"""
        has_package_json = os.path.exists(os.path.join(repo_path, 'package.json'))
        has_requirements = os.path.exists(os.path.join(repo_path, 'requirements.txt')) or \
                            any(fname.endswith('.py') for fname in os.listdir(repo_path) if fname.endswith('.py'))
        has_pyproject = os.path.exists(os.path.join(repo_path, 'pyproject.toml'))

        # Priority logic: If both ecosystems present -> Mixed
        if (has_package_json and (has_requirements or has_pyproject)):
            return 'Mixed'
        if has_package_json:
            return 'Node.js'
        if has_requirements or has_pyproject:
            return 'Python'
        # Fallback to primary language if available
        try:
            # Attempt to reuse earlier computed language stats if called after _analyze_languages
            # but since we don't have that passed, recompute cheap heuristic scanning top-level
            for item in os.listdir(repo_path):
                if item.endswith('.go'):
                    return 'Go'
                if item.endswith('.rs'):
                    return 'Rust'
                if item.endswith('.java'):
                    return 'Java'
        except Exception:
            pass
        return 'Unknown'
    
    async def _analyze_dependencies(self, repo_path: str) -> Dict[str, Any]:
        """Analyze project dependencies using DependencyAnalyzer"""
        return self.dependency_analyzer.analyze_project_dependencies(repo_path)
    
    def _parse_package_json(self, file_path: str) -> Dict[str, Any]:
        """Parse package.json file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _parse_requirements_txt(self, file_path: str) -> Dict[str, str]:
        """Parse requirements.txt file"""
        deps = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '==' in line:
                        name, version = line.split('==', 1)
                        deps[name.strip()] = version.strip()
                    elif '>=' in line:
                        name, version = line.split('>=', 1)
                        deps[name.strip()] = f">={version.strip()}"
                    else:
                        deps[line] = "latest"
        return deps
    
    def _parse_pyproject_toml(self, file_path: str) -> Dict[str, Any]:
        """Parse pyproject.toml file"""
        try:
            import toml
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            result = {}
            if 'tool' in data and 'poetry' in data['tool']:
                poetry_data = data['tool']['poetry']
                result['dependencies'] = poetry_data.get('dependencies', {})
                result['dev_dependencies'] = poetry_data.get('dev-dependencies', {})
            
            return result
        except ImportError:
            logger.warning("toml library not available, skipping pyproject.toml parsing")
            return {}
    
    def _extract_metadata(self, repo_path: str) -> Dict[str, Any]:
        """Extract repository metadata"""
        metadata = {
            "readme_files": [],
            "license_files": [],
            "config_files": [],
            "ci_cd_files": [],
            "documentation_dirs": []
        }
        
        # Check for common files
        common_files = {
            "readme": ["README.md", "README.rst", "README.txt", "readme.md"],
            "license": ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"],
            "config": [".gitignore", ".env.example", "config.json", "settings.json"],
            "ci_cd": [".github", ".gitlab-ci.yml", "Jenkinsfile", ".travis.yml", "azure-pipelines.yml"]
        }
        
        for category, files in common_files.items():
            for file_name in files:
                file_path = os.path.join(repo_path, file_name)
                if os.path.exists(file_path):
                    if category == "readme":
                        metadata["readme_files"].append(file_name)
                    elif category == "license":
                        metadata["license_files"].append(file_name)
                    elif category == "config":
                        metadata["config_files"].append(file_name)
                    elif category == "ci_cd":
                        metadata["ci_cd_files"].append(file_name)
        
        # Check for documentation directories
        doc_dirs = ["docs", "documentation", "doc", "wiki"]
        for doc_dir in doc_dirs:
            doc_path = os.path.join(repo_path, doc_dir)
            if os.path.isdir(doc_path):
                metadata["documentation_dirs"].append(doc_dir)
        
        return metadata
    
    def _detect_architecture_patterns(self, repo_path: str) -> List[str]:
        """Detect common architecture patterns"""
        patterns = []
        
        # Check directory structure for patterns
        dirs = []
        for item in os.listdir(repo_path):
            if os.path.isdir(os.path.join(repo_path, item)) and not item.startswith('.'):
                dirs.append(item.lower())
        
        # MVC Pattern
        if any(d in dirs for d in ['models', 'views', 'controllers']) or \
           any(d in dirs for d in ['model', 'view', 'controller']):
            patterns.append("MVC (Model-View-Controller)")
        
        # Microservices
        if 'services' in dirs or 'microservices' in dirs:
            patterns.append("Microservices Architecture")
        
        # Clean Architecture / Hexagonal
        if any(d in dirs for d in ['domain', 'application', 'infrastructure']) or \
           any(d in dirs for d in ['core', 'adapters', 'ports']):
            patterns.append("Clean Architecture")
        
        # Layered Architecture
        if any(d in dirs for d in ['business', 'data', 'presentation']) or \
           any(d in dirs for d in ['dal', 'bll', 'ui']):
            patterns.append("Layered Architecture")
        
        # Component-based (React/Vue/Angular)
        if 'components' in dirs:
            patterns.append("Component-based Architecture")
        
        # Plugin Architecture
        if 'plugins' in dirs or 'extensions' in dirs:
            patterns.append("Plugin Architecture")
        
        return patterns