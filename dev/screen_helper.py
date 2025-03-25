
import subprocess
import re
import ctypes
import sys
from math import sqrt

from anywall_app.models import MODE
from anywall_app.logger import setup_logger
from config import MAX_WINDOWS, DEFAULT_DISPLAY_SIZE

logger = setup_logger(__name__)

# Global process list
processes = {}

def makeProcessWindow(process_manager, window, size_x, size_y, coord_x, coord_y, pos=None):
    """
    Prepare window data for creating a new window process.
    
    Args:
        process_manager: The process manager instance
        window: Window object with attributes
        size_x, size_y: Window dimensions
        coord_x, coord_y: Window coordinates
        pos: Optional position index
    """
    try:
        # Create a copy of window data without the dimension attributes
        window_data = window.__dict__.copy()
        if hasattr(window, "width"):
            del window_data["width"]
        if hasattr(window, "height"):
            del window_data["height"]
        if hasattr(window, "coord_x"):
            del window_data["coord_x"]
        if hasattr(window, "coord_y"):
            del window_data["coord_y"]
        
        # Add dimensions to window data
        window_data.update({
            "width": size_x,
            "height": size_y,
            "coord_x": coord_x,
            "coord_y": coord_y
        })
        
        # Store in shared dictionary
        window_key = f"window_p_{window.window_id}"
        process_manager.shared_dict[window_key] = window_data
        logger.debug(f"Prepared window {window.window_id} data: {size_x}x{size_y} at ({coord_x},{coord_y})")
    except Exception as e:
        logger.error(f"Error making process window: {e}")

class Screen:
    """
    Manages the layout and creation of window processes.
    """
    
    def __init__(self, process_manager, state_instance, windows_list):
        """Initialize the screen with windows based on the current state."""
        global processes
        self.window_handler = None
        
        try:
            if state_instance.mode == MODE['TELECAMERE']:
                self.windows_list = windows_list
                self.win_number = state_instance.windows_number
                self.active_windows = state_instance.active_windows
                
                # Get display dimensions
                self.width, self.height = self.get_display_size()
                self.process_manager = process_manager
                
                # Create layout based on windows list
                self.createLayout(self.windows_list, self.win_number, self.active_windows)
                logger.info(f"Screen initialized with {self.active_windows} active windows out of {self.win_number}")
            else:
                logger.info(f"Screen not initialized, mode is not TELECAMERE: {state_instance.mode}")
        except Exception as e:
            logger.error(f"Error initializing screen: {e}")

    def createLayout(self, windows_list, win_number, active_windows):
        """Create layout based on window data."""
        try:
            # Process each window
            for window in windows_list:
                logger.info(f"Window {window.window_id}: {window.width}x{window.height}, "
                           f"({window.coord_x}, {window.coord_y}), {window.isActive}")
                makeProcessWindow(
                    self.process_manager, 
                    window, 
                    window.width, 
                    window.height, 
                    window.coord_x, 
                    window.coord_y
                )
        except Exception as e:
            logger.error(f"Error in screen.createLayout: {e}")
            if processes:
                processes.clear()
            self.createLayoutFrom0(windows_list, win_number, active_windows)
    
    def createLayoutFrom0(self, windows_list, win_number, active_windows):
        """Create a fresh layout when existing layout data is unavailable or corrupt."""
        logger.debug("Creating layout from scratch")
        try:
            # Calculate grid dimensions
            win_per_line = int(sqrt(win_number))
            size_x = int(self.width / win_per_line)
            size_y = int(self.height / win_per_line)
            
            # Initialize tracking variables
            coord_x = 0
            coord_y = 0
            lines_in_offset = 0
            offset_multiplier = 0
            
            # Create each window
            for i in range(MAX_WINDOWS):
                # Get zoom factor
                zoom = windows_list[i].zoom if hasattr(windows_list[i], 'zoom') else 1
                
                # Adjust for zoomed windows
                if zoom != 1:
                    lines_in_offset = zoom if lines_in_offset <= 0 else lines_in_offset
                    offset_multiplier = zoom
                
                # Create the window
                makeProcessWindow(
                    self.process_manager, 
                    windows_list[i], 
                    size_x * zoom, 
                    size_y * zoom, 
                    coord_x, 
                    coord_y
                )
                
                # Update coordinates for next window
                coord_x += size_x * zoom
                
                # Handle wrapping to next row
                if coord_x >= self.width:
                    lines_in_offset -= 1 * zoom
                    if lines_in_offset <= 0:
                        offset_multiplier = 0
                    coord_x = size_x * offset_multiplier 
                    coord_y += size_y * zoom
                    
            logger.info(f"Created fresh layout with {win_number} windows")
        except KeyboardInterrupt:
            logger.warning("Caught KeyboardInterrupt, terminating processes...")
            for key, p in processes.items():
                logger.debug(p['process'])
                p['process'].terminate()
            for key, p in processes.items():
                p['process'].join()
            processes.clear()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error creating fresh layout: {e}")

    def get_display_size_linux(self):
        """Get display size on Linux systems."""
        cmd = ['xrandr']
        cmd2 = ['grep', '+0+0']
        pattern = r'\b\d+x\d+\b'

        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            p2 = subprocess.Popen(cmd2, stdin=p.stdout, stdout=subprocess.PIPE)
            p.stdout.close()

            resolution_string, _ = p2.communicate()
            p2.stdout.close()
            resolution_string = resolution_string.decode("utf-8")
            logger.debug(f"Resolution string: {resolution_string}")

            # Check if the expected pattern is found
            if "connected" in resolution_string:
                resolution = re.search(pattern, resolution_string).group(0)
                width, height = map(int, resolution.split('x'))
                return width, height
            else:
                raise ValueError("Resolution not found in xrandr output")
        except Exception as e:
            logger.warning(f"Failed to get display size on Linux: {e}")
            
        logger.warning("Using default display size 1920x1080")
        return DEFAULT_DISPLAY_SIZE

    def get_display_size(self):
        """Get display size (platform-specific implementation)."""
        try:
            # Try Windows implementation first
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()  # Enables high DPI awareness
            width = user32.GetSystemMetrics(0)  # Screen width
            height = user32.GetSystemMetrics(1)  # Screen height

            logger.info(f"Detected display size: {width}x{height}")
            return width, height
        except Exception as e:
            logger.warning(f"Failed to get display size on Windows: {e}")
            
            # Try Linux implementation as fallback
            try:
                return self.get_display_size_linux()
            except Exception as e2:
                logger.warning(f"Failed to get display size on Linux: {e2}")
                return DEFAULT_DISPLAY_SIZE
