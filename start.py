#!/usr/bin/env python3
"""
Startup script for the Multi-Agent Software Development System.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        import yaml
        print("✅ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_config():
    """Check if configuration file exists and environment is valid."""
    print("🔍 Checking configuration...")
    
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ Configuration file 'config.yaml' not found")
        return False
    
    print("✅ Configuration file found")
    
    # Check environment variables
    print("🔍 Checking environment variables...")
    try:
        from shared.config import validate_environment
        validation = validate_environment()
        
        missing_vars = [var for var, present in validation.items() if not present]
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("   Copy env.example to .env and fill in your values")
            print("   Some features may not work without these variables")
        else:
            print("✅ All required environment variables are set")
        
        return True
    except Exception as e:
        print(f"⚠️  Could not validate environment: {e}")
        return True  # Don't fail startup for env validation issues

def create_directories():
    """Create necessary directories."""
    print("🔍 Creating directories...")
    
    directories = ["database", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created")

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting Multi-Agent Software Development System...")
    
    try:
        # Import and run the main application
        from main import app
        import uvicorn
        from shared.config import get_config
        
        config = get_config()
        
        print(f"   Host: {config.api.host}")
        print(f"   Port: {config.api.port}")
        print(f"   Debug: {config.app.debug}")
        print(f"   Log level: {config.logging.level}")
        
        uvicorn.run(
            "main:app",
            host=config.api.host,
            port=config.api.port,
            reload=config.app.debug,
            log_level=config.logging.level.lower()
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def wait_for_server(url="http://localhost:8000", timeout=30):
    """Wait for the server to be ready."""
    print(f"⏳ Waiting for server to be ready at {url}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
    
    print("❌ Server did not become ready in time")
    return False

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_agent.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def main():
    """Main startup function."""
    print("=" * 60)
    print("🤖 Multi-Agent Software Development System")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check if we should run tests
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("\n🧪 Test mode enabled")
        start_server()
        return
    
    # Start the server
    print("\n" + "=" * 60)
    start_server()

if __name__ == "__main__":
    main() 