from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineSettings

class BrowserWindow(QMainWindow):
    def __init__(self, window, DISPLAY_SIZE):
        super().__init__()
        self.browser = QWebEngineView()

        # Override createWindow to prevent pop-ups
        self.browser.createWindow = self.createWindow

        # Set the URL you want to load
        self.browser.setUrl(QUrl("https://www.crismasecurity.it"))

        # Remove window borders
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Disable persistent cookies
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)

        # Disable scrollbars and JavaScript pop-ups via QWebEngineSettings
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)  # Disable pop-ups

        # Set window size and position
        self.setGeometry(window.coordinates[0],
                         window.coordinates[1] + int(DISPLAY_SIZE[1] * 0.035),
                         window.width,
                         window.height - int(DISPLAY_SIZE[1] * 0.035))

        # Add the browser to the main window
        self.setCentralWidget(self.browser)

    def createWindow(self, _type):
        # Prevent new windows (pop-ups) from being created
        return None

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Example window coordinates and size (adjust as needed)
    class Window:
        coordinates = (100, 100)
        width = 1024
        height = 768

    DISPLAY_SIZE = (1920, 1080)  # Example display size

    mainWindow = BrowserWindow(Window, DISPLAY_SIZE)
    mainWindow.show()

    sys.exit(app.exec_())