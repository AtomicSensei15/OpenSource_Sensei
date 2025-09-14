"""
Dependency analysis utilities for detecting and analyzing project dependencies
across various programming languages and package managers.

Optional dependencies:
- toml: For parsing TOML files (pyproject.toml, Pipfile, Cargo.toml)
  Install with: pip install toml
"""

import os
import json
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DependencyAnalyzer:
    """
    Analyzes project dependencies across various programming languages and package managers.
    
    This class provides a comprehensive analysis of software dependencies in a project,
    supporting multiple programming languages and their package managers. It can detect
    dependencies from configuration files, analyze versions, check for security
    vulnerabilities, and provide recommendations for dependency management.
    
    Supported languages and package managers:
    - Python: pip (requirements.txt), pipenv (Pipfile), poetry (pyproject.toml), setup.py
    - JavaScript: npm (package.json, package-lock.json), yarn (yarn.lock)
    - Java: Maven (pom.xml), Gradle (build.gradle)
    - Rust: Cargo (Cargo.toml)
    - Go: Go modules (go.mod)
    - PHP: Composer (composer.json)
    - Ruby: Bundler (Gemfile)
    
    Examples:
        # Basic dependency analysis
        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_project_dependencies("/path/to/project")
        
        # Get the list of package managers detected
        package_managers = dependencies["package_managers"]
        print(f"Detected package managers: {', '.join(package_managers)}")
        
        # Get direct dependencies
        direct_deps = dependencies["dependencies"]
        print(f"Total direct dependencies: {len(direct_deps)}")
        
        # Check for security issues
        security_issues = dependencies["security_issues"]
        for issue in security_issues:
            print(f"Security issue in {issue['package']} {issue['version']}: {issue['description']}")
        
        # Get dependency recommendations
        recommendations = analyzer.get_dependency_recommendations("/path/to/project")
        for sec_update in recommendations["security_updates"]:
            print(f"Security update: {sec_update['recommendation']}")
    """
    
    def __init__(self):
        """Initialize the dependency analyzer with supported package managers"""
        self.supported_package_managers = {
            # Python package managers
            'pip': {
                'files': ['requirements.txt'],
                'parser': self._parse_requirements_txt
            },
            'pipenv': {
                'files': ['Pipfile', 'Pipfile.lock'],
                'parser': self._parse_pipfile
            },
            'poetry': {
                'files': ['pyproject.toml'],
                'parser': self._parse_pyproject_toml
            },
            'setup.py': {
                'files': ['setup.py'],
                'parser': self._parse_setup_py
            },
            
            # JavaScript package managers
            'npm': {
                'files': ['package.json', 'package-lock.json'],
                'parser': self._parse_package_json
            },
            'yarn': {
                'files': ['yarn.lock'],
                'parser': self._parse_yarn_lock
            },
            
            # Java package managers
            'maven': {
                'files': ['pom.xml'],
                'parser': self._parse_pom_xml
            },
            'gradle': {
                'files': ['build.gradle', 'build.gradle.kts'],
                'parser': self._parse_gradle
            },
            
            # Other package managers
            'cargo': {
                'files': ['Cargo.toml'],
                'parser': self._parse_cargo_toml
            },
            'go': {
                'files': ['go.mod'],
                'parser': self._parse_go_mod
            },
            'composer': {
                'files': ['composer.json'],
                'parser': self._parse_composer_json
            },
            'gemfile': {
                'files': ['Gemfile', 'Gemfile.lock'],
                'parser': self._parse_gemfile
            }
        }
        
        # Default vulnerability database update time
        self.last_vulnerability_db_update = None
    
    def analyze_project_dependencies(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze dependencies for a project across all supported package managers.
        
        This is the main entry point for dependency analysis. It scans the project
        directory for configuration files from various package managers, analyzes
        dependencies from each detected package manager, and consolidates the results.
        
        The analysis includes:
        - Detection of package managers used in the project
        - Direct dependencies and their versions
        - Development dependencies
        - Security vulnerability scanning (placeholder implementation)
        - Outdated package detection (placeholder implementation)
        - Dependency statistics
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary containing:
            - package_managers: List of detected package managers
            - dependencies: Dict of direct dependencies and versions
            - dev_dependencies: Dict of development dependencies
            - peer_dependencies: Dict of peer dependencies (for JS)
            - transitive_dependencies: Dict of transitive dependencies
            - security_issues: List of detected security issues
            - outdated_packages: List of outdated packages
            - stats: Statistics about dependencies and security issues
            
        Raises:
            ValueError: If project_path is not a directory
            
        Example:
            ```python
            analyzer = DependencyAnalyzer()
            result = analyzer.analyze_project_dependencies("./my_project")
            
            # Print detected package managers
            print(f"Detected package managers: {result['package_managers']}")
            
            # Print total dependencies
            print(f"Total dependencies: {result['stats']['total_dependencies']}")
            
            # Print security issues
            for issue in result['security_issues']:
                print(f"Security issue: {issue['id']} in {issue['package']}")
            ```
        """
        if not os.path.isdir(project_path):
            raise ValueError(f"Project path {project_path} is not a directory")
        
        result = {
            "package_managers": [],
            "dependencies": {},
            "dev_dependencies": {},
            "peer_dependencies": {},
            "transitive_dependencies": {},
            "dependency_graph": {},
            "security_issues": [],
            "outdated_packages": [],
            "stats": {
                "total_dependencies": 0,
                "direct_dependencies": 0,
                "dev_dependencies": 0,
                "critical_security_issues": 0,
                "high_security_issues": 0,
                "medium_security_issues": 0,
                "low_security_issues": 0
            }
        }
        
        # Detect package managers by looking for their configuration files
        detected_managers = self._detect_package_managers(project_path)
        result["package_managers"] = list(detected_managers.keys())
        
        # Parse dependencies for each detected package manager
        for manager, file_paths in detected_managers.items():
            logger.info(f"Analyzing dependencies for {manager}")
            
            try:
                manager_config = self.supported_package_managers.get(manager)
                if not manager_config:
                    logger.warning(f"No parser configuration for {manager}")
                    continue
                
                parser = manager_config['parser']
                
                # Parse each configuration file for this package manager
                for file_path in file_paths:
                    deps_result = parser(file_path)
                    
                    # Merge dependencies into the result
                    if deps_result.get("dependencies"):
                        result["dependencies"].update(deps_result.get("dependencies", {}))
                    
                    if deps_result.get("dev_dependencies"):
                        result["dev_dependencies"].update(deps_result.get("dev_dependencies", {}))
                    
                    if deps_result.get("peer_dependencies"):
                        result["peer_dependencies"].update(deps_result.get("peer_dependencies", {}))
                    
                    if deps_result.get("transitive_dependencies"):
                        result["transitive_dependencies"].update(deps_result.get("transitive_dependencies", {}))
                    
            except Exception as e:
                logger.error(f"Error analyzing dependencies for {manager}: {e}")
        
        # Update stats
        result["stats"]["direct_dependencies"] = len(result["dependencies"])
        result["stats"]["dev_dependencies"] = len(result["dev_dependencies"])
        result["stats"]["total_dependencies"] = (
            len(result["dependencies"]) + 
            len(result["dev_dependencies"]) + 
            len(result["transitive_dependencies"])
        )
        
        # Check for security issues
        security_issues = self._check_security_issues(result["dependencies"])
        result["security_issues"] = security_issues
        
        # Count security issues by severity
        for issue in security_issues:
            severity = issue.get("severity", "").lower()
            if severity == "critical":
                result["stats"]["critical_security_issues"] += 1
            elif severity == "high":
                result["stats"]["high_security_issues"] += 1
            elif severity == "medium":
                result["stats"]["medium_security_issues"] += 1
            elif severity == "low":
                result["stats"]["low_security_issues"] += 1
        
        # Check for outdated packages
        result["outdated_packages"] = self._check_outdated_packages(result["dependencies"])
        
        return result
    
    def _detect_package_managers(self, project_path: str) -> Dict[str, List[str]]:
        """
        Detect package managers used in the project by looking for configuration files
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary of detected package managers and their config file paths
        """
        detected = {}
        
        for manager, config in self.supported_package_managers.items():
            for file_pattern in config['files']:
                # Look for the file in the project root
                file_path = os.path.join(project_path, file_pattern)
                if os.path.exists(file_path):
                    if manager not in detected:
                        detected[manager] = []
                    detected[manager].append(file_path)
        
        return detected
    
    def _parse_requirements_txt(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Python requirements.txt file
        
        Args:
            file_path: Path to requirements.txt file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                        
                    # Skip options (lines starting with -)
                    if line.startswith('-'):
                        continue
                        
                    # Handle dependencies with version specifiers
                    if '==' in line:
                        name, version = line.split('==', 1)
                        result["dependencies"][name.strip()] = version.strip()
                    elif '>=' in line:
                        name, version = line.split('>=', 1)
                        result["dependencies"][name.strip()] = f">={version.strip()}"
                    elif '<=' in line:
                        name, version = line.split('<=', 1)
                        result["dependencies"][name.strip()] = f"<={version.strip()}"
                    elif '~=' in line:
                        name, version = line.split('~=', 1)
                        result["dependencies"][name.strip()] = f"~={version.strip()}"
                    elif '>' in line:
                        name, version = line.split('>', 1)
                        result["dependencies"][name.strip()] = f">{version.strip()}"
                    elif '<' in line:
                        name, version = line.split('<', 1)
                        result["dependencies"][name.strip()] = f"<{version.strip()}"
                    # Handle direct GitHub/URL dependencies
                    elif 'git+' in line or 'http' in line:
                        parts = line.split('#')
                        if len(parts) > 1 and 'egg=' in parts[1]:
                            egg_part = parts[1].split('egg=')[1]
                            name = egg_part.split('&')[0]
                            result["dependencies"][name.strip()] = "git-dependency"
                        else:
                            # Just use the URL as the name if we can't extract it
                            result["dependencies"][line] = "url-dependency"
                    # Just package name without version
                    else:
                        result["dependencies"][line.strip()] = "latest"
                        
        except Exception as e:
            logger.error(f"Error parsing requirements.txt {file_path}: {e}")
        
        return result
    
    def _parse_pyproject_toml(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Python pyproject.toml file used by Poetry, Flit, etc.
        
        Args:
            file_path: Path to pyproject.toml file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {}
        }
        
        try:
            # Try to import toml module
            try:
                import toml  # Optional dependency - install with: pip install toml
            except ImportError:
                logger.warning("Toml module not available, using basic parsing for pyproject.toml")
                return self._basic_parse_pyproject_toml(file_path)
            
            # Parse the toml file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Check for Poetry dependencies
            if 'tool' in data and 'poetry' in data['tool']:
                poetry_data = data['tool']['poetry']
                
                # Regular dependencies
                if 'dependencies' in poetry_data:
                    for name, version in poetry_data['dependencies'].items():
                        if name.lower() == 'python':  # Skip Python version specification
                            continue
                        
                        if isinstance(version, dict):
                            # Complex version specifier like {version = "^1.2.3", extras = ["dev"]}
                            if 'version' in version:
                                result["dependencies"][name] = version['version']
                            else:
                                result["dependencies"][name] = "complex-dependency"
                        else:
                            result["dependencies"][name] = version
                
                # Development dependencies
                if 'dev-dependencies' in poetry_data:
                    for name, version in poetry_data['dev-dependencies'].items():
                        if isinstance(version, dict):
                            if 'version' in version:
                                result["dev_dependencies"][name] = version['version']
                            else:
                                result["dev_dependencies"][name] = "complex-dependency"
                        else:
                            result["dev_dependencies"][name] = version
            
            # Check for PDM dependencies
            elif 'tool' in data and 'pdm' in data['tool'] and 'dependencies' in data['tool']['pdm']:
                pdm_data = data['tool']['pdm']
                
                # Regular dependencies
                for name, version in pdm_data.get('dependencies', {}).items():
                    result["dependencies"][name] = version
                
                # Development dependencies
                dev_deps = pdm_data.get('dev-dependencies', {})
                for group, deps in dev_deps.items():
                    for name, version in deps.items():
                        result["dev_dependencies"][name] = version
            
            # Check for PEP 621 standard dependencies
            elif 'project' in data and 'dependencies' in data['project']:
                # Regular dependencies
                for dep in data['project']['dependencies']:
                    # Handle complex dependencies like "package[extra] >= 1.0.0"
                    match = re.match(r'([a-zA-Z0-9_\-\.]+)(\[[a-zA-Z0-9_\-\.]+\])?\s*(.*)', dep)
                    if match:
                        name = match.group(1)
                        version = match.group(3).strip() if match.group(3) else "latest"
                        result["dependencies"][name] = version
                    else:
                        # Just use the whole string as the name if we can't parse
                        result["dependencies"][dep] = "latest"
                
                # Optional dependencies are like dev dependencies
                if 'optional-dependencies' in data['project']:
                    for group, deps in data['project']['optional-dependencies'].items():
                        for dep in deps:
                            match = re.match(r'([a-zA-Z0-9_\-\.]+)(\[[a-zA-Z0-9_\-\.]+\])?\s*(.*)', dep)
                            if match:
                                name = match.group(1)
                                version = match.group(3).strip() if match.group(3) else "latest"
                                result["dev_dependencies"][name] = version
                            else:
                                result["dev_dependencies"][dep] = "latest"
            
        except Exception as e:
            logger.error(f"Error parsing pyproject.toml {file_path}: {e}")
        
        return result
    
    def _basic_parse_pyproject_toml(self, file_path: str) -> Dict[str, Any]:
        """
        Basic parsing of pyproject.toml without toml module
        
        Args:
            file_path: Path to pyproject.toml file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Very basic regex-based parsing, not as reliable as proper TOML parsing
            dependencies_section = re.search(r'\[tool\.poetry\.dependencies\](.*?)(\[|\Z)', content, re.DOTALL)
            if dependencies_section:
                deps_text = dependencies_section.group(1)
                for line in deps_text.strip().split('\n'):
                    line = line.strip()
                    if line and '=' in line:
                        parts = line.split('=', 1)
                        name = parts[0].strip().strip('"\'')
                        if name.lower() != 'python':  # Skip Python version
                            version = parts[1].strip().strip('"\'')
                            result["dependencies"][name] = version
            
            # Look for dev-dependencies section
            dev_dependencies_section = re.search(r'\[tool\.poetry\.dev-dependencies\](.*?)(\[|\Z)', content, re.DOTALL)
            if dev_dependencies_section:
                deps_text = dev_dependencies_section.group(1)
                for line in deps_text.strip().split('\n'):
                    line = line.strip()
                    if line and '=' in line:
                        parts = line.split('=', 1)
                        name = parts[0].strip().strip('"\'')
                        version = parts[1].strip().strip('"\'')
                        result["dev_dependencies"][name] = version
            
        except Exception as e:
            logger.error(f"Error basic parsing pyproject.toml {file_path}: {e}")
        
        return result
    
    def _parse_setup_py(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Python setup.py file to extract dependencies
        
        Args:
            file_path: Path to setup.py file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # First try AST parsing for more accurate results
            try:
                tree = ast.parse(content)
                
                # Look for setup() function call
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and hasattr(node, 'func'):
                        if (isinstance(node.func, ast.Name) and node.func.id == 'setup') or \
                           (isinstance(node.func, ast.Attribute) and node.func.attr == 'setup'):
                            
                            # Extract keywords from setup function call
                            for keyword in node.keywords:
                                # Check for install_requires parameter
                                if keyword.arg == 'install_requires':
                                    if isinstance(keyword.value, ast.List):
                                        for elt in keyword.value.elts:
                                            if isinstance(elt, ast.Str):
                                                self._parse_req_string(elt.s, result["dependencies"])
                                    elif isinstance(keyword.value, ast.Name):
                                        # If it's a variable, we try regex as fallback
                                        var_name = keyword.value.id
                                        var_pattern = rf'{var_name}\s*=\s*\[(.*?)\]'
                                        var_match = re.search(var_pattern, content, re.DOTALL)
                                        if var_match:
                                            for dep in re.finditer(r'[\'"](.+?)[\'"]', var_match.group(1)):
                                                self._parse_req_string(dep.group(1), result["dependencies"])
                                
                                # Check for extras_require parameter for dev dependencies
                                elif keyword.arg == 'extras_require':
                                    if isinstance(keyword.value, ast.Dict):
                                        for key, value in zip(keyword.value.keys, keyword.value.values):
                                            if isinstance(key, ast.Str) and isinstance(value, ast.List):
                                                extras_deps = {}
                                                for elt in value.elts:
                                                    if isinstance(elt, ast.Str):
                                                        self._parse_req_string(elt.s, extras_deps)
                                                
                                                # We treat dev, test, etc. as dev dependencies
                                                if key.s in ('dev', 'test', 'testing', 'development'):
                                                    result["dev_dependencies"].update(extras_deps)
                                                # Otherwise just add to regular dependencies
                                                else:
                                                    result["dependencies"].update(extras_deps)
            
            except SyntaxError:
                logger.warning(f"Could not parse {file_path} with AST, falling back to regex")
            
            # Fallback to regex-based parsing
            if not result["dependencies"] and not result["dev_dependencies"]:
                # Find install_requires
                install_requires = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if install_requires:
                    for dep in re.finditer(r'[\'"](.+?)[\'"]', install_requires.group(1)):
                        self._parse_req_string(dep.group(1), result["dependencies"])
                
                # Find extras_require
                extras_require = re.search(r'extras_require\s*=\s*{(.*?)}', content, re.DOTALL)
                if extras_require:
                    extras_text = extras_require.group(1)
                    for extra_match in re.finditer(r'[\'"](.+?)[\'"]\s*:\s*\[(.*?)\]', extras_text, re.DOTALL):
                        extra_name = extra_match.group(1)
                        deps_dict = {}
                        for dep in re.finditer(r'[\'"](.+?)[\'"]', extra_match.group(2)):
                            self._parse_req_string(dep.group(1), deps_dict)
                        
                        # Add to appropriate category
                        if extra_name in ('dev', 'test', 'testing', 'development'):
                            result["dev_dependencies"].update(deps_dict)
                        else:
                            result["dependencies"].update(deps_dict)
            
        except Exception as e:
            logger.error(f"Error parsing setup.py {file_path}: {e}")
        
        return result
    
    def _parse_pipfile(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Python Pipfile for dependencies
        
        Args:
            file_path: Path to Pipfile
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {}
        }
        
        try:
            # Try to import toml module (Pipfile is TOML format)
            try:
                import toml  # Optional dependency - install with: pip install toml
            except ImportError:
                logger.warning("Toml module not available, using basic parsing for Pipfile")
                return self._basic_parse_pipfile(file_path)
            
            # Parse the toml file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Get regular dependencies
            if 'packages' in data:
                for name, version in data['packages'].items():
                    if isinstance(version, dict):
                        # Complex specifier
                        if 'version' in version:
                            result["dependencies"][name] = version['version']
                        else:
                            result["dependencies"][name] = "complex-dependency"
                    else:
                        result["dependencies"][name] = version
            
            # Get dev dependencies
            if 'dev-packages' in data:
                for name, version in data['dev-packages'].items():
                    if isinstance(version, dict):
                        if 'version' in version:
                            result["dev_dependencies"][name] = version['version']
                        else:
                            result["dev_dependencies"][name] = "complex-dependency"
                    else:
                        result["dev_dependencies"][name] = version
                        
        except Exception as e:
            logger.error(f"Error parsing Pipfile {file_path}: {e}")
        
        return result
    
    def _basic_parse_pipfile(self, file_path: str) -> Dict[str, Any]:
        """
        Basic parsing of Pipfile without toml module
        
        Args:
            file_path: Path to Pipfile
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Very basic regex-based parsing
            packages_section = re.search(r'\[packages\](.*?)(\[|\Z)', content, re.DOTALL)
            if packages_section:
                deps_text = packages_section.group(1)
                for line in deps_text.strip().split('\n'):
                    line = line.strip()
                    if line and '=' in line:
                        parts = line.split('=', 1)
                        name = parts[0].strip().strip('"\'')
                        version = parts[1].strip().strip('"\'')
                        result["dependencies"][name] = version
            
            # Look for dev-packages section
            dev_packages_section = re.search(r'\[dev-packages\](.*?)(\[|\Z)', content, re.DOTALL)
            if dev_packages_section:
                deps_text = dev_packages_section.group(1)
                for line in deps_text.strip().split('\n'):
                    line = line.strip()
                    if line and '=' in line:
                        parts = line.split('=', 1)
                        name = parts[0].strip().strip('"\'')
                        version = parts[1].strip().strip('"\'')
                        result["dev_dependencies"][name] = version
            
        except Exception as e:
            logger.error(f"Error basic parsing Pipfile {file_path}: {e}")
        
        return result
    
    def _parse_req_string(self, req_string: str, deps_dict: Dict[str, str]):
        """
        Parse a single requirement string and add to dependencies dictionary
        
        Args:
            req_string: Requirement string (e.g., "package>=1.0.0")
            deps_dict: Dictionary to add the dependency to
        """
        # Skip empty strings and comments
        req_string = req_string.strip()
        if not req_string or req_string.startswith('#'):
            return
        
        # Handle various version specifiers
        if '==' in req_string:
            name, version = req_string.split('==', 1)
            deps_dict[name.strip()] = version.strip()
        elif '>=' in req_string:
            name, version = req_string.split('>=', 1)
            deps_dict[name.strip()] = f">={version.strip()}"
        elif '<=' in req_string:
            name, version = req_string.split('<=', 1)
            deps_dict[name.strip()] = f"<={version.strip()}"
        elif '~=' in req_string:
            name, version = req_string.split('~=', 1)
            deps_dict[name.strip()] = f"~={version.strip()}"
        elif '>' in req_string:
            name, version = req_string.split('>', 1)
            deps_dict[name.strip()] = f">{version.strip()}"
        elif '<' in req_string:
            name, version = req_string.split('<', 1)
            deps_dict[name.strip()] = f"<{version.strip()}"
        # Handle direct GitHub/URL dependencies
        elif 'git+' in req_string or 'http' in req_string:
            parts = req_string.split('#')
            if len(parts) > 1 and 'egg=' in parts[1]:
                egg_part = parts[1].split('egg=')[1]
                name = egg_part.split('&')[0]
                deps_dict[name.strip()] = "git-dependency"
            else:
                # Just use the URL as the name if we can't extract it
                deps_dict[req_string] = "url-dependency"
        # Package with extras like 'package[extra]'
        elif '[' in req_string and ']' in req_string:
            parts = req_string.split('[', 1)
            name = parts[0].strip()
            deps_dict[name] = f"with-extras"
        # Just package name without version
        else:
            deps_dict[req_string.strip()] = "latest"
    
    def _parse_package_json(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Node.js package.json file
        
        Args:
            file_path: Path to package.json file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {},
            "peer_dependencies": {},
            "optional_dependencies": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Regular dependencies
            if 'dependencies' in data:
                for name, version in data['dependencies'].items():
                    result["dependencies"][name] = version
            
            # Development dependencies
            if 'devDependencies' in data:
                for name, version in data['devDependencies'].items():
                    result["dev_dependencies"][name] = version
            
            # Peer dependencies
            if 'peerDependencies' in data:
                for name, version in data['peerDependencies'].items():
                    result["peer_dependencies"][name] = version
            
            # Optional dependencies
            if 'optionalDependencies' in data:
                for name, version in data['optionalDependencies'].items():
                    result["optional_dependencies"][name] = version
            
            # For package.json, also extract metadata
            result["metadata"] = {
                "name": data.get("name", ""),
                "version": data.get("version", ""),
                "description": data.get("description", ""),
                "author": data.get("author", ""),
                "license": data.get("license", ""),
                "main": data.get("main", ""),
                "engines": data.get("engines", {})
            }
            
        except Exception as e:
            logger.error(f"Error parsing package.json {file_path}: {e}")
        
        return result
    
    def _parse_yarn_lock(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Yarn lock file for more precise dependency versions
        
        Args:
            file_path: Path to yarn.lock file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "resolved_dependencies": {},
            "metadata": {
                "yarn_version": "unknown"
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the package.json file in the same directory
            package_json_path = os.path.join(os.path.dirname(file_path), 'package.json')
            if os.path.exists(package_json_path):
                package_json_result = self._parse_package_json(package_json_path)
                # Get all direct dependencies from package.json
                all_deps = {}
                all_deps.update(package_json_result.get("dependencies", {}))
                all_deps.update(package_json_result.get("dev_dependencies", {}))
                all_deps.update(package_json_result.get("peer_dependencies", {}))
                all_deps.update(package_json_result.get("optional_dependencies", {}))
                
                # Add direct dependencies from package.json to result
                result["dependencies"] = all_deps
            
            # Pattern to match yarn.lock entries
            # Each entry looks like: "package-name@version":
            #   version "x.y.z"
            #   resolved "https://registry.yarnpkg.com/package-name/-/package-name-x.y.z.tgz#abcdef123456"
            #   integrity "sha1-abcdef123456="
            entry_pattern = re.compile(r'^"?([^@"]+)(?:@[^"]*)"?:(?:\r?\n[\s]+[^\r\n]+)*\r?\n[\s]+version "([^"]+)"', re.MULTILINE)
            
            # Extract dependency versions from the yarn.lock file
            for match in entry_pattern.finditer(content):
                package_name = match.group(1)
                version = match.group(2)
                result["resolved_dependencies"][package_name] = version
            
            # Try to determine the Yarn version
            yarn_version_match = re.search(r'# yarn lockfile v(\d+)', content)
            if yarn_version_match:
                result["metadata"]["yarn_version"] = yarn_version_match.group(1)
            
        except Exception as e:
            logger.error(f"Error parsing yarn.lock {file_path}: {e}")
        
        return result
    
    def _parse_package_lock_json(self, file_path: str) -> Dict[str, Any]:
        """
        Parse npm's package-lock.json file for more precise dependency versions
        
        Args:
            file_path: Path to package-lock.json file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "resolved_dependencies": {},
            "metadata": {
                "lockfile_version": "unknown"
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find the package.json file in the same directory
            package_json_path = os.path.join(os.path.dirname(file_path), 'package.json')
            if os.path.exists(package_json_path):
                package_json_result = self._parse_package_json(package_json_path)
                # Get all direct dependencies from package.json
                all_deps = {}
                all_deps.update(package_json_result.get("dependencies", {}))
                all_deps.update(package_json_result.get("dev_dependencies", {}))
                all_deps.update(package_json_result.get("peer_dependencies", {}))
                all_deps.update(package_json_result.get("optional_dependencies", {}))
                
                # Add direct dependencies from package.json to result
                result["dependencies"] = all_deps
            
            # Extract lockfile version
            if 'lockfileVersion' in data:
                result["metadata"]["lockfile_version"] = data['lockfileVersion']
            
            # Extract resolved dependencies
            if 'dependencies' in data:
                for name, info in data['dependencies'].items():
                    if 'version' in info:
                        result["resolved_dependencies"][name] = info['version']
            
            # Check for npm 7+ style dependencies
            elif 'packages' in data:
                for path, info in data['packages'].items():
                    # Skip the root package
                    if path == '':
                        continue
                    
                    # Extract package name from path
                    name = path.split('/')[-1]
                    if 'version' in info:
                        result["resolved_dependencies"][name] = info['version']
            
        except Exception as e:
            logger.error(f"Error parsing package-lock.json {file_path}: {e}")
        
        return result
    
    def _parse_pom_xml(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Maven pom.xml file for Java dependencies
        
        Args:
            file_path: Path to pom.xml file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {},
            "metadata": {
                "group_id": "",
                "artifact_id": "",
                "version": ""
            }
        }
        
        try:
            # Basic XML parsing for pom.xml
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract project metadata
            group_id_match = re.search(r'<groupId>([^<]+)</groupId>', content)
            if group_id_match:
                result["metadata"]["group_id"] = group_id_match.group(1).strip()
            
            artifact_id_match = re.search(r'<artifactId>([^<]+)</artifactId>', content)
            if artifact_id_match:
                result["metadata"]["artifact_id"] = artifact_id_match.group(1).strip()
            
            version_match = re.search(r'<version>([^<]+)</version>', content)
            if version_match:
                result["metadata"]["version"] = version_match.group(1).strip()
            
            # Extract dependencies
            # Regular pattern for dependencies
            dependency_pattern = re.compile(
                r'<dependency>\s*'
                r'<groupId>([^<]+)</groupId>\s*'
                r'<artifactId>([^<]+)</artifactId>\s*'
                r'(?:<version>([^<]+)</version>)?.*?'
                r'(?:<scope>([^<]+)</scope>)?.*?'
                r'</dependency>', 
                re.DOTALL
            )
            
            for match in dependency_pattern.finditer(content):
                group_id = match.group(1).strip()
                artifact_id = match.group(2).strip()
                version = match.group(3).strip() if match.group(3) else "latest"
                scope = match.group(4).strip() if match.group(4) else "compile"
                
                # Format dependency name as Maven coordinates
                dep_name = f"{group_id}:{artifact_id}"
                
                # Categorize by scope
                if scope in ("test", "provided"):
                    result["dev_dependencies"][dep_name] = version
                else:
                    result["dependencies"][dep_name] = version
            
            # Look for parent POM
            parent_pattern = re.compile(
                r'<parent>\s*'
                r'<groupId>([^<]+)</groupId>\s*'
                r'<artifactId>([^<]+)</artifactId>\s*'
                r'<version>([^<]+)</version>.*?'
                r'</parent>', 
                re.DOTALL
            )
            
            parent_match = parent_pattern.search(content)
            if parent_match:
                result["metadata"]["parent"] = {
                    "group_id": parent_match.group(1).strip(),
                    "artifact_id": parent_match.group(2).strip(),
                    "version": parent_match.group(3).strip()
                }
            
            # Look for dependencyManagement section
            managed_deps = []
            dependency_management = re.search(r'<dependencyManagement>(.*?)</dependencyManagement>', content, re.DOTALL)
            if dependency_management:
                managed_deps = dependency_pattern.finditer(dependency_management.group(1))
                
                # Add managed dependencies to a separate section
                result["managed_dependencies"] = {}
                for match in managed_deps:
                    group_id = match.group(1).strip()
                    artifact_id = match.group(2).strip()
                    version = match.group(3).strip() if match.group(3) else "latest"
                    
                    # Format dependency name as Maven coordinates
                    dep_name = f"{group_id}:{artifact_id}"
                    result["managed_dependencies"][dep_name] = version
            
        except Exception as e:
            logger.error(f"Error parsing pom.xml {file_path}: {e}")
        
        return result
    
    def _parse_gradle(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Gradle build.gradle file for Java dependencies
        
        Args:
            file_path: Path to build.gradle file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {},
            "metadata": {
                "version": "",
                "group": ""
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract project version
            version_match = re.search(r'version\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if version_match:
                result["metadata"]["version"] = version_match.group(1).strip()
            
            # Extract project group
            group_match = re.search(r'group\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if group_match:
                result["metadata"]["group"] = group_match.group(1).strip()
            
            # Find dependencies section
            dependencies_section = re.search(r'dependencies\s*\{(.*?)\}', content, re.DOTALL)
            if dependencies_section:
                deps_text = dependencies_section.group(1)
                
                # Pattern to match Gradle dependencies
                # Examples:
                # - implementation 'group:artifact:version'
                # - testImplementation('group:artifact:version')
                # - implementation group: 'group', name: 'artifact', version: 'version'
                
                # Simple format: scope 'group:artifact:version'
                simple_dep_pattern = re.compile(r'(\w+)\s*[\'"]([^\'":]+):([^\'":]+):([^\'")]+)[\'"]')
                for match in simple_dep_pattern.finditer(deps_text):
                    scope = match.group(1).strip()
                    group_id = match.group(2).strip()
                    artifact_id = match.group(3).strip()
                    version = match.group(4).strip()
                    
                    # Format dependency name
                    dep_name = f"{group_id}:{artifact_id}"
                    
                    # Categorize by scope
                    if scope in ("testImplementation", "testCompile", "testRuntime"):
                        result["dev_dependencies"][dep_name] = version
                    else:
                        result["dependencies"][dep_name] = version
                
                # Map format: scope group: 'group', name: 'artifact', version: 'version'
                map_dep_pattern = re.compile(
                    r'(\w+)\s+group\s*:\s*[\'"]([^\'"]+)[\'"],\s*'
                    r'name\s*:\s*[\'"]([^\'"]+)[\'"],\s*'
                    r'version\s*:\s*[\'"]([^\'"]+)[\'"]'
                )
                for match in map_dep_pattern.finditer(deps_text):
                    scope = match.group(1).strip()
                    group_id = match.group(2).strip()
                    artifact_id = match.group(3).strip()
                    version = match.group(4).strip()
                    
                    # Format dependency name
                    dep_name = f"{group_id}:{artifact_id}"
                    
                    # Categorize by scope
                    if scope in ("testImplementation", "testCompile", "testRuntime"):
                        result["dev_dependencies"][dep_name] = version
                    else:
                        result["dependencies"][dep_name] = version
            
            # Look for buildscript dependencies
            buildscript_section = re.search(r'buildscript\s*\{\s*dependencies\s*\{(.*?)\}\s*\}', content, re.DOTALL)
            if buildscript_section:
                # Add buildscript dependencies to a separate section
                result["buildscript_dependencies"] = {}
                
                deps_text = buildscript_section.group(1)
                # Same patterns as above
                simple_dep_pattern = re.compile(r'(\w+)\s*[\'"]([^\'":]+):([^\'":]+):([^\'")]+)[\'"]')
                for match in simple_dep_pattern.finditer(deps_text):
                    scope = match.group(1).strip()
                    group_id = match.group(2).strip()
                    artifact_id = match.group(3).strip()
                    version = match.group(4).strip()
                    
                    # Format dependency name
                    dep_name = f"{group_id}:{artifact_id}"
                    result["buildscript_dependencies"][dep_name] = version
            
            # Look for plugins
            plugins_section = re.search(r'plugins\s*\{(.*?)\}', content, re.DOTALL)
            if plugins_section:
                # Add plugins to a separate section
                result["plugins"] = {}
                
                plugins_text = plugins_section.group(1)
                # id 'plugin.id' version 'version'
                plugin_pattern = re.compile(r'id\s*[\'"]([^\'"]+)[\'"](?:\s+version\s*[\'"]([^\'"]+)[\'"])?')
                for match in plugin_pattern.finditer(plugins_text):
                    plugin_id = match.group(1).strip()
                    version = match.group(2).strip() if match.group(2) else "latest"
                    result["plugins"][plugin_id] = version
            
        except Exception as e:
            logger.error(f"Error parsing build.gradle {file_path}: {e}")
        
        return result
        
    def _parse_cargo_toml(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Rust's Cargo.toml file
        
        Args:
            file_path: Path to Cargo.toml file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {},
            "build_dependencies": {},
            "metadata": {
                "name": "",
                "version": ""
            }
        }
        
        try:
            # Try to import toml module
            try:
                import toml  # Optional dependency - install with: pip install toml
            except ImportError:
                logger.warning("Toml module not available, using basic parsing for Cargo.toml")
                return self._basic_parse_cargo_toml(file_path)
            
            # Parse the toml file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
            
            # Get package metadata
            if 'package' in data:
                package = data['package']
                result["metadata"]["name"] = package.get("name", "")
                result["metadata"]["version"] = package.get("version", "")
                result["metadata"]["description"] = package.get("description", "")
                result["metadata"]["authors"] = package.get("authors", [])
                result["metadata"]["license"] = package.get("license", "")
            
            # Get regular dependencies
            if 'dependencies' in data:
                for name, version_info in data['dependencies'].items():
                    if isinstance(version_info, dict):
                        # Complex dependency specification
                        if 'version' in version_info:
                            result["dependencies"][name] = version_info['version']
                        else:
                            # For git dependencies, etc.
                            result["dependencies"][name] = "complex-dependency"
                    else:
                        # Simple version string
                        result["dependencies"][name] = version_info
            
            # Get dev dependencies
            if 'dev-dependencies' in data:
                for name, version_info in data['dev-dependencies'].items():
                    if isinstance(version_info, dict):
                        if 'version' in version_info:
                            result["dev_dependencies"][name] = version_info['version']
                        else:
                            result["dev_dependencies"][name] = "complex-dependency"
                    else:
                        result["dev_dependencies"][name] = version_info
            
            # Get build dependencies
            if 'build-dependencies' in data:
                for name, version_info in data['build-dependencies'].items():
                    if isinstance(version_info, dict):
                        if 'version' in version_info:
                            result["build_dependencies"][name] = version_info['version']
                        else:
                            result["build_dependencies"][name] = "complex-dependency"
                    else:
                        result["build_dependencies"][name] = version_info
            
        except Exception as e:
            logger.error(f"Error parsing Cargo.toml {file_path}: {e}")
        
        return result
    
    def _basic_parse_cargo_toml(self, file_path: str) -> Dict[str, Any]:
        """
        Basic parsing of Cargo.toml without toml module
        
        Args:
            file_path: Path to Cargo.toml file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {},
            "build_dependencies": {},
            "metadata": {
                "name": "",
                "version": ""
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract package name and version
            name_match = re.search(r'\[package\].*?name\s*=\s*"([^"]+)"', content, re.DOTALL)
            if name_match:
                result["metadata"]["name"] = name_match.group(1).strip()
            
            version_match = re.search(r'\[package\].*?version\s*=\s*"([^"]+)"', content, re.DOTALL)
            if version_match:
                result["metadata"]["version"] = version_match.group(1).strip()
            
            # Extract dependencies
            deps_section = re.search(r'\[dependencies\](.*?)(\[|\Z)', content, re.DOTALL)
            if deps_section:
                deps_text = deps_section.group(1)
                # Simple format: name = "version"
                dep_pattern = re.compile(r'([a-zA-Z0-9_\-]+)\s*=\s*"([^"]+)"')
                for match in dep_pattern.finditer(deps_text):
                    name = match.group(1).strip()
                    version = match.group(2).strip()
                    result["dependencies"][name] = version
            
            # Extract dev dependencies
            dev_deps_section = re.search(r'\[dev-dependencies\](.*?)(\[|\Z)', content, re.DOTALL)
            if dev_deps_section:
                deps_text = dev_deps_section.group(1)
                dep_pattern = re.compile(r'([a-zA-Z0-9_\-]+)\s*=\s*"([^"]+)"')
                for match in dep_pattern.finditer(deps_text):
                    name = match.group(1).strip()
                    version = match.group(2).strip()
                    result["dev_dependencies"][name] = version
            
            # Extract build dependencies
            build_deps_section = re.search(r'\[build-dependencies\](.*?)(\[|\Z)', content, re.DOTALL)
            if build_deps_section:
                deps_text = build_deps_section.group(1)
                dep_pattern = re.compile(r'([a-zA-Z0-9_\-]+)\s*=\s*"([^"]+)"')
                for match in dep_pattern.finditer(deps_text):
                    name = match.group(1).strip()
                    version = match.group(2).strip()
                    result["build_dependencies"][name] = version
            
        except Exception as e:
            logger.error(f"Error basic parsing Cargo.toml {file_path}: {e}")
        
        return result
    
    def _parse_go_mod(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Go modules file (go.mod)
        
        Args:
            file_path: Path to go.mod file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "metadata": {
                "module": "",
                "go_version": ""
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract module name
            module_match = re.search(r'module\s+([^\s]+)', content)
            if module_match:
                result["metadata"]["module"] = module_match.group(1).strip()
            
            # Extract Go version
            go_version_match = re.search(r'go\s+([^\s]+)', content)
            if go_version_match:
                result["metadata"]["go_version"] = go_version_match.group(1).strip()
            
            # Extract dependencies
            # Look for require blocks
            require_block_pattern = re.compile(r'require\s*\((.*?)\)', re.DOTALL)
            require_blocks = require_block_pattern.finditer(content)
            
            for block in require_blocks:
                block_content = block.group(1)
                # Pattern for each dependency line
                dep_pattern = re.compile(r'([^\s]+)\s+([^\s]+)')
                for match in dep_pattern.finditer(block_content):
                    name = match.group(1).strip()
                    version = match.group(2).strip()
                    result["dependencies"][name] = version
            
            # Look for single-line requires
            single_require_pattern = re.compile(r'require\s+([^\s]+)\s+([^\s]+)')
            for match in single_require_pattern.finditer(content):
                name = match.group(1).strip()
                version = match.group(2).strip()
                result["dependencies"][name] = version
            
            # Look for replace directives
            result["replacements"] = {}
            replace_block_pattern = re.compile(r'replace\s*\((.*?)\)', re.DOTALL)
            replace_blocks = replace_block_pattern.finditer(content)
            
            for block in replace_blocks:
                block_content = block.group(1)
                # Pattern for each replacement line
                replace_pattern = re.compile(r'([^\s]+)\s+=>\s+([^\s]+)\s+([^\s]+)')
                for match in replace_pattern.finditer(block_content):
                    orig_name = match.group(1).strip()
                    new_name = match.group(2).strip()
                    version = match.group(3).strip()
                    result["replacements"][orig_name] = {"replacement": new_name, "version": version}
            
            # Look for single-line replaces
            single_replace_pattern = re.compile(r'replace\s+([^\s]+)\s+=>\s+([^\s]+)\s+([^\s]+)')
            for match in single_replace_pattern.finditer(content):
                orig_name = match.group(1).strip()
                new_name = match.group(2).strip()
                version = match.group(3).strip()
                result["replacements"][orig_name] = {"replacement": new_name, "version": version}
            
        except Exception as e:
            logger.error(f"Error parsing go.mod {file_path}: {e}")
        
        return result
    
    def _parse_composer_json(self, file_path: str) -> Dict[str, Any]:
        """
        Parse PHP Composer's composer.json file
        
        Args:
            file_path: Path to composer.json file
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {},
            "metadata": {
                "name": "",
                "description": ""
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract metadata
            if 'name' in data:
                result["metadata"]["name"] = data['name']
            if 'description' in data:
                result["metadata"]["description"] = data['description']
            
            # Extract dependencies
            if 'require' in data:
                for name, version in data['require'].items():
                    # Skip PHP version requirement
                    if name.lower() == 'php':
                        continue
                    result["dependencies"][name] = version
            
            # Extract dev dependencies
            if 'require-dev' in data:
                for name, version in data['require-dev'].items():
                    result["dev_dependencies"][name] = version
            
        except Exception as e:
            logger.error(f"Error parsing composer.json {file_path}: {e}")
        
        return result
    
    def _parse_gemfile(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Ruby's Gemfile
        
        Args:
            file_path: Path to Gemfile
            
        Returns:
            Dictionary with parsed dependencies
        """
        result = {
            "dependencies": {},
            "dev_dependencies": {},
            "metadata": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract source
            source_match = re.search(r'source\s+[\'"]([^\'"]+)[\'"]', content)
            if source_match:
                result["metadata"]["source"] = source_match.group(1).strip()
            
            # Extract Ruby version
            ruby_version_match = re.search(r'ruby\s+[\'"]([^\'"]+)[\'"]', content)
            if ruby_version_match:
                result["metadata"]["ruby_version"] = ruby_version_match.group(1).strip()
            
            # Standard gems (non-grouped)
            gem_pattern = re.compile(r'^\s*gem\s+[\'"]([^\'"]+)[\'"](?:\s*,\s*[\'"]([^\'"]+)[\'"])?', re.MULTILINE)
            for match in gem_pattern.finditer(content):
                name = match.group(1).strip()
                version = match.group(2).strip() if match.group(2) else "latest"
                result["dependencies"][name] = version
            
            # Grouped gems
            group_pattern = re.compile(r'group\s+:(\w+)(?:,\s*:(\w+))?\s+do(.*?)end', re.DOTALL)
            for match in group_pattern.finditer(content):
                group_name = match.group(1).strip()
                group_content = match.group(3)
                
                # Extract gems in this group
                group_gems = re.compile(r'gem\s+[\'"]([^\'"]+)[\'"](?:\s*,\s*[\'"]([^\'"]+)[\'"])?')
                for gem_match in group_gems.finditer(group_content):
                    name = gem_match.group(1).strip()
                    version = gem_match.group(2).strip() if gem_match.group(2) else "latest"
                    
                    # Development and test gems are dev dependencies
                    if group_name in ('development', 'test'):
                        result["dev_dependencies"][name] = version
                    else:
                        result["dependencies"][name] = version
            
        except Exception as e:
            logger.error(f"Error parsing Gemfile {file_path}: {e}")
        
        return result
    
    def _check_security_issues(self, dependencies: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Check for known security issues in dependencies
        
        Args:
            dependencies: Dictionary of dependencies to check
            
        Returns:
            List of detected security issues
        """
        security_issues = []
        
        # This is a placeholder implementation that should be replaced with actual
        # security vulnerability database integration
        
        # Example: Hardcoded list of known vulnerable packages
        # In a real implementation, this would connect to security databases like:
        # - NIST NVD (National Vulnerability Database)
        # - GitHub Advisory Database
        # - OSV (Open Source Vulnerability) Database
        # - Snyk Vulnerability Database
        # - Sonatype OSS Index
        
        known_vulnerabilities = {
            # Python vulnerabilities
            "django": {
                "3.0.0": {
                    "id": "CVE-2021-3281",
                    "severity": "high",
                    "description": "SQL injection vulnerability in Django 3.0.0",
                    "fixed_in": "3.0.14",
                    "url": "https://nvd.nist.gov/vuln/detail/CVE-2021-3281"
                }
            },
            "flask": {
                "0.12": {
                    "id": "CVE-2019-1010083",
                    "severity": "medium",
                    "description": "Information disclosure vulnerability in Flask 0.12",
                    "fixed_in": "1.0",
                    "url": "https://nvd.nist.gov/vuln/detail/CVE-2019-1010083"
                }
            },
            
            # JavaScript vulnerabilities
            "lodash": {
                "4.17.11": {
                    "id": "CVE-2019-10744",
                    "severity": "critical",
                    "description": "Prototype pollution vulnerability in lodash before 4.17.12",
                    "fixed_in": "4.17.12",
                    "url": "https://nvd.nist.gov/vuln/detail/CVE-2019-10744"
                }
            },
            "jquery": {
                "1.9.1": {
                    "id": "CVE-2019-11358",
                    "severity": "medium",
                    "description": "Prototype pollution in jQuery before 3.4.0",
                    "fixed_in": "3.4.0",
                    "url": "https://nvd.nist.gov/vuln/detail/CVE-2019-11358"
                }
            },
            
            # Java vulnerabilities
            "org.apache.struts:struts2-core": {
                "2.5.12": {
                    "id": "CVE-2017-9805",
                    "severity": "critical",
                    "description": "Remote Code Execution in Apache Struts",
                    "fixed_in": "2.5.13",
                    "url": "https://nvd.nist.gov/vuln/detail/CVE-2017-9805"
                }
            },
            "com.fasterxml.jackson.core:jackson-databind": {
                "2.9.9": {
                    "id": "CVE-2019-14379",
                    "severity": "high",
                    "description": "Deserialization vulnerability in Jackson",
                    "fixed_in": "2.9.10",
                    "url": "https://nvd.nist.gov/vuln/detail/CVE-2019-14379"
                }
            }
        }
        
        # Check each dependency against known vulnerabilities
        for dep_name, dep_version in dependencies.items():
            if dep_name in known_vulnerabilities:
                for vuln_version, vuln_info in known_vulnerabilities[dep_name].items():
                    # This is a simplified version check, a real implementation would use
                    # version comparison libraries to properly handle version ranges
                    if dep_version == vuln_version or dep_version.startswith(vuln_version):
                        security_issues.append({
                            "package": dep_name,
                            "version": dep_version,
                            "id": vuln_info["id"],
                            "severity": vuln_info["severity"],
                            "description": vuln_info["description"],
                            "fixed_in": vuln_info["fixed_in"],
                            "url": vuln_info["url"]
                        })
        
        # In a real implementation, you would also check for:
        # 1. Transitive dependencies vulnerabilities
        # 2. License compliance issues
        # 3. Unmaintained or deprecated packages
        # 4. Supply chain risks
        
        return security_issues
    
    def _check_outdated_packages(self, dependencies: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Check for outdated packages and suggest updates
        
        Args:
            dependencies: Dictionary of dependencies to check
            
        Returns:
            List of outdated packages with update recommendations
        """
        outdated = []
        
        # This is a placeholder implementation that should be replaced with actual
        # package registry API calls or local package manager commands
        
        # For Python packages, you could use:
        # pip list --outdated --format=json
        
        # For npm packages, you could use:
        # npm outdated --json
        
        # For Java/Maven packages, you could use:
        # mvn versions:display-dependency-updates
        
        # Example hardcoded data for demonstration
        latest_versions = {
            # Python packages
            "django": "4.2.0",
            "flask": "2.3.2",
            "requests": "2.31.0",
            "numpy": "1.24.3",
            "pandas": "2.0.1",
            
            # JavaScript packages
            "react": "18.2.0",
            "vue": "3.3.2",
            "lodash": "4.17.21",
            "axios": "1.4.0",
            "express": "4.18.2",
            
            # Java packages
            "org.springframework:spring-core": "6.0.9",
            "com.google.guava:guava": "32.0.0",
            "org.hibernate:hibernate-core": "6.2.2.Final",
            
            # Other languages
            "rails": "7.0.4",
            "symfony/symfony": "6.3.0"
        }
        
        # Check each dependency against latest versions
        for dep_name, dep_version in dependencies.items():
            if dep_name in latest_versions:
                latest = latest_versions[dep_name]
                
                # Very basic version comparison, a real implementation would use
                # semantic version comparison libraries
                if dep_version != latest and dep_version != "latest":
                    # Remove any version prefix operators
                    clean_version = re.sub(r'^[~^>=<]+', '', dep_version)
                    
                    update_urgency = "low"
                    # Determine update urgency based on version difference
                    if "." in clean_version and "." in latest:
                        current_parts = clean_version.split(".")
                        latest_parts = latest.split(".")
                        
                        # Compare major version
                        if len(current_parts) > 0 and len(latest_parts) > 0:
                            if int(latest_parts[0]) > int(current_parts[0]):
                                update_urgency = "high"
                            # Compare minor version
                            elif len(current_parts) > 1 and len(latest_parts) > 1:
                                if int(latest_parts[0]) == int(current_parts[0]) and int(latest_parts[1]) > int(current_parts[1]):
                                    update_urgency = "medium"
                    
                    outdated.append({
                        "package": dep_name,
                        "current_version": dep_version,
                        "latest_version": latest,
                        "update_urgency": update_urgency
                    })
        
        return outdated
    
    def get_dependency_recommendations(self, project_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Provide recommendations for dependency management and updates.
        
        This method analyzes the project dependencies and provides actionable 
        recommendations for improving dependency management, security, and updates.
        
        The recommendations include:
        - Security updates for dependencies with known vulnerabilities
        - Version updates for outdated dependencies
        - Best practices for dependency management
        - Language-specific recommendations
        
        Args:
            project_path: Path to the project directory
            language: Optional language to limit recommendations to
            
        Returns:
            Dictionary with dependency recommendations:
            - security_updates: List of recommended security-related updates
            - version_updates: List of recommended version updates
            - alternative_packages: List of alternative package recommendations
            - dependency_removal: List of dependencies that could be removed
            - best_practices: List of dependency management best practices
            
        Example:
            ```python
            analyzer = DependencyAnalyzer()
            recommendations = analyzer.get_dependency_recommendations("./my_project")
            
            # Print security update recommendations
            for update in recommendations["security_updates"]:
                print(f"Security update: {update['package']} -> {update['recommendation']}")
                
            # Print best practices
            for practice in recommendations["best_practices"]:
                print(f"Best practice: {practice['title']} - {practice['description']}")
            
            # Get Python-specific recommendations
            python_recommendations = analyzer.get_dependency_recommendations(
                "./my_project", language="python"
            )
            ```
        """
        # Analyze the project dependencies first
        analysis = self.analyze_project_dependencies(project_path)
        
        recommendations = {
            "security_updates": [],
            "version_updates": [],
            "alternative_packages": [],
            "dependency_removal": [],
            "best_practices": []
        }
        
        # Security update recommendations
        for issue in analysis.get("security_issues", []):
            recommendations["security_updates"].append({
                "package": issue["package"],
                "current_version": issue["version"],
                "recommendation": f"Update to {issue['fixed_in']} or later to fix {issue['id']} ({issue['severity']} severity)",
                "severity": issue["severity"]
            })
        
        # Version update recommendations
        for outdated in analysis.get("outdated_packages", []):
            recommendations["version_updates"].append({
                "package": outdated["package"],
                "current_version": outdated["current_version"],
                "recommendation": f"Update to {outdated['latest_version']}",
                "urgency": outdated["update_urgency"]
            })
        
        # Best practices
        recommendations["best_practices"] = [
            {
                "title": "Use dependency locking",
                "description": "Lock your dependencies to specific versions to ensure reproducible builds",
                "applicable_to": ["python", "javascript", "php", "ruby"]
            },
            {
                "title": "Regular security audits",
                "description": "Run security audits regularly using tools like npm audit, pip-audit, or OWASP Dependency Check",
                "applicable_to": ["python", "javascript", "java", "php", "ruby"]
            },
            {
                "title": "Minimize dependencies",
                "description": "Reduce the number of direct dependencies to minimize security and maintenance burden",
                "applicable_to": ["all"]
            },
            {
                "title": "Use semantic versioning",
                "description": "Specify dependencies using semantic versioning to balance stability and updates",
                "applicable_to": ["all"]
            }
        ]
        
        # Language-specific recommendations
        if language == "python" or (language is None and "pip" in analysis.get("package_managers", [])):
            recommendations["best_practices"].append({
                "title": "Use virtual environments",
                "description": "Isolate project dependencies using virtualenv, pipenv, or conda environments",
                "applicable_to": ["python"]
            })
        
        if language == "javascript" or (language is None and "npm" in analysis.get("package_managers", [])):
            recommendations["best_practices"].append({
                "title": "Use package-lock.json",
                "description": "Commit package-lock.json to ensure consistent dependency installation",
                "applicable_to": ["javascript"]
            })
        
        # Filter by language if specified
        if language:
            recommendations["best_practices"] = [
                bp for bp in recommendations["best_practices"] 
                if language in bp["applicable_to"] or "all" in bp["applicable_to"]
            ]
        
        return recommendations
