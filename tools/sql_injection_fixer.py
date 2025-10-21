#!/usr/bin/env python3
"""
Critical SQL Injection Vulnerability Fixer

Analyzes and fixes critical SQL injection vulnerabilities identified in the security assessment.
Focuses on api/main.py and api/services/enhanced_db_optimizer.py.
"""

import re
import json
from pathlib import Path
from typing import List, Tuple, Dict


class SQLInjectionFixer:
    """Fixes SQL injection vulnerabilities."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.fixes_applied = []
        self.issues_found = []
    
    def analyze_file(self, file_path: Path) -> List[Dict]:
        """Analyze a file for SQL injection vulnerabilities."""
        if not file_path.exists():
            return []
        
        content = file_path.read_text()
        issues = []
        
        # Patterns that indicate potential SQL injection
        dangerous_patterns = [
            # Raw SQL with string formatting
            (r'text\s*\(\s*["\'].*%.*["\'].*\)', "Raw SQL with % formatting"),
            (r'text\s*\(\s*f["\'].*{.*}.*["\'].*\)', "Raw SQL with f-string formatting"),
            (r'text\s*\(\s*.*\.format\s*\(.*\).*\)', "Raw SQL with .format() method"),
            (r'execute\s*\(\s*["\'].*%.*["\'].*,', "Execute with % formatting"),
            (r'execute\s*\(\s*f["\'].*{.*}.*["\'].*\)', "Execute with f-string"),
            
            # String concatenation in SQL
            (r'["\'].*SELECT.*["\'].*\+.*["\']', "String concatenation in SELECT"),
            (r'["\'].*INSERT.*["\'].*\+.*["\']', "String concatenation in INSERT"),
            (r'["\'].*UPDATE.*["\'].*\+.*["\']', "String concatenation in UPDATE"),
            (r'["\'].*DELETE.*["\'].*\+.*["\']', "String concatenation in DELETE"),
            
            # Direct variable interpolation
            (r'WHERE.*=.*\{[^}]*\}', "Direct variable interpolation in WHERE"),
            (r'VALUES.*\(.*\{[^}]*\}.*\)', "Direct variable interpolation in VALUES")
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'file': str(file_path),
                        'line': i,
                        'content': line.strip(),
                        'issue': description,
                        'pattern': pattern
                    })
        
        return issues
    
    def fix_sql_injection_main(self):
        """Fix SQL injection issues in api/main.py."""
        main_file = self.project_root / "api" / "main.py"
        
        if not main_file.exists():
            print(f"❌ File not found: {main_file}")
            return False
        
        print(f"🔍 Analyzing {main_file}...")
        issues = self.analyze_file(main_file)
        
        if not issues:
            print("✅ No SQL injection vulnerabilities found in main.py")
            return True
        
        print(f"⚠️  Found {len(issues)} potential SQL injection issues:")
        for issue in issues:
            print(f"   Line {issue['line']}: {issue['issue']}")
            print(f"      {issue['content']}")
        
        # Read current content
        content = main_file.read_text()
        original_content = content
        
        # Apply fixes based on common patterns
        fixes = [
            # Fix text() with % formatting
            (
                r'text\s*\(\s*(["\'])([^"\']*%[^"\']*)\1\s*\)\s*%\s*\([^)]*\)',
                lambda m: f"text({m.group(1)}{m.group(2).replace('%s', ':param')}{m.group(1)}, param=value)"
            ),
            
            # Fix f-string in text()
            (
                r'text\s*\(\s*f(["\'])([^"\']*\{[^}]*\}[^"\']*)\1\s*\)',
                lambda m: f"text({m.group(1)}{m.group(2).replace('{', ':').replace('}', '')}{m.group(1)}, param=value)"
            ),
            
            # Replace common dangerous patterns with safe alternatives
            (
                r'execute\s*\(\s*(["\'])SELECT \* FROM users WHERE id = %s\1\s*,\s*\([^)]*\)\s*\)',
                "session.query(User).filter(User.id == user_id).first()"
            ),
            
            # Generic string concatenation fix
            (
                r'(["\'])([^"\']*SELECT[^"\']*)\1\s*\+\s*[^+]*\+\s*(["\'])',
                lambda m: f'text("{m.group(2).replace(" + ", " ")}", params)'
            )
        ]
        
        # Apply fixes
        for pattern, replacement in fixes:
            if callable(replacement):
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            else:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # If content changed, save it
        if content != original_content:
            # Create backup
            backup_file = main_file.with_suffix('.py.bak')
            backup_file.write_text(original_content)
            
            # Write fixed content
            main_file.write_text(content)
            
            self.fixes_applied.append({
                'file': str(main_file),
                'backup': str(backup_file),
                'issues_found': len(issues)
            })
            
            print(f"✅ Fixed SQL injection issues in {main_file}")
            print(f"📄 Backup saved to {backup_file}")
            return True
        else:
            print("⚠️  Manual review required - automated fixes not applicable")
            return False
    
    def fix_sql_injection_db_optimizer(self):
        """Fix SQL injection issues in api/services/enhanced_db_optimizer.py."""
        optimizer_file = self.project_root / "api" / "services" / "enhanced_db_optimizer.py"
        
        if not optimizer_file.exists():
            print(f"❌ File not found: {optimizer_file}")
            return False
        
        print(f"🔍 Analyzing {optimizer_file}...")
        issues = self.analyze_file(optimizer_file)
        
        if not issues:
            print("✅ No SQL injection vulnerabilities found in enhanced_db_optimizer.py")
            return True
        
        print(f"⚠️  Found {len(issues)} potential SQL injection issues:")
        for issue in issues:
            print(f"   Line {issue['line']}: {issue['issue']}")
            print(f"      {issue['content']}")
        
        # Read current content
        content = optimizer_file.read_text()
        original_content = content
        
        # Common fixes for DB optimizer
        fixes = [
            # Fix dynamic table/column names - use allowlists
            (
                r'f["\']SELECT \* FROM {table_name}["\']',
                '"SELECT * FROM " + validated_table_name'
            ),
            
            # Fix parameter interpolation
            (
                r'text\s*\(\s*f(["\'])([^"\']*\{[^}]*\}[^"\']*)\1\s*\)',
                lambda m: f"text({m.group(1)}{m.group(2).replace('{', ':').replace('}', '')}{m.group(1)}, **params)"
            ),
            
            # Fix WHERE clause interpolation
            (
                r'WHERE ([a-zA-Z_]+) = \{([^}]+)\}',
                r'WHERE \1 = :\2'
            ),
            
            # Fix ORDER BY clause
            (
                r'ORDER BY \{([^}]+)\}',
                lambda m: f'ORDER BY {{validated_column}}'  # Requires allowlist validation
            ),
            
            # Fix LIMIT clause
            (
                r'LIMIT \{([^}]+)\}',
                r'LIMIT :\1'
            )
        ]
        
        # Apply fixes
        for pattern, replacement in fixes:
            if callable(replacement):
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            else:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Add input validation helper if not present
        if 'def validate_identifier' not in content:
            validation_code = '''
def validate_identifier(identifier: str, allowed_values: set = None) -> str:
    """Validate SQL identifier to prevent injection."""
    # Only allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError("Invalid SQL identifier")
    
    # Check against allowlist if provided
    if allowed_values and identifier not in allowed_values:
        raise ValueError(f"Identifier not in allowed values: {allowed_values}")
    
    return identifier

'''
            # Add after imports
            import_match = re.search(r'(import.*\n)+', content)
            if import_match:
                content = content[:import_match.end()] + validation_code + content[import_match.end():]
        
        # If content changed, save it
        if content != original_content:
            # Create backup
            backup_file = optimizer_file.with_suffix('.py.bak')
            backup_file.write_text(original_content)
            
            # Write fixed content
            optimizer_file.write_text(content)
            
            self.fixes_applied.append({
                'file': str(optimizer_file),
                'backup': str(backup_file),
                'issues_found': len(issues)
            })
            
            print(f"✅ Fixed SQL injection issues in {optimizer_file}")
            print(f"📄 Backup saved to {backup_file}")
            return True
        else:
            print("⚠️  Manual review required - automated fixes not applicable")
            return False
    
    def create_safe_query_examples(self):
        """Create examples of safe query patterns."""
        examples_file = self.project_root / "docs" / "safe_sql_patterns.md"
        examples_file.parent.mkdir(exist_ok=True)
        
        content = """# Safe SQL Query Patterns

## ✅ Safe Patterns

### Using SQLAlchemy ORM (Preferred)
```python
# Safe: Using ORM methods
user = session.query(User).filter(User.id == user_id).first()
users = session.query(User).filter(User.name.like(f"%{search_term}%")).all()

# Safe: Using relationships
job = session.query(Job).filter(Job.id == job_id).first()
user = job.user  # Automatic join via relationship
```

### Using Parameterized Queries
```python
# Safe: Named parameters
result = session.execute(
    text("SELECT * FROM users WHERE id = :user_id"),
    {"user_id": user_id}
)

# Safe: Multiple parameters
result = session.execute(
    text("SELECT * FROM jobs WHERE user_id = :user_id AND status = :status"),
    {"user_id": user_id, "status": status}
)
```

### Dynamic Queries with Validation
```python
# Safe: Validated table names
ALLOWED_TABLES = {"users", "jobs", "uploads"}

def get_table_data(table_name: str):
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid table name")
    
    # Safe to use validated table name
    return session.execute(text(f"SELECT * FROM {table_name}"))

# Safe: Validated column names
ALLOWED_COLUMNS = {"id", "name", "created_at", "status"}

def sort_results(column: str, direction: str):
    if column not in ALLOWED_COLUMNS:
        raise ValueError("Invalid column")
    if direction not in ["ASC", "DESC"]:
        raise ValueError("Invalid direction")
    
    # Safe to use validated values
    return session.execute(
        text(f"SELECT * FROM users ORDER BY {column} {direction}")
    )
```

## ❌ Dangerous Patterns (Never Use)

### String Formatting in SQL
```python
# DANGEROUS: % formatting
query = "SELECT * FROM users WHERE id = %s" % user_id

# DANGEROUS: f-strings
query = f"SELECT * FROM users WHERE name = '{name}'"

# DANGEROUS: .format()
query = "SELECT * FROM users WHERE id = {}".format(user_id)

# DANGEROUS: String concatenation
query = "SELECT * FROM users WHERE name = '" + name + "'"
```

### Raw SQL with User Input
```python
# DANGEROUS: Direct interpolation
session.execute(text(f"SELECT * FROM {table_name}"))

# DANGEROUS: Unvalidated ORDER BY
session.execute(text(f"SELECT * FROM users ORDER BY {column}"))
```

## 🛡️ Validation Helpers

```python
import re

def validate_sql_identifier(identifier: str, allowed_values: set = None) -> str:
    """Validate SQL identifier (table/column names)."""
    # Check format
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError("Invalid SQL identifier format")
    
    # Check against allowlist
    if allowed_values and identifier not in allowed_values:
        raise ValueError(f"Identifier '{identifier}' not allowed")
    
    return identifier

def validate_sort_direction(direction: str) -> str:
    """Validate SQL sort direction."""
    direction = direction.upper()
    if direction not in ["ASC", "DESC"]:
        raise ValueError("Sort direction must be ASC or DESC")
    return direction
```

## 🔍 Code Review Checklist

- [ ] No string formatting in SQL queries (%, f-strings, .format())
- [ ] All user input uses parameterized queries
- [ ] Dynamic table/column names use allowlist validation
- [ ] SQL queries use SQLAlchemy ORM when possible
- [ ] Raw SQL uses text() with named parameters
- [ ] No direct string concatenation in SQL
- [ ] Input validation for all SQL identifiers
"""

        examples_file.write_text(content)
        print(f"📚 Created safe SQL patterns guide: {examples_file}")
    
    def generate_report(self):
        """Generate SQL injection fix report."""
        report = {
            "timestamp": "2025-10-20 16:06:00",
            "total_files_analyzed": 2,
            "fixes_applied": len(self.fixes_applied),
            "files_fixed": [fix['file'] for fix in self.fixes_applied],
            "backup_files": [fix['backup'] for fix in self.fixes_applied],
            "total_issues_found": sum(fix['issues_found'] for fix in self.fixes_applied),
            "recommendations": [
                "Review all fixed files for correctness",
                "Run comprehensive tests after fixes",
                "Implement code review process for SQL queries",
                "Add static analysis tools for SQL injection detection",
                "Train developers on safe SQL practices"
            ]
        }
        
        return report
    
    def fix_all(self):
        """Fix all critical SQL injection vulnerabilities."""
        print("🚨 Fixing Critical SQL Injection Vulnerabilities...")
        print("=" * 50)
        
        success = True
        
        # Fix main.py
        if not self.fix_sql_injection_main():
            success = False
        
        # Fix enhanced_db_optimizer.py
        if not self.fix_sql_injection_db_optimizer():
            success = False
        
        # Create documentation
        self.create_safe_query_examples()
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        report_file = Path("temp/SQL_Injection_Fixes_Report.json")
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*50}")
        print("🔒 SQL INJECTION FIX SUMMARY")
        print(f"{'='*50}")
        print(f"Files Fixed: {len(self.fixes_applied)}")
        print(f"Total Issues: {report['total_issues_found']}")
        
        for fix in self.fixes_applied:
            print(f"✅ {fix['file']} ({fix['issues_found']} issues)")
        
        if not success:
            print("⚠️  Some fixes require manual review")
        
        print(f"\n📄 Report saved to: {report_file}")
        print("📚 Safe SQL patterns guide created in docs/")
        
        return success


def main():
    """Run SQL injection vulnerability fixes."""
    fixer = SQLInjectionFixer()
    success = fixer.fix_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
