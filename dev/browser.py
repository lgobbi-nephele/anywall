
import os
import ctypes
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from dotenv import load_dotenv
from config import CONFIG_FILE
from config import SERVER_IP

from anywall_app.models import VISUALIZZAZIONE
from anywall_app.logger import setup_logger

logger = setup_logger(__name__)
DISPLAY_SIZE = (1920, 1080)

class BrowserHandler(QMainWindow):
    """
    Handles browser window creation and management for web content display.
    Uses PyQt5 WebEngine to render web content.
    """

    def __init__(self, window, process_manager, url):
        """Initialize the browser window."""
        super().__init__()

        # Load environment variables
        try:
            load_dotenv(CONFIG_FILE, override=True)
        except Exception as e:
            logger.warning(f"Failed to load env file: {e}")

        # Store references and window properties
        self.process_manager = process_manager
        self.urlBrowser = url
        self.coord_x = window.coordinates[0]
        self.coord_y = window.coordinates[1]
        self.width = window.width
        self.height = window.height
        self.isActive = window.isActive
        self.window_id = window.window_id
        self.vis_attuale = window.visualizzazione

        # Configure browser environment
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--ignore-certificate-errors"

        # Detect and configure monitors
        try:
            self.monitors = self.get_monitors()
            self.target_monitor_index = int(os.getenv("MONITOR_INDEX", 0))
            if self.target_monitor_index >= len(self.monitors):
                logger.warning(f"Monitor index {self.target_monitor_index} out of range, using 0")
                self.target_monitor_index = 0
            self.target_monitor = self.monitors[self.target_monitor_index]
        except Exception as e:
            logger.error(f"Failed to get monitors: {e}")
            self.target_monitor = {"x": 0, "y": 0, "width": 1920, "height": 1080}

        # Initialize browser view
        self.setup_browser()
        
        # Set update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_for_updates)
        self.timer.start(1000)  # Check every 1 second
        
        # Show window if active
        if self.isActive:
            self.show()
        else:
            self.hide()

    def setup_browser(self):
        """Set up the browser window and its settings."""
        try:
            # Create browser view
            self.browser = QWebEngineView()
            self.browser.createWindow = self.createWindow  # Override to prevent pop-ups

            # Configure browser settings
            profile = QWebEngineProfile.defaultProfile()
            profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
            profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
            
            settings = self.browser.settings()
            settings.setAttribute(settings.ScrollAnimatorEnabled, False)
            settings.setAttribute(settings.FullScreenSupportEnabled, True)
            settings.setAttribute(settings.ShowScrollBars, False)
            settings.setAttribute(settings.JavascriptCanOpenWindows, False)

            # Remove window borders
            self.setWindowFlags(Qt.FramelessWindowHint)
            
            # Set window position and size
            self.setGeometry(
                self.target_monitor["x"] + self.coord_x, 
                self.target_monitor["y"] + self.coord_y, 
                self.width, 
                self.height
            )

            # Add browser to window
            self.setCentralWidget(self.browser)

            # Load URL
            self.browser.setUrl(QUrl(self.urlBrowser))

            # Connect signals
            if self.vis_attuale == VISUALIZZAZIONE['DESKTOP']:
                self.browser.loadFinished.connect(self.on_load_finished)

            self.browser.loadFinished.connect(self.inject_login_script)

            logger.info(f"Browser window {self.window_id} set up with URL: {self.urlBrowser}")
        except Exception as e:
            logger.error(f"Failed to set up browser window {self.window_id}: {e}")

    def inject_login_script(self):
        """Inject login script to auto-fill credentials if needed."""
        try:
            if '/clock-view' not in self.urlBrowser and '/receiver' not in self.urlBrowser:
                return

            login_script = """
            if (document.getElementById('username') && document.getElementById('password')) {
                document.getElementById('username').value = 'admin';
                document.getElementById('password').value = 'ViabilitaAnywall2';
                document.querySelector('form').submit();
            }
            """
            self.browser.page().runJavaScript(login_script)
        except Exception as e:
            logger.error(f"Failed to inject login script: {e}")

    def on_load_finished(self):
        """Handle page load completion."""
        try:
            script = f"document.getElementById('window_id').value = '{self.window_id}';"
            self.browser.page().runJavaScript(script)
        except Exception as e:
            logger.error(f"Failed to set window_id after load: {e}")

    def createWindow(self, _type):
        """Prevent pop-ups by overriding window creation."""
        return None

    def get_monitors(self):
        """Get available monitors information."""
        monitors = []
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()

            def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
                monitor_info = ctypes.create_string_buffer(40)
                ctypes.windll.user32.GetMonitorInfoA(hMonitor, monitor_info)
                rect = ctypes.cast(lprcMonitor, ctypes.POINTER(ctypes.wintypes.RECT)).contents
                monitors.append({
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top
                })
                return True

            monitor_enum_proc_type = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                ctypes.c_void_p, ctypes.c_void_p,
                ctypes.POINTER(ctypes.wintypes.RECT), ctypes.c_double
            )
            monitor_enum_proc_cb = monitor_enum_proc_type(monitor_enum_proc)

            ctypes.windll.user32.EnumDisplayMonitors(0, 0, monitor_enum_proc_cb, 0)

            for i, monitor in enumerate(monitors):
                logger.debug(f"Monitor {i + 1}: {monitor}")

            return monitors
        except Exception as e:
            logger.error(f"Failed to get monitors: {e}")
            return [{"x": 0, "y": 0, "width": 1920, "height": 1080}]

    def check_for_updates(self):
        """Check for window updates from the process manager."""
        try:
            # First check if window should be shown/hidden
            if not self.isActive:
                self.hide()
            else:
                self.show()
                
            # Check for updates to this window
            if self.window_id in self.process_manager.shared_dict:
                new_window_data = self.process_manager.shared_dict.pop(self.window_id)
                self.apply_window_updates(new_window_data)
        except Exception as e:
            logger.exception(f"Exception in check_for_updates: {e}")

    def apply_window_updates(self, new_window_data):
        """Apply updates to the browser window."""
        try:
            logger.info(f"Applying updates for window {self.window_id}: {new_window_data.keys()}")
            
            # URL changes
            if "urlBrowser" in new_window_data:
                logger.info(f"Window {self.window_id}: Changing URL to {new_window_data['urlBrowser']}")
                self.urlBrowser = new_window_data['urlBrowser']
                self.browser.setUrl(QUrl(self.urlBrowser))
                self.show()

            # Size changes
            if "width" in new_window_data or "height" in new_window_data:
                if "width" in new_window_data:
                    self.width = new_window_data['width']
                if "height" in new_window_data:
                    self.height = new_window_data['height']
                logger.info(f"Window {self.window_id}: Resizing to {self.width}x{self.height}")
                self.update_geometry()

            # Position changes
            if "coord_x" in new_window_data or "coord_y" in new_window_data:
                if "coord_x" in new_window_data:
                    self.coord_x = new_window_data["coord_x"]
                if "coord_y" in new_window_data:
                    self.coord_y = new_window_data["coord_y"]
                logger.info(f"Window {self.window_id}: Moving to ({self.coord_x}, {self.coord_y})")
                self.update_geometry()

            # Visibility changes
            if "isActive" in new_window_data:
                self.isActive = new_window_data["isActive"]
                if self.isActive:
                    self.show()
                else:
                    self.hide()
                logger.info(f"Window {self.window_id}: Active state changed to {self.isActive}")

            # Visualization mode changes
            if "visualizzazione" in new_window_data:
                if new_window_data.get("visualizzazione") != self.vis_attuale:
                    logger.info(f"Window {self.window_id}: Visualization changed, closing")
                    self.close()

            # Close request
            if "close" in new_window_data:
                logger.info(f"Window {self.window_id}: Close requested")
                self.destroy()
                
        except Exception as e:
            logger.error(f"Failed to apply window updates: {e}")

    def update_geometry(self):
        """Update window geometry based on current properties."""
        try:
            self.setGeometry(
                self.target_monitor["x"] + self.coord_x, 
                self.target_monitor["y"] + self.coord_y, 
                self.width, 
                self.height
            )
            self.show()
        except Exception as e:
            logger.error(f"Failed to update geometry: {e}")

    def closeEvent(self, event):
        """Handle window close event."""
        try:
            self.timer.stop()
            event.accept()
            logger.info(f"Window {self.window_id} closed")
        except Exception as e:
            logger.error(f"Error during window close: {e}")
