"""
Comprehensive debug logging system for SlateLink.
Provides detailed error tracking and crash reporting for production debugging.
"""

import logging
import sys
import traceback
import platform
import json
from pathlib import Path
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
import threading
from functools import wraps

# Try to import PySide6 for version info
try:
    from PySide6 import __version__ as pyside_version
except ImportError:
    pyside_version = "Not available"


class DebugLogger:
    """Comprehensive debug logging with crash reporting."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single logger instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the debug logging system."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.enabled = False
        self.log_dir = Path.home() / '.slatelink' / 'debug'
        self.crash_dir = Path.home() / '.slatelink' / 'crash_reports'
        self.logger = None
        self.file_handler = None
        self.console_handler = None
        self.last_error_details = {}
        
        # System information
        self.system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'platform_release': platform.release(),
            'platform_machine': platform.machine(),
            'python_version': platform.python_version(),
            'pyside_version': pyside_version,
            'app_version': '0.2.0'
        }
    
    def initialize(self, debug_mode: bool = False, log_level: str = 'INFO'):
        """
        Initialize the logging system.
        
        Args:
            debug_mode: Enable verbose debug logging
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.enabled = True
        
        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('SlateLink')
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # File handler with rotation
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'slatelink_{timestamp}.log'
        self.file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(file_formatter)
        self.logger.addHandler(self.file_handler)
        
        # Console handler for debug mode
        if debug_mode:
            self.console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(
                '%(levelname)s - %(name)s - %(message)s'
            )
            self.console_handler.setFormatter(console_formatter)
            self.console_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(self.console_handler)
        
        self.info("Debug logging initialized", extra={
            'debug_mode': debug_mode,
            'log_level': log_level,
            'log_file': str(log_file),
            'system_info': self.system_info
        })
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        if self.logger:
            self.logger.debug(message, extra={'context': kwargs})
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context."""
        if self.logger:
            self.logger.info(message, extra={'context': kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        if self.logger:
            self.logger.warning(message, extra={'context': kwargs})
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with exception details."""
        if self.logger:
            # Store error details for crash reporting
            self.last_error_details = {
                'message': message,
                'exception': str(exception) if exception else None,
                'traceback': traceback.format_exc() if exception else None,
                'context': kwargs,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if exception:
                self.logger.error(f"{message}: {exception}", exc_info=True, extra={'context': kwargs})
            else:
                self.logger.error(message, extra={'context': kwargs})
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical error and generate crash report."""
        if self.logger:
            self.logger.critical(f"{message}: {exception}" if exception else message, 
                               exc_info=True, extra={'context': kwargs})
            
            # Generate crash report
            crash_report = self.generate_crash_report(message, exception, kwargs)
            crash_file = self.save_crash_report(crash_report)
            
            return crash_file
    
    def generate_crash_report(self, message: str, exception: Optional[Exception] = None, 
                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive crash report."""
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': message,
            'system_info': self.system_info,
            'context': context or {},
            'last_error': self.last_error_details
        }
        
        if exception:
            report['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        # Get recent log entries
        if self.file_handler:
            try:
                log_file = Path(self.file_handler.baseFilename)
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        report['recent_logs'] = lines[-100:] if len(lines) > 100 else lines
            except Exception as e:
                report['log_read_error'] = str(e)
        
        return report
    
    def save_crash_report(self, report: Dict[str, Any]) -> Path:
        """Save crash report to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        crash_file = self.crash_dir / f'crash_{timestamp}.json'
        
        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.info(f"Crash report saved to: {crash_file}")
            return crash_file
        except Exception as e:
            self.error(f"Failed to save crash report: {e}")
            return None
    
    def log_function_call(self, func_name: str, args: tuple = None, kwargs: dict = None):
        """Log function call with arguments (for debugging)."""
        if self.logger and self.logger.level <= logging.DEBUG:
            self.debug(f"Calling {func_name}", args=args, kwargs=kwargs)
    
    def log_function_result(self, func_name: str, result: Any = None, error: Exception = None):
        """Log function result or error."""
        if self.logger and self.logger.level <= logging.DEBUG:
            if error:
                self.error(f"{func_name} failed", exception=error)
            else:
                self.debug(f"{func_name} completed", result_type=type(result).__name__)


# Global logger instance
debug_logger = DebugLogger()


def log_exceptions(func):
    """Decorator to automatically log exceptions from functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            debug_logger.log_function_call(func.__name__, args, kwargs)
            result = func(*args, **kwargs)
            debug_logger.log_function_result(func.__name__, result)
            return result
        except Exception as e:
            debug_logger.error(f"Exception in {func.__name__}", exception=e)
            raise
    return wrapper


def setup_exception_handler():
    """Setup global exception handler for uncaught exceptions."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        debug_logger.critical(
            "Uncaught exception",
            exception=exc_value,
            exc_type=exc_type.__name__,
            traceback_obj=traceback.format_tb(exc_traceback)
        )
        
        # Show crash dialog if in GUI mode
        try:
            from PySide6.QtWidgets import QMessageBox, QApplication
            if QApplication.instance():
                # Get the actual crash file that was saved
                crash_report = debug_logger.generate_crash_report(
                    "Uncaught exception",
                    exc_value,
                    {'exc_type': exc_type.__name__, 'traceback_obj': traceback.format_tb(exc_traceback)}
                )
                crash_file = debug_logger.save_crash_report(crash_report)
                
                if crash_file:
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Critical)
                    msg_box.setWindowTitle("SlateLink Crash Report")
                    msg_box.setText("SlateLink has encountered an unexpected error and needs to close.")
                    msg_box.setInformativeText(
                        f"A detailed crash report has been saved to:\n{crash_file}\n\n"
                        f"Please share this file with the developer for analysis.\n\n"
                        f"The crash report includes:\n"
                        f"• System information\n"
                        f"• Error details and stack trace\n"
                        f"• Recent application logs\n"
                        f"• No personal data is included"
                    )
                    msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Open)
                    result = msg_box.exec()
                    
                    # Open crash report folder if user clicks Open
                    if result == QMessageBox.Open:
                        import subprocess
                        import platform
                        if platform.system() == "Darwin":  # macOS
                            subprocess.call(["open", "-R", str(crash_file)])
                        elif platform.system() == "Windows":
                            subprocess.call(["explorer", "/select,", str(crash_file)])
                        else:  # Linux
                            subprocess.call(["xdg-open", str(crash_file.parent)])
                else:
                    QMessageBox.critical(
                        None,
                        "Application Crash",
                        f"SlateLink has encountered an error and needs to close.\n\n"
                        f"Unable to save crash report. Please report this issue manually."
                    )
        except:
            pass
        
        # Call the default handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = handle_exception