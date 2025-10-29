#!/usr/bin/env python3
"""
Process Manager - Bypasses terminal issues entirely

This creates completely independent processes that don't rely on 
VS Code terminals, preventing the hanging command problem.
"""

import subprocess
import time
import signal
import os
import sys
import psutil
from typing import Optional, Dict, Any, List
import threading
import json
import tempfile

class ProcessManager:
    """Manages processes independently of VS Code terminals."""
    
    def __init__(self):
        self.active_processes = {}
        self.lock = threading.Lock()
    
    def run_detached_command(self, command: str, cwd: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Run a command in a completely detached process.
        This bypasses VS Code terminals entirely.
        """
        try:
            # Create a new process group completely detached from parent
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd or os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                start_new_session=True  # This is key - completely detaches
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return {
                    'success': True,
                    'returncode': process.returncode,
                    'stdout': stdout,
                    'stderr': stderr,
                    'pid': process.pid
                }
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return {
                    'success': False,
                    'returncode': -1,
                    'stdout': stdout,
                    'stderr': stderr + f'\n[TIMEOUT after {timeout}s]',
                    'pid': process.pid
                }
                
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'pid': None
            }
    
    def start_background_service(self, command: str, cwd: Optional[str] = None, expected_port: Optional[int] = None) -> Dict[str, Any]:
        """Start a service in the background, completely detached."""
        try:
            # Check if already running
            if expected_port and self.is_port_in_use(expected_port):
                return {
                    'success': True,
                    'already_running': True,
                    'port': expected_port,
                    'pid': self.get_pid_using_port(expected_port)
                }
            
            # Start detached background process
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd or os.getcwd(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Wait for service to start if port specified
            if expected_port:
                for _ in range(30):  # Wait up to 30 seconds
                    if self.is_port_in_use(expected_port):
                        with self.lock:
                            self.active_processes[process.pid] = {
                                'process': process,
                                'command': command,
                                'port': expected_port
                            }
                        return {
                            'success': True,
                            'already_running': False,
                            'port': expected_port,
                            'pid': process.pid
                        }
                    time.sleep(1)
                
                # Service didn't start
                try:
                    process.terminate()
                except:
                    pass
                return {
                    'success': False,
                    'error': f'Service did not start on port {expected_port}',
                    'pid': process.pid
                }
            
            # No port to check, assume success
            with self.lock:
                self.active_processes[process.pid] = {
                    'process': process,
                    'command': command,
                    'port': None
                }
            
            return {
                'success': True,
                'already_running': False,
                'port': None,
                'pid': process.pid
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'pid': None
            }
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        try:
            for conn in psutil.net_connections():
                if hasattr(conn, 'laddr') and conn.laddr and len(conn.laddr) >= 2:
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        return True
            return False
        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            return False
    
    def get_pid_using_port(self, port: int) -> Optional[int]:
        """Get PID of process using a specific port."""
        try:
            for conn in psutil.net_connections():
                if hasattr(conn, 'laddr') and conn.laddr and len(conn.laddr) >= 2:
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        return conn.pid
            return None
        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            return None
    
    def stop_service_by_port(self, port: int) -> bool:
        """Stop a service by port."""
        pid = self.get_pid_using_port(port)
        if pid:
            return self.stop_service_by_pid(pid)
        return False
    
    def stop_service_by_pid(self, pid: int) -> bool:
        """Stop a service by PID."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait()
            
            with self.lock:
                self.active_processes.pop(pid, None)
            
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all managed processes."""
        status = {
            'active_processes': [],
            'ports_in_use': []
        }
        
        with self.lock:
            for pid, info in self.active_processes.items():
                try:
                    process = psutil.Process(pid)
                    status['active_processes'].append({
                        'pid': pid,
                        'command': info['command'],
                        'port': info['port'],
                        'status': process.status(),
                        'cpu_percent': process.cpu_percent(),
                        'memory_mb': process.memory_info().rss / 1024 / 1024
                    })
                except psutil.NoSuchProcess:
                    # Process no longer exists
                    pass
        
        # Check common ports
        for port in [8000, 3000, 5432, 6379, 5673]:
            if self.is_port_in_use(port):
                status['ports_in_use'].append({
                    'port': port,
                    'pid': self.get_pid_using_port(port)
                })
        
        return status

# Global instance
process_manager = ProcessManager()

def run_command_safely(command: str, **kwargs) -> Dict[str, Any]:
    """Run a command safely without terminal interference."""
    return process_manager.run_detached_command(command, **kwargs)

def ensure_server_running(port: int = 8000) -> bool:
    """Ensure the FastAPI server is running."""
    if process_manager.is_port_in_use(port):
        return True
    
    # Start the server
    result = process_manager.start_background_service(
        'python -m uvicorn api.main:app --host 0.0.0.0 --port 8000',
        expected_port=port
    )
    return result['success']

if __name__ == '__main__':
    # Test the process manager
    import json
    
    print("🔍 Testing Process Manager")
    
    # Check current status
    status = process_manager.get_status()
    print(f"📊 Current Status:")
    print(json.dumps(status, indent=2))
    
    # Test a simple command
    result = run_command_safely('echo "Hello from detached process"')
    print(f"✅ Test command result: {result['stdout'].strip()}")
    
    # Check if server should be started
    if not process_manager.is_port_in_use(8000):
        print("🚀 Starting server...")
        server_result = ensure_server_running()
        print(f"📡 Server start result: {server_result}")
    else:
        print("✅ Server already running on port 8000")