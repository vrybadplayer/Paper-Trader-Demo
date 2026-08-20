"""
Process Guard
Runtime monitoring and error detection engine for the trading bot.
Monitors system health, detects anomalies, and triggers self-healing mechanisms.
"""

import psutil
import threading
import time
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import os
import signal

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    GPUtil = None

logger = logging.getLogger(__name__)

class ProcessGuard:
    """
    Runtime monitoring and error detection engine.
    Monitors CPU, memory, disk, GPU usage, and process health.
    Can detect anomalies and trigger self-healing mechanisms.
    """
    
    def __init__(self, check_interval: float = 5.0):
        """
        Initialize the process guard.
        
        Args:
            check_interval: How often to check system health (in seconds)
        """
        self.check_interval = check_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.alert_callbacks: List[Callable] = []
        self.health_history: List[Dict] = []
        self.max_history_size = 1000
        
        # Thresholds for alerts
        self.thresholds = {
            'cpu_percent': 80.0,          # CPU usage percentage
            'memory_percent': 85.0,       # Memory usage percentage
            'disk_percent': 90.0,         # Disk usage percentage
            'gpu_percent': 90.0,          # GPU usage percentage
            'gpu_memory_percent': 90.0,   # GPU memory usage percentage
            'temperature': 80.0,          # CPU temperature (Celsius)
            'io_wait': 10.0,              # I/O wait percentage
            'context_switches': 10000,    # Context switches per second
        }
        
        # Process-specific monitoring
        self.process_name = os.path.basename(__file__)
        self.pid = os.getpid()
        
        logger.info(f"ProcessGuard initialized for PID {self.pid}")
    
    def add_alert_callback(self, callback: Callable[[Dict], None]):
        """
        Add a callback function to be called when an alert is triggered.
        
        Args:
            callback: Function that takes an alert dictionary as argument
        """
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Process monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Process monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                health_data = self.collect_health_data()
                self.health_history.append(health_data)
                
                # Keep history size manageable
                if len(self.health_history) > self.max_history_size:
                    self.health_history = self.health_history[-self.max_history_size:]
                
                # Check for anomalies and trigger alerts
                alerts = self.check_for_anomalies(health_data)
                for alert in alerts:
                    self._trigger_alert(alert)
                
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def collect_health_data(self) -> Dict:
        """
        Collect current system health data.
        
        Returns:
            Dictionary containing health metrics
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process(self.pid)
            process_memory = process.memory_info()
            process_cpu_percent = process.cpu_percent(interval=0.1)
            
            # GPU metrics (if available)
            gpu_data = {}
            if GPU_AVAILABLE:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]  # Use first GPU
                        gpu_data = {
                            'gpu_percent': gpu.load * 100,
                            'gpu_memory_percent': gpu.memoryUtil * 100,
                            'gpu_temperature': gpu.temperature,
                            'gpu_used_memory': gpu.memoryUsed,
                            'gpu_total_memory': gpu.memoryTotal
                        }
                except Exception as e:
                    logger.debug(f"Could not get GPU data: {e}")
            
            # Temperature (if available)
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get the first available temperature
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
            except Exception:
                pass  # Temperature might not be available on all systems
            
            # System load
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Context switches and interrupts
            sys_stats = psutil.cpu_stats()
            
            health_data = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else 0,
                    'load_avg_1m': load_avg[0],
                    'load_avg_5m': load_avg[1],
                    'load_avg_15m': load_avg[2],
                    'context_switches': sys_stats.ctx_switches,
                    'interrupts': sys_stats.interrupts,
                    'soft_interrupts': sys_stats.soft_interrupts,
                    'syscalls': sys_stats.syscalls
                },
                'memory': {
                    'percent': memory.percent,
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'total_gb': memory.total / (1024**3),
                    'swap_percent': swap.percent,
                    'swap_used_gb': swap.used / (1024**3),
                    'swap_total_gb': swap.total / (1024**3)
                },
                'disk': {
                    'percent': (disk.used / disk.total) * 100,
                    'free_gb': disk.free / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'total_gb': disk.total / (1024**3),
                    'read_count': disk.read_count,
                    'write_count': disk.write_count,
                    'read_bytes': disk.read_bytes,
                    'write_bytes': disk.write_bytes
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv,
                    'errin': network.errin,
                    'errout': network.errout,
                    'dropin': network.dropin,
                    'dropout': network.dropout
                },
                'process': {
                    'pid': self.pid,
                    'name': self.process_name,
                    'cpu_percent': process_cpu_percent,
                    'memory_mb': process_memory.rss / (1024**2),
                    'memory_vms_mb': process_memory.vms / (1024**2),
                    'num_threads': process.num_threads(),
                    'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                    'create_time': datetime.fromtimestamp(process.create_time()).isoformat() + 'Z',
                    'status': process.status()
                },
                'gpu': gpu_data,
                'temperature': temperature
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error collecting health data: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error': str(e)
            }
    
    def check_for_anomalies(self, health_data: Dict) -> List[Dict]:
        """
        Check health data for anomalies based on thresholds.
        
        Args:
            health_data: Health data dictionary from collect_health_data
            
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        if 'error' in health_data:
            alerts.append({
                'type': 'data_collection_error',
                'severity': 'high',
                'message': f"Failed to collect health data: {health_data['error']}",
                'timestamp': health_data['timestamp'],
                'data': health_data
            })
            return alerts
        
        # Check CPU usage
        cpu_percent = health_data['cpu']['percent']
        if cpu_percent > self.thresholds['cpu_percent']:
            alerts.append({
                'type': 'high_cpu_usage',
                'severity': 'medium' if cpu_percent < 95 else 'high',
                'message': f"CPU usage is high: {cpu_percent:.1f}% (threshold: {self.thresholds['cpu_percent']}%)",
                'timestamp': health_data['timestamp'],
                'value': cpu_percent,
                'threshold': self.thresholds['cpu_percent']
            })
        
        # Check memory usage
        memory_percent = health_data['memory']['percent']
        if memory_percent > self.thresholds['memory_percent']:
            alerts.append({
                'type': 'high_memory_usage',
                'severity': 'medium' if memory_percent < 95 else 'high',
                'message': f"Memory usage is high: {memory_percent:.1f}% (threshold: {self.thresholds['memory_percent']}%)",
                'timestamp': health_data['timestamp'],
                'value': memory_percent,
                'threshold': self.thresholds['memory_percent']
            })
        
        # Check disk usage
        disk_percent = health_data['disk']['percent']
        if disk_percent > self.thresholds['disk_percent']:
            alerts.append({
                'type': 'high_disk_usage',
                'severity': 'medium' if disk_percent < 98 else 'high',
                'message': f"Disk usage is high: {disk_percent:.1f}% (threshold: {self.thresholds['disk_percent']}%)",
                'timestamp': health_data['timestamp'],
                'value': disk_percent,
                'threshold': self.thresholds['disk_percent']
            })
        
        # Check GPU usage (if available)
        if health_data['gpu']:
            gpu_percent = health_data['gpu'].get('gpu_percent', 0)
            if gpu_percent > self.thresholds['gpu_percent']:
                alerts.append({
                    'type': 'high_gpu_usage',
                    'severity': 'medium' if gpu_percent < 95 else 'high',
                    'message': f"GPU usage is high: {gpu_percent:.1f}% (threshold: {self.thresholds['gpu_percent']}%)",
                    'timestamp': health_data['timestamp'],
                    'value': gpu_percent,
                    'threshold': self.thresholds['gpu_percent']
                })
            
            gpu_memory_percent = health_data['gpu'].get('gpu_memory_percent', 0)
            if gpu_memory_percent > self.thresholds['gpu_memory_percent']:
                alerts.append({
                    'type': 'high_gpu_memory_usage',
                    'severity': 'medium' if gpu_memory_percent < 95 else 'high',
                    'message': f"GPU memory usage is high: {gpu_memory_percent:.1f}% (threshold: {self.thresholds['gpu_memory_percent']}%)",
                    'timestamp': health_data['timestamp'],
                    'value': gpu_memory_percent,
                    'threshold': self.thresholds['gpu_memory_percent']
                })
        
        # Check temperature (if available)
        temperature = health_data.get('temperature')
        if temperature is not None and temperature > self.thresholds['temperature']:
            alerts.append({
                'type': 'high_temperature',
                'severity': 'medium' if temperature < 85 else 'high',
                'message': f"CPU temperature is high: {temperature:.1f}°C (threshold: {self.thresholds['temperature']}°C)",
                'timestamp': health_data['timestamp'],
                'value': temperature,
                'threshold': self.thresholds['temperature']
            })
        
        # Check I/O wait (approximation from context switches)
        # This is a simplified check - real I/O wait would require more detailed metrics
        ctx_switches = health_data['cpu']['context_switches']
        if ctx_switches > self.thresholds['context_switches']:
            alerts.append({
                'type': 'high_context_switches',
                'severity': 'low',
                'message': f"High context switches: {ctx_switches:.0f} (threshold: {self.thresholds['context_switches']:.0f})",
                'timestamp': health_data['timestamp'],
                'value': ctx_switches,
                'threshold': self.thresholds['context_switches']
            })
        
        return alerts
    
    def _trigger_alert(self, alert: Dict):
        """
        Trigger an alert by calling all registered callbacks.
        
        Args:
            alert: Alert dictionary to trigger
        """
        logger.warning(f"ALERT [{alert['severity']}]: {alert['message']}")
        
        # Call all registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def get_health_summary(self, last_n_minutes: int = 5) -> Dict:
        """
        Get a summary of health data over the last N minutes.
        
        Args:
            last_n_minutes: Number of minutes to look back
            
        Returns:
            Dictionary containing health summary
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=last_n_minutes)
        cutoff_str = cutoff_time.isoformat() + 'Z'
        
        # Filter history to last N minutes
        recent_history = [
            h for h in self.health_history
            if h.get('timestamp', '0') >= cutoff_str
        ]
        
        if not recent_history:
            return {'error': 'No health data available for the specified time period'}
        
        # Calculate averages for key metrics
        cpu_values = [h['cpu']['percent'] for h in recent_history if 'cpu' in h]
        memory_values = [h['memory']['percent'] for h in recent_history if 'memory' in h]
        disk_values = [h['disk']['percent'] for h in recent_history if 'disk' in h]
        
        summary = {
            'period_minutes': last_n_minutes,
            'samples_count': len(recent_history),
            'time_range': {
                'start': recent_history[0]['timestamp'],
                'end': recent_history[-1]['timestamp']
            },
            'averages': {
                'cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'memory_percent': sum(memory_values) / len(memory_values) if memory_values else 0,
                'disk_percent': sum(disk_values) / len(disk_values) if disk_values else 0
            },
            'maximums': {
                'cpu_percent': max(cpu_values) if cpu_values else 0,
                'memory_percent': max(memory_values) if memory_values else 0,
                'disk_percent': max(disk_values) if disk_values else 0
            },
            'latest': recent_history[-1] if recent_history else {}
        }
        
        # Add GPU averages if available
        gpu_values = [h['gpu'].get('gpu_percent', 0) for h in recent_history if h.get('gpu')]
        if gpu_values:
            summary['averages']['gpu_percent'] = sum(gpu_values) / len(gpu_values)
            summary['maximums']['gpu_percent'] = max(gpu_values)
        
        return summary
    
    def is_system_healthy(self) -> bool:
        """
        Quick check if the system is currently healthy based on thresholds.
        
        Returns:
            bool: True if all metrics are within thresholds, False otherwise
        """
        health_data = self.collect_health_data()
        alerts = self.check_for_anomalies(health_data)
        return len(alerts) == 0
    
    def get_current_health(self) -> Dict:
        """
        Get current health data without storing in history.
        
        Returns:
            Current health data dictionary
        """
        return self.collect_health_data()

# Example usage (for testing)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create process guard
    guard = ProcessGuard(check_interval=2.0)
    
    # Add an alert callback
    def alert_handler(alert):
        print(f"ALERT RECEIVED: {alert['type']} - {alert['message']}")
    
    guard.add_alert_callback(alert_handler)
    
    # Start monitoring
    guard.start_monitoring()
    
    try:
        # Run for 30 seconds
        print("Monitoring system health for 30 seconds...")
        time.sleep(30)
        
        # Get health summary
        summary = guard.get_health_summary(last_n_minutes=1)
        print(f"\nHealth summary: {summary}")
        
        # Check if system is healthy
        is_healthy = guard.is_system_healthy()
        print(f"System healthy: {is_healthy}")
        
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        guard.stop_monitoring()