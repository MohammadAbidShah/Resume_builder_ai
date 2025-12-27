"""Logging utilities for Resume Builder AI."""
import logging
import os
from datetime import datetime
from config.settings import LOG_LEVEL, LOG_DIR

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = os.path.join(LOG_DIR, f"resume_builder_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger

# Global logger
logger = setup_logger("ResumeBuilder")

__all__ = ["logger", "setup_logger"]
