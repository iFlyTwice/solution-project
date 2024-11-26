"""
Centralized logging configuration for the application.
Provides consistent logging across all modules with configurable output formats and destinations.
"""

import logging
import os
from datetime import datetime
from typing import Optional

class AppLogger:
    _instance: Optional['AppLogger'] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not AppLogger._initialized:
            self._setup_logging()
            AppLogger._initialized = True

    def _setup_logging(self):
        # Create logs directory if it doesn't exist
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Generate log filename with timestamp
        log_filename = os.path.join(logs_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        # Create logger instance
        self.logger = logging.getLogger('SolutionGUI')
        self.logger.setLevel(logging.DEBUG)

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Get the singleton logger instance.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        if cls._instance is None:
            cls()
        return cls._instance.logger

# Convenience function to get logger
def get_logger() -> logging.Logger:
    """
    Convenience function to get the application logger.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return AppLogger.get_logger()
