from multiprocessing import Manager
import time
import os
import multiprocessing

from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

# possibili elementi in shared_dict:
# {
#     "manager": pid,
#     "django": pid,
#     0...15: {win_info per comunicazione con finestre},
#     "window_p_{0...15}": pid finestre
#     "reset": booleano
# }

# implementare exit con errore, handlarlo e testare funzionamento con monitor

class ProcessManager:
    pid = None
    p = None
    shared_dict = None
    _instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if ProcessManager._instance is None:
            logger.info("ProcessManager instance is None")
        return ProcessManager._instance

    @staticmethod
    def deleteInstance():
        ProcessManager.pid = None
        ProcessManager.p = None
        ProcessManager.shared_dict = None
        
    @staticmethod
    def updateInstance():
        ProcessManager.shared_dict = None
        ProcessManager.pid = None
        ProcessManager.p = None
        ProcessManager()
    
    def __init__(self, shared_dict, pid, p):
        """ Private constructor for the singleton pattern. """
        if ProcessManager._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.shared_dict = shared_dict
            self.pid = pid
            self.p = p
            ProcessManager._instance = self
            logger.debug(f"PM Process PID: {self.pid}")
    
    def insertNewWindow(window_id, stream='', zoom=1, size_x=1920, size_y=1080, coord_x=0, coord_y=0):
        ProcessManager._instance.shared_dict[window_id] = {"stream": stream, "zoom": zoom, "size_x": size_x, "size_y": size_y, "coord_x":coord_x, "coord_y":coord_y}