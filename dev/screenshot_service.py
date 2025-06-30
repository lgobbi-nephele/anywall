import time
from screen_capture import capture_screenshot
from anywall_app.logger import setup_logger

logger = setup_logger(__name__)


def run_screenshot_service():
    """Run the screenshot service to capture screenshots every 5 seconds"""
    logger.info("Starting screenshot capture service")

    try:
        while True:
            # Capture screenshot
            filename = capture_screenshot()
            if filename is None:
                logger.warning("Failed to capture screenshot")

            # Wait for 5 seconds
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Screenshot service stopped by user")
    except Exception as e:
        logger.error(f"Screenshot service error: {e}")


if __name__ == "__main__":
    # Run the service
    run_screenshot_service()
