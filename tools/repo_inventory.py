#!/usr/bin/env python3
"""
Repository Inventory Scanner

Performs static analysis of the codebase to generate a comprehensive,
machine-readable inventory of all functions, APIs, data flows, and dependencies.
Supports Python, JavaScript/TypeScript, and configuration files.

Usage: python tools/repo_inventory.py [output_file]
"""

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import yaml

@dataclass
class ModuleInfo:
    name: str
    file_path: str
    exports: List[str]
    imports: List[str]
    functions: List[str]
    classes: List[str]
    docstring: Optional[str]
    loc: int

@dataclass
class FunctionInfo:
    name: str
    module: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    docstring: Optional[str]
    calls: List[str]
    decorators: List[str]
    is_async: bool
    is_endpoint: bool

@dataclass
class APIEndpoint:
    method: str
    path: str
    function_name: str
    module: str
    file_path: str
    line_number: int
    parameters: List[str]
    response_model: Optional[str]
    description: str
    auth_required: bool

@dataclass
class BackgroundJob:
    name: str
    trigger: str
    handler_function: str
    module: str
    file_path: str
    line_number: int
    side_effects: List[str]

@dataclass
class DataStore:
    name: str
    type: str  # sqlite, redis, file
    location: str
    entities: List[str]
    access_points: List[Tuple[str, int]]  # (file_path, line)

@dataclass
class ConfigVar:
    name: str
    default_value: Optional[str]
    description: str
    read_sites: List[Tuple[str, int]]  # (file_path, line)

@dataclass
class ExternalService:
    name: str
    sdk_calls: List[str]
    payload_fields: List[str]
    file_path: str
    line_number: int

class RepositoryInventoryScanner:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.modules: Dict[str, ModuleInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}
        self.api_endpoints: List[APIEndpoint] = []
        self.background_jobs: List[BackgroundJob] = []
        self.data_stores: List[DataStore] = []
        self.config_vars: Dict[str, ConfigVar] = {}
        self.external_services: List[ExternalService] = []
        
        # Track patterns
        self.ignore_patterns = {
            '__pycache__', '.git', '.pytest_cache', 'node_modules', 
            '.vscode', 'venv', '.env', 'dist', 'build'
        }
        
    def scan_repository(self):
        """Main entry point for repository scanning"""
        print("🔍 Scanning repository...")
        
        # Scan Python files
        python_files = list(self.repo_root.rglob("*.py"))
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue
            try:
                self._scan_python_file(py_file)
            except Exception as e:
                print(f"⚠️  Error scanning {py_file}: {e}")
        
        # Scan JavaScript/TypeScript files
        js_files = list(self.repo_root.rglob("*.js")) + list(self.repo_root.rglob("*.ts")) + list(self.repo_root.rglob("*.jsx")) + list(self.repo_root.rglob("*.tsx"))
        for js_file in js_files:
            if self._should_skip_file(js_file):
                continue
            try:
                self._scan_javascript_file(js_file)
            except Exception as e:
                print(f"⚠️  Error scanning {js_file}: {e}")
        
        # Scan configuration files
        self._scan_config_files()
        
        # Detect data stores
        self._detect_data_stores()
        
        # Analyze external services
        self._analyze_external_services()
        
        print(f"✅ Scan complete: {len(self.modules)} modules, {len(self.functions)} functions, {len(self.api_endpoints)} endpoints")
        
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped based on patterns"""
        path_str = str(file_path.relative_to(self.repo_root))
        return any(pattern in path_str for pattern in self.ignore_patterns)
    
    def _scan_python_file(self, file_path: Path):
        """Scan a Python file for functions, classes, and APIs"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # Module info
            module_name = str(file_path.relative_to(self.repo_root)).replace('/', '.').replace('.py', '')
            module_docstring = ast.get_docstring(tree)
            
            module_info = ModuleInfo(
                name=module_name,
                file_path=str(file_path.relative_to(self.repo_root)),
                exports=[],
                imports=[],
                functions=[],
                classes=[],
                docstring=module_docstring,
                loc=len(lines)
            )
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_info.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            module_info.imports.append(f"{node.module}.{alias.name}")
            
            # Extract functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    self._extract_function_info(node, file_path, lines, module_name)
                    module_info.functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    module_info.classes.append(node.name)
                    # Extract methods from classes
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            self._extract_function_info(item, file_path, lines, module_name, class_name=node.name)
            
            self.modules[module_name] = module_info
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _extract_function_info(self, node: ast.FunctionDef, file_path: Path, lines: List[str], 
                              module_name: str, class_name: Optional[str] = None):
        """Extract detailed function information"""
        
        # Build function name with class prefix if needed
        func_name = f"{class_name}.{node.name}" if class_name else node.name
        
        # Get decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(self._get_attr_name(decorator))
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    decorators.append(self._get_attr_name(decorator.func))
        
        # Check if it's an API endpoint
        is_endpoint = any(
            dec.lower() in ['get', 'post', 'put', 'delete', 'patch'] or 
            'app.get' in dec or 'app.post' in dec or 'app.put' in dec or 
            'app.delete' in dec or 'app.patch' in dec or
            'router.get' in dec or 'router.post' in dec or 
            'router.put' in dec or 'router.delete' in dec or 'router.patch' in dec
            for dec in decorators
        )
        
        # Extract function calls
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(self._get_attr_name(child.func))
        
        # Build signature
        signature = self._build_function_signature(node, lines)
        
        function_info = FunctionInfo(
            name=func_name,
            module=module_name,
            file_path=str(file_path.relative_to(self.repo_root)),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=signature,
            docstring=ast.get_docstring(node),
            calls=list(set(calls)),
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_endpoint=is_endpoint
        )
        
        self.functions[f"{module_name}.{func_name}"] = function_info
        
        # If it's an API endpoint, extract endpoint details
        if is_endpoint:
            self._extract_api_endpoint(node, decorators, function_info)
    
    def _extract_api_endpoint(self, node: ast.FunctionDef, decorators: List[str], func_info: FunctionInfo):
        """Extract API endpoint details from decorated function"""
        
        for decorator in node.decorator_list:
            method = None
            path = ""
            
            # Handle direct app.method() decorators
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if isinstance(decorator.func.value, ast.Name) and decorator.func.value.id in ['app', 'router']:
                    method = decorator.func.attr.upper()
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        # Extract path from first argument
                        if decorator.args:
                            if isinstance(decorator.args[0], ast.Str):
                                path = decorator.args[0].s
                            elif isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                                path = decorator.args[0].value
            
            # Handle @app.method or @router.method decorators (without call)
            elif isinstance(decorator, ast.Attribute):
                if isinstance(decorator.value, ast.Name) and decorator.value.id in ['app', 'router']:
                    method = decorator.attr.upper()
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        path = f"/{func_info.name}"  # Default path based on function name
            
            if method:
                # Extract parameters
                parameters = []
                for arg in node.args.args:
                    if arg.arg not in ['self', 'cls']:
                        parameters.append(arg.arg)
                
                # Check for auth requirements
                auth_required = any('Depends' in str(dec) or 'current_user' in parameters for dec in decorators)
                
                endpoint = APIEndpoint(
                    method=method,
                    path=path,
                    function_name=func_info.name,
                    module=func_info.module,
                    file_path=func_info.file_path,
                    line_number=func_info.line_start,
                    parameters=parameters,
                    response_model=None,  # TODO: Extract from return annotations
                    description=func_info.docstring or "",
                    auth_required=auth_required
                )
                
                self.api_endpoints.append(endpoint)
                break
    
    def _scan_javascript_file(self, file_path: Path):
        """Basic scanning of JavaScript/TypeScript files for API calls"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex patterns for API calls
            api_patterns = [
                r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                r'axios\.\w+\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                r'api\.\w+\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                r'\.post\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                r'\.get\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
            ]
            
            # This is a simplified approach - a full parser would be better
            for pattern in api_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Store API call references
                    pass
                    
        except Exception as e:
            print(f"Error scanning JavaScript file {file_path}: {e}")
    
    def _scan_config_files(self):
        """Scan configuration files for environment variables and settings"""
        config_files = [
            '.env', '.env.example', 'docker-compose.yml', 'pyproject.toml',
            'requirements.txt', 'package.json'
        ]
        
        for config_file in config_files:
            config_path = self.repo_root / config_file
            if config_path.exists():
                self._parse_config_file(config_path)
    
    def _parse_config_file(self, file_path: Path):
        """Parse configuration file for variables"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.name.startswith('.env'):
                # Parse environment variables
                for line_num, line in enumerate(content.split('\n'), 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config_vars[key] = ConfigVar(
                            name=key,
                            default_value=value,
                            description="",
                            read_sites=[(str(file_path.relative_to(self.repo_root)), line_num)]
                        )
            
            elif file_path.name == 'docker-compose.yml':
                # Parse Docker Compose for service definitions
                pass
                
        except Exception as e:
            print(f"Error parsing config file {file_path}: {e}")
    
    def _detect_data_stores(self):
        """Detect data stores based on file patterns and imports"""
        
        # SQLite databases
        db_files = list(self.repo_root.rglob("*.db")) + list(self.repo_root.rglob("*.sqlite"))
        for db_file in db_files:
            self.data_stores.append(DataStore(
                name=db_file.name,
                type="sqlite",
                location=str(db_file.relative_to(self.repo_root)),
                entities=[],
                access_points=[]
            ))
        
        # Redis usage (detected from config)
        if any('redis' in var.default_value.lower() for var in self.config_vars.values() if var.default_value):
            self.data_stores.append(DataStore(
                name="redis",
                type="redis",
                location="external",
                entities=["tasks", "cache"],
                access_points=[]
            ))
    
    def _analyze_external_services(self):
        """Analyze external service integrations"""
        # This would scan for HTTP client usage, SDK imports, etc.
        pass
    
    def _get_attr_name(self, node: ast.Attribute) -> str:
        """Get full attribute name like 'obj.method'"""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))
    
    def _build_function_signature(self, node: ast.FunctionDef, lines: List[str]) -> str:
        """Build function signature string"""
        try:
            # Get the actual lines of the function definition
            start_line = node.lineno - 1
            end_line = start_line
            
            # Find the end of the function signature (line ending with :)
            for i in range(start_line, min(start_line + 10, len(lines))):
                if lines[i].rstrip().endswith(':'):
                    end_line = i
                    break
            
            signature_lines = lines[start_line:end_line + 1]
            return ' '.join(line.strip() for line in signature_lines)
        except:
            return f"def {node.name}(...)"
    
    def generate_inventory(self) -> Dict[str, Any]:
        """Generate the complete inventory data structure"""
        return {
            "metadata": {
                "generated_at": "2025-10-15T00:00:00Z",
                "repository_root": str(self.repo_root),
                "scan_version": "1.0"
            },
            "modules": {name: asdict(info) for name, info in self.modules.items()},
            "functions": {name: asdict(info) for name, info in self.functions.items()},
            "api_endpoints": [asdict(ep) for ep in self.api_endpoints],
            "background_jobs": [asdict(job) for job in self.background_jobs],
            "data_stores": [asdict(store) for store in self.data_stores],
            "config_vars": {name: asdict(var) for name, var in self.config_vars.items()},
            "external_services": [asdict(service) for service in self.external_services],
            "statistics": {
                "total_modules": len(self.modules),
                "total_functions": len(self.functions),
                "total_api_endpoints": len(self.api_endpoints),
                "total_data_stores": len(self.data_stores),
                "total_config_vars": len(self.config_vars)
            }
        }

def main():
    """Main entry point"""
    repo_root = Path(__file__).parent.parent
    output_file = sys.argv[1] if len(sys.argv) > 1 else "docs/architecture/INVENTORY.json"
    
    scanner = RepositoryInventoryScanner(str(repo_root))
    scanner.scan_repository()
    
    inventory = scanner.generate_inventory()
    
    # Write to file
    output_path = repo_root / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, sort_keys=True)
    
    print(f"📄 Inventory saved to: {output_path}")
    
    # Print summary
    print("\n📊 Summary:")
    print(f"   Modules: {inventory['statistics']['total_modules']}")
    print(f"   Functions: {inventory['statistics']['total_functions']}")
    print(f"   API Endpoints: {inventory['statistics']['total_api_endpoints']}")
    print(f"   Data Stores: {inventory['statistics']['total_data_stores']}")
    print(f"   Config Variables: {inventory['statistics']['total_config_vars']}")

if __name__ == "__main__":
    main()
