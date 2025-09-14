"""
File analysis utilities for the repository analyzer
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileAnalyzer:
    """Analyzes individual files for various characteristics"""
    
    def __init__(self):
        self.supported_extensions = {
            '.py': self._analyze_python_file,
            '.js': self._analyze_javascript_file,
            '.ts': self._analyze_typescript_file,
            '.json': self._analyze_json_file,
            '.md': self._analyze_markdown_file,
            '.yml': self._analyze_yaml_file,
            '.yaml': self._analyze_yaml_file
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file and return metadata"""
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        file_info = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "extension": Path(file_path).suffix.lower(),
            "lines": 0,
            "complexity": 0,
            "functions": [],
            "classes": [],
            "imports": [],
            "content_type": "unknown"
        }
        
        try:
            # Count lines
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_info["lines"] = sum(1 for line in f)
            
            # Analyze based on file extension
            ext = file_info["extension"]
            if ext in self.supported_extensions:
                analyzer = self.supported_extensions[ext]
                analysis = analyzer(file_path)
                file_info.update(analysis)
            
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
            file_info["error"] = str(e)
        
        return file_info
    
    def _analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Python file for functions, classes, imports"""
        analysis = {
            "content_type": "python",
            "functions": [],
            "classes": [],
            "imports": [],
            "complexity": 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis["functions"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": len(node.args.args),
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    analysis["classes"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "method_count": len(methods)
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis["imports"].append(alias.name)
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            analysis["imports"].append(f"{module}.{alias.name}" if module else alias.name)
            
            # Simple complexity calculation (count control flow statements)
            complexity = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                    complexity += 1
            analysis["complexity"] = complexity
            
        except Exception as e:
            logger.warning(f"Error parsing Python file {file_path}: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _analyze_javascript_file(self, file_path: str) -> Dict[str, Any]:
        """Basic analysis of JavaScript files"""
        analysis = {
            "content_type": "javascript",
            "functions": [],
            "imports": [],
            "exports": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Detect function declarations
                if line.startswith('function ') or 'function(' in line:
                    func_name = line.split('(')[0].replace('function', '').strip()
                    analysis["functions"].append({"name": func_name, "line": i})
                
                # Detect arrow functions
                elif '=>' in line and ('const ' in line or 'let ' in line or 'var ' in line):
                    func_name = line.split('=')[0].replace('const', '').replace('let', '').replace('var', '').strip()
                    analysis["functions"].append({"name": func_name, "line": i, "type": "arrow"})
                
                # Detect imports
                elif line.startswith('import ') or line.startswith('const ') and 'require(' in line:
                    analysis["imports"].append(line)
                
                # Detect exports
                elif line.startswith('export ') or line == 'module.exports':
                    analysis["exports"].append(line)
            
        except Exception as e:
            logger.warning(f"Error analyzing JavaScript file {file_path}: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _analyze_typescript_file(self, file_path: str) -> Dict[str, Any]:
        """Basic analysis of TypeScript files"""
        # For now, use JavaScript analyzer as base
        analysis = self._analyze_javascript_file(file_path)
        analysis["content_type"] = "typescript"
        
        # Add TypeScript-specific analysis
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count type definitions
            type_count = content.count('interface ') + content.count('type ') + content.count('enum ')
            analysis["type_definitions"] = type_count
            
        except Exception as e:
            logger.warning(f"Error analyzing TypeScript file {file_path}: {e}")
        
        return analysis
    
    def _analyze_json_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze JSON files"""
        analysis = {
            "content_type": "json",
            "valid": False,
            "keys": [],
            "depth": 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            analysis["valid"] = True
            if isinstance(data, dict):
                analysis["keys"] = list(data.keys())
                analysis["depth"] = self._calculate_json_depth(data)
            
        except Exception as e:
            logger.warning(f"Error analyzing JSON file {file_path}: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _analyze_markdown_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Markdown files"""
        analysis = {
            "content_type": "markdown",
            "headings": [],
            "links": 0,
            "images": 0,
            "code_blocks": 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                
                # Count headings
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    heading_text = line.lstrip('#').strip()
                    analysis["headings"].append({"level": level, "text": heading_text})
                
                # Count links and images
                analysis["links"] += line.count('[')
                analysis["images"] += line.count('![')
                
                # Count code blocks
                if line.startswith('```'):
                    analysis["code_blocks"] += 1
            
            analysis["code_blocks"] //= 2  # Each code block has start and end
            
        except Exception as e:
            logger.warning(f"Error analyzing Markdown file {file_path}: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _analyze_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze YAML files"""
        analysis = {
            "content_type": "yaml",
            "valid": False,
            "keys": []
        }
        
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            analysis["valid"] = True
            if isinstance(data, dict):
                analysis["keys"] = list(data.keys())
            
        except ImportError:
            logger.warning("PyYAML not available, skipping YAML analysis")
        except Exception as e:
            logger.warning(f"Error analyzing YAML file {file_path}: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _calculate_json_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate the maximum depth of a JSON object"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_json_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._calculate_json_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth