"""
Configuration settings for the application.
Centralizes constants and settings to avoid duplicating values across modules.
"""

import os
from dotenv import load_dotenv

# Load environment variables
ROOT_ANYWALL_DIR = "C:\\anywall\\"
CONFIG_FILE = ROOT_ANYWALL_DIR + "conf\\config.env"
RESOURCES_DIR = ROOT_ANYWALL_DIR + "resources"
LOG_DIR = ROOT_ANYWALL_DIR + "logs"
load_dotenv(CONFIG_FILE, override=True)

# Application constants
MAX_WINDOWS = 16
DEFAULT_DISPLAY_SIZE = (1920, 1080)
DEFAULT_MONITOR_INDEX = int(os.getenv("MONITOR_INDEX", 0))

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_IP = str(os.getenv("SERVER_IP", "127.0.0.1"))
SERVER_PORT = "8000"
HTTP = "http://"
API_SERVER_URL = f"{HTTP}{SERVER_IP}:{SERVER_PORT}"

#DB settings
DB_NAME = os.getenv("DB_NAME", "myDatabase")
DB_PASSWORD = os.getenv("DB_PASSWORD", "anywall")

# Paths
ASSETS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'conf')
LOGO_PATH = os.path.join(ASSETS_PATH, 'logo.png')
PLACEHOLDER_PATH = os.path.join(ASSETS_PATH, 'placeholder.png')
WATERMARK_PATH = os.path.join(ASSETS_PATH, 'warning.png')

# Process check intervals (seconds)
PROCESS_CHECK_INTERVAL = 1.0
WINDOW_UPDATE_INTERVAL = 1.0
API_CHECK_INTERVAL = 1.0


# Credentials (in production, these should be in environment variables)
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "ViabilitaAnywall2"
