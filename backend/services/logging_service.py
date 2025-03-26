import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.settings import settings

logger = logging.getLogger("visualize-it")

class LoggingService:
    """
    Service for handling logging functionality
    """
    def __init__(self):
        self.server_log_file = settings.SERVER_LOG_FILE
        self.client_log_file = settings.CLIENT_LOG_FILE
        
        # Ensure log files exist
        for log_file in [self.server_log_file, self.client_log_file]:
            if not os.path.exists(log_file):
                with open(log_file, 'w') as f:
                    f.write(f"# Log file created at {datetime.now().isoformat()}\n")
        
        logger.info(f"LoggingService initialized with server_log_file={self.server_log_file}, client_log_file={self.client_log_file}")
    
    def get_server_logs(self, max_lines: int = 1000) -> List[str]:
        """
        Get the server logs
        """
        return self._get_logs_from_file(self.server_log_file, max_lines)
    
    def get_client_logs(self, max_lines: int = 1000) -> List[str]:
        """
        Get the client logs
        """
        return self._get_logs_from_file(self.client_log_file, max_lines)
    
    def clear_server_logs(self) -> bool:
        """
        Clear the server logs
        """
        return self._clear_log_file(self.server_log_file)
    
    def clear_client_logs(self) -> bool:
        """
        Clear the client logs
        """
        return self._clear_log_file(self.client_log_file)
    
    def log_client_message(self, log_data: Dict[str, Any]) -> bool:
        """
        Log a message from the client
        """
        try:
            level = log_data.get("level", "info").lower()
            message = log_data.get("message", "")
            timestamp = log_data.get("timestamp", datetime.now().isoformat())
            source = log_data.get("source", "client")
            
            log_line = f"{timestamp} - {source} - {level.upper()} - {message}\n"
            
            with open(self.client_log_file, 'a') as f:
                f.write(log_line)
            
            return True
        except Exception as e:
            logger.error(f"Error logging client message: {str(e)}")
            return False
    
    def _get_logs_from_file(self, file_path: str, max_lines: int = 1000) -> List[str]:
        """
        Get logs from a file
        """
        try:
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, 'r') as f:
                # Read the last max_lines lines
                lines = f.readlines()
                return lines[-max_lines:] if len(lines) > max_lines else lines
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {str(e)}")
            return []
    
    def _clear_log_file(self, file_path: str) -> bool:
        """
        Clear a log file
        """
        try:
            with open(file_path, 'w') as f:
                f.write(f"# Log file cleared at {datetime.now().isoformat()}\n")
            return True
        except Exception as e:
            logger.error(f"Error clearing log file {file_path}: {str(e)}")
            return False
