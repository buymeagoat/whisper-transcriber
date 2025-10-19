#!/usr/bin/env python3
"""
Architecture Documentation Updater

Updates architecture documentation files based on the current INVENTORY.json.
This script refreshes dynamic sections in ARCHITECTURE.md, ICD.md, and TRACEABILITY.md
while preserving manual content.

Usage: python tools/update_architecture_docs.py
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

class DocumentationUpdater:
    def __init__(self, inventory_path: str = "docs/architecture/INVENTORY.json"):
        self.inventory_path = Path(inventory_path)
        self.docs_dir = Path("docs/architecture")
        self.inventory = self._load_inventory()
        
    def _load_inventory(self) -> Dict[str, Any]:
        """Load the current inventory data."""
        if not self.inventory_path.exists():
            raise FileNotFoundError(f"Inventory file not found: {self.inventory_path}")
            
        with open(self.inventory_path) as f:
            return json.load(f)
    
    def update_all_docs(self):
        """Update all architecture documentation files."""
        print("🔄 Updating architecture documentation...")
        
        self.update_architecture_md()
        self.update_icd_md()
        self.update_traceability_md()
        
        print("✅ Architecture documentation updated successfully")
    
    def update_architecture_md(self):
        """Update dynamic sections in ARCHITECTURE.md."""
        arch_file = self.docs_dir / "ARCHITECTURE.md"
        if not arch_file.exists():
            print(f"⚠️  {arch_file} not found, skipping")
            return
            
        content = arch_file.read_text()
        
        # Update system statistics
        stats = self.inventory.get("statistics", {})
        stats_section = f"""
## 📊 System Statistics

| Metric | Count |
|--------|-------|
| Total Modules | {stats.get('total_modules', 0)} |
| Total Functions | {stats.get('total_functions', 0)} |
| API Endpoints | {stats.get('total_api_endpoints', 0)} |
| Configuration Variables | {stats.get('total_config_vars', 0)} |
| Data Stores | {stats.get('total_data_stores', 0)} |

*Last updated: {self.inventory.get('metadata', {}).get('scan_timestamp', 'Unknown')}*
"""
        
        # Replace or append statistics section
        if "## 📊 System Statistics" in content:
            # Find the section and replace it
            pattern = r'## 📊 System Statistics.*?(?=\n## |\Z)'
            content = re.sub(pattern, stats_section.strip(), content, flags=re.DOTALL)
        else:
            # Insert after the main heading - find first line starting with #
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('# '):
                    lines.insert(i + 1, stats_section)
                    break
            content = '\n'.join(lines)
        
        # Update component overview
        modules_dict = self.inventory.get("modules", {})
        component_list = []
        
        # Convert dict to list and take first 10
        module_items = list(modules_dict.items())[:10]
        
        for module_name, module_info in module_items:
            func_count = len(module_info.get("functions", []))
            component_list.append(f"- **{module_name}**: {func_count} functions")
        
        if len(modules_dict) > 10:
            component_list.append(f"- *...and {len(modules_dict) - 10} more modules*")
        
        component_section = f"""
### 🏗️ Component Overview

{chr(10).join(component_list)}
"""
        
        # Replace component overview if it exists
        if "### 🏗️ Component Overview" in content:
            pattern = r'### 🏗️ Component Overview.*?(?=\n### |\n## |\Z)'
            content = re.sub(pattern, component_section.strip(), content, flags=re.DOTALL)
        
        arch_file.write_text(content)
        print(f"📝 Updated {arch_file}")
    
    def update_icd_md(self):
        """Update API endpoint specifications in ICD.md."""
        icd_file = self.docs_dir / "ICD.md"
        if not icd_file.exists():
            print(f"⚠️  {icd_file} not found, skipping")
            return
            
        content = icd_file.read_text()
        
        # Generate endpoint table
        endpoints = self.inventory.get("api_endpoints", [])
        if not endpoints:
            return
            
        endpoint_rows = []
        for endpoint in endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "/unknown")
            handler = endpoint.get("handler_function", "unknown")
            module = endpoint.get("module", "unknown")
            
            endpoint_rows.append(f"| `{method}` | `{path}` | `{handler}` | {module} |")
        
        endpoints_table = f"""
## 🔗 API Endpoints Overview

| Method | Path | Handler | Module |
|--------|------|---------|--------|
{chr(10).join(endpoint_rows)}

*Total endpoints: {len(endpoints)}*
"""
        
        # Replace endpoints overview if it exists
        if "## 🔗 API Endpoints Overview" in content:
            pattern = r'## 🔗 API Endpoints Overview.*?(?=\n## |\Z)'
            content = re.sub(pattern, endpoints_table.strip(), content, flags=re.DOTALL)
        else:
            # Insert after the main heading - find first line starting with #
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('# '):
                    lines.insert(i + 1, endpoints_table)
                    break
            content = '\n'.join(lines)
        
        icd_file.write_text(content)
        print(f"📝 Updated {icd_file}")
    
    def update_traceability_md(self):
        """Update code-to-test mappings in TRACEABILITY.md."""
        trace_file = self.docs_dir / "TRACEABILITY.md"
        if not trace_file.exists():
            print(f"⚠️  {trace_file} not found, skipping")
            return
            
        content = trace_file.read_text()
        
        # Generate module coverage summary
        modules_dict = self.inventory.get("modules", {})
        coverage_rows = []
        
        for module_name, module_info in modules_dict.items():
            file_path = module_info.get("file_path", "")
            functions = module_info.get("functions", [])
            
            # Simple heuristic: check if there's a corresponding test file
            test_file = self._find_test_file(file_path)
            status = "✅ Covered" if test_file else "❌ Missing"
            
            coverage_rows.append(f"| {module_name} | {len(functions)} | {status} |")
        
        coverage_table = f"""
## 📊 Test Coverage Summary

| Module | Functions | Test Status |
|--------|-----------|-------------|
{chr(10).join(coverage_rows)}

*Coverage analysis based on file naming conventions*
"""
        
        # Replace coverage summary if it exists
        if "## 📊 Test Coverage Summary" in content:
            pattern = r'## 📊 Test Coverage Summary.*?(?=\n## |\Z)'
            content = re.sub(pattern, coverage_table.strip(), content, flags=re.DOTALL)
        
        trace_file.write_text(content)
        print(f"📝 Updated {trace_file}")
    
    def _find_test_file(self, source_path: str) -> bool:
        """Check if a corresponding test file exists for the given source file."""
        if not source_path:
            return False
            
        source = Path(source_path)
        
        # Common test file patterns
        test_patterns = [
            f"test_{source.stem}.py",
            f"{source.stem}_test.py",
            f"test_{source.stem.replace('_', '')}.py"
        ]
        
        # Check in tests/ directory
        tests_dir = Path("tests")
        if tests_dir.exists():
            for pattern in test_patterns:
                if (tests_dir / pattern).exists():
                    return True
        
        # Check in same directory
        for pattern in test_patterns:
            if (source.parent / pattern).exists():
                return True
                
        return False

def main():
    """Main entry point."""
    try:
        updater = DocumentationUpdater()
        updater.update_all_docs()
    except Exception as e:
        print(f"❌ Error updating documentation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
