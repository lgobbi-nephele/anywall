import os
import mss
import base64
from datetime import datetime
from anywall_app.logger import setup_logger
from dotenv import load_dotenv
from django.conf import settings  # Import Django settings

logger = setup_logger(__name__)

SCREENSHOT_DIR = os.path.join(settings.MEDIA_ROOT, 'screenshots')  # Use MEDIA_ROOT from settings

# Load environment variables
load_dotenv()

MONITOR_NUMBER = int(os.getenv("MONITOR_INDEX", 1))  # Default to monitor 1 if not specified

def ensure_screenshot_dir():
    """Ensure the screenshot directory exists"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def capture_monitor(monitor_number: int, filepath: str):
    with mss.mss() as sct:
        # sct.monitors[0] is a "virtual monitor" with entire bounding rectangle (all screens).
        # sct.monitors[1] is your first physical monitor, sct.monitors[2] is your second, etc.
        if monitor_number >= len(sct.monitors):
            logger.info(f"Monitor {monitor_number} not found. Available: {len(sct.monitors)-1}")
            return

        # Get bounding box for the specified monitor
        monitor = sct.monitors[monitor_number]
        screenshot = sct.grab(monitor)

        # Save as PNG
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=filepath)
        #logger.info(f"Saved {filepath}")

def capture_screenshot():
    """Capture a screenshot of the specified monitor and save it to the screenshots directory"""
    try:
        ensure_screenshot_dir()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)

        capture_monitor(MONITOR_NUMBER + 1, filepath)
        # Keep only the 10 most recent screenshots
        cleanup_old_screenshots()

        #logger.info(f"Screenshot captured: {filepath}")
        return filename
    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}")
        return None

def cleanup_old_screenshots():
    """Keep only the 10 most recent screenshots"""
    try:
        files = [os.path.join(SCREENSHOT_DIR, f) for f in os.listdir(SCREENSHOT_DIR) 
                if f.startswith("screenshot_") and f.endswith(".png")]
        files.sort(key=os.path.getctime, reverse=True)

        # Delete all but the 10 most recent files
        for old_file in files[10:]:
            os.remove(old_file)
    except Exception as e:
        logger.error(f"Error cleaning up screenshots: {e}")

def get_latest_screenshot():
    """Get the filename of the latest screenshot"""
    try:
        ensure_screenshot_dir()
        absolute_screenshot_dir = os.path.abspath(SCREENSHOT_DIR)

        files = [f for f in os.listdir(absolute_screenshot_dir) 
                 if f.startswith("screenshot_") and f.endswith(".png")]

        if not files:
            logger.warning("No screenshot files found")
            return None

        files.sort(key=lambda f: os.path.getctime(os.path.join(absolute_screenshot_dir, f)), reverse=True)
        latest_screenshot_file = os.path.join(absolute_screenshot_dir, files[0])

        # Read bytes and encode to base64
        with open(latest_screenshot_file, "rb") as image_file:
            image_data = image_file.read()
        base64_encoded = base64.b64encode(image_data).decode("utf-8")

        return base64_encoded
    except Exception as e:
        logger.error(f"Error getting latest screenshot: {e}")
        return None