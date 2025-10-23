"""
Terminal Management Utility for Safe Command Execution

This utility helps prevent the common issue of commands hanging when
terminals have foreground processes running.
"""

import subprocess
import time
import threading
import queue
import signal
import os
from typing import Optional, Dict, Any, List
import psutil
import logging

logger = logging.getLogger(__name__)

class TerminalManager:
    """Manages terminal processes and prevents hanging commands."""
    
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.process_lock = threading.Lock()
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
            return False
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return False
    
    def wait_for_port(self, port: int, timeout: int = 30) -> bool:
        """Wait for a port to become available (service to start)."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_port_in_use(port):
                return True
            time.sleep(0.5)
        return False
    
    def wait_for_port_free(self, port: int, timeout: int = 30) -> bool:
        """Wait for a port to become free (service to stop)."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.is_port_in_use(port):
                return True
            time.sleep(0.5)
        return False
    
    def run_command_safe(self, 
                        command: str, 
                        cwd: Optional[str] = None,
                        timeout: int = 60,
                        capture_output: bool = True) -> Dict[str, Any]:
        """
        Run a command safely without hanging terminals.
        
        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Maximum execution time
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dict with returncode, stdout, stderr, success
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=True,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Store process for potential cleanup
            process_id = f"proc_{int(time.time())}"
            with self.process_lock:
                self.active_processes[process_id] = process
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                returncode = process.returncode
                
                return {
                    'returncode': returncode,
                    'stdout': stdout or '',
                    'stderr': stderr or '',
                    'success': returncode == 0
                }
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Command timed out after {timeout}s: {command}")
                self.kill_process_group(process)
                return {
                    'returncode': -1,
                    'stdout': '',
                    'stderr': f'Command timed out after {timeout} seconds',
                    'success': False
                }
            
            finally:
                # Clean up process reference
                with self.process_lock:
                    self.active_processes.pop(process_id, None)
                    
        except Exception as e:
            logger.error(f"Error running command '{command}': {e}")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }
    
    def kill_process_group(self, process: subprocess.Popen):
        """Kill a process and its entire process group."""
        try:
            # Kill the entire process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if necessary
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
                
        except (OSError, ProcessLookupError):
            # Process already terminated
            pass
    
    def start_background_service(self, 
                                command: str, 
                                cwd: Optional[str] = None,
                                port: Optional[int] = None,
                                wait_for_startup: bool = True,
                                startup_timeout: int = 30) -> Dict[str, Any]:
        """
        Start a background service safely.
        
        Args:
            command: Command to start service
            cwd: Working directory  
            port: Port to monitor for service startup
            wait_for_startup: Whether to wait for service to be ready
            startup_timeout: How long to wait for startup
            
        Returns:
            Dict with process info and success status
        """
        try:
            # Check if port is already in use
            if port and self.is_port_in_use(port):
                logger.info(f"Service already running on port {port}")
                return {
                    'success': True,
                    'already_running': True,
                    'port': port,
                    'pid': None
                }
            
            # Start the process
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                preexec_fn=os.setsid
            )
            
            # Store process for management
            process_id = f"service_{port or int(time.time())}"
            with self.process_lock:
                self.active_processes[process_id] = process
            
            # Wait for startup if requested
            if wait_for_startup and port:
                startup_success = self.wait_for_port(port, startup_timeout)
                if not startup_success:
                    self.kill_process_group(process)
                    return {
                        'success': False,
                        'error': f'Service failed to start on port {port} within {startup_timeout}s',
                        'pid': process.pid
                    }
            
            return {
                'success': True,
                'already_running': False,
                'port': port,
                'pid': process.pid,
                'process_id': process_id
            }
            
        except Exception as e:
            logger.error(f"Error starting background service: {e}")
            return {
                'success': False,
                'error': str(e),
                'pid': None
            }
    
    def stop_service(self, process_id: Optional[str] = None, port: Optional[int] = None):
        """Stop a background service by process_id or port."""
        if process_id:
            with self.process_lock:
                process = self.active_processes.get(process_id)
                if process:
                    self.kill_process_group(process)
                    self.active_processes.pop(process_id, None)
                    logger.info(f"Stopped service with process_id: {process_id}")
        
        elif port:
            # Find and kill processes using the port
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        process = psutil.Process(conn.pid)
                        process.terminate()
                        logger.info(f"Stopped service on port {port}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
    
    def cleanup_all(self):
        """Clean up all managed processes."""
        with self.process_lock:
            for process_id, process in list(self.active_processes.items()):
                try:
                    self.kill_process_group(process)
                except:
                    pass
            self.active_processes.clear()
        logger.info("All managed processes cleaned up")

# Global instance for easy access
terminal_manager = TerminalManager()

def run_safe_command(command: str, **kwargs) -> Dict[str, Any]:
    """Convenience function to run commands safely."""
    return terminal_manager.run_command_safe(command, **kwargs)

def ensure_service_running(command: str, port: int, **kwargs) -> bool:
    """Ensure a service is running on the specified port."""
    result = terminal_manager.start_background_service(
        command=command, 
        port=port, 
        **kwargs
    )
    return result['success']