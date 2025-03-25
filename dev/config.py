"""
Configuration settings for the application.
Centralizes constants and settings to avoid duplicating values across modules.
"""

import os
from dotenv import load_dotenv

# Load environment variables
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                         'conf', 'config.env')
load_dotenv(CONFIG_PATH, override=True)

# Application constants
MAX_WINDOWS = 16
DEFAULT_DISPLAY_SIZE = (1920, 1080)
DEFAULT_MONITOR_INDEX = int(os.getenv("MONITOR_INDEX", 0))

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = "8000"
API_SERVER_URL = "http://10.140.16.109:8000"

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
