"""
Logging utilities for semgrep_pov_assistant.

This module provides comprehensive logging functionality with colored output,
file logging, and structured logging for the application.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for cross-platform colored output
colorama.init()

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log messages.
    
    Colors are used to make different log levels easily distinguishable:
    - DEBUG: Blue
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red with background
    """
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }
    
    def format(self, record):
        # Add color to the level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        
        return super().format(record)

def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    config: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    Set up the application logger with colored output and file logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console_output: Whether to output to console
        config: Configuration dictionary for additional settings
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('semgrep_pov_assistant')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Log configuration information
    if config:
        logger.info("Application Configuration:")
        logger.info(f"  App Name: {config.get('app', {}).get('name', 'Unknown')}")
        logger.info(f"  App Version: {config.get('app', {}).get('version', 'Unknown')}")
        logger.info(f"  Debug Mode: {config.get('app', {}).get('debug', False)}")
        logger.info(f"  Claude Model: {config.get('claude', {}).get('model', 'Unknown')}")
        logger.info(f"  Max Tokens: {config.get('claude', {}).get('max_tokens', 'Unknown')}")
        logger.info(f"  Temperature: {config.get('claude', {}).get('temperature', 'Unknown')}")
    
    return logger

def get_logger(name: str = 'semgrep_pov_assistant') -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_info(message: str, logger: Optional[logging.Logger] = None):
    """Log an info message."""
    if logger is None:
        logger = get_logger()
    logger.info(message)

def log_error(message: str, logger: Optional[logging.Logger] = None):
    """Log an error message."""
    if logger is None:
        logger = get_logger()
    logger.error(message)

def log_warning(message: str, logger: Optional[logging.Logger] = None):
    """Log a warning message."""
    if logger is None:
        logger = get_logger()
    logger.warning(message)

def log_debug(message: str, logger: Optional[logging.Logger] = None):
    """Log a debug message."""
    if logger is None:
        logger = get_logger()
    logger.debug(message)

def log_critical(message: str, logger: Optional[logging.Logger] = None):
    """Log a critical message."""
    if logger is None:
        logger = get_logger()
    logger.critical(message)

def log_exception(message: str, exception: Exception, logger: Optional[logging.Logger] = None):
    """Log an exception with message."""
    if logger is None:
        logger = get_logger()
    logger.exception(f"{message}: {exception}")

def log_performance(operation: str, duration: float, logger: Optional[logging.Logger] = None):
    """Log performance metrics."""
    if logger is None:
        logger = get_logger()
    logger.info(f"Performance: {operation} completed in {duration:.2f} seconds")

def log_api_usage(api_name: str, tokens_used: int, cost_estimate: float, logger: Optional[logging.Logger] = None):
    """Log API usage statistics."""
    if logger is None:
        logger = get_logger()
    logger.info(f"API Usage: {api_name} - Tokens: {tokens_used}, Estimated Cost: ${cost_estimate:.4f}")

def log_file_processing(filename: str, status: str, details: str = "", logger: Optional[logging.Logger] = None):
    """Log file processing status."""
    if logger is None:
        logger = get_logger()
    message = f"File Processing: {filename} - {status}"
    if details:
        message += f" ({details})"
    logger.info(message)

def log_configuration_loaded(config_file: str, logger: Optional[logging.Logger] = None):
    """Log configuration file loading."""
    if logger is None:
        logger = get_logger()
    logger.info(f"Configuration loaded from: {config_file}")

def log_environment_check(env_vars: Dict[str, bool], logger: Optional[logging.Logger] = None):
    """Log environment variable check results."""
    if logger is None:
        logger = get_logger()
    
    logger.info("Environment Variables Check:")
    for var, present in env_vars.items():
        status = "✅ Present" if present else "❌ Missing"
        logger.info(f"  {var}: {status}")

def log_startup_info(config: Dict[str, Any], logger: Optional[logging.Logger] = None):
    """Log startup information."""
    if logger is None:
        logger = get_logger()
    
    logger.info("=" * 60)
    logger.info("🚀 SEMGREP POV ASSISTANT STARTING")
    logger.info("=" * 60)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    
    if config:
        logger.info("Configuration:")
        logger.info(f"  App Name: {config.get('app', {}).get('name', 'Unknown')}")
        logger.info(f"  App Version: {config.get('app', {}).get('version', 'Unknown')}")
        logger.info(f"  Debug Mode: {config.get('app', {}).get('debug', False)}")
        logger.info(f"  Claude Model: {config.get('claude', {}).get('model', 'Unknown')}")
        logger.info(f"  Max Tokens: {config.get('claude', {}).get('max_tokens', 'Unknown')}")
        logger.info(f"  Temperature: {config.get('claude', {}).get('temperature', 'Unknown')}")

def log_shutdown_info(logger: Optional[logging.Logger] = None):
    """Log shutdown information."""
    if logger is None:
        logger = get_logger()
    
    logger.info("=" * 60)
    logger.info("🛑 SEMGREP POV ASSISTANT SHUTTING DOWN")
    logger.info("=" * 60)
    logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def log_error_with_context(error: Exception, context: str = "", logger: Optional[logging.Logger] = None):
    """Log an error with additional context."""
    if logger is None:
        logger = get_logger()
    
    message = f"Error in {context}: {error}" if context else str(error)
    logger.error(message, exc_info=True)

def log_success_with_metrics(operation: str, metrics: Dict[str, Any], logger: Optional[logging.Logger] = None):
    """Log successful operation with metrics."""
    if logger is None:
        logger = get_logger()
    
    logger.info(f"✅ {operation} completed successfully")
    for key, value in metrics.items():
        logger.info(f"  {key}: {value}")

def log_progress(current: int, total: int, operation: str, logger: Optional[logging.Logger] = None):
    """Log progress for long-running operations."""
    if logger is None:
        logger = get_logger()
    
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"Progress: {operation} - {current}/{total} ({percentage:.1f}%)")

# Convenience functions for common logging patterns
def log_api_request(api_name: str, endpoint: str, status: str, logger: Optional[logging.Logger] = None):
    """Log API request details."""
    if logger is None:
        logger = get_logger()
    logger.debug(f"API Request: {api_name} - {endpoint} - Status: {status}")

def log_file_operation(operation: str, filepath: str, success: bool, logger: Optional[logging.Logger] = None):
    """Log file operation results."""
    if logger is None:
        logger = get_logger()
    
    status = "✅ Success" if success else "❌ Failed"
    logger.info(f"File {operation}: {filepath} - {status}")

def log_processing_summary(total_files: int, successful: int, failed: int, logger: Optional[logging.Logger] = None):
    """Log processing summary."""
    if logger is None:
        logger = get_logger()
    
    logger.info("=" * 40)
    logger.info("📊 PROCESSING SUMMARY")
    logger.info("=" * 40)
    logger.info(f"Total Files: {total_files}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(successful/total_files)*100:.1f}%" if total_files > 0 else "N/A")
    logger.info("=" * 40) 