#!/usr/bin/env python3
"""
T026 Security Hardening - Log Injection Vulnerability Scanner and Fixer
Scans and fixes log injection vulnerabilities across all logging statements.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Any, Set, Optional, Union
import json
from datetime import datetime

def create_log_injection_scanner():
    """Create comprehensive log injection vulnerability scanner and fixer"""
    
    print("🔍 T026 Security Hardening - Log Injection Vulnerability Scanner")
    print("=" * 70)
    
    # Step 1: Scan for all logging statements
    log_statements = scan_for_logging_statements()
    
    # Step 2: Analyze for injection vulnerabilities
    vulnerabilities = analyze_log_injection_vulnerabilities(log_statements)
    
    # Step 3: Create sanitization utilities
    create_log_sanitization_utilities()
    
    # Step 4: Fix vulnerable logging statements
    fix_vulnerable_logging_statements(vulnerabilities)
    
    # Step 5: Generate report
    generate_vulnerability_report(log_statements, vulnerabilities)
    
    print("\\n" + "=" * 70)
    print("✅ Log injection vulnerability scanning and fixing completed!")

def scan_for_logging_statements() -> List[Dict[str, Any]]:
    """Scan all Python files for logging statements"""
    
    print("\\n🔍 Scanning for logging statements...")
    
    log_statements = []
    python_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk('/home/buymeagoat/dev/whisper-transcriber'):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', 'temp', 'cache'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"   📁 Found {len(python_files)} Python files to scan")
    
    # Analyze each file for logging statements
    for file_path in python_files:
        try:
            statements = analyze_file_for_logging(file_path)
            log_statements.extend(statements)
        except Exception as e:
            print(f"   ⚠️ Error analyzing {file_path}: {e}")
    
    print(f"   📝 Found {len(log_statements)} logging statements")
    return log_statements

def analyze_file_for_logging(file_path: str) -> List[Dict[str, Any]]:
    """Analyze a single file for logging statements"""
    
    statements = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        # Walk the AST to find logging calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                statement = analyze_logging_call(node, file_path, content)
                if statement:
                    statements.append(statement)
    
    except Exception as e:
        # Fall back to regex-based scanning if AST parsing fails
        statements = regex_scan_logging(file_path, content if 'content' in locals() else None)
    
    return statements

def analyze_logging_call(node: ast.Call, file_path: str, content: str) -> Optional[Dict[str, Any]]:
    """Analyze a specific logging call for vulnerabilities"""
    
    # Check if this is a logging call
    if not is_logging_call(node):
        return None
    
    # Get line number and source code
    line_number = node.lineno
    lines = content.split('\\n')
    source_line = lines[line_number - 1] if line_number <= len(lines) else ""
    
    # Extract logging method and arguments
    method_name = get_logging_method_name(node)
    
    # Analyze arguments for potential injection
    vulnerable_args = []
    for i, arg in enumerate(node.args):
        vulnerability = analyze_logging_argument(arg, i)
        if vulnerability:
            vulnerable_args.append(vulnerability)
    
    # Analyze keyword arguments
    for keyword in node.keywords:
        vulnerability = analyze_logging_argument(keyword.value, keyword.arg)
        if vulnerability:
            vulnerable_args.append(vulnerability)
    
    return {
        'file_path': file_path,
        'line_number': line_number,
        'source_line': source_line.strip(),
        'method_name': method_name,
        'vulnerable_args': vulnerable_args,
        'risk_level': calculate_risk_level(vulnerable_args, source_line)
    }

def is_logging_call(node: ast.Call) -> bool:
    """Check if an AST node is a logging call"""
    
    # Direct logging calls: logger.info(), log.error(), etc.
    if isinstance(node.func, ast.Attribute):
        attr_name = node.func.attr
        if attr_name in ['debug', 'info', 'warning', 'warn', 'error', 'critical', 'exception']:
            return True
    
    # Module-level logging calls: logging.info(), etc.
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        if node.func.value.id == 'logging' and node.func.attr in ['debug', 'info', 'warning', 'warn', 'error', 'critical', 'exception']:
            return True
    
    # Print statements (potential logging)
    if isinstance(node.func, ast.Name) and node.func.id == 'print':
        return True
    
    return False

def get_logging_method_name(node: ast.Call) -> str:
    """Get the logging method name from an AST node"""
    
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    elif isinstance(node.func, ast.Name):
        return node.func.id
    return "unknown"

def analyze_logging_argument(arg: ast.AST, position: Any) -> Optional[Dict[str, Any]]:
    """Analyze a logging argument for injection vulnerabilities"""
    
    vulnerability = {
        'position': position,
        'type': None,
        'risk': 'low',
        'description': None
    }
    
    # String formatting (high risk)
    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
        vulnerability['type'] = 'string_formatting'
        vulnerability['risk'] = 'high'
        vulnerability['description'] = 'Uses % string formatting which can be vulnerable to injection'
        return vulnerability
    
    # f-string with variables (medium risk)
    if isinstance(arg, ast.JoinedStr):
        vulnerability['type'] = 'f_string'
        vulnerability['risk'] = 'medium'
        vulnerability['description'] = 'Uses f-string with variables that may not be sanitized'
        return vulnerability
    
    # String concatenation with variables (medium risk)
    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
        vulnerability['type'] = 'string_concatenation'
        vulnerability['risk'] = 'medium'
        vulnerability['description'] = 'Uses string concatenation with variables'
        return vulnerability
    
    # .format() calls (medium risk)
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == 'format':
        vulnerability['type'] = 'format_method'
        vulnerability['risk'] = 'medium'
        vulnerability['description'] = 'Uses .format() method which may include unsanitized variables'
        return vulnerability
    
    # Variable references (low to medium risk)
    if isinstance(arg, (ast.Name, ast.Attribute, ast.Subscript)):
        vulnerability['type'] = 'variable_reference'
        vulnerability['risk'] = 'low'
        vulnerability['description'] = 'References variable that may contain unsanitized data'
        return vulnerability
    
    return None

def regex_scan_logging(file_path: str, content: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fallback regex-based logging scanner"""
    
    if content is None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return []
    
    statements = []
    lines = content.split('\\n')
    
    # Regex patterns for logging statements
    patterns = [
        r'\b(logger|log|logging)\.(debug|info|warning|warn|error|critical|exception)\s*\(',
        r'\bprint\s*\(',
        r'\bsystem_log\.(debug|info|warning|warn|error|critical|exception)\s*\(',
        r'\bbackend_log\.(debug|info|warning|warn|error|critical|exception)\s*\(',
    ]
    
    for line_num, line in enumerate(lines, 1):
        for pattern in patterns:
            if re.search(pattern, line):
                # Analyze for injection patterns
                vulnerable_args = []
                risk_level = 'low'
                
                # Check for high-risk patterns
                if re.search(r'%[sdf]', line):
                    vulnerable_args.append({
                        'type': 'string_formatting',
                        'risk': 'high',
                        'description': 'Uses % string formatting'
                    })
                    risk_level = 'high'
                
                elif re.search(r'f["\'].*{.*}', line):
                    vulnerable_args.append({
                        'type': 'f_string',
                        'risk': 'medium', 
                        'description': 'Uses f-string with variables'
                    })
                    risk_level = 'medium'
                
                elif re.search(r'\\.format\\(', line):
                    vulnerable_args.append({
                        'type': 'format_method',
                        'risk': 'medium',
                        'description': 'Uses .format() method'
                    })
                    risk_level = 'medium'
                
                statements.append({
                    'file_path': file_path,
                    'line_number': line_num,
                    'source_line': line.strip(),
                    'method_name': 'unknown',
                    'vulnerable_args': vulnerable_args,
                    'risk_level': risk_level
                })
                break
    
    return statements

def calculate_risk_level(vulnerable_args: List[Dict], source_line: str) -> str:
    """Calculate overall risk level for a logging statement"""
    
    if not vulnerable_args:
        return 'safe'
    
    highest_risk = 'low'
    for arg in vulnerable_args:
        if arg['risk'] == 'high':
            highest_risk = 'high'
        elif arg['risk'] == 'medium' and highest_risk != 'high':
            highest_risk = 'medium'
    
    # Additional risk factors
    if any(keyword in source_line.lower() for keyword in ['error', 'exception', 'fail']):
        if highest_risk == 'medium':
            highest_risk = 'high'
        elif highest_risk == 'low':
            highest_risk = 'medium'
    
    return highest_risk

def analyze_log_injection_vulnerabilities(log_statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze logging statements for injection vulnerabilities"""
    
    print("\\n🚨 Analyzing for log injection vulnerabilities...")
    
    vulnerabilities = []
    risk_counts = {'high': 0, 'medium': 0, 'low': 0, 'safe': 0}
    
    for statement in log_statements:
        risk_level = statement['risk_level']
        risk_counts[risk_level] += 1
        
        if risk_level in ['high', 'medium']:
            vulnerabilities.append(statement)
    
    print(f"   📊 Risk Analysis:")
    print(f"     🔴 High Risk: {risk_counts['high']} statements")
    print(f"     🟡 Medium Risk: {risk_counts['medium']} statements") 
    print(f"     🟢 Low Risk: {risk_counts['low']} statements")
    print(f"     ✅ Safe: {risk_counts['safe']} statements")
    
    print(f"   🚨 Found {len(vulnerabilities)} statements requiring fixes")
    
    return vulnerabilities

def create_log_sanitization_utilities():
    """Create utilities for safe logging"""
    
    print("\\n🛠️ Creating log sanitization utilities...")
    
    sanitization_content = '''"""
Log Sanitization Utilities for T026 Security Hardening
Provides safe logging functions to prevent log injection attacks.
"""

import re
import html
import json
from typing import Any, Dict, List, Union, Optional
from datetime import datetime


class LogSanitizer:
    """
    Comprehensive log sanitization utility to prevent injection attacks.
    
    Features:
    - Input sanitization for log injection prevention
    - Structured logging support
    - Safe string formatting
    - Control character removal
    - Length limiting
    """
    
    def __init__(self, max_length: int = 1000):
        self.max_length = max_length
        self._setup_sanitization_patterns()
    
    def _setup_sanitization_patterns(self):
        """Setup regex patterns for sanitization"""
        
        # Dangerous patterns that could be used for log injection
        self.dangerous_patterns = [
            # Control characters including CRLF injection
            (r'[\\r\\n\\f\\t\\v\\x00-\\x1f\\x7f-\\x9f]', ''),
            # Log4j-style variable substitution
            (r'\\${[^}]*}', '[REMOVED]'),
            # Format string attacks
            (r'%[a-zA-Z0-9#\\-\\+\\s]*[diouxXeEfFgGcs]', '[REMOVED]'),
            # Script tags
            (r'<script[^>]*>.*?</script>', '[SCRIPT_REMOVED]'),
            # JavaScript URLs
            (r'javascript:', '[JS_REMOVED]'),
            # Data URLs
            (r'data:.*?base64', '[DATA_URL_REMOVED]'),
            # LDAP injection patterns
            (r'\\(.*?\\)', '[LDAP_REMOVED]'),
            # SQL injection patterns
            (r'(union|select|insert|update|delete|drop|create|alter)\\s+', '[SQL_REMOVED]'),
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE | re.DOTALL), replacement)
            for pattern, replacement in self.dangerous_patterns
        ]
    
    def sanitize_log_input(self, data: Any) -> str:
        """
        Sanitize input data for safe logging.
        
        Args:
            data: Input data to sanitize
            
        Returns:
            Sanitized string safe for logging
        """
        
        # Convert to string first
        if data is None:
            return "None"
        
        if isinstance(data, (dict, list)):
            try:
                data_str = json.dumps(data, default=str, separators=(',', ':'))
            except (TypeError, ValueError):
                data_str = str(data)
        else:
            data_str = str(data)
        
        # Apply sanitization patterns
        sanitized = data_str
        for pattern, replacement in self.compiled_patterns:
            sanitized = pattern.sub(replacement, sanitized)
        
        # HTML escape for additional safety
        sanitized = html.escape(sanitized)
        
        # Remove any remaining control characters
        sanitized = re.sub(r'[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]', '', sanitized)
        
        # Limit length to prevent log flooding
        if len(sanitized) > self.max_length:
            sanitized = sanitized[:self.max_length - 3] + "..."
        
        return sanitized
    
    def safe_format(self, template: str, *args, **kwargs) -> str:
        """
        Safe string formatting for logging.
        
        Args:
            template: Log message template
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Safely formatted log message
        """
        
        # Sanitize template
        safe_template = self.sanitize_log_input(template)
        
        # Sanitize arguments
        safe_args = [self.sanitize_log_input(arg) for arg in args]
        safe_kwargs = {k: self.sanitize_log_input(v) for k, v in kwargs.items()}
        
        try:
            # Use .format() instead of % formatting for safety
            return safe_template.format(*safe_args, **safe_kwargs)
        except (KeyError, ValueError, IndexError):
            # Fallback to template if formatting fails
            return safe_template
    
    def create_log_entry(self, level: str, message: str, **context) -> Dict[str, Any]:
        """
        Create a structured, safe log entry.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **context: Additional context data
            
        Returns:
            Structured log entry dictionary
        """
        
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.upper(),
            'message': self.sanitize_log_input(message),
        }
        
        # Add sanitized context data
        if context:
            entry['context'] = {
                k: self.sanitize_log_input(v) for k, v in context.items()
            }
        
        return entry


# Global sanitizer instance
_log_sanitizer = LogSanitizer()


def safe_log_format(template: str, *args, **kwargs) -> str:
    """
    Safe log message formatting function.
    
    Usage:
        logger.info(safe_log_format("User {} logged in from {}", username, ip_address))
    """
    return _log_sanitizer.safe_format(template, *args, **kwargs)


def sanitize_for_log(data: Any) -> str:
    """
    Sanitize data for safe logging.
    
    Usage:
        logger.info(f"Processing file: {sanitize_for_log(filename)}")
    """
    return _log_sanitizer.sanitize_log_input(data)


def create_safe_log_entry(level: str, message: str, **context) -> str:
    """
    Create a safe, structured log entry as JSON string.
    
    Usage:
        logger.info(create_safe_log_entry("INFO", "User action", user_id=user_id, action=action))
    """
    entry = _log_sanitizer.create_log_entry(level, message, **context)
    return json.dumps(entry, separators=(',', ':'))


# Convenient wrapper functions for common logging patterns
def safe_user_log(message: str, user_id: str = None, ip_address: str = None, **kwargs) -> str:
    """Safe logging for user-related events"""
    context = {}
    if user_id:
        context['user_id'] = user_id
    if ip_address:
        context['ip_address'] = ip_address
    context.update(kwargs)
    
    return safe_log_format(message, **context)


def safe_error_log(message: str, error: Exception = None, **kwargs) -> str:
    """Safe logging for error events"""
    if error:
        kwargs['error_type'] = type(error).__name__
        kwargs['error_message'] = str(error)
    
    return safe_log_format(message, **kwargs)


def safe_security_log(message: str, threat_type: str = None, source_ip: str = None, **kwargs) -> str:
    """Safe logging for security events"""
    if threat_type:
        kwargs['threat_type'] = threat_type
    if source_ip:
        kwargs['source_ip'] = source_ip
    
    return safe_log_format(message, **kwargs)


# Migration helpers for updating existing logging statements
def migrate_format_string(original: str, *args) -> str:
    """
    Migrate % formatting to safe formatting.
    
    Usage:
        # Old: logger.info("User %s logged in" % username)
        # New: logger.info(migrate_format_string("User %s logged in", username))
    """
    # Replace % placeholders with {} placeholders
    safe_template = re.sub(r'%[sdf]', '{}', original)
    return safe_log_format(safe_template, *args)


def migrate_fstring(template: str, **kwargs) -> str:
    """
    Migrate f-strings to safe formatting.
    
    Usage:
        # Old: logger.info(f"User {username} from {ip}")
        # New: logger.info(migrate_fstring("User {username} from {ip}", username=username, ip=ip))
    """
    return safe_log_format(template, **kwargs)
'''

    # Write sanitization utilities
    utils_dir = Path("api/utils")
    utils_dir.mkdir(exist_ok=True)
    
    with open(utils_dir / "log_sanitization.py", 'w') as f:
        f.write(sanitization_content)
    
    print(f"   ✅ Created log sanitization utilities: {utils_dir / 'log_sanitization.py'}")

def fix_vulnerable_logging_statements(vulnerabilities: List[Dict[str, Any]]):
    """Fix vulnerable logging statements"""
    
    print("\\n🔧 Fixing vulnerable logging statements...")
    
    if not vulnerabilities:
        print("   ✅ No vulnerabilities found to fix")
        return
    
    # Group by file for efficient processing
    files_to_fix = {}
    for vuln in vulnerabilities:
        file_path = vuln['file_path']
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append(vuln)
    
    fixes_applied = 0
    
    for file_path, file_vulns in files_to_fix.items():
        try:
            fixes_applied += fix_file_logging_statements(file_path, file_vulns)
        except Exception as e:
            print(f"   ❌ Error fixing {file_path}: {e}")
    
    print(f"   ✅ Applied {fixes_applied} logging security fixes")

def fix_file_logging_statements(file_path: str, vulnerabilities: List[Dict[str, Any]]) -> int:
    """Fix logging statements in a single file"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\\n')
        fixes_applied = 0
        
        # Sort vulnerabilities by line number (descending) to avoid line number shifts
        vulnerabilities.sort(key=lambda x: x['line_number'], reverse=True)
        
        for vuln in vulnerabilities:
            line_num = vuln['line_number'] - 1  # Convert to 0-based index
            if line_num < len(lines):
                original_line = lines[line_num]
                fixed_line = fix_logging_line(original_line, vuln)
                
                if fixed_line != original_line:
                    lines[line_num] = fixed_line
                    fixes_applied += 1
        
        # Write back if changes were made
        if fixes_applied > 0:
            # Add import for sanitization utilities
            if 'from api.utils.log_sanitization import' not in content:
                # Find a good place to add the import
                import_line = "from api.utils.log_sanitization import safe_log_format, sanitize_for_log\\n"
                
                # Find existing imports or add at the top
                for i, line in enumerate(lines):
                    if line.startswith('from ') or line.startswith('import '):
                        lines.insert(i, import_line)
                        break
                else:
                    lines.insert(0, import_line)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\\n'.join(lines))
        
        return fixes_applied
    
    except Exception as e:
        print(f"   ❌ Error processing {file_path}: {e}")
        return 0

def fix_logging_line(line: str, vulnerability: Dict[str, Any]) -> str:
    """Fix a specific logging line"""
    
    # Add sanitization import comment if not present
    if '# T026 Security: Fixed log injection' in line:
        return line  # Already fixed
    
    fixed_line = line
    
    # Fix % string formatting
    if any(arg.get('type') == 'string_formatting' for arg in vulnerability['vulnerable_args']):
        # Convert % formatting to safe_log_format
        if '%s' in line or '%d' in line or '%f' in line:
            # Simple pattern matching for common cases
            pattern = r'(["\'])([^"\']*%[sdf][^"\']*)\\1\\s*%\\s*(.+)'
            match = re.search(pattern, line)
            if match:
                quote, template, args = match.groups()
                # Convert to safe formatting
                safe_template = template.replace('%s', '{}').replace('%d', '{}').replace('%f', '{}')
                replacement = f'safe_log_format({quote}{safe_template}{quote}, {args})'
                fixed_line = re.sub(pattern, replacement, line)
    
    # Fix f-strings with variables
    elif any(arg.get('type') == 'f_string' for arg in vulnerability['vulnerable_args']):
        # Convert f-strings to use sanitized variables
        fstring_pattern = r'f["\']([^"\']*{[^}]+}[^"\']*)["\']'
        
        def replace_fstring(match):
            template = match.group(1)
            # Extract variables from f-string
            var_pattern = r'{([^}]+)}'
            variables = re.findall(var_pattern, template)
            
            # Replace with safe formatting
            safe_template = re.sub(var_pattern, '{}', template)
            sanitized_vars = [f'sanitize_for_log({var})' for var in variables]
            
            return f'safe_log_format("{safe_template}", {", ".join(sanitized_vars)})'
        
        fixed_line = re.sub(fstring_pattern, replace_fstring, line)
    
    # Add security comment
    if fixed_line != line:
        # Add comment about the fix
        indent = len(line) - len(line.lstrip())
        comment = ' ' * indent + '# T026 Security: Fixed log injection vulnerability\\n'
        fixed_line = comment + fixed_line
    
    return fixed_line

def generate_vulnerability_report(log_statements: List[Dict[str, Any]], vulnerabilities: List[Dict[str, Any]]):
    """Generate comprehensive vulnerability report"""
    
    print("\\n📊 Generating vulnerability report...")
    
    # Calculate statistics
    total_statements = len(log_statements)
    total_vulnerabilities = len(vulnerabilities)
    
    risk_stats = {'high': 0, 'medium': 0, 'low': 0, 'safe': 0}
    for stmt in log_statements:
        risk_stats[stmt['risk_level']] += 1
    
    # Group vulnerabilities by file
    files_affected = {}
    for vuln in vulnerabilities:
        file_path = vuln['file_path']
        if file_path not in files_affected:
            files_affected[file_path] = []
        files_affected[file_path].append(vuln)
    
    # Generate report
    report = {
        'scan_timestamp': datetime.now().isoformat(),
        'summary': {
            'total_files_scanned': len(set(stmt['file_path'] for stmt in log_statements)),
            'total_logging_statements': total_statements,
            'total_vulnerabilities': total_vulnerabilities,
            'vulnerability_rate': round(total_vulnerabilities / total_statements * 100, 2) if total_statements > 0 else 0,
            'risk_distribution': risk_stats
        },
        'files_affected': len(files_affected),
        'vulnerabilities_by_type': {},
        'files': {}
    }
    
    # Analyze vulnerability types
    for vuln in vulnerabilities:
        for arg in vuln['vulnerable_args']:
            vuln_type = arg['type']
            if vuln_type not in report['vulnerabilities_by_type']:
                report['vulnerabilities_by_type'][vuln_type] = 0
            report['vulnerabilities_by_type'][vuln_type] += 1
    
    # Add file details
    for file_path, file_vulns in files_affected.items():
        rel_path = os.path.relpath(file_path, '/home/buymeagoat/dev/whisper-transcriber')
        report['files'][rel_path] = {
            'vulnerability_count': len(file_vulns),
            'highest_risk': max(vuln['risk_level'] for vuln in file_vulns),
            'vulnerabilities': [
                {
                    'line': vuln['line_number'],
                    'risk': vuln['risk_level'],
                    'types': [arg['type'] for arg in vuln['vulnerable_args']]
                }
                for vuln in file_vulns
            ]
        }
    
    # Write report
    reports_dir = Path("logs/security")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / "log_injection_vulnerability_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"   📄 Report saved: {report_file}")
    print(f"\\n📈 Vulnerability Summary:")
    print(f"   📁 Files scanned: {report['summary']['total_files_scanned']}")
    print(f"   📝 Total logging statements: {total_statements}")
    print(f"   🚨 Vulnerabilities found: {total_vulnerabilities}")
    print(f"   📊 Vulnerability rate: {report['summary']['vulnerability_rate']}%")
    print(f"\\n🔍 Risk Distribution:")
    print(f"   🔴 High Risk: {risk_stats['high']}")
    print(f"   🟡 Medium Risk: {risk_stats['medium']}")
    print(f"   🟢 Low Risk: {risk_stats['low']}")
    print(f"   ✅ Safe: {risk_stats['safe']}")
    
    if files_affected:
        print(f"\\n📁 Most Affected Files:")
        sorted_files = sorted(files_affected.items(), key=lambda x: len(x[1]), reverse=True)
        for file_path, file_vulns in sorted_files[:5]:
            rel_path = os.path.relpath(file_path, '/home/buymeagoat/dev/whisper-transcriber')
            print(f"   • {rel_path}: {len(file_vulns)} vulnerabilities")

def main():
    """Main function to scan and fix log injection vulnerabilities"""
    
    create_log_injection_scanner()
    
    print("\\n" + "=" * 70)
    print("📋 T026 Security Hardening - Log Injection Fixes Summary:")
    print("   • Scanned all Python files for logging statements")
    print("   • Identified log injection vulnerabilities")
    print("   • Created comprehensive sanitization utilities")
    print("   • Applied automated fixes to vulnerable statements")
    print("   • Generated detailed vulnerability report")
    print("\\n🔒 Security Improvements:")
    print("   • Input sanitization prevents CRLF injection")
    print("   • Safe string formatting prevents format string attacks")
    print("   • Control character removal prevents log manipulation")
    print("   • Length limiting prevents log flooding")
    print("   • Structured logging with proper escaping")

if __name__ == "__main__":
    main()