# -*- coding: utf-8 -*-
"""
Error Handler

Comprehensive error handling system with custom exceptions and centralized error management.
"""

import logging
import traceback
import sys
from typing import Optional, Dict, Any, Callable, Type
from functools import wraps
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """
    Error severity levels.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """
    Error categories for better classification.
    """
    API = "api"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    VALIDATION = "validation"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    USER_INPUT = "user_input"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    UNKNOWN = "unknown"

class BaseAppError(Exception):
    """
    Base exception class for the YouTube Data Analyzer application.
    """
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize the base application error.
        
        Args:
            message (str): Error message
            category (ErrorCategory): Error category
            severity (ErrorSeverity): Error severity
            details (Optional[Dict[str, Any]]): Additional error details
            original_exception (Optional[Exception]): Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.original_exception = original_exception
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Error dictionary
        """
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }

class APIError(BaseAppError):
    """
    Exception for API-related errors.
    """
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = {
            "api_name": api_name,
            "status_code": status_code,
            "response_data": response_data
        }
        super().__init__(
            message,
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )

class DatabaseError(BaseAppError):
    """
    Exception for database-related errors.
    """
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs
    ):
        details = {
            "operation": operation,
            "table": table
        }
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )

class ConfigurationError(BaseAppError):
    """
    Exception for configuration-related errors.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        details = {
            "config_key": config_key,
            "config_file": config_file
        }
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )

class DependencyError(BaseAppError):
    """
    Exception for dependency-related errors.
    """
    
    def __init__(
        self,
        message: str,
        dependency_name: Optional[str] = None,
        required_version: Optional[str] = None,
        **kwargs
    ):
        details = {
            "dependency_name": dependency_name,
            "required_version": required_version
        }
        super().__init__(
            message,
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.CRITICAL,
            details=details,
            **kwargs
        )

class ValidationError(BaseAppError):
    """
    Exception for validation-related errors.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        **kwargs
    ):
        details = {
            "field_name": field_name,
            "field_value": str(field_value) if field_value is not None else None
        }
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            **kwargs
        )

class NetworkError(BaseAppError):
    """
    Exception for network-related errors.
    """
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ):
        details = {
            "url": url,
            "timeout": timeout
        }
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )

class FileSystemError(BaseAppError):
    """
    Exception for file system-related errors.
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = {
            "file_path": file_path,
            "operation": operation
        }
        super().__init__(
            message,
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            **kwargs
        )

class AuthenticationError(BaseAppError):
    """
    Exception for authentication-related errors.
    """
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        **kwargs
    ):
        details = {
            "service": service
        }
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            **kwargs
        )

class ErrorHandler:
    """
    Centralized error handler for the application.
    """
    
    def __init__(self, log_errors: bool = True, log_file: Optional[Path] = None):
        """
        Initialize the error handler.
        
        Args:
            log_errors (bool): Whether to log errors
            log_file (Optional[Path]): Path to error log file
        """
        self.log_errors = log_errors
        self.log_file = log_file
        self.error_callbacks: Dict[Type[Exception], Callable] = {}
        
        if log_file:
            self._setup_file_logging()
    
    def _setup_file_logging(self) -> None:
        """
        Setup file logging for errors.
        """
        if self.log_file:
            # Create log directory if it doesn't exist
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Setup file handler
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.ERROR)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            error_logger = logging.getLogger('error_handler')
            error_logger.addHandler(file_handler)
            error_logger.setLevel(logging.ERROR)
    
    def register_callback(self, exception_type: Type[Exception], callback: Callable) -> None:
        """
        Register a callback function for a specific exception type.
        
        Args:
            exception_type (Type[Exception]): Exception type
            callback (Callable): Callback function
        """
        self.error_callbacks[exception_type] = callback
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Handle an error with logging and optional callbacks.
        
        Args:
            error (Exception): The error to handle
            context (Optional[Dict[str, Any]]): Additional context information
            reraise (bool): Whether to reraise the exception
            
        Returns:
            Optional[Dict[str, Any]]: Error information dictionary
        """
        error_info = self._create_error_info(error, context)
        
        # Log the error
        if self.log_errors:
            self._log_error(error_info)
        
        # Execute callback if registered
        error_type = type(error)
        if error_type in self.error_callbacks:
            try:
                self.error_callbacks[error_type](error, error_info)
            except Exception as callback_error:
                logger.error(f"Error in callback for {error_type.__name__}: {callback_error}")
        
        # Reraise if requested
        if reraise:
            raise error
        
        return error_info
    
    def _create_error_info(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create comprehensive error information.
        
        Args:
            error (Exception): The error
            context (Optional[Dict[str, Any]]): Additional context
            
        Returns:
            Dict[str, Any]: Error information
        """
        error_info = {
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
            )) if logger.handlers else None,
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        # Add additional info for BaseAppError instances
        if isinstance(error, BaseAppError):
            error_info.update(error.to_dict())
        
        return error_info
    
    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """
        Log error information.
        
        Args:
            error_info (Dict[str, Any]): Error information
        """
        severity = error_info.get("severity", "medium")
        category = error_info.get("category", "unknown")
        
        log_message = f"[{category.upper()}] {error_info['message']}"
        
        if severity == "critical":
            logger.critical(log_message, extra=error_info)
        elif severity == "high":
            logger.error(log_message, extra=error_info)
        elif severity == "medium":
            logger.warning(log_message, extra=error_info)
        else:
            logger.info(log_message, extra=error_info)
        
        # Log traceback for debugging
        if error_info.get("traceback"):
            logger.debug(f"Traceback: {error_info['traceback']}")

def handle_exceptions(reraise: bool = False, log_errors: bool = True):
    """
    Decorator for automatic exception handling.
    
    Args:
        reraise (bool): Whether to reraise exceptions
        log_errors (bool): Whether to log errors
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = ErrorHandler(log_errors=log_errors)
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args": str(args)[:200],  # Limit length
                    "kwargs": str(kwargs)[:200]  # Limit length
                }
                error_handler.handle_error(e, context=context, reraise=reraise)
                
                if not reraise:
                    return None
        
        return wrapper
    return decorator

def safe_execute(
    func: Callable,
    *args,
    default_return=None,
    log_errors: bool = True,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func (Callable): Function to execute
        *args: Function arguments
        default_return: Default return value on error
        log_errors (bool): Whether to log errors
        **kwargs: Function keyword arguments
        
    Returns:
        Any: Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            error_handler = ErrorHandler(log_errors=True)
            context = {
                "function": func.__name__,
                "module": getattr(func, '__module__', 'unknown')
            }
            error_handler.handle_error(e, context=context)
        
        return default_return

def create_user_friendly_message(error: Exception) -> str:
    """
    Create a user-friendly error message from an exception.
    
    Args:
        error (Exception): The exception
        
    Returns:
        str: User-friendly error message
    """
    if isinstance(error, BaseAppError):
        if error.category == ErrorCategory.API:
            return f"API Error: {error.message}. Please check your API keys and internet connection."
        elif error.category == ErrorCategory.DATABASE:
            return f"Database Error: {error.message}. Please check your database configuration."
        elif error.category == ErrorCategory.CONFIGURATION:
            return f"Configuration Error: {error.message}. Please check your settings."
        elif error.category == ErrorCategory.DEPENDENCY:
            return f"Dependency Error: {error.message}. Please install required dependencies."
        elif error.category == ErrorCategory.VALIDATION:
            return f"Validation Error: {error.message}. Please check your input."
        elif error.category == ErrorCategory.NETWORK:
            return f"Network Error: {error.message}. Please check your internet connection."
        elif error.category == ErrorCategory.FILE_SYSTEM:
            return f"File Error: {error.message}. Please check file permissions and paths."
        elif error.category == ErrorCategory.AUTHENTICATION:
            return f"Authentication Error: {error.message}. Please check your credentials."
        else:
            return f"Error: {error.message}"
    else:
        # Generic error messages for common exceptions
        error_type = type(error).__name__
        if "ConnectionError" in error_type or "TimeoutError" in error_type:
            return "Connection error. Please check your internet connection and try again."
        elif "FileNotFoundError" in error_type:
            return "File not found. Please check the file path and try again."
        elif "PermissionError" in error_type:
            return "Permission denied. Please check file permissions and try again."
        elif "ValueError" in error_type:
            return "Invalid value provided. Please check your input and try again."
        else:
            return f"An unexpected error occurred: {str(error)}"

# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.
    
    Returns:
        ErrorHandler: The error handler instance
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(
            log_errors=True,
            log_file=Path("data/logs/errors.log")
        )
    return _global_error_handler