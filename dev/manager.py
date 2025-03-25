
import os
import sys
import json
import time
import signal
import requests
from multiprocessing import current_process
from config import API_SERVER_URL
from config import MAX_WINDOWS

from django.db import connection
from django.utils import timezone
from django.db.utils import ProgrammingError
from django.db import OperationalError
from django.core.management import call_command

from anywall_app.logger import setup_logger
from anywall_app.models import Window as django_window
from anywall_app.models import RequestedWindow as django_requested_window
from anywall_app.models import State as django_state
from anywall_app.models import Delta as django_delta
from anywall_app.models import Api_calls as django_api_calls
from anywall_app.models import MODE, IMAGE_SCOPE

import utils as utils
import screen_helper as screen_helper

logger = setup_logger(__name__)

# Initialize environment variables
if 'PYOPENGL_PLATFORM' not in os.environ:
    os.environ['PYOPENGL_PLATFORM'] = "x11"

if 'PYTHONPATH' not in os.environ:
    os.environ['PYTHONPATH'] = ""

# If running a script (not a frozen executable)
if not getattr(sys, 'frozen', False):
    # Add the directory to PYTHONPATH
    os.environ['PYTHONPATH'] += ":" + sys.path[0].replace('\\','/') + "/anywall"
    logger.debug(f"sys path: {sys.path[0]}")
    logger.debug(f"python path: {os.environ['PYTHONPATH']}")


# Global variables
screen = None
server_process = None
shutdown_flag = False


class DatabaseError(Exception):
    """Base exception for database related errors"""
    pass


class ApiError(Exception):
    """Base exception for API related errors"""
    pass


class WindowManager:
    """
    Main window management class that handles window updates, state changes,
    and interactions with the process manager.
    """
    def __init__(self, process_manager):
        self.process_manager = process_manager
        self.screen = None
        self.last_api_call_dt_creation = timezone.localtime(timezone.now())
        self.state_instance = None
        
    def initialize_windows(self):
        """Initialize window list from database"""
        try:
            self.state_instance = django_state.objects.latest('created')
            windows_list = utils.read_windows()
            self.screen = screen_helper.Screen(self.process_manager, self.state_instance, windows_list)
            connection.close()
            return True
        except (OperationalError, ProgrammingError, django_state.DoesNotExist) as e:
            logger.error(f"Error initializing windows: {e}")
            if isinstance(e, (ProgrammingError, django_state.DoesNotExist)):
                self._create_initial_database()
                return self.initialize_windows()
            return False
            
    def _create_initial_database(self):
        """Create initial database structure and mock data"""
        logger.info("Creating initial database structure and mock data")
        try:
            self._make_migrations()
            self._create_mock_data()
            return True
        except Exception as e:
            logger.error(f"Failed to create initial database: {e}")
            return False
    
    def _make_migrations(self):
        """Apply database migrations"""
        try:
            call_command("migrate", "anywall_app")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def _create_mock_data(self):
        """Create mock data for initial setup"""
        # Create and upload 16 mocked window instances
        mocked_windows_list = []
        for i in range(16):
            mocked_windows_list.append(utils.createMockedWindowObject(i))
            utils.createMockedReqWindowObject(i)

        # Create mock state, API call, delta, and backup windows
        utils.createMockedStateObject()
        utils.createMockedApiCallObject()
        utils.createMockedDeltaObject()
        for i in range(MAX_WINDOWS):
            utils.createMockedBackupWindowObject(i)
            
    def fetch_state(self):
        """Fetch the current application state"""
        try:
            self.state_instance = django_state.objects.latest('created')
            
            # Update mode if there are alarm windows
            if self.state_instance.alarm_windows > 0:
                self.state_instance.mode = MODE['ALLARME']
                callAlarmExpired()
            elif self.state_instance.mode == MODE['ALLARME'] and self.state_instance.alarm_windows == 0:
                callAlarmClear()
                
            connection.close()
            return self.state_instance
        except OperationalError as e:
            logger.error(f"Database error when fetching state: {e}")
            raise DatabaseError("Failed to fetch application state") from e
        except django_state.DoesNotExist:
            logger.warning("No state found in database")
            return None
    
    def process_api_calls(self):
        """Process incoming API calls and apply changes"""
        try:
            # Get new API calls
            api_calls = utils.getReceivedApiCalls(self.last_api_call_dt_creation)
            if not api_calls:
                return False
                
            # Process each API call
            for current_api_call in api_calls:
                self._process_single_api_call(current_api_call)
                self.last_api_call_dt_creation = timezone.localtime(current_api_call.created)
                
            return True
        except OperationalError as e:
            logger.error(f"Database error when processing API calls: {e}")
            connection.close()
            raise DatabaseError("Failed to process API calls") from e
    
    def _process_single_api_call(self, current_api_call):
        """Process a single API call and apply relevant changes"""
        try:
            # Read delta changes
            delta_list, split_list = self._read_delta_main(current_api_call)
            
            # Handle image selection for all windows
            if current_api_call.name == "select-image/" and current_api_call.data.get("window_id") is None:
                self._update_general_pictures(current_api_call.data.get("image_scope"))
                return
                
            # Skip if no delta changes
            if not delta_list:
                logger.debug("No delta changes to apply")
                return
                
            # Read state changes if needed
            if delta_list[0].readState:
                state_instance, do_alarm_checks, cont = self._read_state_changes(delta_list)
                if cont:
                    return
                    
            # Apply window-specific changes
            for same_window_list in split_list:
                req_window, new_info = self._collect_window_changes(same_window_list)
                
                if req_window is not None:
                    self._update_render_data(req_window.window_id, new_info)
                    
                    # Handle visualization mode changes
                    if "visualizzazione" in new_info:
                        self._handle_view_mode_change(req_window)
                        
            # Apply delta changes to windows table
            utils.applyDeltaChangesInWindows()
            
        except Exception as e:
            logger.error(f"Error processing API call: {e}")
            raise
    
    def _read_delta_main(self, current_api_call):
        """Read delta changes for an API call"""
        try:
            delta_list = django_delta.objects.filter(call_id=current_api_call.id).order_by('window_id')
            
            if not delta_list:
                logger.debug(f"Empty delta list for API call {current_api_call.id}")
                
            # Group delta objects by window ID
            unique_window_ids = set(obj.window_id for obj in delta_list)
            split_list = [[obj for obj in delta_list if obj.window_id == window_id] for window_id in unique_window_ids]
            
            connection.close()
            return delta_list, split_list
        except OperationalError as e:
            logger.error(f"Database error in read_delta_main: {e}")
            connection.close()
            raise DatabaseError("Failed to read delta changes") from e
    
    def _read_state_changes(self, delta_list):
        """Read state changes from delta list"""
        try:
            state_instance = django_state.objects.latest('created')
            
            # Handle different modes
            do_alarm_checks = False
            continue_flag = False
            
            if state_instance.mode == MODE['ALLARME']:
                logger.info("Read mode: ALLARME")
                do_alarm_checks = True
            elif state_instance.mode == MODE['BROWSER']:
                logger.info("Read mode: BROWSER")
                continue_flag = True
            elif state_instance.mode == MODE['DESKTOP']:
                logger.info("Read mode: DESKTOP")
                continue_flag = True
            elif state_instance.mode == MODE['TELECAMERE']:
                logger.info("Read mode: TELECAMERE")
                
            connection.close()
            return state_instance, do_alarm_checks, continue_flag
        except OperationalError as e:
            logger.error(f"Database error in read_state_changes: {e}")
            connection.close()
            raise DatabaseError("Failed to read state changes") from e
    
    def _collect_window_changes(self, same_window_list):
        """Collect changes for a specific window from delta list"""
        new_info = {}
        req_window = None
        
        try:
            for el in same_window_list:
                if el.window_id == -1:
                    continue
                    
                # Query the window only once for the entire same_window_list
                if req_window is None:
                    req_window = django_requested_window.objects.get(window_id=el.window_id)
                
                # Stream and text changes
                if el.windows_column_name in ["stream", "labelText"]:
                    new_info.update({"stream": req_window.stream, "labelText": req_window.labelText})
                
                # Zoom settings
                if el.windows_column_name == "zoom":
                    new_info.update({"zoom": req_window.zoom})
                if el.windows_column_name == "isZoom":
                    new_info.update({"isZoom": req_window.isZoom})
                
                # UI element visibility
                if el.windows_column_name == "enableLogo":
                    new_info.update({"enableLogo": req_window.enableLogo})
                if el.windows_column_name == "enableAlarmIcon":
                    new_info.update({"enableAlarmIcon": req_window.enableAlarmIcon})
                if el.windows_column_name == "enableWatermark":
                    new_info.update({"enableWatermark": req_window.enableWatermark})
                
                # Image paths
                if el.windows_column_name == "logoPath":
                    new_info.update({"logoPath": req_window.logoPath})
                if el.windows_column_name == "alarmIconPath":
                    new_info.update({"alarmIconPath": req_window.alarmIconPath})
                
                # Position and size
                if el.windows_column_name == "coord_x":
                    new_info.update({"coord_x": req_window.coord_x})
                if el.windows_column_name == "coord_y":
                    new_info.update({"coord_y": req_window.coord_y})
                if el.windows_column_name in ["width", "height"]:
                    new_info.update({"width": req_window.width, "height": req_window.height})
                
                # Window state
                if el.windows_column_name == "isActive":
                    logger.debug(f"Win {el.window_id}: detected isActive")
                    new_info.update({"isActive": req_window.isActive})
                
                # Browser settings
                if el.windows_column_name == "isBrowser":
                    new_info.update({"isBrowser": req_window.isBrowser})
                if el.windows_column_name == "urlBrowser":
                    new_info.update({"urlBrowser": req_window.urlBrowser})
                if el.windows_column_name == "visualizzazione":
                    new_info.update({"visualizzazione": req_window.visualizzazione})
                
                # Alarm settings
                if el.windows_column_name == "isAlarm":
                    logger.debug(f"Received alarm {req_window.isAlarm} for window {req_window.window_id}")
                    new_info.update({"isAlarm": req_window.isAlarm})
                if el.windows_column_name == "timeout":
                    new_info.update({"timeout": timezone.localtime(req_window.timeout)})
                
                # Rolling settings
                if el.windows_column_name == "isRolling":
                    new_info.update({"isRolling": req_window.isRolling})
                if el.windows_column_name == "timerRolling":
                    new_info.update({"timerRolling": req_window.timerRolling})
            
            connection.close()
            return req_window, new_info
        except OperationalError as e:
            logger.error(f"Database error in collect_window_changes: {e}")
            connection.close()
            raise DatabaseError("Failed to collect window changes") from e
    
    def _update_render_data(self, window_id, new_info):
        """Update rendering data for a window"""
        logger.debug(f"Updating window {window_id} with: {new_info}")
        self.process_manager.shared_dict[window_id] = new_info
    
    def _update_general_pictures(self, image_scope):
        """Update pictures for all windows"""
        if image_scope == IMAGE_SCOPE['PLACEHOLDER']:
            update_key = "PLACEHOLDER"
        elif image_scope == IMAGE_SCOPE['WATERMARK']:
            update_key = "WATERMARK"
        else:
            return
            
        logger.debug(f"Updating {update_key} for all windows")
        for i in range(16):
            self.process_manager.shared_dict[i] = {update_key: True}
    
    def _handle_view_mode_change(self, req_window):
        """Handle visualization mode changes"""
        screen_helper.makeProcessWindow(
            self.process_manager, 
            req_window, 
            req_window.width, 
            req_window.height, 
            req_window.coord_x, 
            req_window.coord_y
        )
        self.process_manager.shared_dict["switchView"] = req_window.window_id
    
    def check_alarm_timers(self):
        """Check for expired alarms"""
        if not self.state_instance or self.state_instance.mode != MODE['ALLARME']:
            logger.warning("Must be in ALARM mode to check expired alarms")
            return False
            
        try:
            requested_windows = utils.read_requested_windows()
            alarm_windows = list(filter(lambda window: window.timeout, requested_windows))
            
            expired_alarms = []
            for alarm in alarm_windows:
                if self._is_alarm_expired(alarm.timeout):
                    expired_alarms.append(alarm)
            
            if expired_alarms:
                callAlarmExpired()
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error checking alarm timers: {e}")
            return False
    
    def _is_alarm_expired(self, timeout):
        """Check if an alarm has expired"""
        now = timezone.localtime(timezone.now())
        alarm_time = timezone.localtime(timeout)
        return now > alarm_time


# API Functions
def callAlarmExpired():
    """Call the alarm expired API endpoint"""
    try:
        # Convert the payload to JSON format
        json_payload = json.dumps({"check": True})
        # Define the headers
        headers = {
            'Content-Type': 'application/json',
        }

        # Make the POST request
        response = requests.post(
            API_SERVER_URL + '/api/alarm/expired/', 
            data=json_payload, 
            headers=headers, 
            verify=False,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            logger.debug("Successfully called alarm expired API")
            return data
        else:
            logger.warning(f"Failed to send POST request. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error when calling alarm expired API: {e}")
        return None


def callAlarmClear():
    """Call the alarm clear API endpoint"""
    try:
        # Convert the payload to JSON format
        json_payload = json.dumps({"clear": True})

        # Define the headers
        headers = {
            'Content-Type': 'application/json',
        }

        # Make the POST request
        response = requests.post(
            API_SERVER_URL + '/api/alarm/clear/', 
            data=json_payload, 
            headers=headers, 
            verify=False,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            logger.debug("Successfully called alarm clear API")
            return data
        else:
            logger.warning(f"Failed to send POST request. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error when calling alarm clear API: {e}")
        return None


def kill_all_win_processes():
    """Kill all window processes"""
    global screen
    global server_process
    
    logger.info("Killing all window processes")
    
    # Kill window processes
    for key, p in screen_helper.processes.items():
        try:
            p['process'].terminate()
        except Exception as e:
            logger.error(f"Error terminating process {key}: {e}")
            
    # Wait for processes to end
    for key, p in screen_helper.processes.items():
        try:
            p['process'].join(timeout=2)
        except Exception as e:
            logger.error(f"Error joining process {key}: {e}")
            
    screen_helper.processes.clear()
    
    if screen:
        del screen
        
    # Kill server process if it exists
    if server_process:
        try:
            server_process.terminate()
            server_process.join(timeout=2)
        except Exception as e:
            logger.error(f"Error terminating server process: {e}")


def signal_handler(sig, frame):
    """Handle termination signals"""
    global shutdown_flag
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_flag = True
    kill_all_win_processes()
    sys.exit(0)


def execute(init, shared_dict):
    """Main execution function"""
    from process_manager import ProcessManager
    global shutdown_flag
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize process manager
    process_manager = ProcessManager(shared_dict, os.getpid(), current_process())
    
    try:
        # Initialize window manager
        window_manager = WindowManager(process_manager)
        
        # Initialize windows if requested
        if init == 'init_windows':
            if window_manager.initialize_windows():
                try:
                    process_manager.shared_dict["ready"] = True
                except BrokenPipeError:
                    process_manager.deleteInstance()
                    process_manager.getInstance()
        
        # Main processing loop
        while not shutdown_flag:
            try:
                # Fetch current state
                state_instance = window_manager.fetch_state()
                
                # Process API calls
                window_manager.process_api_calls()
                
                # Check alarm timers if in alarm mode
                if state_instance and state_instance.mode == MODE['ALLARME']:
                    window_manager.check_alarm_timers()
                
                # Sleep to prevent CPU overuse
                time.sleep(1)
                
            except (django_state.DoesNotExist, django_window.DoesNotExist, 
                   django_delta.DoesNotExist, django_api_calls.DoesNotExist) as e:
                logger.warning(f"Entity not found: {e}")
                
                # Re-initialize windows if needed
                if (isinstance(e, django_state.DoesNotExist) or 
                    isinstance(e, django_window.DoesNotExist) or 
                    isinstance(e, django_delta.DoesNotExist)):
                    window_manager.initialize_windows()
                    
                # Create mock API call if needed
                elif isinstance(e, django_api_calls.DoesNotExist):
                    logger.warning("No API calls found, creating mock API call")
                    utils.createMockedApiCallObject()
                    window_manager.last_api_call_dt_creation = timezone.localtime(timezone.now())
                    
            except DatabaseError as e:
                logger.error(f"Database error: {e}")
                time.sleep(5)  # Wait before retry
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(2)  # Wait before retry
                
            finally:
                # Always close the connection to prevent connection leaks
                connection.close()
                
    except Exception as e:
        logger.error(f"Fatal error in execute: {e}")
        kill_all_win_processes()
        sys.exit(1)


def main(init, shared_dict):
    """Entry point function"""
    cur_dir = os.path.dirname(__file__) 
    logger.debug(f"Current directory: {cur_dir}")
    
    try:
        execute(init, shared_dict)
    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)
    except ProgrammingError as e:
        logger.warning(f"Database schema error, attempting migrations: {e}")
        try:
            call_command("migrate", "anywall_app")
            execute(init, shared_dict)
        except Exception as migration_error:
            logger.error(f"Migration failed: {migration_error}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        sys.exit(1)
