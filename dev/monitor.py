
import time
import sys
import os
import psutil
from django.utils import timezone
from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, freeze_support, Manager
from config import MAX_WINDOWS

# Constants
PROCESS_CHECK_INTERVAL = 1  # seconds

# Set up paths
if getattr(sys, 'frozen', False):
    # Running as a bundled executable
    BASE_DIR = sys._MEIPASS
else:
    # Running as a script
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Add Django project to sys.path
    sys.path.append(os.path.join(BASE_DIR, 'django', 'anywall'))

# Setup logging
from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

current_pid = os.getpid()

# Initialize Django
import django
from django.test.runner import DiscoverRunner

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anywall.settings")
test_runner = DiscoverRunner()
django.setup(test_runner)
django.setup()

# Import Django models
from anywall_app.models import Api_calls as django_api_calls
from anywall_app.models import VISUALIZZAZIONE
from django.db.utils import ProgrammingError
from django.db import OperationalError

# Global variables
processes = {}
reset_windows = False

class ProcessMonitor:
    """Handles monitoring and management of subprocesses."""
    
    @staticmethod
    def start_server():
        """Start the Django server using Daphne."""
        try:
            from daphne.server import Server
            from daphne.endpoints import build_endpoint_description_strings
            from anywall.asgi import application

            if getattr(sys, 'frozen', False):
                asgi_dir = BASE_DIR
            else:
                # Running as a script
                asgi_dir = os.path.join(BASE_DIR, 'django', 'anywall')

            sys.path.append(asgi_dir)
            os.chdir(asgi_dir)

            # Start the Daphne server programmatically
            endpoints = build_endpoint_description_strings(host="0.0.0.0", port="8000")
            server = Server(application=application, endpoints=endpoints)
            server.run()
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            sys.exit(0)

    @staticmethod
    def run_django_server():
        """Start Django server in a separate process."""
        global processes
        p = Process(target=ProcessMonitor.start_server)
        p.start()
        processes['server_process'] = p
        logger.debug("Django server process started")

    @staticmethod
    def start_manager(init, shared_dict):
        """Start the manager process."""
        import manager
        try:
            manager.main(init, shared_dict)
        except Exception as e:
            logger.error(f"Manager process failed: {e}")
            sys.exit(0)

    @staticmethod
    def run_manager(init):
        """Start manager in a separate process."""
        global processes, pm
        logger.debug(f"Starting manager with init: {init}")
        p = Process(target=ProcessMonitor.start_manager, args=(init, pm.shared_dict))
        p.start()
        processes['manager_process'] = p
        logger.debug("Manager process started")

    @staticmethod
    def check_process_running(p, pm):
        """Check if a process is still running."""
        try:
            if not p.is_alive():
                raise psutil.NoSuchProcess(p.pid)

            # Use psutil to check if the process is still running
            process = psutil.Process(p.pid)
            if not process.is_running():
                raise psutil.NoSuchProcess(p.pid)

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Process {p.pid} error: {e}")
            
            # Handle view switching if needed
            if "switchView" in pm.shared_dict:
                window_id = pm.shared_dict.pop("switchView")
                ProcessMonitor.handle_window_switch(pm, window_id)
                return True

            # Clean up the dead process
            p.terminate()
            p.join()
            return False
        else:
            return True

    @staticmethod
    def handle_window_switch(pm, window_id):
        """Handle window view switching."""
        global processes
        
        # Terminate old window process if it exists
        window_key = f"window_p_{window_id}"
        if window_key in processes and processes[window_key]:
            processes[window_key].terminate()
            processes[window_key].join()
            processes[window_key] = None

        # Get window data if it exists
        window_data = None
        if window_key in pm.shared_dict:
            window_data = pm.shared_dict.pop(window_key)

        # Remove any existing data for the window
        if window_id in pm.shared_dict:
            pm.shared_dict.pop(window_id)

        # Create a new window if we have data
        if window_data:
            ProcessMonitor.add_single_window(pm, window_key, window_data)

    @staticmethod
    def restart_process_manager(pm, force_restart=False):
        """Restart the process manager if needed."""
        global processes
        
        if force_restart or processes['PM_process'] is None or not ProcessMonitor.check_process_running(processes['PM_process'], pm):
            logger.info("Process Manager down, restarting...")
            processes['PM_process'] = None
            pm.deleteInstance()
            pm = ProcessManager.getInstance()
            processes['PM_process'] = pm.p
            return True
        return False

    @staticmethod
    def restart_server():
        """Restart the Django server if needed."""
        global processes
        
        if processes['server_process'] is None or not ProcessMonitor.check_process_running(processes['server_process'], pm):
            logger.info("Restarting Django server...")
            processes['server_process'] = None
            ProcessMonitor.run_django_server()

    @staticmethod
    def restart_manager(init='noinit'):
        """Restart the manager if needed."""
        global processes
        
        if processes['manager_process'] is None or not ProcessMonitor.check_process_running(processes['manager_process'], pm):
            logger.info("Restarting manager...")
            processes['manager_process'] = None
            ProcessMonitor.run_manager(init)

    @staticmethod
    def restart_windows(force_restart=False):
        """Restart all window processes."""
        global reset_windows, processes
        
        # Filter for active window processes
        window_processes = {key: value for key, value in processes.items() 
                           if key.startswith('window_p_') and value is not None}

        if force_restart or len(window_processes) < MAX_WINDOWS:
            # First try to gracefully close windows
            for i in range(len(window_processes)):
                pm.shared_dict[i] = {"close": True}

            # Then terminate any remaining processes
            for key, p in window_processes.items():
                p.terminate()
                p.join()

            # Clear the shared dictionary
            pm.shared_dict.clear()

            # Reset window process list
            for i in range(16):
                processes[f"window_p_{i}"] = None

            reset_windows = True
            
            # Restart manager to initialize windows
            if processes['manager_process'] is not None:
                os.kill(processes['manager_process'].pid, 15)
                
            ProcessMonitor.restart_manager('init_windows')
            return True
        return False

    @staticmethod
    def kill_manager_and_windows():
        """Kill manager and all window processes."""
        global processes
        
        if processes['manager_process'] is not None:
            processes['manager_process'].terminate()
            processes['manager_process'].join()
            processes['manager_process'] = None

    @staticmethod
    def total_restart(pm):
        """Restart all processes."""
        ProcessMonitor.restart_process_manager(pm=pm, force_restart=True)
        ProcessMonitor.kill_manager_and_windows()
        ProcessMonitor.restart_windows(force_restart=True)
        ProcessMonitor.restart_server()
        ProcessMonitor.restart_manager()

    @staticmethod
    def restart_processes():
        """Restart processes as needed."""
        global pm
        
        logger.debug("Checking and restarting processes as needed")

        if ProcessMonitor.restart_process_manager(pm):
            ProcessMonitor.kill_manager_and_windows()
            ProcessMonitor.restart_windows(force_restart=True)
            ProcessMonitor.restart_server()
            return

        ProcessMonitor.restart_server()

        if ProcessMonitor.restart_windows():
            return

        ProcessMonitor.restart_manager()
        pm.shared_dict.clear()

    @staticmethod
    def add_single_window(pm, el, data):
        """Create a single window process."""
        global processes
        
        p = Process(target=ProcessMonitor.create_window, args=(pm.shared_dict,), kwargs=data)
        p.start()
        processes[el] = p
        logger.debug(f"Started window process {el} with PID {p.pid}")

    @staticmethod
    def start_windows():
        """Start all window processes."""
        global processes, reset_windows, pm
        
        try:
            if ProcessMonitor.check_process_running(processes['PM_process'], pm):
                logger.debug(f"Checking if windows are ready: {'ready' in pm.shared_dict}")
                
                # Wait for windows to be ready
                while "ready" not in pm.shared_dict:
                    logger.debug("Waiting for windows to be ready")
                    if not ProcessMonitor.check_process_running(processes["manager_process"], pm):
                        logger.debug("Manager process not running, abandoning window start")
                        processes["manager_process"] = None
                        reset_windows = False
                        return
                    time.sleep(0.5)

                # Remove ready flag
                pm.shared_dict.pop("ready")

                # Start all window processes that are ready
                for el in list(pm.shared_dict.keys()):
                    if isinstance(el, str) and el.startswith("window_p_"):
                        data = pm.shared_dict.pop(el)
                        ProcessMonitor.add_single_window(pm, el, data)
                
                reset_windows = False
                logger.debug(f"All windows started: {processes}")
                return

            raise BrokenPipeError("Process manager not running")
            
        except BrokenPipeError:
            pm.deleteInstance()
            processes['PM_process'] = None
            reset_windows = False

    @staticmethod
    def create_window(shared_dict, **kwargs):
        """Create a window instance."""
        from window_handler import WindowHandler
        from multiprocessing import current_process
        from process_manager import ProcessManager
        
        process_manager = ProcessManager(shared_dict=shared_dict, pid=os.getpid(), p=current_process())
        visualizzazione = kwargs.get("visualizzazione")

        try:
            # Different initialization based on visualization type
            if visualizzazione == VISUALIZZAZIONE['BROWSERWINDOW'] or visualizzazione == VISUALIZZAZIONE['DESKTOP']:
                app = QApplication(sys.argv)
                window = WindowHandler(**kwargs, process_manager=process_manager)
                sys.exit(app.exec_())
            else:
                WindowHandler(**kwargs, process_manager=process_manager)

            logger.debug(f"Window created with visualization {visualizzazione}")
            
        except Exception as e:
            logger.error(f"Failed to create window: {e}")
            sys.exit(1)

def execute():
    """Main execution function for the monitor."""
    global reset_windows, processes, pm
    
    logger.info("Application started")
    reset_windows = True
    logger.debug(f"Parent Process PID: {os.getpid()}")

    # Start initial processes
    ProcessMonitor.run_django_server()
    ProcessMonitor.run_manager('init_windows')

    from utils import getReceivedApiCalls
    last_api_call_dt_creation = timezone.localtime(timezone.now())

    try:
        while True:
            # Start windows if needed
            if reset_windows:
                logger.info("Starting windows after reset")
                ProcessMonitor.start_windows()

            # Check for API calls
            gotReset = False
            count_read_api = 0

            while count_read_api < 5:
                api_calls = []
                try:
                    api_calls = getReceivedApiCalls(last_api_call_dt_creation)
                except OperationalError as e:
                    logger.error(f"Database connection error when getting API calls: {e}")
                except django_api_calls.DoesNotExist as e:
                    logger.error(f"API calls not found: {e}")
                    time.sleep(5)

                # Process API calls
                while api_calls:
                    current_api_call = api_calls.pop(0)
                    if current_api_call.name == 'reset':
                        logger.info("Reset requested, restarting windows...")
                        ProcessMonitor.restart_windows(force_restart=True)
                        last_api_call_dt_creation = timezone.localtime(current_api_call.created)
                        gotReset = True
                        break
                    last_api_call_dt_creation = timezone.localtime(current_api_call.created)
                
                if gotReset:
                    break

                count_read_api += 1
                time.sleep(PROCESS_CHECK_INTERVAL)
                
            if gotReset:
                continue

            # Check all processes
            toRestart = False
            try:
                for key, el in list(processes.items()):
                    if el is None or not ProcessMonitor.check_process_running(el, pm):
                        processes[key] = None
                        if el is None:
                            logger.debug(f"Process {key} is null")
                        else:
                            logger.debug(f"Process {key} is dead")
                        toRestart = True
            except RuntimeError as e:
                logger.error(f"Error checking processes: {e}")
                continue

            # Restart processes if needed
            if toRestart:
                ProcessMonitor.restart_processes()

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
        logger.info("Cleaning up processes...")
        for key, process in processes.items():
            if process is not None:
                logger.info(f"Terminating process {key} with PID {process.pid}")
                process.terminate()
                process.join()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    from multiprocessing import Manager
    from process_manager import ProcessManager

    freeze_support()
    logger.debug(f"Monitor current process PID is: {current_pid}")
    
    # Create shared manager
    manager = Manager()
    shared_dict = manager.dict()
    
    # Create process manager
    global pm
    pm = ProcessManager(shared_dict, manager._process.pid, manager._process)
    processes['PM_process'] = pm.p

    # Start execution
    execute()
