import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(log_level="DEBUG"):
    """
    Configure general and detection logging with file rotation.
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    Returns:
        logger, detections_logger
    """
    # Map string log levels to logging module levels
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # Validate and set log level
    log_level = log_level.upper()
    if log_level not in log_level_map:
        log_level = "DEBUG"  # Default to DEBUG if invalid
        logging.getLogger(__name__).warning(f"Invalid log level {log_level}. Using DEBUG instead.")
    
    # Configure general logging
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level_map[log_level])
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'app.log', maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.handlers.clear()  # Clear existing handlers to prevent duplicates
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Configure detection logging
    detections_logger = logging.getLogger('detections')
    detections_logger.setLevel(logging.INFO)  # Detection logger remains at INFO
    
    # Detection file handler with rotation
    detections_handler = RotatingFileHandler(
        'detections.log', maxBytes=10*1024*1024, backupCount=5
    )
    detections_handler.setFormatter(formatter)
    
    # Clear existing handlers and add new one
    detections_logger.handlers.clear()
    detections_logger.addHandler(detections_handler)
    
    logger.info(f"Logging configured successfully with level {log_level}")
    return logger, detections_logger