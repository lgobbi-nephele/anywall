
from anywall_app.models import VISUALIZZAZIONE
from opengl import OpenGLHandler
from browser import BrowserHandler
from config import API_SERVER_URL

from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

class WindowHandler:
    """
    Manages window creation and switching between different visualization modes.
    Acts as a factory for different viewer types (OpenGL, Browser).
    """
    
    def __init__(self, process_manager, **window_attrs):
        self.process_manager = process_manager
        
        # Extract and store window attributes
        self.window_id = window_attrs.pop("window_id")
        self.width = window_attrs.pop("width")
        self.height = window_attrs.pop("height")
        self.coordinates = (window_attrs.pop("coord_x"), window_attrs.pop("coord_y"))
        self.isActive = window_attrs.pop("isActive")
        
        # Stream and display attributes
        self.stream = window_attrs.pop("stream")
        self.urlBrowser = window_attrs.pop("urlBrowser")
        self.labelText = window_attrs.pop("labelText")
        self.isAlarm = window_attrs.pop("isAlarm") 
        
        # UI customization attributes
        self.enableLogo = window_attrs.pop("enableLogo")
        self.enableAlarmIcon = window_attrs.pop("enableAlarmIcon")
        self.enableWatermark = window_attrs.pop("enableWatermark")
        self.logoPath = window_attrs.pop("logoPath")
        self.alarmIconPath = window_attrs.pop("alarmIconPath")
        
        # Display mode
        self.visualizzazione = window_attrs.pop("visualizzazione")

        logger.info(f"Window {self.window_id} created: {self.width}x{self.height}, " 
                   f"pos={self.coordinates}, active={self.isActive}, "
                   f"mode={self.visualizzazione}")
        
        self.viewer = None
        self.selectViewer()
    
    def update_url(self, url):
        """Update the stream URL."""
        self.stream = url
        if self.viewer and hasattr(self.viewer, 'update_url'):
            self.viewer.update_url(url)
    
    def load_GL_window(self):
        """Create an OpenGL-based window for video streams."""
        try:
            self.viewer = OpenGLHandler(self, self.stream, process_manager=self.process_manager)
            logger.debug(f"Window {self.window_id}: OpenGL window loaded")
        except Exception as e:
            logger.error(f"Failed to load OpenGL window for window {self.window_id}: {e}")
    
    def load_browser_window(self):
        """Create a browser-based window for web content."""
        try:
            self.viewer = BrowserHandler(self, process_manager=self.process_manager, url=self.urlBrowser)
            logger.debug(f"Window {self.window_id}: Browser window loaded with URL: {self.urlBrowser}")
        except Exception as e:
            logger.error(f"Failed to load browser window for window {self.window_id}: {e}")
    
    def load_desktop_window(self):
        """Create a browser-based window for desktop view."""
        try:
            self.viewer = BrowserHandler(self, process_manager=self.process_manager, 
                                         url=API_SERVER_URL + '/receiver')
            logger.debug(f"Window {self.window_id}: Desktop window loaded")
        except Exception as e:
            logger.error(f"Failed to load desktop window for window {self.window_id}: {e}")

    def selectViewer(self):
        """Select and initialize the appropriate viewer based on visualization mode."""
        try:
            if self.visualizzazione == VISUALIZZAZIONE['OPENGL']:
                logger.info(f"Window {self.window_id}: Using OpenGL visualization")
                self.load_GL_window()
            elif self.visualizzazione == VISUALIZZAZIONE['BROWSERWINDOW']:
                logger.info(f"Window {self.window_id}: Using browser visualization")
                self.load_browser_window()
            elif self.visualizzazione == VISUALIZZAZIONE['DESKTOP']:
                logger.info(f"Window {self.window_id}: Using desktop visualization")
                self.load_desktop_window()
            else:
                logger.warning(f"Window {self.window_id}: Unknown visualization mode: {self.visualizzazione}")
        except Exception as e:
            logger.error(f"Error selecting viewer for window {self.window_id}: {e}")
            
    def close(self):
        """Close the window and clean up resources."""
        if self.viewer and hasattr(self.viewer, 'close'):
            self.viewer.close()
            logger.debug(f"Window {self.window_id}: Closed")
