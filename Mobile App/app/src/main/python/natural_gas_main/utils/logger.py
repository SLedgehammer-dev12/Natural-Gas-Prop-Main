"""
Logging configuration and utilities.

Centralizes logging setup for the application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from natural_gas_main.config.settings import config


def _resolve_log_path(log_file: str) -> Path:
    """Resolve log file path to a writable absolute location.

    Relative paths are resolved against ~/.local/state/NaturalGasProp/
    on Linux/macOS, or %LOCALAPPDATA%/NaturalGasProp/ on Windows.
    """
    if os.path.isabs(log_file):
        return Path(log_file)

    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif os.environ.get("XDG_STATE_HOME"):
        base = Path(os.environ["XDG_STATE_HOME"])
    else:
        base = Path.home() / ".local" / "state"

    log_dir = base / "NaturalGasProp"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / log_file


def setup_logging(
    log_file: Optional[str] = None,
    level: Optional[str] = None,
    encoding: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """Configure application logging with rotation support.

    If the log file cannot be created (e.g. read-only filesystem),
    falls back to a temporary directory or console-only logging.
    """
    log_file = log_file or config.LOG_FILE
    level = level or config.LOG_LEVEL
    encoding = encoding or config.LOG_ENCODING

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = None
    resolved = _resolve_log_path(log_file)

    # Try the resolved path
    try:
        handler = RotatingFileHandler(
            filename=str(resolved),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
        )
    except OSError:
        pass

    # Fallback: try temp directory
    if handler is None:
        import tempfile
        try:
            fallback = Path(tempfile.gettempdir()) / log_file
            handler = RotatingFileHandler(
                filename=str(fallback),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=encoding,
            )
        except OSError:
            pass

    # Last resort: log to stderr only
    if handler is None:
        handler = logging.StreamHandler()

    handler.setLevel(numeric_level)
    handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logging.info("=" * 60)
    logging.info("Natural Gas Prop Main başlatıldı")
    logging.info(f"Log seviyesi: {level}")
    logging.info(f"Log dosyasi: {getattr(handler, 'baseFilename', 'stderr')}")
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
