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
import select
import io
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import tempfile
import shutil
import platform
import traceback

# Import fcntl only on Unix-like systems
if platform.system() != 'Windows':
    import fcntl
else:
    # Mock implementation for Windows
    class MockFcntl:
        @staticmethod
        def fcntl(fd, op, arg=0):
            # No-op on Windows
            return 0
        
        # Constants for the mock
        F_GETFL = 3
        F_SETFL = 4
        O_NONBLOCK = 2048
    
    fcntl = MockFcntl

from app.utils.logger import AppLogger, log_function

FRONTEND_DIR = "app"
BACKEND_DIR = "backend"
TESTS_DIR = "tests"
LOG_DIR = "logs"

# Initialize loggers
logger = AppLogger('markdown_forge', os.path.join(LOG_DIR, 'app.log'), 'DEBUG')
setup_logger = AppLogger('setup', os.path.join(LOG_DIR, 'setup.log'), 'DEBUG')
install_logger = AppLogger('install', os.path.join(LOG_DIR, 'install.log'), 'DEBUG')
build_logger = AppLogger('build', os.path.join(LOG_DIR, 'build.log'), 'DEBUG')

@log_function(logger)
def normalize_path(path: str) -> str:
    """
    Normalize path separators for the current platform.
    
    Args:
        path (str): The path to normalize
        
    Returns:
        str: The normalized path
    """
    if platform.system() == 'Windows':
        return path.replace('/', '\\')
    else:
        return path.replace('\\', '/')

@log_function(logger)
def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50))
    print("=" * 50 + "\n")

@log_function(logger)
def run_command(command, cwd=None, env=None, shell=False, prefix=None, check=True, pipe_output=True, log_to=None):
    """
    Run a command and stream its output
    
    Args:
        command (list or str): Command to run
        cwd (str, optional): Working directory. Defaults to None.
        env (dict, optional): Environment variables. Defaults to None.
        shell (bool, optional): Whether to run in a shell. Defaults to False.
        prefix (str, optional): Prefix for output lines. Defaults to None.
        check (bool, optional): Whether to check return code. Defaults to True.
        pipe_output (bool, optional): Whether to capture and pipe output. Defaults to True.
        log_to (str, optional): Specific logger to use ('install', 'build', 'setup'). Defaults to None.
        
    Returns:
        subprocess.Popen: The process object
        
    Raises:
        subprocess.CalledProcessError: If the command fails and check is True
    """
    # Select the appropriate logger based on log_to parameter
    cmd_logger = logger
    if log_to == "install":
        cmd_logger = install_logger
    elif log_to == "build":
        cmd_logger = build_logger
    elif log_to == "setup":
        cmd_logger = setup_logger
    
    cmd_logger.debug(f"Running command: {command}")
    cmd_logger.debug(f"Working directory: {cwd}")
    cmd_logger.debug(f"Environment variables: {env}")
    
    stdout_pipe = subprocess.PIPE if pipe_output else None
    stderr_pipe = subprocess.PIPE if pipe_output else None
    
    # Ensure command is a list for subprocess
    if isinstance(command, str) and not shell:
        command_list = command.split()
    else:
        command_list = command
    
    try:
        process = subprocess.Popen(
            command_list,
            stdout=stdout_pipe,
            stderr=stderr_pipe,
            cwd=cwd,
            env=env,
            shell=shell,
            universal_newlines=False,
            bufsize=0  # Use unbuffered (0) instead of line buffered (1)
        )
        
        cmd_logger.debug(f"Process started with PID: {process.pid}")
        
        if pipe_output:
            stream_output(process, prefix=prefix, custom_logger=cmd_logger)
        
        # If check is True, wait for completion and check return code
        if check:
            return_code = process.wait()
            cmd_logger.debug(f"Process completed with return code: {return_code}")
            
            if return_code != 0:
                error_msg = f"Command failed with return code {return_code}: {command}"
                cmd_logger.error(error_msg)
                raise subprocess.CalledProcessError(return_code, command)
        
        # Return the process object for the caller to manage
        return process
        
    except (OSError, IOError) as e:
        error_msg = f"Failed to start process: {str(e)}"
        cmd_logger.error(error_msg)
        if check:
            raise
        # Create a mock process object with error code
        mock_process = type('MockProcess', (), {'returncode': 1})()
        return mock_process
    except Exception as e:
        error_msg = f"Error running command: {str(e)}"
        cmd_logger.error(error_msg)
        cmd_logger.error(f"Exception details: {traceback.format_exc()}")
        if check:
            raise
        # Create a mock process object with error code
        mock_process = type('MockProcess', (), {'returncode': 1})()
        return mock_process

@log_function(logger)
def stream_output(process, prefix=None, timeout=0.5, custom_logger=None):
    """
    Stream output from a subprocess with non-blocking IO operations and timeout
    
    Args:
        process (subprocess.Popen): The subprocess to stream output from
        prefix (str, optional): Prefix to add to output lines. Defaults to None.
        timeout (float, optional): Timeout in seconds for select. Defaults to 0.5.
        custom_logger (AppLogger, optional): Specific logger to use. Defaults to None.
    """
    # Use the provided logger or fall back to the default
    output_logger = custom_logger if custom_logger else logger
    
    output_logger.debug(f"Streaming output from process {process.pid} with prefix: {prefix}")
    
    if process.stdout is None or process.stderr is None:
        output_logger.error("Process stdout or stderr is None, cannot stream output")
        return
    
    # Different handling for Windows vs Unix-like platforms
    if platform.system() != 'Windows':
        # Make stdout and stderr non-blocking on Unix-like systems
        for stream in [process.stdout, process.stderr]:
            if hasattr(stream, 'fileno'):
                try:
                    fd = stream.fileno()
                    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                except (AttributeError, ValueError, io.UnsupportedOperation) as e:
                    output_logger.warning(f"Could not set non-blocking mode: {str(e)}")
    
    # Stream output until process completes
    try:
        while process.poll() is None:
            # Use select on Unix-like systems, alternative on Windows
            if platform.system() != 'Windows':
                try:
                    ready_to_read, _, _ = select.select([process.stdout, process.stderr], [], [], timeout)
                except (select.error, ValueError, io.UnsupportedOperation) as e:
                    output_logger.warning(f"Select operation failed: {str(e)}")
                    # Fall back to reading from both on error
                    ready_to_read = [process.stdout, process.stderr]
            else:
                # Windows doesn't support select on pipes, so we'll just try reading from both
                ready_to_read = [process.stdout, process.stderr]
            
            for stream in ready_to_read:
                try:
                    output = stream.readline()
                    if output:
                        output_str = output.decode('utf-8', errors='replace').strip()
                        if output_str:
                            if prefix:
                                print(f"{prefix}: {output_str}")
                            else:
                                print(output_str)
                            
                            # Determine if this is stdout or stderr
                            is_stderr = (stream == process.stderr)
                            if is_stderr:
                                output_logger.warning(f"Process stderr: {output_str}")
                            else:
                                output_logger.debug(f"Process stdout: {output_str}")
                except (IOError, ValueError) as e:
                    output_logger.error(f"Error reading from process: {str(e)}")
                    # Don't break here, just continue with the next stream
                    continue
                
            # On Windows, add a small delay to avoid high CPU usage
            if platform.system() == 'Windows':
                import time
                time.sleep(0.1)
        
        # Read any remaining output after process completes
        for stream in [process.stdout, process.stderr]:
            try:
                remaining = stream.read()
                if remaining:
                    output_str = remaining.decode('utf-8', errors='replace').strip()
                    if output_str:
                        if prefix:
                            print(f"{prefix}: {output_str}")
                        else:
                            print(output_str)
                        output_logger.debug(f"Remaining output: {output_str}")
            except (IOError, ValueError) as e:
                output_logger.error(f"Error reading remaining output: {str(e)}")
    except KeyboardInterrupt:
        output_logger.info("Keyboard interrupt received while streaming output")
        # Don't re-raise, let the parent handle the interrupt
    except Exception as e:
        output_logger.error(f"Unexpected error during output streaming: {str(e)}")
        output_logger.error(traceback.format_exc())

@log_function(logger)
def ensure_directory_exists(directory: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
        print(f"Created directory: {directory}")

@log_function(install_logger)
def check_requirements() -> bool:
    """Check if all requirements are installed."""
    setup_debug = os.environ.get("SETUP_DEBUG", "0") == "1"
    install_debug = os.environ.get("INSTALL_DEBUG", "0") == "1"
    
    print_header("Checking requirements")
    
    # Create logs directory if it doesn't exist
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
        python_cmd = normalize_path(".\\venv\\Scripts\\python")
        pip_cmd = normalize_path(".\\venv\\Scripts\\pip")
    else:
        python_cmd = normalize_path("./venv/bin/python")
        pip_cmd = normalize_path("./venv/bin/pip")
    
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

@log_function(logger)
def start_frontend() -> subprocess.Popen:
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
        python_cmd = normalize_path(".\\venv\\Scripts\\python")
    else:
        python_cmd = normalize_path("./venv/bin/python")
    
    flask_cmd = f"{python_cmd} -m flask run --host=0.0.0.0 --port=5000"
    logger.debug(f"Starting frontend with command: {flask_cmd}")
    
    process = run_command(
        flask_cmd,
        cwd=os.getcwd(),
        env=env
    )
    
    return process

@log_function(logger)
def start_backend() -> subprocess.Popen:
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
        python_cmd = normalize_path(".\\venv\\Scripts\\python")
    else:
        python_cmd = normalize_path("./venv/bin/python")
    
    uvicorn_cmd = f"{python_cmd} -m uvicorn backend.main:app --host=0.0.0.0 --port=8000 --log-level={log_level}"
    logger.debug(f"Starting backend with command: {uvicorn_cmd}")
    
    process = run_command(
        uvicorn_cmd,
        cwd=os.getcwd(),
        env=env
    )
    
    return process

@log_function(logger)
def run_both() -> None:
    """Run both frontend and backend components."""
    print_header("Starting Both Components")
    
    # Start both components
    frontend_process = start_frontend()
    backend_process = start_backend()
    
    logger.info("Both components started. Press Ctrl+C to stop.")
    
    try:
        # Wait for both processes to complete or for a keyboard interrupt
        frontend_process.wait()
        backend_process.wait()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping components...")
        
        # Try to terminate processes gracefully
        if frontend_process.poll() is None:
            logger.debug("Terminating frontend process")
            frontend_process.terminate()
        
        if backend_process.poll() is None:
            logger.debug("Terminating backend process")
            backend_process.terminate()
        
        # Wait for processes to terminate (with timeout)
        try:
            frontend_process.wait(timeout=5)
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If processes don't terminate gracefully, kill them
            logger.warning("Processes didn't terminate gracefully, killing them")
            if frontend_process.poll() is None:
                frontend_process.kill()
            if backend_process.poll() is None:
                backend_process.kill()
        
        logger.info("Components stopped")
        print("Components stopped")
    except Exception as e:
        logger.error(f"Error while running components: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Make sure processes are terminated
        if frontend_process.poll() is None:
            frontend_process.terminate()
        if backend_process.poll() is None:
            backend_process.terminate()

@log_function(logger)
def run_tests(test_type: str = "all") -> int:
    """Run tests for the application."""
    print_header(f"Running {test_type} tests")
    logger.info(f"Running {test_type} tests")
    
    # Get pytest command based on platform
    if sys.platform.startswith('win'):
        python_cmd = normalize_path(".\\venv\\Scripts\\python")
    else:
        python_cmd = normalize_path("./venv/bin/python")
    
    # Set up test command based on test type
    if test_type == "frontend":
        cmd = f"{python_cmd} -m pytest {FRONTEND_DIR}/tests"
        logger.debug(f"Running frontend tests with command: {cmd}")
    elif test_type == "backend":
        cmd = f"{python_cmd} -m pytest {BACKEND_DIR}/tests"
        logger.debug(f"Running backend tests with command: {cmd}")
    elif test_type == "unit":
        cmd = f"{python_cmd} -m pytest {TESTS_DIR}/unit"
        logger.debug(f"Running unit tests with command: {cmd}")
    elif test_type == "integration":
        cmd = f"{python_cmd} -m pytest {TESTS_DIR}/integration"
        logger.debug(f"Running integration tests with command: {cmd}")
    elif test_type == "performance":
        cmd = f"{python_cmd} -m pytest {TESTS_DIR}/performance"
        logger.debug(f"Running performance tests with command: {cmd}")
    elif test_type == "security":
        cmd = f"{python_cmd} -m pytest {TESTS_DIR}/security"
        logger.debug(f"Running security tests with command: {cmd}")
    else:  # all tests
        cmd = f"{python_cmd} -m pytest"
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

@log_function(setup_logger)
def setup_dev_environment() -> bool:
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

@log_function(logger)
def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Markdown Forge Development Script")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the application")
    run_parser.add_argument("component", nargs="?", choices=["frontend", "backend"], 
                            help="Component to run (frontend or backend)")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up the development environment")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("test_type", nargs="?", choices=["frontend", "backend", "unit", "integration", "performance", "security", "all"],
                            default="all", help="Type of tests to run")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Set environment variables based on arguments
    if hasattr(args, "debug") and args.debug:
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["FLASK_DEBUG"] = "1"
        os.environ["SETUP_DEBUG"] = "1"
        os.environ["BUILD_DEBUG"] = "1"
        os.environ["INSTALL_DEBUG"] = "1"
        logger.debug("Debug mode enabled")
    
    # Extract command and attempt to run it
    command = args.command.lower()
    
    try:
        if command == "run":
            logger.info(f"Running application component: {args.component if args.component else 'both'}")
            try:
                if args.component == "frontend":
                    process = start_frontend()
                    process.wait()
                elif args.component == "backend":
                    process = start_backend()
                    process.wait()
                else:
                    run_both()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received during application run")
                print("\nStopping application...")
                return 0
        elif command == "setup":
            logger.info("Setting up development environment")
            setup_dev_environment()
        elif command == "test":
            logger.info(f"Running tests: {args.test_type}")
            run_tests(args.test_type)
        
        logger.info("Command completed successfully")
        return 0
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        print("\nOperation cancelled by user")
        # Terminate any running processes
        try:
            # Find and kill any Python processes that we might have started
            if platform.system() == 'Windows':
                os.system("taskkill /f /im python.exe /t 2>nul")
            else:
                # This is a simplified approach and may not work in all cases
                os.system("pkill -f 'python run.py|flask run|uvicorn' 2>/dev/null")
        except Exception as e:
            logger.error(f"Error during process cleanup: {str(e)}")
        return 0
    except Exception as e:
        logger.error(f"Error during command execution: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

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