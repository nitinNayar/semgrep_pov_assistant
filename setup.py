#!/usr/bin/env python3
"""
Setup script for semgrep_pov_assistant.

This script helps users set up the application by checking dependencies,
creating necessary directories, and guiding through configuration.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("🚀 SEMGREP POV ASSISTANT - SETUP")
    print("=" * 60)
    print("A Python application that analyzes call transcripts using")
    print("Claude AI and generates comprehensive summary documents.")
    print("=" * 60)

def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported.")
        print("   Please use Python 3.8 or higher.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def install_dependencies() -> bool:
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories() -> bool:
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "data",
        "data/transcripts",
        "data/output",
        "logs",
        "config"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {directory}")
        else:
            print(f"   ℹ️  Exists: {directory}")
    
    return True

def setup_environment_file() -> bool:
    """Set up environment configuration file."""
    print("\n🔧 Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("   ℹ️  .env file already exists")
        return True
    
    if not env_example.exists():
        print("   ❌ env.example not found")
        return False
    
    try:
        # Copy env.example to .env
        with open(env_example, 'r') as src:
            content = src.read()
        
        with open(env_file, 'w') as dst:
            dst.write(content)
        
        print("   ✅ Created .env file from template")
        print("   📝 Please edit .env file with your API keys:")
        print("   ANTHROPIC_API_KEY=your_actual_api_key_here")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create .env file: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("1. 🔑 Get your Anthropic API key:")
    print("   - Go to https://console.anthropic.com/")
    print("   - Create an account and get your API key")
    print("   - Add your API key to the .env file")
    print("   ANTHROPIC_API_KEY=your_actual_api_key_here")
    
    print("\n2. 📄 Add your transcript files:")
    print("   - Place your call transcript files in data/transcripts/")
    print("   - Supported formats: .txt, .docx, .pdf")
    
    print("\n3. 🚀 Run the application:")
    print("   python main.py")
    
    print("\n4. 🧪 Test the setup:")
    print("   python test_setup.py")
    
    print("\n📚 For more information, see README.md")

def main():
    """Main setup function."""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return False
    
    # Create directories
    if not create_directories():
        print("❌ Setup failed at directory creation")
        return False
    
    # Setup environment file
    if not setup_environment_file():
        print("❌ Setup failed at environment configuration")
        return False
    
    # Print next steps
    print_next_steps()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 