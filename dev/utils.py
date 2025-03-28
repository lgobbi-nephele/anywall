"""
Utility functions for the application.
"""

import json
import requests
from django.db import connection, OperationalError
from django.utils import timezone

from anywall_app.models import Window
from anywall_app.models import Api_calls as django_api_calls
from anywall_app.service import (
    createMockedWindowObject,
    createMockedReqWindowObject,
    createMockedBackupWindowObject,
    createMockedStateObject,
    createMockedDeltaObject,
    createMockedApiCallObject,
    read_windows,
    read_requested_windows,
)

from anywall_app.logger import setup_logger
from config import API_SERVER_URL

logger = setup_logger(__name__)


def applyDeltaChangesInWindows():
    """Apply changes from RequestedWindow to Window model."""
    try:
        requested_windows = read_requested_windows()
        for window in requested_windows:
            # Copy window data for update
            window_data = window.__dict__.copy()
            window_data.pop("_state", None)
            window_data.pop("window_id", None)

            # Update or create Window object
            try:
                Window.objects.update_or_create(
                    window_id=window.window_id, defaults={**window_data}
                )
                logger.debug(f"Updated Window {window.window_id}")
            except OperationalError as e:
                logger.error(f"Database error updating Window {window.window_id}: {e}")

        connection.close()
    except Exception as e:
        logger.error(f"Error applying delta changes: {e}")


def read_state_json(state_instance):
    """Read window state from JSON string."""
    try:
        state_str = state_instance.state
        windows_list_tmp = json.loads(state_str)
        windows = [el["fields"] for el in windows_list_tmp]
        return windows
    except Exception as e:
        logger.error(f"Error reading state JSON: {e}")
        return []


def loadListFromStateStr(StateStr):
    """Convert state string to list of window data."""
    try:
        last_state_json = json.loads(StateStr)
        last_state_list = [el["fields"] for el in last_state_json]
        return last_state_list
    except Exception as e:
        logger.error(f"Error loading list from state string: {e}")
        return []


def getReceivedApiCalls(last_api_call_dt_creation):
    """Get API calls received after a specified time."""
    try:
        api_calls = list(
            django_api_calls.objects.filter(
                created__gt=last_api_call_dt_creation
            ).order_by("created")
        )
        connection.close()
        return api_calls
    except Exception as e:
        logger.error(f"Error getting API calls: {e}")
        connection.close()
        return []


def callRestartWindows():
    """Send request to restart windows."""
    try:
        response = requests.post(
            f"{API_SERVER_URL}/api/restart-windows/",
            headers={"Content-Type": "application/json"},
            verify=False,
        )
        if response.status_code == 200:
            logger.debug("Windows restart command sent successfully")
            return response.json()
        else:
            logger.warning(
                f"Failed to send restart windows command. Status code: {response.status_code}"
            )
            return None
    except Exception as e:
        logger.error(f"Error calling restart windows: {e}")
        return None


def callAlarmExpired():
    """Send request to check expired alarms."""
    try:
        json_payload = json.dumps({"check": True})
        headers = {"Content-Type": "application/json"}

        response = requests.post(
            f"{API_SERVER_URL}/api/alarm/expired/",
            data=json_payload,
            headers=headers,
            verify=False,
        )

        if response.status_code == 200:
            data = response.json()
            logger.debug("Alarm expired check successful")
            return data
        else:
            logger.warning(
                f"Failed to check expired alarms. Status code: {response.status_code}"
            )
            return None
    except Exception as e:
        logger.error(f"Error checking expired alarms: {e}")
        return None


def callAlarmClear():
    """Send request to clear alarms."""
    try:
        json_payload = json.dumps({"clear": True})
        headers = {"Content-Type": "application/json"}

        response = requests.post(
            f"{API_SERVER_URL}/api/alarm/clear/",
            data=json_payload,
            headers=headers,
            verify=False,
        )

        if response.status_code == 200:
            data = response.json()
            logger.debug("Alarm clear successful")
            return data
        else:
            logger.warning(
                f"Failed to clear alarms. Status code: {response.status_code}"
            )
            return None
    except Exception as e:
        logger.error(f"Error clearing alarms: {e}")
        return None


def isAlarmExpired(timeout):
    """Check if an alarm has expired."""
    try:
        current_time = timezone.localtime(timezone.now())
        timeout_time = timezone.localtime(timeout)

        if current_time > timeout_time:
            logger.debug(
                f"Alarm expired. Timeout: {timeout_time}, Current: {current_time}"
            )
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking if alarm expired: {e}")
        return False


def get_display_size():
    """Get the display size of the primary monitor."""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)

        logger.info(f"Display size: {width}x{height}")
        return (width, height)
    except Exception as e:
        logger.warning(f"Failed to get display size: {e}")
        return (1920, 1080)
