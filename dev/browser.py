import time
from anywall_app.models import VISUALIZZAZIONE
from anywall_app.logger import setup_logger
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
import ctypes

from dotenv import load_dotenv
import os

logger = setup_logger(__name__)
DISPLAY_SIZE = (1920, 1080)

class BrowserHandler(QMainWindow):
    def __init__(self, window, process_manager, url):
        super().__init__()
        load_dotenv('.\\..\\con\\conf.env')
        self.process_manager = process_manager
        self.urlBrowser = url
        self.coord_x = window.coordinates[0]
        self.coord_y = window.coordinates[1]
        self.width = window.width
        self.height = window.height
        self.isActive = window.isActive
        self.window_id = window.window_id
        self.vis_attuale = window.visualizzazione

        import os
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--ignore-certificate-errors"

        self.monitors = self.get_monitors()
        self.target_monitor_index = int(os.getenv("MONITOR_INDEX", 0))  # Choose the second monitor (index starts from 0)
        self.target_monitor = self.monitors[self.target_monitor_index]

        self.browser = QWebEngineView()

        # Override createWindow to prevent pop-ups
        self.browser.createWindow = self.createWindow

        # Set the URL you want to load
        self.browser.setUrl(QUrl(self.urlBrowser))

        # Remove window borders
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Disable persistent cookies
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)

        # Disable scrollbars and JavaScript pop-ups via QWebEngineSettings
        settings = self.browser.settings()
        settings.setAttribute(settings.ScrollAnimatorEnabled, False)
        settings.setAttribute(settings.FullScreenSupportEnabled, True)
        settings.setAttribute(settings.ShowScrollBars, False)
        settings.setAttribute(settings.JavascriptCanOpenWindows, False)  # Disable pop-ups

        # Set window size and position
        self.setGeometry(self.target_monitor["x"] + self.coord_x, self.target_monitor["y"] + self.coord_y, self.width, self.height)

        # Add the browser to the main window
        self.setCentralWidget(self.browser)

        if not self.isActive:
            self.hide()
        else:
            self.show()

        if window.visualizzazione == VISUALIZZAZIONE['DESKTOP']:
            self.browser.loadFinished.connect(self.on_load_finished)

        self.browser.loadFinished.connect(self.inject_login_script)

        # Use a QTimer to periodically check for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_for_updates)
        self.timer.start(1000)  # Check every 1 second


    def inject_login_script(self):
        login_script = """
        document.getElementById('username').value = 'admin';
        document.getElementById('password').value = 'admin';
        document.querySelector('form').submit();
        """
        self.browser.page().runJavaScript(login_script)

    def on_load_finished(self):
        script = f"document.getElementById('window_id').value = '{self.window_id}';"
        self.browser.page().runJavaScript(script)

    def createWindow(self, _type):
        # Prevent new windows (pop-ups) from being created
        return None

    def load_monitor_index(self):
        config_path = "config.json"  # Adjust the path to your config file if needed
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as config_file:
                    config = json.load(config_file)
                    monitor_index = config.get("monitor_index", 0)  # Default to the first monitor
                    return monitor_index
            else:
                logger.warning(f"Config file not found at {config_path}. Defaulting to primary monitor.")
                return 0
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
            return 0  # Default to the first monitor

    def get_monitors(self):
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()

        monitors = []

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
            print(f"Monitor {i + 1}: {monitor}")

        return monitors

    def check_for_updates(self):
        try:
            if not self.isActive:
                self.hide()
            else:
                self.show()
            if self.window_id in self.process_manager.shared_dict:
                new_window_data = self.process_manager.shared_dict.pop(self.window_id)
                logger.info(f"New window data for window {self.window_id}: {new_window_data}")

                if "urlBrowser" in new_window_data:
                    logger.info(f"Window {self.window_id}: Changing URL")
                    self.urlBrowser = new_window_data['urlBrowser']
                    self.browser.setUrl(QUrl(self.urlBrowser))
                    self.show()

                if "width" in new_window_data and "height" in new_window_data:
                    logger.info(f"Window {self.window_id}: Changing size")
                    self.width = new_window_data['width']
                    self.height = new_window_data['height']
                    self.setGeometry(self.target_monitor["x"] + self.coord_x, self.target_monitor["y"] + self.coord_y, self.width, self.height)
                    self.show()

                if "coord_x" in new_window_data or "coord_y" in new_window_data:
                    logger.info(f"Window {self.window_id}: Changing coordinates")
                    if "coord_x" in new_window_data:
                        self.coord_x = new_window_data["coord_x"]
                    if "coord_y" in new_window_data:
                        self.coord_y = new_window_data["coord_y"]
                    self.setGeometry(self.target_monitor["x"] + self.coord_x, self.target_monitor["y"] + self.coord_y, self.width, self.height)
                    self.show()

                if "isActive" in new_window_data:
                    if new_window_data["isActive"] is True:
                        self.isActive = True
                        self.show()
                    else:
                        self.isActive = False
                        self.hide()

                if "visualizzazione" in new_window_data:
                    if (new_window_data.get("visualizzazione", VISUALIZZAZIONE['BROWSERWINDOW']) != self.vis_attuale):
                        logger.info(f"Window {self.window_id}: Preparing to close")
                        self.close()
                        # self.destroy()
                        logger.info(f"Window {self.window_id}: Closed")

                if "close" in new_window_data:
                    logger.info(f"Window {self.window_id}: Preparing to close")
                    # self.close()
                    self.destroy()
                    logger.info(f"Window {self.window_id}: Closed")


        except BrokenPipeError:
            # self.close()
            self.destroy()

        except Exception as e:
            logger.exception(f"Exception in check_for_updates: {e}")

    def closeEvent(self, event):
        # Perform any cleanup here
        self.timer.stop()
        event.accept()
