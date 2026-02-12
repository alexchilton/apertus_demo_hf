#!/usr/bin/env python3
"""
Quick verification script for Swiss RAG demo dependencies.
Run this before testing the full application.
"""

import sys

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("⚠️  Warning: Python 3.11+ recommended")
    return True

def check_imports():
    """Check all required imports."""
    required = {
        'gradio': 'gradio',
        'huggingface_hub': 'huggingface_hub',
        'numpy': 'numpy',
        'scipy': 'scipy',
        'fitz': 'pymupdf',
        'requests': 'requests'
    }
    
    all_ok = True
    for module, package in required.items():
        try:
            if module == 'fitz':
                import fitz
                version = fitz.version[0]
            else:
                mod = __import__(module)
                version = getattr(mod, '__version__', 'unknown')
            print(f"✓ {package}: {version}")
        except ImportError:
            print(f"✗ {package}: NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_env_var():
    """Check for HF_TOKEN environment variable."""
    import os
    token = os.environ.get('HF_TOKEN')
    if token:
        print(f"✓ HF_TOKEN: Set (length: {len(token)})")
        return True
    else:
        print("✗ HF_TOKEN: NOT SET")
        print("  Set it with: export HF_TOKEN=your_token_here")
        return False

def check_internet():
    """Check internet connectivity."""
    import requests
    try:
        response = requests.get('https://huggingface.co', timeout=5)
        print(f"✓ Internet: Connected (status {response.status_code})")
        return True
    except:
        print("✗ Internet: Connection failed")
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("Swiss RAG Demo - Dependency Verification")
    print("=" * 60)
    print()
    
    checks = {
        "Python Version": check_python_version(),
        "Package Imports": check_imports(),
        "Environment Variable": check_env_var(),
        "Internet Connection": check_internet()
    }
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = all(checks.values())
    
    for name, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    
    if all_passed:
        print("🎉 All checks passed! Ready to run the Swiss RAG demo.")
        print()
        print("Next steps:")
        print("  1. Ensure HF_TOKEN is set: export HF_TOKEN=your_token")
        print("  2. Run the app: python app.py")
        print("  3. Open browser at: http://localhost:7860")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        if not checks["Package Imports"]:
            print("To install missing packages:")
            print("  pip install -r requirements-swiss-rag.txt")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
