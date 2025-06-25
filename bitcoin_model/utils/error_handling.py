"""
Error handling utilities for Bitcoin Strategic Investment Model
"""

import functools
import logging
from typing import Any, Callable, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BSIError(Exception):
    """Base exception for BSI Model errors"""
    pass

class DataProviderError(BSIError):
    """Error related to data provider issues"""
    pass

class SignalCalculationError(BSIError):
    """Error in signal calculation"""
    pass

class TradingError(BSIError):
    """Error related to trading operations"""
    pass

class ConfigurationError(BSIError):
    """Error in configuration"""
    pass

def retry_on_exception(max_retries: int = 3, 
                      delay: float = 1.0,
                      exceptions: tuple = (Exception,)):
    """
    Decorator to retry function calls on specific exceptions
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                                     f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

def safe_division(numerator: float, denominator: float, 
                 default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default value on division by zero
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        default: Default value to return if division by zero
        
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            logger.warning(f"Division by zero: {numerator} / {denominator}, returning {default}")
            return default
        return numerator / denominator
    except (TypeError, ValueError) as e:
        logger.error(f"Error in division: {str(e)}, returning {default}")
        return default

def validate_percentage(value: float, name: str = "value") -> float:
    """
    Validate that a value is a valid percentage (0-1)
    
    Args:
        value: Value to validate
        name: Name of the value for error messages
        
    Returns:
        Validated value
        
    Raises:
        ValueError: If value is not between 0 and 1
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number, got {type(value)}")
    
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")
    
    return float(value)

def validate_positive_number(value: float, name: str = "value") -> float:
    """
    Validate that a value is a positive number
    
    Args:
        value: Value to validate
        name: Name of the value for error messages
        
    Returns:
        Validated value
        
    Raises:
        ValueError: If value is not positive
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number, got {type(value)}")
    
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    
    return float(value)

class ErrorTracker:
    """Track and analyze errors in the BSI system"""
    
    def __init__(self):
        self.errors = []
        self.error_counts = {}
    
    def record_error(self, error: Exception, context: str = "", 
                    component: str = "unknown"):
        """
        Record an error for tracking and analysis
        
        Args:
            error: The exception that occurred
            context: Additional context about when/where the error occurred
            component: System component where error occurred
        """
        error_record = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context,
            'component': component
        }
        
        self.errors.append(error_record)
        
        # Update error counts
        error_key = f"{component}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        logger.error(f"Error recorded - {error_key}: {str(error)} (Context: {context})")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of errors
        
        Returns:
            Dictionary with error statistics
        """
        if not self.errors:
            return {'total_errors': 0, 'error_types': {}, 'recent_errors': []}
        
        recent_errors = self.errors[-10:]  # Last 10 errors
        
        return {
            'total_errors': len(self.errors),
            'error_types': self.error_counts.copy(),
            'recent_errors': [
                {
                    'timestamp': err['timestamp'].isoformat(),
                    'type': err['error_type'],
                    'message': err['message'],
                    'component': err['component']
                }
                for err in recent_errors
            ]
        }
    
    def clear_errors(self):
        """Clear all recorded errors"""
        self.errors.clear()
        self.error_counts.clear()
        logger.info("Error tracking cleared")

# Global error tracker instance
error_tracker = ErrorTracker()

def handle_api_error(func: Callable) -> Callable:
    """
    Decorator to handle API-related errors consistently
    
    Wraps API calls and converts various error types to appropriate BSI exceptions
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Convert common errors to BSI-specific exceptions
            error_message = str(e).lower()
            
            if any(keyword in error_message for keyword in ['timeout', 'connection', 'network']):
                raise DataProviderError(f"Network error in {func.__name__}: {str(e)}")
            elif any(keyword in error_message for keyword in ['unauthorized', 'forbidden', 'api key']):
                raise DataProviderError(f"Authentication error in {func.__name__}: {str(e)}")
            elif any(keyword in error_message for keyword in ['rate limit', 'too many requests']):
                raise DataProviderError(f"Rate limit error in {func.__name__}: {str(e)}")
            else:
                # Record the error and re-raise as DataProviderError
                error_tracker.record_error(e, func.__name__, 'data_provider')
                raise DataProviderError(f"API error in {func.__name__}: {str(e)}")
    
    return wrapper