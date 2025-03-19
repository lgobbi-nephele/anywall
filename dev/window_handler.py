from anywall_app.models import VISUALIZZAZIONE
from opengl import OpenGLHandler
from browser import BrowserHandler

from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

class WindowHandler:
    
    def __init__(self, process_manager, **window_attrs):
        self.process_manager = process_manager
        self.width, self.height = window_attrs.pop("width"), window_attrs.pop("height")
        self.coordinates = (window_attrs.pop("coord_x"), window_attrs.pop("coord_y"))
        self.window_id = window_attrs.pop("window_id")
        self.isActive = window_attrs.pop("isActive")
        logger.info(f'{self.width}x{self.height}, {self.coordinates}, window_id={self.window_id}')
        self.stream = window_attrs.pop("stream")
        self.urlBrowser = window_attrs.pop("urlBrowser")
        self.labelText = window_attrs.pop("labelText")
        self.isAlarm = window_attrs.pop("isAlarm") 
        self.enableLogo = window_attrs.pop("enableLogo")
        self.enableAlarmIcon = window_attrs.pop("enableAlarmIcon")
        self.enableWatermark = window_attrs.pop("enableWatermark")
        self.logoPath = window_attrs.pop("logoPath")
        self.alarmIconPath = window_attrs.pop("alarmIconPath")
        self.visualizzazione = window_attrs.pop("visualizzazione")

        self.viewer = None

        self.selectViewer()

        # print(f"Finestra {window.window_id}: screen_helper.py Window dopo selectViewer() iniziale")
        
        # while True:
        #     if PM.shared_dict and window.window_id in PM.shared_dict:
        #         new_window_data = PM.shared_dict.pop(window.window_id)
        #         print(f"screen_helper new_window_data finestra {window.window_id}: {new_window_data}")
        #         if "visualizzazione" in new_window_data:
        #             print(f"Finestra {window.window_id}: screen_helper.py Window cambio visualizzazione")
        #             self.visualizzazione = new_window_data['visualizzazione']
        #             del self.viewer
        #             self.selectViewer()
        #     time.sleep(1)
    
    def update_url(self, url):
        self.stream = url
    
    def load_GL_window(self):
        self.viewer = OpenGLHandler(self,self.stream, process_manager=self.process_manager)
    
    def load_browser_window(self):
        self.viewer = BrowserHandler(self, process_manager=self.process_manager, url=self.urlBrowser)
    
    def load_desktop_window(self):
        self.viewer = BrowserHandler(self, process_manager=self.process_manager, url='http://daattnnn:8000/receiver')

        # self.viewer = BrowserHandler(self, process_manager=self.process_manager, url='https://192.168.1.13:8080')

    def selectViewer(self):
        if self.visualizzazione == VISUALIZZAZIONE['OPENGL']:
            logger.info("selectViewer detect OPENGL")
            self.load_GL_window()
        elif self.visualizzazione == VISUALIZZAZIONE['BROWSERWINDOW']:
            logger.info("selectViewer detect BROWSERWINDOW")
            self.load_browser_window()
        elif self.visualizzazione == VISUALIZZAZIONE['DESKTOP']:
            logger.info("selectViewer detect DESKTOP")
            self.load_desktop_window()

    # def play(self):
    #     self.OpenGLHandler.play()