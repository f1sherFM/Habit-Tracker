#!/usr/bin/env python3
"""
SQL Security Verification Script
Verifies that all database operations use SQLAlchemy ORM properly to prevent SQL injection
"""

import ast
import os
import re
from typing import List, Tuple, Dict
from sql_security import ORMSecurityVerifier


class SQLSecurityAuditor:
    """
    Audits Python code for SQL injection vulnerabilities
    """
    
    def __init__(self):
        self.issues = []
        self.safe_patterns = []
        self.orm_verifier = ORMSecurityVerifier()
    
    def audit_file(self, file_path: str) -> Tuple[bool, List[Dict]]:
        """
        Audit a Python file for SQL security issues.
        
        Args:
            file_path: Path to the Python file to audit
            
        Returns:
            Tuple of (is_secure: bool, issues: List[Dict])
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Check for dangerous patterns
            issues.extend(self._check_raw_sql_usage(content, file_path))
            issues.extend(self._check_string_formatting_in_queries(content, file_path))
            issues.extend(self._check_execute_statements(tree, file_path))
            
            # Check for good patterns
            self._check_orm_usage(tree, file_path)
            
        except Exception as e:
            issues.append({
                'file': file_path,
                'line': 0,
                'severity': 'ERROR',
                'message': f'Failed to parse file: {str(e)}'
            })
        
        return len(issues) == 0, issues
    
    def _check_raw_sql_usage(self, content: str, file_path: str) -> List[Dict]:
        """Check for raw SQL string usage that might be vulnerable."""
        issues = []
        lines = content.split('\n')
        
        # Patterns that indicate raw SQL usage
        dangerous_patterns = [
            r'SELECT\s+.*\s+FROM\s+',
            r'INSERT\s+INTO\s+',
            r'UPDATE\s+.*\s+SET\s+',
            r'DELETE\s+FROM\s+',
            r'DROP\s+TABLE\s+',
            r'CREATE\s+TABLE\s+',
            r'ALTER\s+TABLE\s+',
        ]
        
        for line_num, line in enumerate(lines, 1):
            line_upper = line.upper()
            
            # Skip comments and docstrings
            if line.strip().startswith('#') or '"""' in line or "'''" in line:
                continue
            
            for pattern in dangerous_patterns:
                if re.search(pattern, line_upper):
                    # Check if it's in a safe context (using text() or similar)
                    if 'text(' in line or 'db.session.execute' in line:
                        # This might be safe if using parameters
                        if ':' in line or '?' in line or '%s' in line:
                            self.safe_patterns.append({
                                'file': file_path,
                                'line': line_num,
                                'message': 'Raw SQL with parameters - likely safe',
                                'code': line.strip()
                            })
                        else:
                            # Check if it's a migration script
                            if 'migrate' in file_path.lower() or 'migration' in file_path.lower():
                                # Migration scripts often need raw SQL
                                issues.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'severity': 'MEDIUM',
                                    'message': 'Migration script with raw SQL - verify it\'s safe for migration purposes',
                                    'code': line.strip()
                                })
                            else:
                                issues.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'severity': 'HIGH',
                                    'message': 'Raw SQL without parameters - potential SQL injection risk',
                                    'code': line.strip()
                                })
                    else:
                        # Check if it's a migration script
                        if 'migrate' in file_path.lower() or 'migration' in file_path.lower():
                            issues.append({
                                'file': file_path,
                                'line': line_num,
                                'severity': 'MEDIUM',
                                'message': 'Migration script with raw SQL - verify it\'s safe for migration purposes',
                                'code': line.strip()
                            })
                        else:
                            issues.append({
                                'file': file_path,
                                'line': line_num,
                                'severity': 'MEDIUM',
                                'message': 'Raw SQL detected - verify it uses ORM or parameterized queries',
                                'code': line.strip()
                            })
        
        return issues
    
    def _check_string_formatting_in_queries(self, content: str, file_path: str) -> List[Dict]:
        """Check for string formatting in SQL queries."""
        issues = []
        lines = content.split('\n')
        
        # Patterns that indicate string formatting in SQL
        formatting_patterns = [
            r'\.format\(',
            r'%\s*\(',
            r'f["\'].*SELECT',
            r'f["\'].*INSERT',
            r'f["\'].*UPDATE',
            r'f["\'].*DELETE',
        ]
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue
            
            # Skip flash messages and other non-SQL contexts
            if 'flash(' in line or 'print(' in line or 'logger.' in line:
                continue
            
            for pattern in formatting_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if it's in a SQL context
                    if any(sql_word in line.upper() for sql_word in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                        issues.append({
                            'file': file_path,
                            'line': line_num,
                            'severity': 'HIGH',
                            'message': 'String formatting in SQL query - high risk for SQL injection',
                            'code': line.strip()
                        })
        
        return issues
    
    def _check_execute_statements(self, tree: ast.AST, file_path: str) -> List[Dict]:
        """Check for execute statements that might be vulnerable."""
        issues = []
        
        class ExecuteVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if (hasattr(node.func, 'attr') and 
                    node.func.attr in ['execute', 'executemany']):
                    
                    # Check if the first argument is a string literal
                    if (node.args and 
                        isinstance(node.args[0], (ast.Str, ast.Constant))):
                        
                        # Handle both old ast.Str and new ast.Constant
                        if isinstance(node.args[0], ast.Str):
                            sql_content = node.args[0].s
                        else:
                            sql_content = str(node.args[0].value) if isinstance(node.args[0].value, str) else ""
                        
                        # Check if it contains SQL keywords
                        if any(keyword in sql_content.upper() for keyword in 
                               ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE']):
                            
                            # Check if it uses parameters
                            if ':' in sql_content or '?' in sql_content or '%s' in sql_content:
                                # Likely safe - using parameters
                                pass
                            else:
                                # Check if it's a migration script (these are expected to have raw SQL)
                                if 'migrate' in file_path.lower() or 'migration' in file_path.lower():
                                    # Migration scripts often need raw SQL - mark as medium risk
                                    issues.append({
                                        'file': file_path,
                                        'line': node.lineno,
                                        'severity': 'MEDIUM',
                                        'message': 'Migration script with raw SQL - verify it\'s safe for migration purposes',
                                        'code': sql_content[:100] + '...' if len(sql_content) > 100 else sql_content
                                    })
                                else:
                                    issues.append({
                                        'file': file_path,
                                        'line': node.lineno,
                                        'severity': 'HIGH',
                                        'message': 'Execute statement with raw SQL - potential injection risk',
                                        'code': sql_content[:100] + '...' if len(sql_content) > 100 else sql_content
                                    })
                
                self.generic_visit(node)
        
        visitor = ExecuteVisitor()
        visitor.visit(tree)
        
        return issues
    
    def _check_orm_usage(self, tree: ast.AST, file_path: str):
        """Check for proper ORM usage patterns."""
        
        class ORMVisitor(ast.NodeVisitor):
            def __init__(self, auditor):
                self.auditor = auditor
            
            def visit_Call(self, node):
                # Look for ORM query patterns
                if (hasattr(node.func, 'attr') and 
                    node.func.attr in ['query', 'filter', 'filter_by', 'first', 'all']):
                    
                    self.auditor.safe_patterns.append({
                        'file': file_path,
                        'line': node.lineno,
                        'message': 'Using SQLAlchemy ORM - automatically parameterized',
                        'pattern': node.func.attr
                    })
                
                self.generic_visit(node)
        
        visitor = ORMVisitor(self)
        visitor.visit(tree)
    
    def audit_directory(self, directory: str) -> Tuple[bool, Dict]:
        """
        Audit all Python files in a directory.
        
        Args:
            directory: Directory to audit
            
        Returns:
            Tuple of (is_secure: bool, results: Dict)
        """
        results = {
            'files_audited': 0,
            'secure_files': 0,
            'issues': [],
            'safe_patterns': []
        }
        
        for root, dirs, files in os.walk(directory):
            # Skip virtual environment and cache directories
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    results['files_audited'] += 1
                    
                    is_secure, issues = self.audit_file(file_path)
                    
                    if is_secure:
                        results['secure_files'] += 1
                    
                    results['issues'].extend(issues)
        
        results['safe_patterns'] = self.safe_patterns
        
        return results['secure_files'] == results['files_audited'], results


def main():
    """Main function to run the SQL security audit."""
    print("🔍 SQL Security Audit - Verifying ORM Usage and SQL Injection Prevention")
    print("=" * 80)
    
    auditor = SQLSecurityAuditor()
    
    # Audit the current directory
    is_secure, results = auditor.audit_directory('.')
    
    print(f"\n📊 Audit Results:")
    print(f"Files audited: {results['files_audited']}")
    print(f"Secure files: {results['secure_files']}")
    print(f"Files with issues: {results['files_audited'] - results['secure_files']}")
    
    # Report issues
    if results['issues']:
        print(f"\n⚠️  Security Issues Found ({len(results['issues'])}):")
        print("-" * 50)
        
        for issue in results['issues']:
            severity_emoji = {
                'HIGH': '🔴',
                'MEDIUM': '🟡',
                'LOW': '🟢',
                'ERROR': '💥'
            }.get(issue['severity'], '❓')
            
            print(f"{severity_emoji} {issue['severity']}: {issue['file']}:{issue['line']}")
            print(f"   {issue['message']}")
            if 'code' in issue:
                print(f"   Code: {issue['code']}")
            print()
    
    # Report safe patterns
    if results['safe_patterns']:
        print(f"\n✅ Safe Patterns Found ({len(results['safe_patterns'])}):")
        print("-" * 50)
        
        for pattern in results['safe_patterns'][:10]:  # Show first 10
            print(f"✓ {pattern['file']}:{pattern['line']} - {pattern['message']}")
        
        if len(results['safe_patterns']) > 10:
            print(f"   ... and {len(results['safe_patterns']) - 10} more safe patterns")
    
    # Overall security status
    print(f"\n🛡️  Overall Security Status:")
    if is_secure:
        print("✅ All files appear to use secure database practices!")
    else:
        print("❌ Security issues detected. Please review and fix the issues above.")
    
    print("\n📋 Recommendations:")
    print("1. Use SQLAlchemy ORM queries instead of raw SQL")
    print("2. If raw SQL is necessary, use parameterized queries with text()")
    print("3. Never use string formatting or concatenation in SQL queries")
    print("4. Validate and sanitize all user inputs")
    print("5. Use the @sql_injection_protection decorator on routes")
    
    return is_secure


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)