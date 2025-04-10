#!/usr/bin/env python3
"""
Markdown Forge run script.
Provides commands for starting the application, running tests, and other common tasks.
"""

import os
import sys
import argparse
import subprocess
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor

FRONTEND_DIR = "app"
BACKEND_DIR = "backend"
TESTS_DIR = "tests"

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")

def run_command(command, cwd=None, env=None):
    """Run a shell command and return the process."""
    return subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        env=env or os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

def stream_output(process, prefix=""):
    """Stream the output of a process to the console."""
    for line in iter(process.stdout.readline, ""):
        if line.strip():
            print(f"{prefix} | {line.rstrip()}")
    
    # Make sure we catch all stderr output
    for line in iter(process.stderr.readline, ""):
        if line.strip():
            print(f"{prefix} | ERROR: {line.rstrip()}")

def ensure_directory_exists(directory):
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def check_requirements():
    """Check if all requirements are installed."""
    print_header("Checking requirements")
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("Error: Python 3.8 or higher is required.")
        return False
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found.")
        return False
    
    # Check if virtual environment exists
    if not os.path.exists("venv"):
        print("Virtual environment not found. Creating...")
        run_command("python -m venv venv").wait()
    
    # Install requirements
    print("Installing requirements...")
    if sys.platform.startswith('win'):
        pip_cmd = ".\\venv\\Scripts\\pip"
    else:
        pip_cmd = "./venv/bin/pip"
    
    process = run_command(f"{pip_cmd} install -r requirements.txt")
    process.wait()
    
    if process.returncode != 0:
        print("Error: Failed to install requirements.")
        return False
    
    print("All requirements installed successfully.")
    return True

def start_frontend():
    """Start the frontend Flask application."""
    print_header("Starting Frontend (Flask)")
    
    # Set environment variables
    env = os.environ.copy()
    env["FLASK_APP"] = f"{FRONTEND_DIR}/main.py"
    env["FLASK_ENV"] = "development"
    
    # Run Flask application
    if sys.platform.startswith('win'):
        python_cmd = ".\\venv\\Scripts\\python"
    else:
        python_cmd = "./venv/bin/python"
    
    process = run_command(
        f"{python_cmd} -m flask run --host=0.0.0.0 --port=5000",
        cwd=os.getcwd(),
        env=env
    )
    
    print(f"Frontend started on http://localhost:5000")
    return process

def start_backend():
    """Start the backend FastAPI application."""
    print_header("Starting Backend (FastAPI)")
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    # Run FastAPI application
    if sys.platform.startswith('win'):
        python_cmd = ".\\venv\\Scripts\\python"
        uvicorn_cmd = ".\\venv\\Scripts\\uvicorn"
    else:
        python_cmd = "./venv/bin/python"
        uvicorn_cmd = "./venv/bin/uvicorn"
    
    process = run_command(
        f"{uvicorn_cmd} backend.main:app --host 0.0.0.0 --port 8000 --reload",
        cwd=os.getcwd(),
        env=env
    )
    
    print(f"Backend started on http://localhost:8000")
    return process

def run_both():
    """Run both frontend and backend applications concurrently."""
    print_header("Starting Markdown Forge (Frontend + Backend)")
    
    if not check_requirements():
        return
    
    # Start both services
    backend_process = start_backend()
    frontend_process = start_frontend()
    
    # Wait a moment for services to start
    time.sleep(3)
    
    # Open browser
    webbrowser.open("http://localhost:5000")
    
    # Stream output from both processes
    with ThreadPoolExecutor(max_workers=2) as executor:
        backend_future = executor.submit(stream_output, backend_process, "Backend")
        frontend_future = executor.submit(stream_output, frontend_process, "Frontend")
        
        try:
            # Wait for futures to complete (they won't unless there's an error)
            backend_future.result()
            frontend_future.result()
        except KeyboardInterrupt:
            print_header("Shutting down...")
            backend_process.terminate()
            frontend_process.terminate()
            sys.exit(0)

def run_tests(test_type="all"):
    """Run tests for the application."""
    print_header(f"Running {test_type} tests")
    
    if not check_requirements():
        return
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    # Determine test command
    if sys.platform.startswith('win'):
        python_cmd = ".\\venv\\Scripts\\python"
        pytest_cmd = ".\\venv\\Scripts\\pytest"
    else:
        python_cmd = "./venv/bin/python"
        pytest_cmd = "./venv/bin/pytest"
    
    test_command = f"{pytest_cmd} -v"
    
    if test_type == "frontend":
        test_command += f" {FRONTEND_DIR}/tests"
    elif test_type == "backend":
        test_command += f" {BACKEND_DIR}/tests"
    elif test_type == "unit":
        test_command += f" {TESTS_DIR}/unit"
    elif test_type == "integration":
        test_command += f" {TESTS_DIR}/integration"
    elif test_type == "all":
        # Run all tests
        pass
    else:
        print(f"Unknown test type: {test_type}")
        return
    
    # Run tests
    process = run_command(test_command, env=env)
    process.wait()
    
    if process.returncode == 0:
        print(f"\n✅ {test_type.capitalize()} tests passed successfully.")
    else:
        print(f"\n❌ {test_type.capitalize()} tests failed.")

def setup_dev_environment():
    """Set up development environment."""
    print_header("Setting up development environment")
    
    # Create virtual environment
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        run_command("python -m venv venv").wait()
    
    # Install requirements
    print("Installing requirements...")
    if sys.platform.startswith('win'):
        pip_cmd = ".\\venv\\Scripts\\pip"
    else:
        pip_cmd = "./venv/bin/pip"
    
    process = run_command(f"{pip_cmd} install -r requirements.txt")
    process.wait()
    
    # Create necessary directories
    ensure_directory_exists(f"{FRONTEND_DIR}/static/uploads")
    ensure_directory_exists(f"{FRONTEND_DIR}/static/converted")
    ensure_directory_exists(f"{FRONTEND_DIR}/templates")
    ensure_directory_exists(f"{FRONTEND_DIR}/logs")
    ensure_directory_exists(f"{BACKEND_DIR}/logs")
    ensure_directory_exists(f"{BACKEND_DIR}/data")
    
    print("Development environment set up successfully.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Markdown Forge run script")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the application")
    run_parser.add_argument("service", choices=["frontend", "backend", "all"], default="all", nargs="?", help="Service to run")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("type", choices=["frontend", "backend", "unit", "integration", "all"], default="all", nargs="?", help="Test type to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up development environment")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "run":
        if args.service == "frontend":
            frontend_process = start_frontend()
            stream_output(frontend_process, "Frontend")
        elif args.service == "backend":
            backend_process = start_backend()
            stream_output(backend_process, "Backend")
        else:
            run_both()
    elif args.command == "test":
        run_tests(args.type)
    elif args.command == "setup":
        setup_dev_environment()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_header("Shutting down...")
        sys.exit(0) 