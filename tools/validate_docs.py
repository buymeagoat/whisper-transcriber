#!/usr/bin/env python3
"""
Documentation Validator

Validates architecture documentation for consistency, syntax, and completeness.
Used by the Makefile and CI/CD pipeline to ensure documentation quality.

Usage: python tools/validate_docs.py
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

class DocumentationValidator:
    def __init__(self):
        self.docs_dir = Path("docs/architecture")
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> bool:
        """Validate all architecture documentation. Returns True if valid."""
        print("🔍 Validating architecture documentation...")
        
        self.validate_inventory()
        self.validate_markdown_files()
        self.validate_links()
        self.validate_mermaid_syntax()
        
        # Report results
        if self.errors:
            print(f"\n❌ {len(self.errors)} errors found:")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ All documentation validation checks passed")
        elif not self.errors:
            print("✅ No errors found (warnings are informational)")
        
        return len(self.errors) == 0
    
    def validate_inventory(self):
        """Validate INVENTORY.json structure and content."""
        inventory_file = self.docs_dir / "INVENTORY.json"
        
        if not inventory_file.exists():
            self.errors.append("INVENTORY.json not found")
            return
        
        try:
            with open(inventory_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"INVENTORY.json is invalid JSON: {e}")
            return
        
        # Check required sections
        required_sections = ["metadata", "statistics", "modules", "api_endpoints"]
        for section in required_sections:
            if section not in data:
                self.errors.append(f"INVENTORY.json missing required section: {section}")
        
        # Validate statistics
        stats = data.get("statistics", {})
        if stats.get("total_modules", 0) == 0:
            self.warnings.append("No modules found in inventory")
        
        if stats.get("total_functions", 0) == 0:
            self.warnings.append("No functions found in inventory")
        
        # Check metadata
        metadata = data.get("metadata", {})
        if not metadata.get("scan_timestamp"):
            self.warnings.append("Inventory missing scan timestamp")
    
    def validate_markdown_files(self):
        """Validate markdown file structure and content."""
        required_files = [
            "ARCHITECTURE.md",
            "ICD.md", 
            "TRACEABILITY.md",
            "READ_ME_FIRST.md",
            "CONTRIBUTING_NOTES.md"
        ]
        
        for filename in required_files:
            file_path = self.docs_dir / filename
            if not file_path.exists():
                self.errors.append(f"Required documentation file not found: {filename}")
                continue
            
            content = file_path.read_text()
            
            # Check for empty files
            if len(content.strip()) < 100:
                self.warnings.append(f"{filename} appears to be too short")
            
            # Check for main heading
            if not content.strip().startswith('#'):
                self.warnings.append(f"{filename} missing main heading")
    
    def validate_links(self):
        """Validate internal links in markdown files."""
        for md_file in self.docs_dir.glob("*.md"):
            content = md_file.read_text()
            
            # Find markdown links
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            
            for link_text, link_url in links:
                # Check internal file links
                if link_url.endswith('.md') and not link_url.startswith('http'):
                    target_path = (md_file.parent / link_url).resolve()
                    if not target_path.exists():
                        self.errors.append(f"{md_file.name}: Broken link to {link_url}")
                
                # Check relative paths
                elif link_url.startswith('../') and not link_url.startswith('http'):
                    target_path = (md_file.parent / link_url).resolve()
                    if not target_path.exists():
                        self.warnings.append(f"{md_file.name}: Potentially broken relative link {link_url}")
    
    def validate_mermaid_syntax(self):
        """Basic validation of Mermaid diagram syntax."""
        for md_file in self.docs_dir.glob("*.md"):
            content = md_file.read_text()
            
            # Find mermaid code blocks
            mermaid_blocks = re.findall(r'```mermaid\n(.*?)\n```', content, re.DOTALL)
            
            for i, block in enumerate(mermaid_blocks, 1):
                if not block.strip():
                    self.errors.append(f"{md_file.name}: Empty Mermaid diagram block {i}")
                    continue
                
                # Check for valid diagram types
                valid_types = ['graph', 'flowchart', 'sequenceDiagram', 'stateDiagram', 'classDiagram']
                if not any(diagram_type in block for diagram_type in valid_types):
                    self.warnings.append(f"{md_file.name}: Mermaid block {i} has unknown diagram type")
                
                # Check for basic syntax issues
                if block.count('{') != block.count('}'):
                    self.errors.append(f"{md_file.name}: Mermaid block {i} has mismatched braces")

def main():
    """Main entry point."""
    validator = DocumentationValidator()
    
    if validator.validate_all():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
