#!/usr/bin/env python3
"""
Comprehensive Application Documentation Generator

Generates complete documentation of:
- All functions and their signatures
- API endpoints and data flow
- Component relationships
- Database operations
- Logic chunks and dependencies
"""

import ast
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class FunctionInfo:
    name: str
    file_path: str
    line_number: int
    signature: str
    docstring: Optional[str]
    dependencies: List[str]
    called_by: List[str]
    calls: List[str]
    
@dataclass
class APIEndpoint:
    method: str
    path: str
    file_path: str
    function_name: str
    parameters: List[str]
    response_type: str
    description: str

class ApplicationDocumentationGenerator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.functions = {}
        self.api_endpoints = []
        self.data_flows = []
        
    def analyze_python_files(self):
        """Analyze all Python files to extract function information"""
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if any(skip in str(file_path) for skip in ['.venv', '__pycache__', '.git']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                self._extract_functions_from_ast(tree, file_path, content)
                
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                
    def _extract_functions_from_ast(self, tree: ast.AST, file_path: Path, content: str):
        """Extract function information from AST"""
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                signature = self._get_function_signature(node, lines)
                docstring = ast.get_docstring(node)
                
                func_info = FunctionInfo(
                    name=node.name,
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=node.lineno,
                    signature=signature,
                    docstring=docstring,
                    dependencies=[],
                    called_by=[],
                    calls=[]
                )
                
                # Extract function calls within this function
                func_info.calls = self._extract_function_calls(node)
                
                # Check for FastAPI route decorators
                self._check_for_api_endpoint(node, func_info)
                
                self.functions[f"{file_path.relative_to(self.project_root)}:{node.name}"] = func_info
                
    def _get_function_signature(self, node: ast.FunctionDef, lines: List[str]) -> str:
        """Extract function signature from AST node"""
        try:
            start_line = node.lineno - 1
            signature_lines = []
            
            for i in range(start_line, min(start_line + 10, len(lines))):
                line = lines[i].strip()
                signature_lines.append(line)
                if line.endswith(':'):
                    break
                    
            return ' '.join(signature_lines)
        except:
            return f"def {node.name}(...)"
            
    def _extract_function_calls(self, node: ast.FunctionDef) -> List[str]:
        """Extract function calls within a function"""
        calls = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(f"{self._get_attribute_path(child.func)}")
                    
        return list(set(calls))  # Remove duplicates
        
    def _get_attribute_path(self, node: ast.Attribute) -> str:
        """Get full attribute path like 'obj.method'"""
        parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
            
        if isinstance(current, ast.Name):
            parts.append(current.id)
            
        return '.'.join(reversed(parts))
        
    def _check_for_api_endpoint(self, node: ast.FunctionDef, func_info: FunctionInfo):
        """Check if function is a FastAPI endpoint"""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    method = decorator.func.attr.upper()
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        path = ""
                        if decorator.args and isinstance(decorator.args[0], ast.Str):
                            path = decorator.args[0].s
                        elif decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                            
                        endpoint = APIEndpoint(
                            method=method,
                            path=path,
                            file_path=func_info.file_path,
                            function_name=func_info.name,
                            parameters=[],
                            response_type="",
                            description=func_info.docstring or ""
                        )
                        self.api_endpoints.append(endpoint)
                        
    def generate_documentation(self) -> str:
        """Generate comprehensive documentation"""
        doc = f"""# Whisper Transcriber - Comprehensive Function & API Reference

Generated on: {Path.cwd()}
Total Functions: {len(self.functions)}
Total API Endpoints: {len(self.api_endpoints)}

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Function Reference](#function-reference)
3. [Data Flow Analysis](#data-flow-analysis)
4. [Component Relationships](#component-relationships)

## API Endpoints

"""
        
        # Group endpoints by file
        endpoints_by_file = {}
        for endpoint in self.api_endpoints:
            if endpoint.file_path not in endpoints_by_file:
                endpoints_by_file[endpoint.file_path] = []
            endpoints_by_file[endpoint.file_path].append(endpoint)
            
        for file_path, endpoints in sorted(endpoints_by_file.items()):
            doc += f"\n### {file_path}\n\n"
            for endpoint in endpoints:
                doc += f"**{endpoint.method} {endpoint.path}**\n"
                doc += f"- Function: `{endpoint.function_name}()`\n"
                if endpoint.description:
                    doc += f"- Description: {endpoint.description.split('.')[0]}\n"
                doc += "\n"
                
        doc += "\n## Function Reference\n\n"
        
        # Group functions by file
        functions_by_file = {}
        for func_key, func_info in self.functions.items():
            if func_info.file_path not in functions_by_file:
                functions_by_file[func_info.file_path] = []
            functions_by_file[func_info.file_path].append(func_info)
            
        for file_path, functions in sorted(functions_by_file.items()):
            doc += f"\n### {file_path}\n\n"
            for func in sorted(functions, key=lambda x: x.line_number):
                doc += f"**{func.name}()** (Line {func.line_number})\n"
                doc += f"```python\n{func.signature}\n```\n"
                if func.docstring:
                    doc += f"*{func.docstring.split('.')[0]}*\n"
                if func.calls:
                    doc += f"- Calls: {', '.join(func.calls[:5])}{'...' if len(func.calls) > 5 else ''}\n"
                doc += "\n"
                
        doc += "\n## Data Flow Analysis\n\n"
        doc += self._generate_data_flow_analysis()
        
        return doc
        
    def _generate_data_flow_analysis(self) -> str:
        """Generate data flow analysis"""
        analysis = ""
        
        # Find main entry points
        entry_points = [f for f in self.functions.values() if 'main' in f.name.lower() or 'app' in f.name.lower()]
        
        if entry_points:
            analysis += "### Application Entry Points\n\n"
            for entry in entry_points:
                analysis += f"- **{entry.name}()** in `{entry.file_path}`\n"
                
        # Analyze API call flows
        api_functions = [f for f in self.functions.values() if any(e.function_name == f.name for e in self.api_endpoints)]
        
        if api_functions:
            analysis += "\n### API Call Flows\n\n"
            for func in api_functions:
                endpoint = next((e for e in self.api_endpoints if e.function_name == func.name), None)
                if endpoint:
                    analysis += f"**{endpoint.method} {endpoint.path}**\n"
                    analysis += f"1. Calls `{func.name}()` in `{func.file_path}`\n"
                    if func.calls:
                        analysis += f"2. Which calls: {', '.join(func.calls[:3])}\n"
                    analysis += "\n"
                    
        return analysis
        
    def save_documentation(self, output_path: str):
        """Save documentation to file"""
        self.analyze_python_files()
        doc_content = self.generate_documentation()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)
            
        print(f"Documentation saved to: {output_path}")
        print(f"Functions analyzed: {len(self.functions)}")
        print(f"API endpoints found: {len(self.api_endpoints)}")

if __name__ == "__main__":
    generator = ApplicationDocumentationGenerator("/home/buymeagoat/dev/whisper-transcriber")
    generator.save_documentation("/home/buymeagoat/dev/whisper-transcriber/docs/FUNCTION_REFERENCE.md")
