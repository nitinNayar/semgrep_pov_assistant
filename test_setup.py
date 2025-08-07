#!/usr/bin/env python3
"""
Test setup script for semgrep_pov_assistant.

This script tests the setup and configuration of the application,
including environment variables, dependencies, and API connections.
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_python_version() -> Dict[str, Any]:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return {
            'success': False,
            'error': f"Python {version.major}.{version.minor} is not supported. Please use Python 3.8 or higher."
        }
    
    return {
        'success': True,
        'version': f"{version.major}.{version.minor}.{version.micro}"
    }

def check_dependencies() -> Dict[str, Any]:
    """Check if all required dependencies are installed."""
    required_packages = [
        'anthropic',
        'python-dotenv',
        'pandas',
        'numpy',
        'python-dateutil',
        'pathlib2',
        'chardet',
        'pyyaml',
        'colorama'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            installed_packages.append(package)
        except ImportError:
            missing_packages.append(package)
    
    return {
        'success': len(missing_packages) == 0,
        'installed': installed_packages,
        'missing': missing_packages
    }

def check_environment_variables() -> Dict[str, Any]:
    """Check if required environment variables are set."""
    # Load .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    required_vars = ['ANTHROPIC_API_KEY']
    missing_vars = []
    present_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            present_vars.append(var)
        else:
            missing_vars.append(var)
    
    return {
        'success': len(missing_vars) == 0,
        'present': present_vars,
        'missing': missing_vars
    }

def check_configuration_files() -> Dict[str, Any]:
    """Check if configuration files exist and are valid."""
    config_files = [
        'config/config.yaml',
        'config/prompts.yaml'
    ]
    
    existing_files = []
    missing_files = []
    invalid_files = []
    
    for file_path in config_files:
        path = Path(file_path)
        if path.exists():
            existing_files.append(file_path)
            # Try to parse YAML files
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                except yaml.YAMLError as e:
                    invalid_files.append(f"{file_path}: {str(e)}")
        else:
            missing_files.append(file_path)
    
    return {
        'success': len(missing_files) == 0 and len(invalid_files) == 0,
        'existing': existing_files,
        'missing': missing_files,
        'invalid': invalid_files
    }

def check_directory_structure() -> Dict[str, Any]:
    """Check if required directories exist."""
    required_dirs = [
        'data',
        'data/transcripts',
        'data/output',
        'logs',
        'src',
        'config'
    ]
    
    existing_dirs = []
    missing_dirs = []
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            existing_dirs.append(dir_path)
        else:
            missing_dirs.append(dir_path)
    
    return {
        'success': len(missing_dirs) == 0,
        'existing': existing_dirs,
        'missing': missing_dirs
    }

def test_anthropic_connection() -> Dict[str, Any]:
    """Test connection to Anthropic API."""
    try:
        import anthropic
        from anthropic import Anthropic
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return {
                'success': False,
                'error': 'ANTHROPIC_API_KEY not set'
            }
        
        # Load configuration to get the model
        config_file = Path('config/config.yaml')
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            model = config.get('claude', {}).get('model', 'claude-sonnet-4-20250514')
        else:
            # Fallback to default model if config file doesn't exist
            model = 'claude-sonnet-4-20250514'
        
        client = Anthropic(api_key=api_key)
        
        # Test with a simple message using the configured model
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        return {
            'success': True,
            'model': response.model,
            'response_length': len(response.content[0].text)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Run all tests and display results."""
    print("🔍 Testing Semgrep POV Assistant Setup")
    print("=" * 50)
    
    # Test Python version
    print("\n1. 🐍 Python Version Check")
    python_check = check_python_version()
    if python_check['success']:
        print(f"   ✅ Python {python_check['version']} - Compatible")
    else:
        print(f"   ❌ {python_check['error']}")
    
    # Test dependencies
    print("\n2. 📦 Dependencies Check")
    deps_check = check_dependencies()
    if deps_check['success']:
        print(f"   ✅ All {len(deps_check['installed'])} required packages installed")
    else:
        print(f"   ❌ Missing packages: {', '.join(deps_check['missing'])}")
        print("   💡 Run: pip install -r requirements.txt")
    
    # Test environment variables
    print("\n3. 🔑 Environment Variables Check")
    env_check = check_environment_variables()
    if env_check['success']:
        print(f"   ✅ All {len(env_check['present'])} required environment variables set")
    else:
        print(f"   ❌ Missing variables: {', '.join(env_check['missing'])}")
        print("   💡 Create a .env file with the required variables")
    
    # Test configuration files
    print("\n4. ⚙️ Configuration Files Check")
    config_check = check_configuration_files()
    if config_check['success']:
        print(f"   ✅ All {len(config_check['existing'])} configuration files present and valid")
    else:
        if config_check['missing']:
            print(f"   ❌ Missing files: {', '.join(config_check['missing'])}")
        if config_check['invalid']:
            print(f"   ❌ Invalid files: {', '.join(config_check['invalid'])}")
    
    # Test directory structure
    print("\n5. 📁 Directory Structure Check")
    dir_check = check_directory_structure()
    if dir_check['success']:
        print(f"   ✅ All {len(dir_check['existing'])} required directories exist")
    else:
        print(f"   ❌ Missing directories: {', '.join(dir_check['missing'])}")
        print("   💡 Create the missing directories")
    
    # Test API connection
    print("\n6. 🌐 Anthropic API Connection Test")
    api_check = test_anthropic_connection()
    if api_check['success']:
        print(f"   ✅ API connection successful (model: {api_check['model']})")
    else:
        print(f"   ❌ API connection failed: {api_check['error']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)
    
    all_tests = [
        ("Python Version", python_check),
        ("Dependencies", deps_check),
        ("Environment Variables", env_check),
        ("Configuration Files", config_check),
        ("Directory Structure", dir_check),
        ("API Connection", api_check)
    ]
    
    passed = sum(1 for _, test in all_tests if test['success'])
    total = len(all_tests)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\n📝 Next steps:")
        print("1. Add your transcript files to data/transcripts/")
        print("2. Run: python main.py")
    else:
        print("\n⚠️ Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Add your Anthropic API key to the .env file")
        print("3. Create missing directories: mkdir -p data/transcripts data/output logs")

if __name__ == "__main__":
    main() 