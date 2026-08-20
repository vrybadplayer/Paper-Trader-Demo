"""
Traceback Sanitizer
Uses stackprinter to produce clean, readable tracebacks for debugging.
"""

import sys
import traceback
from typing import Any, Callable, Optional
import functools

try:
    import stackprinter
    STACKPRINTER_AVAILABLE = True
except ImportError:
    STACKPRINTER_AVAILABLE = False
    stackprinter = None

def setup_traceback_excepthook():
    """
    Set up a custom excepthook that uses stackprinter for better tracebacks.
    Should be called at the start of the application.
    """
    if not STACKPRINTER_AVAILABLE:
        print("Warning: stackprinter not available. Using standard traceback formatting.")
        return
    
    def excepthook(exc_type, exc_value, exc_traceback):
        # Use stackprinter to format the exception
        if STACKPRINTER_AVAILABLE:
            stackprinter.print(
                exc_value,
                style="darkbg2",  # Dark background theme
                line_numbers=True,
                caller=1,  # Skip the excepthook frame
                suppress=[click, rich] if 'click' in sys.modules else [],
                bg=True  # Use background colors if supported
            )
        else:
            # Fallback to standard traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = excepthook

def sanitize_traceback(tb: str) -> str:
    """
    Sanitize a traceback string to remove sensitive information and improve readability.
    
    Args:
        tb: Raw traceback string
        
    Returns:
        Sanitized traceback string
    """
    # Remove file paths that might contain sensitive information
    lines = tb.split('\n')
    sanitized_lines = []
    
    for line in lines:
        # Replace absolute paths with relative ones or just filenames
        if 'File "' in line and '.py"' in line:
            # Extract just the filename
            import os
            if 'File "' in line:
                parts = line.split('File "')
                if len(parts) > 1:
                    filename_part = parts[1].split('"')[0]
                    filename = os.path.basename(filename_part)
                    line = line.replace(filename_part, filename)
        sanitized_lines.append(line)
    
    return '\n'.join(sanitized_lines)

def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function safely, catching exceptions and providing sanitized tracebacks.
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Function result if successful, None if exception occurred
        
    Side effect:
        Prints sanitized traceback if exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if STACKPRINTER_AVAILABLE:
            print("Exception occurred:")
            stackprinter.print(e, style="darkbg2", line_numbers=True, caller=1)
        else:
            print("Exception occurred:")
            traceback.print_exc()
        return None

def traceback_sanitizer_decorator(max_args_length: int = 100):
    """
    Decorator that sanitizes tracebacks and limits argument logging.
    
    Args:
        max_args_length: Maximum length to display for each argument
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Sanitize arguments for logging
                safe_args = []
                for arg in args:
                    if isinstance(arg, str) and len(arg) > max_args_length:
                        safe_args.append(arg[:max_args_length] + "... [TRUNCATED]")
                    else:
                        safe_args.append(arg)
                
                safe_kwargs = {}
                for k, v in kwargs.items():
                    if isinstance(v, str) and len(v) > max_args_length:
                        safe_kwargs[k] = v[:max_args_length] + "... [TRUNCATED]"
                    else:
                        safe_kwargs[k] = v
                
                # Log the error with sanitized information
                error_msg = f"Exception in {func.__name__} with args={safe_args}, kwargs={safe_kwargs}"
                print(error_msg)
                
                # Print sanitized traceback
                if STACKPRINTER_AVAILABLE:
                    print("Traceback:")
                    stackprinter.print(e, style="darkbg2", line_numbers=True, caller=1)
                else:
                    print("Traceback:")
                    traceback.print_exc()
                
                # Re-raise the exception if you want it to propagate
                # raise
                return None
        return wrapper
    return decorator

# Example usage (for testing)
if __name__ == "__main__":
    # Set up the excepthook
    setup_traceback_excepthook()
    
    # Test the sanitize_traceback function
    try:
        x = 1 / 0
    except Exception as e:
        tb = traceback.format_exc()
        print("Original traceback:")
        print(tb)
        print("\nSanitized traceback:")
        print(sanitize_traceback(tb))
    
    # Test the decorator
    @traceback_sanitizer_decorator()
    def problematic_function(x, y, z="default"):
        return x / y  # Will cause ZeroDivisionError
    
    print("\nTesting decorator:")
    result = problematic_function(10, 0, z="test")
    print(f"Result: {result}")
    
    # Test safe_execute
    print("\nTesting safe_execute:")
    result = safe_execute(problematic_function, 10, 0)
    print(f"Result: {result}")