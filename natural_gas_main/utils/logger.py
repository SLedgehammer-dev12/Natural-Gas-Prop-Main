"""
Logging configuration and utilities.

Centralizes logging setup for the application.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from natural_gas_main.config.settings import config


def setup_logging(
    log_file: Optional[str] = None,
    level: Optional[str] = None,
    encoding: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """
    Configure application logging with rotation support.
    
    Args:
        log_file: Path to log file (default: from config)
        level: Logging level (default: from config)
        encoding: File encoding (default: from config)
        max_bytes: Maximum size per log file (default: 10 MB)
        backup_count: Number of rotated backup files (default: 3)
        
    Examples:
        >>> setup_logging()  # Uses defaults from config
        >>> setup_logging(level="DEBUG")  # Override level
        >>> setup_logging(max_bytes=5*1024*1024, backup_count=5)
    """
    # Use config defaults if not specified
    log_file = log_file or config.LOG_FILE
    level = level or config.LOG_LEVEL
    encoding = encoding or config.LOG_ENCODING
    
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create rotating file handler
    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=encoding,
    )
    handler.setLevel(numeric_level)
    handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    # Remove any existing handlers
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Log initialization
    logging.info("=" * 60)
    logging.info("Natural Gas Prop Main başlatıldı")
    logging.info(f"Log seviyesi: {level}")
    logging.info(f"Log rotasyonu: {max_bytes} bayt, {backup_count} yedek")
    logging.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Configured logger instance
        
    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Calculation started")
    """
    return logging.getLogger(name)
