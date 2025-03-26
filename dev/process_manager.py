
import os
import logging
import multiprocessing
from multiprocessing import Manager
from threading import Lock
from multiprocessing.managers import BaseManager

from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

class ProcessManager:
    """
    Manages inter-process communication and shared data between window processes.
    
    This class provides a shared dictionary for processes to exchange information 
    and coordinates updates between the main manager process and window processes.
    """
    # Class variable for singleton pattern
    _instance = None
    _lock = Lock()
    
    def __new__(cls, shared_dict=None, pid=None, p=None):
        """Implement singleton pattern"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProcessManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
            
    def __init__(self, shared_dict=None, pid=None, p=None):
        """Initialize the process manager"""
        if self._initialized:
            return
            
        self.manager = None
        self.shared_dict = None
        self.pid = pid
        self.p = p
        
        # Initialize with provided shared dict or create new one
        if shared_dict is not None:
            self.shared_dict = shared_dict
        else:
            self.getInstance()
            
        self._initialized = True
            
    def getInstance(self):
        """Get or create instance of shared manager"""
        if self.manager is None:
            try:
                # Create a new manager
                self.manager = Manager()
                self.shared_dict = self.manager.dict()
                logger.info("Created new shared manager instance")
                return self.shared_dict
            except Exception as e:
                logger.error(f"Error creating manager instance: {e}")
                raise
        return self.shared_dict
    
    def deleteInstance(self):
        """Clean up the manager instance"""
        if self.manager is not None:
            try:
                logger.debug("Shutting down manager")
                self.manager.shutdown()
                self.manager = None
                self.shared_dict = None
                logger.info("Manager instance deleted")
            except Exception as e:
                logger.error(f"Error deleting manager instance: {e}")
    
    def restart(self):
        """Restart the manager"""
        self.deleteInstance()
        return self.getInstance()
    
    def is_alive(self):
        """Check if the process manager is alive"""
        return self.manager is not None and self.shared_dict is not None
    
    def add_window_data(self, window_id, data_dict):
        """Add or update window data in the shared dictionary"""
        try:
            self.shared_dict[window_id] = data_dict
            return True
        except Exception as e:
            logger.error(f"Error adding window data: {e}")
            return False
    
    def get_window_data(self, window_id):
        """Get window data from the shared dictionary"""
        try:
            return self.shared_dict.get(window_id, None)
        except Exception as e:
            logger.error(f"Error getting window data: {e}")
            return None
    
    def remove_window_data(self, window_id):
        """Remove window data from the shared dictionary"""
        try:
            if window_id in self.shared_dict:
                del self.shared_dict[window_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing window data: {e}")
            return False
    
    def clear_all(self):
        """Clear all data from the shared dictionary"""
        try:
            self.shared_dict.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing shared dictionary: {e}")
            return False
    
    def __del__(self):
        """Clean up resources when object is deleted"""
        try:
            self.deleteInstance()
        except Exception as e:
            logger.error(f"Error during process manager deletion: {e}")
