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
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from datetime import datetime
from pathlib import Path

FRONTEND_DIR = "app"
BACKEND_DIR = "backend"
TESTS_DIR = "tests"
LOG_DIR = "logs"

# Configure logging
def setup_logging():
    """Configure logging based on environment variables."""
    # Create logs directory if it doesn't exist
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # Create specific log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_log_file = log_dir / f"setup_{timestamp}.log"
    install_log_file = log_dir / f"install_{timestamp}.log"
    build_log_file = log_dir / f"build_{timestamp}.log"
    general_log_file = log_dir / f"markdown_forge_{timestamp}.log"
    
    # Get log level from environment variables
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    setup_debug = os.environ.get("SETUP_DEBUG", "0") == "1"
    build_debug = os.environ.get("BUILD_DEBUG", "0") == "1"
    install_debug = os.environ.get("INSTALL_DEBUG", "0") == "1"
    
    level = getattr(logging, log_level, logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=general_log_file,
        filemode='w'
    )
    
    # Create console handler for displaying logs in terminal
    console = logging.StreamHandler()
    console.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console)
    
    # Setup dedicated loggers for each component
    setup_logger = logging.getLogger("setup")
    install_logger = logging.getLogger("install")
    build_logger = logging.getLogger("build")
    
    # Create file handlers for specific logs
    setup_handler = logging.FileHandler(setup_log_file)
    install_handler = logging.FileHandler(install_log_file)
    build_handler = logging.FileHandler(build_log_file)
    
    # Set levels based on debug flags
    setup_level = logging.DEBUG if setup_debug else level
    install_level = logging.DEBUG if install_debug else level
    build_level = logging.DEBUG if build_debug else level
    
    setup_handler.setLevel(setup_level)
    install_handler.setLevel(install_level)
    build_handler.setLevel(build_level)
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    setup_handler.setFormatter(formatter)
    install_handler.setFormatter(formatter)
    build_handler.setFormatter(formatter)
    
    # Add handlers to loggers
    setup_logger.addHandler(setup_handler)
    install_logger.addHandler(install_handler)
    build_logger.addHandler(build_handler)
    
    # Set propagation
    setup_logger.propagate = True
    install_logger.propagate = True
    build_logger.propagate = True
    
    # Create the main logger
    logger = logging.getLogger("markdown-forge")
    logger.setLevel(level)
    
    # Log startup information
    logger.info(f"Logging initialized. Log files are stored in: {log_dir.absolute()}")
    logger.info(f"General log file: {general_log_file}")
    logger.info(f"Setup log file: {setup_log_file}")
    logger.info(f"Install log file: {install_log_file}")
    logger.info(f"Build log file: {build_log_file}")
    
    # Log debug configuration
    if any([setup_debug, build_debug, install_debug]):
        logger.debug("Debug logging enabled:")
        logger.debug(f"- SETUP_DEBUG: {setup_debug}")
        logger.debug(f"- BUILD_DEBUG: {build_debug}")
        logger.debug(f"- INSTALL_DEBUG: {install_debug}")
    
    # Return all loggers
    return {
        "main": logger,
        "setup": setup_logger,
        "install": install_logger,
        "build": build_logger
    }

# Initialize loggers
loggers = setup_logging()
logger = loggers["main"]
setup_logger = loggers["setup"]
install_logger = loggers["install"]
build_logger = loggers["build"]

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")
    logger.info(message)

def run_command(command, cwd=None, env=None, log_to=None):
    """Run a command in a subprocess and return the process object."""
    logger.debug(f"Running command: {command}")
    if cwd:
        logger.debug(f"Working directory: {cwd}")
    
    # Use current environment if none is provided
    if env is None:
        env = os.environ.copy()
    
    # Log command to specific logger if requested
    if log_to == "install":
        install_logger.debug(f"Running command: {command}")
    elif log_to == "build":
        build_logger.debug(f"Running command: {command}")
    
    # Start the process with pipes for reading output
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,  # Use binary mode
            bufsize=1,  # Line buffered
            universal_newlines=False,
            cwd=cwd,
            env=env
        )
        return process
    except Exception as e:
        error_msg = f"Error starting process: {str(e)}"
        logger.error(error_msg)
        
        if log_to == "install":
            install_logger.error(error_msg)
        elif log_to == "build":
            build_logger.error(error_msg)
        
        print(f"Error: {str(e)}")
        raise

def stream_output(process, prefix="", log_to=None):
    """Stream output from a process in real-time."""
    output = ""
    try:
        # Check if there's any stdout output
        if process.stdout.peek():
            line = process.stdout.readline().decode('utf-8', errors='replace').strip()
            if line:
                if prefix:
                    formatted_line = f"{prefix} | {line}"
                else:
                    formatted_line = line
                
                print(formatted_line)
                
                if log_to == "install":
                    install_logger.debug(formatted_line)
                elif log_to == "build":
                    build_logger.debug(formatted_line)
                else:
                    logger.debug(formatted_line)
                output += line + "\n"
        
        # Check if there's any stderr output
        if process.stderr.peek():
            line = process.stderr.readline().decode('utf-8', errors='replace').strip()
            if line:
                if prefix:
                    formatted_line = f"{prefix} ERROR | {line}"
                else:
                    formatted_line = f"ERROR | {line}"
                
                print(formatted_line)
                
                if log_to == "install":
                    install_logger.error(formatted_line)
                elif log_to == "build":
                    build_logger.error(formatted_line)
                else:
                    logger.error(formatted_line)
                output += "ERROR: " + line + "\n"
    except (IOError, AttributeError, ValueError) as e:
        logger.error(f"Error streaming output: {str(e)}")
    
    return output

def ensure_directory_exists(directory):
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
        print(f"Created directory: {directory}")

def check_requirements():
    """Check if all requirements are installed."""
    setup_debug = os.environ.get("SETUP_DEBUG", "0") == "1"
    install_debug = os.environ.get("INSTALL_DEBUG", "0") == "1"
    
    print_header("Checking requirements")
    
    # Create logs directory if it doesn't exist (in case we're running this first time)
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # Check Python version
    python_version = sys.version_info
    version_str = f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    print(version_str)
    install_logger.info(version_str)
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        error_msg = "Error: Python 3.8 or higher is required."
        print(error_msg)
        install_logger.error(error_msg)
        return False
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        error_msg = "Error: requirements.txt not found."
        print(error_msg)
        install_logger.error(error_msg)
        return False
    
    # Parse requirements.txt to get required packages
    required_packages = {}
    try:
        with open("requirements.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Handle package==version format
                    if "==" in line:
                        pkg_name, version = line.split("==", 1)
                        required_packages[pkg_name.strip()] = version.strip()
                    else:
                        # Handle package without version
                        required_packages[line.strip()] = None
        install_logger.debug(f"Parsed {len(required_packages)} packages from requirements.txt")
    except Exception as e:
        install_logger.error(f"Error parsing requirements.txt: {str(e)}")
    
    # Check if virtual environment exists
    if not os.path.exists("venv"):
        msg = "Virtual environment not found. Creating..."
        print(msg)
        install_logger.info(msg)
        
        venv_cmd = "python -m venv venv"
        if install_debug:
            venv_cmd += " --verbose"
            
        install_logger.debug(f"Creating virtual environment with command: {venv_cmd}")
        venv_process = run_command(venv_cmd, log_to="install")
        output, error = venv_process.communicate()
        if output:
            install_logger.debug(f"venv output: {output}")
        if error:
            install_logger.error(f"venv error: {error}")
        
        venv_returncode = venv_process.wait()
        install_logger.info(f"venv creation completed with return code: {venv_returncode}")
    
    # Determine pip command based on platform
    if sys.platform.startswith('win'):
        python_cmd = ".\\venv\\Scripts\\python"
        pip_cmd = ".\\venv\\Scripts\\pip"
    else:
        python_cmd = "./venv/bin/python"
        pip_cmd = "./venv/bin/pip"
    
    # Add verbosity flags based on debug settings
    pip_flags = ""
    if install_debug:
        pip_flags = " -v"
        install_logger.debug("Using verbose pip installation")
    
    # Check if pip needs upgrade by getting current version
    try:
        msg = "Checking pip version..."
        print(msg)
        install_logger.info(msg)
        
        pip_version_cmd = f"{pip_cmd} --version"
        pip_version_process = run_command(pip_version_cmd, log_to="install")
        pip_version_output, _ = pip_version_process.communicate()
        
        if pip_version_output:
            # Parse version from output like "pip 20.2.3 from /path/to/pip (python 3.8)"
            pip_version_str = pip_version_output.split()[1] if pip_version_output.split() else "unknown"
            install_logger.info(f"Current pip version: {pip_version_str}")
            print(f"Current pip version: {pip_version_str}")
            
            # Skip pip upgrade to avoid hang
            msg = "Skipping pip upgrade to avoid potential hang issues"
            print(msg)
            install_logger.info(msg)
            upgrade_returncode = 0
        else:
            install_logger.warning("Could not determine pip version, proceeding with upgrade")
            upgrade_returncode = 1
    except Exception as e:
        install_logger.error(f"Error checking pip version: {str(e)}")
        upgrade_returncode = 1
    
    # Get list of already installed packages
    installed_packages = {}
    try:
        msg = "Checking installed packages..."
        print(msg)
        install_logger.info(msg)
        
        list_cmd = f"{pip_cmd} list --format=json"
        list_process = run_command(list_cmd, log_to="install")
        list_output, _ = list_process.communicate()
        
        if list_output:
            try:
                import json
                packages = json.loads(list_output)
                for package in packages:
                    installed_packages[package['name'].lower()] = package['version']
                install_logger.debug(f"Found {len(installed_packages)} installed packages")
            except json.JSONDecodeError:
                install_logger.warning("Could not parse pip list output as JSON")
        else:
            install_logger.warning("No output from pip list command")
    except Exception as e:
        install_logger.error(f"Error checking installed packages: {str(e)}")
    
    # Install core dependencies only if needed
    msg = "Installing core dependencies..."
    print(msg)
    install_logger.info(msg)
    
    # 1. Define core dependencies
    core_deps = [
        "Flask==2.3.3", 
        "fastapi==0.103.1", 
        "uvicorn==0.23.2",
        "python-dotenv==1.0.0",
        "SQLAlchemy==2.0.20",
        "alembic==1.12.0"
    ]
    
    # Extract package names and versions
    core_dep_dict = {}
    for dep in core_deps:
        if "==" in dep:
            name, version = dep.split("==", 1)
            core_dep_dict[name.lower()] = version
        else:
            core_dep_dict[dep.lower()] = None
    
    # Identify missing or outdated core packages
    missing_core_deps = []
    for name, version in core_dep_dict.items():
        if name.lower() not in installed_packages:
            missing_core_deps.append(f"{name}=={version}" if version else name)
        elif version and installed_packages[name.lower()] != version:
            install_logger.debug(f"Package {name} needs upgrade: {installed_packages[name.lower()]} -> {version}")
            missing_core_deps.append(f"{name}=={version}")
    
    # Install missing core dependencies
    if missing_core_deps:
        install_logger.info(f"Installing {len(missing_core_deps)} missing/outdated core packages")
        core_cmd = f"{pip_cmd} install{pip_flags} {' '.join(missing_core_deps)}"
        install_logger.debug(f"Installing core dependencies with command: {core_cmd}")
        
        process = run_command(core_cmd, log_to="install")
        
        # Log output in real-time
        def log_core_install_output():
            stream_output(process, "CORE-DEPS", log_to="install")
            
        core_output_thread = Thread(target=log_core_install_output)
        core_output_thread.daemon = True
        core_output_thread.start()
        
        # Monitor for timeout
        timeout_seconds = 300  # 5 minutes
        start_time = time.time()
        while process.poll() is None:
            if time.time() - start_time > timeout_seconds:
                install_logger.error(f"Core dependencies installation timed out after {timeout_seconds} seconds")
                process.terminate()
                print(f"Core dependencies installation timed out. Check logs for details.")
                break
            time.sleep(1)
        
        core_returncode = process.poll()
        install_logger.info(f"Core dependencies installation completed with return code: {core_returncode}")
        
        if core_returncode != 0:
            error_msg = "Error: Failed to install core dependencies."
            print(error_msg)
            install_logger.error(error_msg)
            return False
    else:
        install_logger.info("All core dependencies are already installed with correct versions")
        print("All core dependencies are already installed")
    
    # 2. Parse and install required packages from requirements.txt
    msg = "Checking requirements.txt packages..."
    print(msg)
    install_logger.info(msg)
    
    # Identify missing or outdated packages from requirements.txt
    missing_req_deps = []
    for name, version in required_packages.items():
        if name.lower() not in installed_packages:
            missing_req_deps.append(f"{name}=={version}" if version else name)
        elif version and installed_packages[name.lower()] != version:
            install_logger.debug(f"Package {name} needs upgrade: {installed_packages[name.lower()]} -> {version}")
            missing_req_deps.append(f"{name}=={version}")
    
    # Install missing requirements
    if missing_req_deps:
        msg = f"Installing {len(missing_req_deps)} missing/outdated packages from requirements.txt"
        print(msg)
        install_logger.info(msg)
        
        # Install in batches to avoid command line length limits
        batch_size = 20
        for i in range(0, len(missing_req_deps), batch_size):
            batch = missing_req_deps[i:i+batch_size]
            base_cmd = f"{pip_cmd} install{pip_flags} {' '.join(batch)}"
            install_logger.debug(f"Installing batch {i//batch_size + 1} with command: {base_cmd}")
            
            process = run_command(base_cmd, log_to="install")
            
            # Log output in real-time
            def log_base_install_output():
                stream_output(process, f"BATCH-{i//batch_size + 1}", log_to="install")
                
            base_output_thread = Thread(target=log_base_install_output)
            base_output_thread.daemon = True
            base_output_thread.start()
            
            # Monitor for timeout
            timeout_seconds = 300  # 5 minutes per batch
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > timeout_seconds:
                    install_logger.error(f"Batch {i//batch_size + 1} installation timed out after {timeout_seconds} seconds")
                    process.terminate()
                    print(f"Batch installation timed out. Check logs for details.")
                    break
                time.sleep(1)
            
            batch_returncode = process.poll()
            install_logger.info(f"Batch {i//batch_size + 1} installation completed with return code: {batch_returncode}")
            
            if batch_returncode != 0:
                warning_msg = f"Warning: Batch {i//batch_size + 1} installation had issues. Continuing with next batch."
                print(warning_msg)
                install_logger.warning(warning_msg)
        
        base_returncode = 0  # Assuming success overall, detailed errors logged per batch
    else:
        install_logger.info("All requirements are already installed with correct versions")
        print("All packages from requirements.txt are already installed")
        base_returncode = 0
    
    # 3. Install platform-specific database drivers if needed
    msg = "Checking platform-specific dependencies..."
    print(msg)
    install_logger.info(msg)
    
    # Check for PostgreSQL driver
    pg_package = "psycopg2-binary" if sys.platform.startswith('win') else "psycopg2"
    pg_version = "2.9.7"
    
    need_pg_install = False
    if pg_package.lower() not in installed_packages:
        need_pg_install = True
    elif installed_packages[pg_package.lower()] != pg_version:
        need_pg_install = True
    
    if need_pg_install:
        if sys.platform.startswith('win'):
            # For Windows: Try to install binary version of PostgreSQL driver
            pg_cmd = f"{pip_cmd} install{pip_flags} {pg_package}=={pg_version}"
            install_logger.debug(f"Installing PostgreSQL driver with command: {pg_cmd}")
            process = run_command(pg_cmd, log_to="install")
            
            # Log output
            def log_pg_install_output():
                stream_output(process, "PG-DEPS", log_to="install")
                
            pg_output_thread = Thread(target=log_pg_install_output)
            pg_output_thread.daemon = True
            pg_output_thread.start()
            
            # Wait for completion with timeout
            timeout_seconds = 180  # 3 minutes
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > timeout_seconds:
                    install_logger.error("PostgreSQL driver installation timed out")
                    process.terminate()
                    break
                time.sleep(1)
            
            pg_returncode = process.poll()
            install_logger.info(f"PostgreSQL driver installation completed with return code: {pg_returncode}")
            
            if pg_returncode != 0:
                warning_msg = "Warning: Could not install PostgreSQL binary driver. Database functionality may be limited to SQLite."
                print(warning_msg)
                install_logger.warning(warning_msg)
        else:
            # For Linux/Mac: Try to install system version with C dependencies
            pg_cmd = f"{pip_cmd} install{pip_flags} {pg_package}=={pg_version}"
            install_logger.debug(f"Installing PostgreSQL driver with command: {pg_cmd}")
            process = run_command(pg_cmd, log_to="install")
            
            # Log output
            def log_pg_install_output():
                stream_output(process, "PG-DEPS", log_to="install")
                
            pg_output_thread = Thread(target=log_pg_install_output)
            pg_output_thread.daemon = True
            pg_output_thread.start()
            
            # Wait for completion with timeout
            timeout_seconds = 180  # 3 minutes
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > timeout_seconds:
                    install_logger.error("PostgreSQL driver installation timed out")
                    process.terminate()
                    break
                time.sleep(1)
            
            pg_returncode = process.poll()
            install_logger.info(f"PostgreSQL driver installation completed with return code: {pg_returncode}")
            
            if pg_returncode != 0:
                warning_msg = "Warning: Could not install PostgreSQL driver. Make sure PostgreSQL development libraries are installed."
                print(warning_msg)
                install_logger.warning(warning_msg)
    else:
        install_logger.info(f"PostgreSQL driver ({pg_package}) is already installed with version {installed_packages.get(pg_package.lower(), 'unknown')}")
        print(f"PostgreSQL driver already installed")
    
    # 4. Install development tools for local development if needed
    is_dev = os.environ.get("MARKDOWN_FORGE_ENV", "development") == "development"
    if is_dev:
        msg = "Checking development dependencies..."
        print(msg)
        install_logger.info(msg)
        
        dev_deps = {
            "pytest": "7.4.0",
            "pytest-asyncio": "0.21.1",
            "pytest-cov": "4.1.0",
            "black": "24.1.0",
            "isort": "5.13.2",
            "flake8": "7.0.0",
            "mypy": "1.8.0"
        }
        
        # Identify missing or outdated dev packages
        missing_dev_deps = []
        for name, version in dev_deps.items():
            if name.lower() not in installed_packages:
                missing_dev_deps.append(f"{name}=={version}")
            elif installed_packages[name.lower()] != version:
                install_logger.debug(f"Package {name} needs upgrade: {installed_packages[name.lower()]} -> {version}")
                missing_dev_deps.append(f"{name}=={version}")
        
        if missing_dev_deps:
            msg = f"Installing {len(missing_dev_deps)} development dependencies..."
            print(msg)
            install_logger.info(msg)
            
            dev_cmd = f"{pip_cmd} install{pip_flags} {' '.join(missing_dev_deps)}"
            install_logger.debug(f"Installing development dependencies with command: {dev_cmd}")
            process = run_command(dev_cmd, log_to="install")
            
            # Log output
            def log_dev_install_output():
                stream_output(process, "DEV-DEPS", log_to="install")
                
            dev_output_thread = Thread(target=log_dev_install_output)
            dev_output_thread.daemon = True
            dev_output_thread.start()
            
            # Wait for completion with timeout
            timeout_seconds = 180  # 3 minutes
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > timeout_seconds:
                    install_logger.error("Development dependencies installation timed out")
                    process.terminate()
                    break
                time.sleep(1)
                
            dev_returncode = process.poll()
            install_logger.info(f"Development dependencies installation completed with return code: {dev_returncode}")
        else:
            install_logger.info("All development dependencies are already installed with correct versions")
            print("All development dependencies are already installed")
    
    # 5. Check for system dependencies
    msg = "Checking system dependencies..."
    print(msg)
    install_logger.info(msg)
    
    # Check for Pandoc
    pandoc_cmd = "pandoc --version"
    install_logger.debug(f"Checking for Pandoc with command: {pandoc_cmd}")
    pandoc_process = run_command(pandoc_cmd, log_to="install")
    
    # Wait a short time for Pandoc check
    pandoc_returncode = None
    try:
        pandoc_returncode = pandoc_process.wait(timeout=10)
        pandoc_output, pandoc_error = pandoc_process.communicate()
        
        if pandoc_output:
            install_logger.debug(f"Pandoc output: {pandoc_output}")
        if pandoc_error:
            install_logger.debug(f"Pandoc error: {pandoc_error}")
            
    except subprocess.TimeoutExpired:
        install_logger.warning("Pandoc check timed out")
        pandoc_process.terminate()
        pandoc_returncode = -1
    
    if pandoc_returncode != 0:
        warning_msg = "Warning: Pandoc is not installed or not in PATH. Some document conversion features may not work."
        install_msg = "Install Pandoc from https://pandoc.org/installing.html"
        print(warning_msg)
        print(install_msg)
        install_logger.warning(warning_msg)
        install_logger.info(install_msg)
    else:
        pandoc_version = ""
        try:
            pandoc_output, _ = pandoc_process.communicate(timeout=1)
            if pandoc_output:
                pandoc_version = pandoc_output.split('\n')[0].strip()
        except Exception as e:
            install_logger.error(f"Error reading Pandoc version: {str(e)}")
            
        version_msg = f"Found Pandoc: {pandoc_version or 'version unknown'}"
        print(version_msg)
        install_logger.info(version_msg)
    
    # Summary of installation status
    print("\nDependency installation summary:")
    install_logger.info("Dependency installation summary:")
    
    if base_returncode != 0:
        warning_msg = "Warning: Some dependencies could not be installed. Limited functionality may be available."
        print(warning_msg)
        install_logger.warning(warning_msg)
    else:
        success_msg = "All dependencies installed successfully."
        print(success_msg)
        install_logger.info(success_msg)
    
    # Final installation summary log
    log_summary = f"Installation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    install_logger.info(log_summary)
    install_logger.info(f"Log file location: {os.path.join(os.getcwd(), LOG_DIR)}")
    
    print(f"\nDetailed installation logs are available in: {os.path.join(os.getcwd(), LOG_DIR)}")
    
    return True

def start_frontend():
    """Start the frontend Flask application."""
    build_debug = os.environ.get("BUILD_DEBUG", "0") == "1"
    
    print_header("Starting Frontend (Flask)")
    
    # Set environment variables
    env = os.environ.copy()
    env["FLASK_APP"] = f"{FRONTEND_DIR}/main.py"
    env["FLASK_ENV"] = "development"
    
    # Enable debug mode if requested
    if build_debug:
        env["FLASK_DEBUG"] = "1"
        logger.debug("Frontend running in debug mode")
    
    # Run Flask application
    if sys.platform.startswith('win'):
        python_cmd = ".\\venv\\Scripts\\python"
    else:
        python_cmd = "./venv/bin/python"
    
    flask_cmd = f"{python_cmd} -m flask run --host=0.0.0.0 --port=5000"
    logger.debug(f"Starting frontend with command: {flask_cmd}")
    
    process = run_command(
        flask_cmd,
        cwd=os.getcwd(),
        env=env
    )
    
    return process

def start_backend():
    """Start the backend FastAPI application."""
    build_debug = os.environ.get("BUILD_DEBUG", "0") == "1"
    
    print_header("Starting Backend (FastAPI)")
    
    # Set environment variables
    env = os.environ.copy()
    env["UVICORN_RELOAD"] = "true"
    
    # Add debug flag if requested
    log_level = "info"
    if build_debug:
        env["DEBUG"] = "1"
        log_level = "debug"
        logger.debug("Backend running in debug mode with log level: debug")
    
    # Run Uvicorn server
    if sys.platform.startswith('win'):
        python_cmd = ".\\venv\\Scripts\\python"
    else:
        python_cmd = "./venv/bin/python"
    
    uvicorn_cmd = f"{python_cmd} -m uvicorn backend.main:app --host=0.0.0.0 --port=8000 --log-level={log_level}"
    logger.debug(f"Starting backend with command: {uvicorn_cmd}")
    
    process = run_command(
        uvicorn_cmd,
        cwd=os.getcwd(),
        env=env
    )
    
    return process

def run_both():
    """Run both frontend and backend applications."""
    print_header("Starting both Frontend and Backend")
    logger.info("Starting both frontend and backend applications")
    
    # Create the required directories
    ensure_directory_exists(os.path.join(FRONTEND_DIR, "data", "converted"))
    ensure_directory_exists(os.path.join(BACKEND_DIR, "data"))
    logger.debug("Ensured required directories exist")
    
    print("Making sure required directories exist...")
    
    # Set environment variables for debugging
    env = os.environ.copy()
    env["FLASK_DEBUG"] = "1"
    env["LOG_LEVEL"] = "DEBUG"
    env["UVICORN_RELOAD"] = "true"
    env["BUILD_DEBUG"] = "1"
    
    print("Starting the backend process...")
    # Start backend first with direct output
    if sys.platform.startswith('win'):
        python_cmd = ".\\venv\\Scripts\\python"
    else:
        python_cmd = "./venv/bin/python"
    
    uvicorn_cmd = f"{python_cmd} -m uvicorn backend.main:app --host=0.0.0.0 --port=8000 --log-level=debug"
    logger.debug(f"Starting backend with command: {uvicorn_cmd}")
    
    backend_process = run_command(
        uvicorn_cmd,
        cwd=os.getcwd(),
        env=env
    )
    
    # Show immediate output from backend
    print("Backend starting (waiting for output)...")
    time.sleep(3)
    stream_output(backend_process, "BACKEND")
    
    # Give the backend a moment to start
    time.sleep(2)
    
    print("Starting the frontend process...")
    # Then start frontend with direct output
    flask_cmd = f"{python_cmd} -m flask run --host=0.0.0.0 --port=5000"
    logger.debug(f"Starting frontend with command: {flask_cmd}")
    
    frontend_process = run_command(
        flask_cmd,
        cwd=os.getcwd(),
        env=env
    )
    
    # Show immediate output from frontend
    print("Frontend starting (waiting for output)...")
    time.sleep(3)
    stream_output(frontend_process, "FRONTEND")
    
    # Wait a moment for both to be running
    time.sleep(2)
    
    # Open browser tabs
    try:
        logger.debug("Opening browser for frontend")
        webbrowser.open("http://localhost:5000")
        
        logger.debug("Opening browser for backend docs")
        webbrowser.open("http://localhost:8000/docs")
    except Exception as e:
        logger.error(f"Failed to open browser: {str(e)}")
        pass
    
    # Wait for processes to complete
    try:
        logger.debug("Both processes started successfully")
        
        # Stream output from both processes
        while True:
            print("Checking process output...")
            backend_output = stream_output(backend_process, "BACKEND")
            frontend_output = stream_output(frontend_process, "FRONTEND")
            
            # Check if either process has terminated
            if backend_process.poll() is not None:
                logger.warning(f"Backend process terminated with code {backend_process.poll()}")
                print(f"Backend process terminated with code {backend_process.poll()}")
                frontend_process.terminate()
                break
                
            if frontend_process.poll() is not None:
                logger.warning(f"Frontend process terminated with code {frontend_process.poll()}")
                print(f"Frontend process terminated with code {frontend_process.poll()}")
                backend_process.terminate()
                break
                
            # Sleep to prevent CPU usage
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
        print("\nShutting down...")
        backend_process.terminate()
        frontend_process.terminate()
        return

def run_tests(test_type="all"):
    """Run tests for the application."""
    print_header(f"Running {test_type} tests")
    logger.info(f"Running {test_type} tests")
    
    # Determine the test command based on the type
    if sys.platform.startswith('win'):
        python_cmd = ".\\venv\\Scripts\\python"
        pytest_cmd = ".\\venv\\Scripts\\pytest"
    else:
        python_cmd = "./venv/bin/python"
        pytest_cmd = "./venv/bin/pytest"
    
    # Set up test command based on test type
    if test_type == "frontend":
        cmd = f"{pytest_cmd} {FRONTEND_DIR}/tests"
        logger.debug(f"Running frontend tests with command: {cmd}")
    elif test_type == "backend":
        cmd = f"{pytest_cmd} {BACKEND_DIR}/tests"
        logger.debug(f"Running backend tests with command: {cmd}")
    elif test_type == "unit":
        cmd = f"{pytest_cmd} {TESTS_DIR}/unit"
        logger.debug(f"Running unit tests with command: {cmd}")
    elif test_type == "integration":
        cmd = f"{pytest_cmd} {TESTS_DIR}/integration"
        logger.debug(f"Running integration tests with command: {cmd}")
    elif test_type == "performance":
        cmd = f"{pytest_cmd} {TESTS_DIR}/performance"
        logger.debug(f"Running performance tests with command: {cmd}")
    elif test_type == "security":
        cmd = f"{pytest_cmd} {TESTS_DIR}/security"
        logger.debug(f"Running security tests with command: {cmd}")
    else:  # all tests
        cmd = f"{pytest_cmd}"
        logger.debug(f"Running all tests with command: {cmd}")
    
    # Add coverage report if running all tests
    if test_type == "all" or test_type == "coverage":
        cmd += " --cov=app --cov=backend --cov-report=term-missing"
        logger.debug("Including coverage reporting")
    
    # Run the tests
    process = run_command(cmd)
    process.wait()
    
    # Check the result
    if process.returncode == 0:
        success_msg = f"{test_type.capitalize()} tests passed successfully!"
        print(success_msg)
        logger.info(success_msg)
    else:
        error_msg = f"{test_type.capitalize()} tests failed with exit code {process.returncode}"
        print(error_msg)
        logger.error(error_msg)
    
    return process.returncode

def setup_dev_environment():
    """Set up the development environment."""
    setup_debug = os.environ.get("SETUP_DEBUG", "0") == "1"
    
    print_header("Setting up development environment")
    
    # Check requirements first
    if not check_requirements():
        error_msg = "Failed to install required dependencies."
        print(error_msg)
        logger.error(error_msg)
        return False
    
    # Ensure directories exist
    logger.debug("Creating required directories")
    ensure_directory_exists(f"{FRONTEND_DIR}/data/uploads")
    ensure_directory_exists(f"{FRONTEND_DIR}/data/converted")
    ensure_directory_exists(f"{FRONTEND_DIR}/logs")
    ensure_directory_exists(f"{BACKEND_DIR}/data")
    ensure_directory_exists(f"{BACKEND_DIR}/logs")
    
    # Create .env files if they don't exist
    if not os.path.exists(f"{FRONTEND_DIR}/.env"):
        logger.debug("Creating frontend .env file")
        with open(f"{FRONTEND_DIR}/.env", "w") as f:
            f.write("FLASK_APP=main.py\n")
            f.write("FLASK_ENV=development\n")
            f.write("FLASK_DEBUG=1\n")
            f.write("API_BASE_URL=http://localhost:8000/api/v1\n")
            f.write("LOG_LEVEL=DEBUG\n")
    
    if not os.path.exists(f"{BACKEND_DIR}/.env"):
        logger.debug("Creating backend .env file")
        with open(f"{BACKEND_DIR}/.env", "w") as f:
            f.write("DATABASE_URL=sqlite:///./data/markdown_forge.db\n")
            f.write("LOG_LEVEL=DEBUG\n")
            f.write("UPLOAD_DIR=./data/uploads\n")
            f.write("OUTPUT_DIR=./data/converted\n")
    
    success_msg = "Development environment set up successfully."
    print(success_msg)
    logger.info(success_msg)
    
    if setup_debug:
        logger.debug("Additional debug setup completed")
    
    return True

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Markdown Forge run script')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the application')
    run_parser.add_argument('component', nargs='?', choices=['frontend', 'backend', 'all'], default='all', 
                         help='Component to run (frontend, backend, or all)')
    run_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('test_type', nargs='?', choices=['all', 'frontend', 'backend', 'unit', 'integration', 'performance', 'security'], 
                          default='all', help='Test type to run')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up development environment')
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging()
    
    # Handle debug mode
    if getattr(args, 'debug', False):
        os.environ['LOG_LEVEL'] = 'DEBUG'
        os.environ['FLASK_DEBUG'] = '1'
        os.environ['SETUP_DEBUG'] = '1'
        os.environ['BUILD_DEBUG'] = '1'
        os.environ['INSTALL_DEBUG'] = '1'
        logger.info("Debug mode enabled")
        print("Debug mode enabled")
    
    # Run the appropriate command
    try:
        if args.command == 'run':
            logger.info(f"Run command: {args.component}")
            
            if args.component == 'frontend':
                process = start_frontend()
                process.wait()
            elif args.component == 'backend':
                process = start_backend()
                process.wait()
            else:  # all
                run_both()
                
        elif args.command == 'test':
            run_tests(args.test_type)
            
        elif args.command == 'setup':
            logger.info("Setup command")
            setup_dev_environment()
            
        else:
            print("Please specify a command. Use --help for more information.")
            return 1
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        print(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
        
    return 0

if __name__ == "__main__":
    try:
        logger.debug("Starting run.py script")
        main()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, exiting")
        print("\nExiting...")
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1) 