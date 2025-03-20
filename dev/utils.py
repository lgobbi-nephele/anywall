import json

from django.db import connection
from anywall_app.models import Window
from anywall_app.models import Api_calls as django_api_calls
from anywall_app.service import createMockedWindowObject, createMockedReqWindowObject, createMockedBackupWindowObject, createMockedStateObject, createMockedDeltaObject, createMockedApiCallObject, read_windows, read_requested_windows
from django.db import OperationalError

from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

def applyDeltaChangesInWindows():
    requested_windows = read_requested_windows()
    for el in requested_windows:
        req_window_data = el.__dict__.copy()
        req_window_data.pop('_state', None)
        req_window_data.pop('window_id', None)
        try:
            Window.objects.update_or_create(window_id=el.window_id, defaults={**req_window_data})
            connection.close()
        except OperationalError as e:
            logger.error(f"utils.applyDeltaChangesInWindows 13: DB connection error: {e}")
            # kill Anywall?

def read_state_json(state_instance):
    state_str = state_instance.state
    windows_list_tmp = json.loads(state_str)
    windows = [el["fields"] for el in windows_list_tmp]
    return windows

def loadListFromStateStr(StateStr):
    last_state_json = json.loads(StateStr)
    last_state_list = [el["fields"] for el in last_state_json]
    return last_state_list

def getReceivedApiCalls(last_api_call_dt_creation):
    # Query to find Api_calls objects created after last_api_call_dt_creation
    api_calls = list(django_api_calls.objects.filter(created__gt=last_api_call_dt_creation).order_by('created'))
    connection.close()
    
    # print(f"api_calls:")
    # for call in api_calls:
    #     print(call.__dict__)

    return api_calls

def gotResetApiCall(api_call):
    if api_call.name == 'reset':
        logger.info("Reset call received. Resetting...")
        return True
    else:
        return False
def callRestartWindows():
    response = requests.post('http://daattnnn:8000/api/restart-windows/', 
                           headers={'Content-Type': 'application/json'},
                           verify=False)
    if response.status_code == 200:
        logger.debug("Windows restart command sent successfully")
        return response.json()
    else:
        logger.warning(f"Failed to send restart windows command. Status code: {response.status_code}")
        return None
