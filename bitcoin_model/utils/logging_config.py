"""
Logging configuration for Bitcoin Strategic Investment Model
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

def setup_logging(log_level: str = "INFO", 
                 log_file: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5) -> logging.Logger:
    """
    Setup logging configuration for the BSI model
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger('bitcoin_model')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info("Logging configured successfully")
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'bitcoin_model.{name}')

class LoggingMixin:
    """Mixin class to add logging capabilities to other classes"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)
    
    def log_method_call(self, method_name: str, **kwargs):
        """Log a method call with parameters"""
        params = ', '.join(f'{k}={v}' for k, v in kwargs.items())
        self.logger.debug(f"Calling {method_name}({params})")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log an error with context"""
        context_str = f" in {context}" if context else ""
        self.logger.error(f"Error{context_str}: {str(error)}", exc_info=True)