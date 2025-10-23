"""
T013: System Resource Usage Dashboard - Extended Backend API

Enhanced system resource monitoring endpoints that provide detailed
resource usage analytics, storage monitoring, and process information
beyond the basic performance metrics in T032.
"""

import psutil
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.routes.auth import get_current_user
from api.models import User
from api.utils.admin_required import check_admin_required

# Create router for resource usage endpoints
resource_router = APIRouter(prefix="/admin/system/resources", tags=["system-resources"])


class SystemResourceService:
    """Service for detailed system resource usage analytics"""
    
    def __init__(self):
        self.cache_timeout = 60  # Cache for 1 minute for resource data
        self._resource_cache = {}
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get detailed storage usage across different directories"""
        try:
            storage_info = {}
            
            # System root partition
            root_usage = shutil.disk_usage('/')
            storage_info['system'] = {
                'path': '/',
                'total': root_usage.total,
                'used': root_usage.used,
                'free': root_usage.free,
                'percentage': round((root_usage.used / root_usage.total) * 100, 2)
            }
            
            # Application directories
            app_dirs = [
                ('models', './models/'),
                ('cache', './cache/'),
                ('logs', './logs/'),
                ('temp', './temp/'),
                ('uploads', './uploads/') if os.path.exists('./uploads/') else None,
                ('database', './')  # For database files
            ]
            
            for name, path in app_dirs:
                if path and os.path.exists(path):
                    try:
                        total_size = self._get_directory_size(path)
                        storage_info[name] = {
                            'path': path,
                            'size': total_size,
                            'human_readable': self._format_bytes(total_size)
                        }
                    except Exception as e:
                        storage_info[name] = {
                            'path': path,
                            'error': str(e),
                            'size': 0
                        }
            
            # Database file sizes
            db_files = ['whisper_app.db', 'whisper_app.db-wal', 'whisper_app.db-shm']
            database_size = 0
            for db_file in db_files:
                if os.path.exists(db_file):
                    database_size += os.path.getsize(db_file)
            
            storage_info['database_files'] = {
                'total_size': database_size,
                'human_readable': self._format_bytes(database_size),
                'files': {
                    db_file: {
                        'size': os.path.getsize(db_file),
                        'human_readable': self._format_bytes(os.path.getsize(db_file))
                    } for db_file in db_files if os.path.exists(db_file)
                }
            }
            
            return {
                'storage': storage_info,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get storage usage: {str(e)}")
    
    def get_process_information(self) -> Dict[str, Any]:
        """Get detailed process information and resource usage"""
        try:
            processes = []
            current_pid = os.getpid()
            
            # Get all processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
                try:
                    proc_info = proc.info
                    proc_info['memory_mb'] = round(proc.memory_info().rss / (1024 * 1024), 2)
                    proc_info['uptime'] = datetime.utcnow().timestamp() - proc_info['create_time']
                    proc_info['is_current'] = proc_info['pid'] == current_pid
                    
                    # Only include processes using significant resources or related to our app
                    if (proc_info['cpu_percent'] > 0.1 or 
                        proc_info['memory_percent'] > 0.1 or 
                        'python' in proc_info['name'].lower() or
                        'whisper' in proc_info['name'].lower() or
                        proc_info['is_current']):
                        processes.append(proc_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage descending
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # Get system load averages
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            # Get boot time and uptime
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.utcnow().timestamp() - boot_time
            
            return {
                'processes': processes[:50],  # Top 50 processes
                'total_processes': len(list(psutil.process_iter())),
                'load_average': {
                    '1_min': round(load_avg[0], 2),
                    '5_min': round(load_avg[1], 2),
                    '15_min': round(load_avg[2], 2)
                },
                'system_uptime': {
                    'seconds': uptime_seconds,
                    'human_readable': self._format_uptime(uptime_seconds)
                },
                'boot_time': datetime.fromtimestamp(boot_time).isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get process information: {str(e)}")
    
    def get_network_details(self) -> Dict[str, Any]:
        """Get detailed network interface and connection information"""
        try:
            # Network interfaces
            interfaces = {}
            for interface, addrs in psutil.net_if_addrs().items():
                interface_stats = psutil.net_if_stats().get(interface)
                io_counters = psutil.net_io_counters(pernic=True).get(interface)
                
                interfaces[interface] = {
                    'addresses': [
                        {
                            'family': addr.family.name,
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        } for addr in addrs
                    ],
                    'is_up': interface_stats.isup if interface_stats else False,
                    'duplex': interface_stats.duplex.name if interface_stats and interface_stats.duplex else 'unknown',
                    'speed': interface_stats.speed if interface_stats else 0,
                    'mtu': interface_stats.mtu if interface_stats else 0,
                    'bytes_sent': io_counters.bytes_sent if io_counters else 0,
                    'bytes_recv': io_counters.bytes_recv if io_counters else 0,
                    'packets_sent': io_counters.packets_sent if io_counters else 0,
                    'packets_recv': io_counters.packets_recv if io_counters else 0,
                    'errors_in': io_counters.errin if io_counters else 0,
                    'errors_out': io_counters.errout if io_counters else 0,
                    'dropped_in': io_counters.dropin if io_counters else 0,
                    'dropped_out': io_counters.dropout if io_counters else 0
                }
            
            # Active connections
            connections = []
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == psutil.CONN_ESTABLISHED:
                        connections.append({
                            'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else 'unknown',
                            'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else 'unknown',
                            'status': conn.status,
                            'pid': conn.pid,
                            'family': conn.family.name,
                            'type': conn.type.name
                        })
            except psutil.AccessDenied:
                connections = [{'error': 'Access denied to connection information'}]
            
            return {
                'interfaces': interfaces,
                'active_connections': connections[:20],  # Top 20 connections
                'total_connections': len(connections),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get network details: {str(e)}")
    
    def get_memory_details(self) -> Dict[str, Any]:
        """Get detailed memory usage breakdown"""
        try:
            # Virtual memory
            virtual_mem = psutil.virtual_memory()
            
            # Swap memory
            swap_mem = psutil.swap_memory()
            
            # Memory by process (top 10 memory consumers)
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    proc_info = proc.info
                    memory_info = proc.memory_info()
                    proc_info['memory_rss'] = memory_info.rss
                    proc_info['memory_vms'] = memory_info.vms
                    proc_info['memory_mb'] = round(memory_info.rss / (1024 * 1024), 2)
                    
                    if proc_info['memory_percent'] > 0.1:  # Only processes using > 0.1% memory
                        processes.append(proc_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            return {
                'virtual_memory': {
                    'total': virtual_mem.total,
                    'available': virtual_mem.available,
                    'used': virtual_mem.used,
                    'free': virtual_mem.free,
                    'percentage': virtual_mem.percent,
                    'active': getattr(virtual_mem, 'active', 0),
                    'inactive': getattr(virtual_mem, 'inactive', 0),
                    'buffers': getattr(virtual_mem, 'buffers', 0),
                    'cached': getattr(virtual_mem, 'cached', 0),
                    'shared': getattr(virtual_mem, 'shared', 0)
                },
                'swap_memory': {
                    'total': swap_mem.total,
                    'used': swap_mem.used,
                    'free': swap_mem.free,
                    'percentage': swap_mem.percent,
                    'sin': swap_mem.sin,
                    'sout': swap_mem.sout
                },
                'top_memory_processes': processes[:10],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get memory details: {str(e)}")
    
    def get_cpu_details(self) -> Dict[str, Any]:
        """Get detailed CPU information and usage"""
        try:
            # CPU usage per core
            cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # CPU frequency
            cpu_freq = psutil.cpu_freq()
            
            # CPU times
            cpu_times = psutil.cpu_times()
            
            # CPU stats
            cpu_stats = psutil.cpu_stats()
            
            # CPU by process (top 10 CPU consumers)
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0.1:  # Only processes using > 0.1% CPU
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return {
                'cpu_count': {
                    'logical': psutil.cpu_count(logical=True),
                    'physical': psutil.cpu_count(logical=False)
                },
                'cpu_percent_total': psutil.cpu_percent(interval=0.1),
                'cpu_percent_per_core': cpu_percent_per_core,
                'cpu_frequency': {
                    'current': cpu_freq.current if cpu_freq else 0,
                    'min': cpu_freq.min if cpu_freq else 0,
                    'max': cpu_freq.max if cpu_freq else 0
                },
                'cpu_times': {
                    'user': cpu_times.user,
                    'system': cpu_times.system,
                    'idle': cpu_times.idle,
                    'nice': getattr(cpu_times, 'nice', 0),
                    'iowait': getattr(cpu_times, 'iowait', 0),
                    'irq': getattr(cpu_times, 'irq', 0),
                    'softirq': getattr(cpu_times, 'softirq', 0),
                    'steal': getattr(cpu_times, 'steal', 0),
                    'guest': getattr(cpu_times, 'guest', 0)
                },
                'cpu_stats': {
                    'ctx_switches': cpu_stats.ctx_switches,
                    'interrupts': cpu_stats.interrupts,
                    'soft_interrupts': cpu_stats.soft_interrupts,
                    'syscalls': getattr(cpu_stats, 'syscalls', 0)
                },
                'top_cpu_processes': processes[:10],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get CPU details: {str(e)}")
    
    def get_application_resource_usage(self, db: Session) -> Dict[str, Any]:
        """Get application-specific resource usage and database statistics"""
        try:
            # Database statistics
            db_stats = {}
            try:
                # Get database file size
                db_path = 'whisper_app.db'
                if os.path.exists(db_path):
                    db_stats['file_size'] = os.path.getsize(db_path)
                    db_stats['file_size_human'] = self._format_bytes(db_stats['file_size'])
                
                # Get table statistics
                tables_result = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in tables_result.fetchall()]
                
                table_stats = {}
                for table in tables:
                    count_result = db.execute(f"SELECT COUNT(*) FROM {table}")
                    table_stats[table] = count_result.scalar()
                
                db_stats['tables'] = table_stats
                
                # Get database page info
                page_info_result = db.execute("PRAGMA page_count")
                page_count = page_info_result.scalar()
                
                page_size_result = db.execute("PRAGMA page_size")
                page_size = page_size_result.scalar()
                
                db_stats['pages'] = {
                    'count': page_count,
                    'size': page_size,
                    'total_size': page_count * page_size
                }
                
                # Get vacuum info
                vacuum_result = db.execute("PRAGMA auto_vacuum")
                db_stats['auto_vacuum'] = vacuum_result.scalar()
                
            except Exception as e:
                db_stats['error'] = str(e)
            
            # Get job statistics for resource impact
            job_stats = {}
            try:
                # Recent job activity (last 24 hours)
                yesterday = datetime.utcnow() - timedelta(days=1)
                
                total_jobs_result = db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE created_at > :yesterday", 
                    {"yesterday": yesterday}
                )
                job_stats['jobs_last_24h'] = total_jobs_result.scalar() or 0
                
                # Jobs by status
                status_result = db.execute(
                    "SELECT status, COUNT(*) FROM jobs GROUP BY status"
                )
                job_stats['by_status'] = {row[0]: row[1] for row in status_result.fetchall()}
                
                # Average job duration
                duration_result = db.execute(
                    """SELECT AVG(CAST((julianday(updated_at) - julianday(created_at)) * 24 * 60 * 60 AS INTEGER)) 
                       FROM jobs WHERE status = 'completed'"""
                )
                avg_duration = duration_result.scalar()
                job_stats['avg_duration_seconds'] = avg_duration if avg_duration else 0
                
            except Exception as e:
                job_stats['error'] = str(e)
            
            return {
                'database': db_stats,
                'jobs': job_stats,
                'application_memory': self._get_current_process_memory(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get application resource usage: {str(e)}")
    
    def _get_directory_size(self, path: str) -> int:
        """Calculate total size of a directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        continue
        except (OSError, IOError):
            pass
        return total_size
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime seconds into human readable string"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _get_current_process_memory(self) -> Dict[str, Any]:
        """Get memory usage of current process"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'rss_human': self._format_bytes(memory_info.rss),
                'vms_human': self._format_bytes(memory_info.vms),
                'percent': process.memory_percent()
            }
        except Exception:
            return {'error': 'Unable to get process memory info'}


# Initialize service
resource_service = SystemResourceService()


@resource_router.get("/storage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user)
):
    """Get detailed storage usage information"""
    await check_admin_required(current_user)
    
    try:
        storage_data = resource_service.get_storage_usage()
        return {"success": True, "data": storage_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@resource_router.get("/processes")
async def get_process_information(
    current_user: User = Depends(get_current_user)
):
    """Get detailed process information"""
    await check_admin_required(current_user)
    
    try:
        process_data = resource_service.get_process_information()
        return {"success": True, "data": process_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@resource_router.get("/network")
async def get_network_details(
    current_user: User = Depends(get_current_user)
):
    """Get detailed network interface and connection information"""
    await check_admin_required(current_user)
    
    try:
        network_data = resource_service.get_network_details()
        return {"success": True, "data": network_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@resource_router.get("/memory")
async def get_memory_details(
    current_user: User = Depends(get_current_user)
):
    """Get detailed memory usage breakdown"""
    await check_admin_required(current_user)
    
    try:
        memory_data = resource_service.get_memory_details()
        return {"success": True, "data": memory_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@resource_router.get("/cpu")
async def get_cpu_details(
    current_user: User = Depends(get_current_user)
):
    """Get detailed CPU information and usage"""
    await check_admin_required(current_user)
    
    try:
        cpu_data = resource_service.get_cpu_details()
        return {"success": True, "data": cpu_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@resource_router.get("/application")
async def get_application_resource_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application-specific resource usage and database statistics"""
    await check_admin_required(current_user)
    
    try:
        app_data = resource_service.get_application_resource_usage(db)
        return {"success": True, "data": app_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@resource_router.get("/overview")
async def get_resource_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive resource usage overview"""
    await check_admin_required(current_user)
    
    try:
        # Collect all resource data
        storage_data = resource_service.get_storage_usage()
        memory_data = resource_service.get_memory_details()
        cpu_data = resource_service.get_cpu_details()
        app_data = resource_service.get_application_resource_usage(db)
        
        overview = {
            'storage': storage_data,
            'memory': memory_data,
            'cpu': cpu_data,
            'application': app_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return {"success": True, "data": overview}
    except Exception as e:
        return {"success": False, "error": str(e)}