"""
Integration script for enhanced security headers middleware
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def integrate_security_headers():
    """Integrate enhanced security headers middleware into main application"""
    
    main_py_path = project_root / "api" / "main.py"
    
    if not main_py_path.exists():
        print(f"Error: {main_py_path} not found")
        return False
    
    # Read current main.py
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Check if enhanced security headers are already imported
    if "EnhancedSecurityHeadersMiddleware" in content:
        print("Enhanced security headers middleware already integrated")
        return True
    
    # Find the import section for middlewares
    import_section = """from api.middlewares.security_headers import SecurityHeadersMiddleware"""
    
    if import_section in content:
        # Replace the existing import
        new_import = """from api.middlewares.enhanced_security_headers import (
    EnhancedSecurityHeadersMiddleware,
    create_security_headers_middleware
)"""
        content = content.replace(import_section, new_import)
    else:
        # Add new import after other middleware imports
        middleware_imports = """from api.middlewares.access_log import AccessLogMiddleware"""
        if middleware_imports in content:
            content = content.replace(
                middleware_imports,
                middleware_imports + """
from api.middlewares.enhanced_security_headers import (
    EnhancedSecurityHeadersMiddleware,
    create_security_headers_middleware
)"""
            )
    
    # Find and replace the middleware setup
    old_middleware = """app.add_middleware(SecurityHeadersMiddleware, enable_hsts=False)  # HSTS disabled for development"""
    
    if old_middleware in content:
        new_middleware = """# Enhanced Security Headers with environment-specific configuration
environment = os.getenv("ENVIRONMENT", "production")
security_headers_middleware = create_security_headers_middleware(
    environment=environment,
    enable_hsts=(environment == "production"),
    excluded_paths=["/docs", "/redoc", "/openapi.json", "/health", "/version"]
)
app.add_middleware(EnhancedSecurityHeadersMiddleware, 
                  environment=environment,
                  excluded_paths=["/docs", "/redoc", "/openapi.json"])"""
        
        content = content.replace(old_middleware, new_middleware)
    
    # Write updated main.py
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print("Enhanced security headers middleware integrated successfully")
    return True

if __name__ == "__main__":
    integrate_security_headers()
