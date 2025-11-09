"""
Test script to verify installation and dependencies
"""

import sys
import importlib

def check_python_version():
    """Check if Python version is 3.9 or higher"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.9+")
        return False

def check_module(module_name, package_name=None):
    """Check if a module is installed"""
    if package_name is None:
        package_name = module_name

    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, '__version__', 'unknown')
        print(f"✓ {package_name} (version {version}) - OK")
        return True
    except ImportError:
        print(f"✗ {package_name} - NOT INSTALLED")
        return False

def check_directories():
    """Check if required directories exist"""
    import os

    print("\nChecking directories...")
    directories = ['uploads', 'results', 'backend', 'frontend']
    all_ok = True

    for directory in directories:
        if os.path.exists(directory):
            print(f"✓ {directory}/ - OK")
        else:
            print(f"✗ {directory}/ - MISSING")
            all_ok = False

    return all_ok

def check_files():
    """Check if required files exist"""
    import os

    print("\nChecking required files...")
    files = [
        'backend/app.py',
        'frontend/index.html',
        'frontend/style.css',
        'frontend/app.js',
        'requirements.txt'
    ]
    all_ok = True

    for file in files:
        if os.path.exists(file):
            print(f"✓ {file} - OK")
        else:
            print(f"✗ {file} - MISSING")
            all_ok = False

    return all_ok

def main():
    """Run all checks"""
    print("=" * 60)
    print("Virtual Try-On Installation Test")
    print("=" * 60)
    print()

    # Check Python version
    python_ok = check_python_version()
    print()

    # Check modules
    print("Checking Python packages...")
    modules = [
        ('flask', 'Flask'),
        ('flask_cors', 'Flask-CORS'),
        ('PIL', 'Pillow'),
        ('requests', 'requests'),
        ('werkzeug', 'Werkzeug'),
    ]

    modules_ok = all(check_module(mod, pkg) for mod, pkg in modules)

    # Optional modules
    print("\nChecking optional packages...")
    try:
        check_module('gradio_client', 'gradio-client')
    except:
        print("⚠ gradio-client - OPTIONAL (for better IDM-VTON integration)")

    # Check directories
    dirs_ok = check_directories()

    # Check files
    files_ok = check_files()

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if python_ok and modules_ok and dirs_ok and files_ok:
        print("✓ All checks passed! You can start the application.")
        print()
        print("Next steps:")
        print("1. Run: python backend/app.py")
        print("2. Open frontend/index.html in your browser")
        print("   OR run: python -m http.server 8080 (in frontend folder)")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print()
        print("To install missing packages, run:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print()
    input("Press Enter to exit...")
    sys.exit(exit_code)
