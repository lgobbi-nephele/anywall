MAX_WINDOWS = 16

import os
import sys
from multiprocessing import current_process
from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

from django.db import connection


# Correctly check if PYOPENGL_PLATFORM is not in os.environ
if 'PYOPENGL_PLATFORM' not in os.environ:
    os.environ['PYOPENGL_PLATFORM'] = "x11"
# Check if PYTHONPATH exists, if not, initialize it
if 'PYTHONPATH' not in os.environ:
    os.environ['PYTHONPATH'] = ""

if 'PYOPENGL_PLATFORM' not in os.environ:
   os.environ['PYOPENGL_PLATFORM'] = ""

# If running a script
if not getattr(sys, 'frozen', False):
    # Add the directory to PYTHONPATH
    os.environ['PYTHONPATH'] += ":" + sys.path[0].replace( '\\','/') + "/anywall"
    logger.debug(f"sys path: {sys.path[0]}")
    logger.debug(f"python path: {os.environ['PYTHONPATH']}")

# export PYOPENGL_PLATFORM=x11

import utils
from anywall_app.models import Window as django_window
from anywall_app.models import RequestedWindow as django_requested_window
from anywall_app.models import State as django_state
from anywall_app.models import Delta as django_delta
from anywall_app.models import Api_calls as django_api_calls
from anywall_app.models import MODE, IMAGE_SCOPE


import json
import time
from multiprocessing import Process
import requests
from django.utils import timezone
from django.db.utils import ProgrammingError
from django.db import OperationalError


from django.core.management import call_command

import screen_helper

# import monitor
screen = None

def make_migrations():
    try:
        # Print the current sys.path
        # print("paths in main.py")
        # for path in sys.path:
        #     print(path)
        call_command("migrate", "anywall_app")
    except Exception as e:
        logger.error(e)
        sys.exit(0)


# riavvio il processo per cambiare tecnologia di visualizzazione
def handleViewModeChange(req_window):
    screen_helper.makeProcessWindow(process_manager, req_window, req_window.width, req_window.height, req_window.coord_x, req_window.coord_y)
    process_manager.shared_dict["switchView"] = req_window.window_id

    # print(f"screen_helper.processes: {screen_helper.processes}")
    # screen_helper.processes[req_window.window_id]['process'].terminate()
    # screen_helper.processes[req_window.window_id]['process'].join()

    
    
    # screen_helper.processes[req_window.window_id]['process'].start()

def collectWindowChanges(same_window_list, ):
    new_info = {}
    req_window = None

    for el in same_window_list:
        logger.debug(f"chiamato a {str(timezone.localtime(timezone.now()))}")
        logger.debug(f"elemento:")
        logger.debug(el.__dict__)
        if el.window_id == -1:
            req_window = None
            continue

        # query the window only one time in its same_window_list cycle
        if req_window is None:
            try:
                req_window = django_requested_window.objects.get(window_id=el.window_id)
            except OperationalError as e:
                logger.error(f"collectWindowChanges(): DB connection error: {e}")
                # kill Anywall?
        if el.windows_column_name == "stream" or el.windows_column_name == "labelText":
            # cambio puntuale stream
            new_info.update({"stream": req_window.stream, "labelText": req_window.labelText})

        if el.windows_column_name == "zoom":
            # cambio puntuale zoom
            new_info.update({"zoom": req_window.zoom})
        if el.windows_column_name == "isZoom":
            # cambio puntuale isZoom
            new_info.update({"isZoom": req_window.isZoom})

        if el.windows_column_name == "enableLogo":
            # cambio puntuale enableLogo
            new_info.update({"enableLogo": req_window.enableLogo})
        if el.windows_column_name == "enableAlarmIcon":
            # cambio puntuale enableAlarmIcon
            new_info.update({"enableAlarmIcon": req_window.enableAlarmIcon})
        if el.windows_column_name == "enableWatermark":
            # cambio puntuale enableWatermark
            new_info.update({"enableWatermark": req_window.enableWatermark})   

        if el.windows_column_name == "logoPath":
            # cambio puntuale logoPath
            new_info.update({"logoPath": req_window.logoPath})
        if el.windows_column_name == "alarmIconPath":
            # cambio puntuale alarmIconPath
            new_info.update({"alarmIconPath": req_window.alarmIconPath})

        if el.windows_column_name == "coord_x":
            # cambio coordinate
            new_info.update({"coord_x": req_window.coord_x})
        if el.windows_column_name == "coord_y":
            # cambio coordinate
            new_info.update({"coord_y": req_window.coord_y})
        if el.windows_column_name == "width" or el.windows_column_name == "height":
            # cambio misure finestra. Causa chiamata a glutWindowReshape()
            new_info.update({"width": req_window.width, "height": req_window.height})
        


        if el.windows_column_name == "isActive":
            # hide o show
            logger.debug(f"Win {el.window_id}: rilevato isActive")
            new_info.update({"isActive": req_window.isActive})


        if el.windows_column_name == "isBrowser":
            # switch a browser in finestra o torno a telecamera
            new_info.update({"isBrowser": req_window.isBrowser})

        if el.windows_column_name == "urlBrowser":
            # cambio browser su pagina nuova
            new_info.update({"urlBrowser": req_window.urlBrowser})

        if el.windows_column_name == "visualizzazione":
            # cambio browser su pagina nuova
            new_info.update({"visualizzazione": req_window.visualizzazione})
            


        if el.windows_column_name == "isAlarm":
            # allarme: implementazione precedente, con anche campo timeout
            logger.debug(f"arrivato allarme {req_window.isAlarm} per finestra {req_window.window_id}")
            new_info.update({"isAlarm": req_window.isAlarm})
            
        if el.windows_column_name == "timeout":
            # allarme: implementazione precedente, con anche campo timeout
            new_info.update({"timeout": timezone.localtime(req_window.timeout)})


        if el.windows_column_name == "isRolling":
            # rolling con timerRolling
            new_info.update({"isRolling": req_window.isRolling})
        if el.windows_column_name == "timerRolling":
            # rolling con timerRolling
            new_info.update({"timerRolling": req_window.timerRolling})
        
    connection.close()
    return req_window, new_info

def readDeltaMain(current_api_call):
    try:
        delta_list = django_delta.objects.filter(call_id=current_api_call.id).order_by('window_id')
    except OperationalError as e:
        logger.error(f"readDeltaMain(): DB connection error: {e}")
        # kill Anywall?

    if not delta_list:
        current_api_call_dict = current_api_call.__dict__.copy()
        logger.debug(f"Empty delta list for current_api_call {current_api_call_dict.get('name', None)}: {current_api_call_dict.get('id', None)}")

        logger.debug(f"Len delta_list: {len(delta_list)}")

    # print("Delta list:")
    # for el in delta_list:
    #     print(el.__dict__.copy())
    unique_window_ids = set(obj.window_id for obj in delta_list)

    logger.debug("Delta list splittata:")
    split_list = [[obj for obj in delta_list if obj.window_id == window_id] for window_id in unique_window_ids]
    # for li in split_list:
        
    #     print(li)
    #     for el in li:
    #         print(el.__dict__.copy())

    connection.close()
    return delta_list, split_list
    
def readStateChangesMain(delta_list):
    state_instance = None
    try:
        state_instance = django_state.objects.latest('created')
    except OperationalError as e:
        logger.error(f"readStateChangesMain(): DB connection error: {e}")
        # kill Anywall?
    
    # modalità: {ALLARME, TELECAMERE, BROWSER, DESKTOP (chiudi processi)}
    if state_instance.mode == MODE['ALLARME']:
        # nascondo finestre precedenti, chiudo browser e aggiungi processi?
        logger.info("letta modalità ALLARME")
        doAlarmChecks = True
        cont = False
    elif state_instance.mode == MODE['BROWSER']:
        # apro browser, lascio finestre telecamere precedenti in background? Le nascondo? Le metto in idle?
        logger.info("letta modalità BROWSER")
        doAlarmChecks = False
        cont = True
    
    elif state_instance.mode == MODE['DESKTOP']:
        # nascondo tutte le finestre telecamere precedenti e/o chiudo browser
        logger.info("letta modalità BROWSER")
        doAlarmChecks = False
        cont = True
    
    elif state_instance.mode == MODE['TELECAMERE']:
        # Nessuna azione, vai a rendering
        logger.info("letta modalità TELECAMERE") 
        doAlarmChecks = False
        cont = False
    
    connection.close()
    return state_instance, doAlarmChecks, cont

def mockedStateInstance():
    # Create and upload 16 mocked django_window instances first, then create a mocked state one.
    mocked_windows_list = []
    for i in range(16):
        mocked_windows_list.append(utils.createMockedWindowObject(i))
        utils.createMockedReqWindowObject(i)

    mocked_state = utils.createMockedStateObject()

    return mocked_state, mocked_windows_list


def init_windows_list():
    # Init lista finestre da db, altirmenti vuota
    global screen

    try:
        state_instance = django_state.objects.latest('created')
        windows_list = utils.read_windows()
        screen = screen_helper.Screen(process_manager, state_instance, windows_list)  # Initialize the screen object

        delta_instance = django_delta.objects.latest('created')

    except OperationalError as e:
        logger.error(f"init_windows_list(): DB connection error: {e}")
        # kill Anywall?
    except (ProgrammingError, django_state.DoesNotExist) as e:
        logger.warning("No django_state object found with the latest 'created' timestamp.")
        make_migrations()
        logger.warning("Creating the first default entry")
        state, windows_list = mockedStateInstance()
        utils.createMockedApiCallObject()
        utils.createMockedDeltaObject()
        for i in range(MAX_WINDOWS):
            utils.createMockedBackupWindowObject(i)
        screen = screen_helper.Screen(process_manager, state, windows_list)

    connection.close()


def kill_all_win_processes():
    global screen
    global server_process
    logger.debug(screen_helper.processes)
    for key, p in screen_helper.processes.items():
        #print(p)
        p['process'].terminate()
    for key, p in screen_helper.processes.items():
        p['process'].join()
    screen_helper.processes.clear()
    del screen

    server_process.terminate()
    server_process.join()

def isAlarmExpired(timeout):
    if timezone.localtime(timezone.now()) > timezone.localtime(timeout):
        logger.debug(f"timeout: {timezone.localtime(timeout)}")
        logger.debug(f"timezone.localtime(timezone.now()): {timezone.localtime(timezone.now())}")
        logger.debug(timezone.localtime(timezone.now()) > timezone.localtime(timeout))
        return True
    return False

def checkAlarmTimers(state_instance):

    if state_instance.mode != MODE['ALLARME']:
        return logger.warning("manager: must be in ALARM mode to check expired alarms")

    requested_windows = utils.read_requested_windows()
    alarm_windows = list(filter(lambda window: window.timeout, requested_windows))

    logger.debug(f"alarm_windows:{alarm_windows}")
    for win in alarm_windows:
        logger.debug(win.__dict__)

    expired_alarms = []

    for alarm in alarm_windows:
        if(isAlarmExpired(alarm.timeout)):
            expired_alarms.append(alarm)
    
    logger.debug(f"expired_alarms: {expired_alarms}")
    for win in expired_alarms:
        logger.debug(win.__dict__)
    
    if len(expired_alarms) == 0:
        return False

    callAlarmExpired()

def callAlarmExpired():
    # Convert the payload to JSON format
    json_payload = json.dumps({"check": True})
    
    # Define the headers
    headers = {
        'Content-Type': 'application/json',
    }
    
    # Make the POST request
    response = requests.post('http://10.140.16.109:8000/api/alarm/expired/', data=json_payload, headers=headers, verify=False)
    
    # response = requests.post('https://192.168.1.13:8000/api/alarm/expired/', data=json_payload, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        logger.debug("Success")
        
        # Process the data as needed
        # For example, print the data or save it to a database
        
        return data
    else:
        # Handle errors
        logger.warning(f"Failed to send POST request. Status code: {response.status_code}")
        return None


def callAlarmClear():
    # Convert the payload to JSON format
    json_payload = json.dumps({"clear": True})
    
    # Define the headers
    headers = {
        'Content-Type': 'application/json',
    }
    
    # Make the POST request
    response = requests.post('http://10.140.16.109:8000/api/alarm/clear/', data=json_payload, headers=headers, verify=False)
    
    # response = requests.post('https://192.168.1.13:8000/api/alarm/clear/', data=json_payload, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        logger.debug("Success")
        
        # Process the data as needed
        # For example, print the data or save it to a database
        
        return data
    else:
        # Handle errors
        logger.warning(f"Failed to send POST request. Status code: {response.status_code}")
        # callReset()
        return None



def updateRenderData(window_id, new_info):
    logger.debug("new_info:")
    logger.debug(new_info)
    process_manager.shared_dict[window_id] = new_info
    logger.debug(f"Finestra {window_id} - ricevute nuove informazioni:")
    for key, value in new_info.items():
        logger.debug(f"{key}: {value}")

def updateGeneralPictures(new_info):
    if new_info == IMAGE_SCOPE['PLACEHOLDER']:
        u = "PLACEHOLDER"
    elif new_info == IMAGE_SCOPE['WATERMARK']:
        u = "WATERMARK"
    logger.debug(f"updating {u}")
    for i in range(16):
        process_manager.shared_dict[i] = {u: True}

def execute(init, shared_dict):
    from process_manager import ProcessManager
    global process_manager
    process_manager = ProcessManager(shared_dict, os.getpid(), current_process())
    try:
        # disaccoppio init a seconda di parametro
        if init == 'init_windows':
            init_windows_list()
            try:
                process_manager.shared_dict["ready"] = True
            except BrokenPipeError:
                process_manager.deleteInstance()
                process_manager.getInstance()
    except Exception as e:
        logger.error(e)
        os.kill(os.getpid(), 15)  # 15 corresponds to SIGTERM

    try:
        state_instance = django_state.objects.latest('created')
    except OperationalError as e:
        logger.error(f"django_state 392: DB connection error: {e}")
        # kill Anywall?
    last_api_call_dt_creation=timezone.localtime(timezone.now())

    while True:
        try:
    
            doAlarmChecks = False

            state_instance = None
            try:
                state_instance = django_state.objects.latest('created')
            except OperationalError as e:
                logger.error(f"django_state 400: DB connection error: {e}")
                # kill Anywall?
            if state_instance.alarm_windows > 0:
                state_instance.mode = MODE['ALLARME']
                doAlarmChecks = True
                callAlarmExpired()
            elif state_instance.mode == MODE['ALLARME'] and state_instance.alarm_windows == 0:
                doAlarmChecks = False
                callAlarmClear()

            # if doAlarmChecks:    
            #     if state_instance.alarm_windows == 0:
            #         logger.debug("state_instance.alarm_windows == 0")
            #         callAlarmClear()

            #         doAlarmChecks = False
            #         continue

            #     checkAlarmTimers(state_instance)
            
            try:
                api_calls = utils.getReceivedApiCalls(last_api_call_dt_creation)
            except OperationalError as e:
                logger.error(f"manager.py: utils.getReceivedApiCalls 423: DB connection error: {e}")
                # kill Anywall?
            # ciclo per ogni elemento in lista di api_calls
            while api_calls:
                current_api_call = api_calls.pop(0)

                try:
                    delta_list, split_list = readDeltaMain(current_api_call)
                except OperationalError as e:
                    logger.error(f"readDeltaMain 429: DB connection error: {e}")
                    # kill Anywall?
                
                # aggiorna placeholder/watermark per tutte le finestre
                if current_api_call.name == "select-image/" and current_api_call.data["window_id"] is None:
                    updateGeneralPictures(current_api_call.data["image_scope"])
                    last_api_call_dt_creation = timezone.localtime(current_api_call.created)
                    continue

                if not delta_list:
                    logger.debug("no_delta_list")
                    last_api_call_dt_creation = timezone.localtime(current_api_call.created)
                    continue
                
                if delta_list[0].readState:
                    try:
                        state_instance, doAlarmChecks, cont = readStateChangesMain(delta_list)
                    except OperationalError as e:
                        logger.error(f"readStateChangesMain 440: DB connection error: {e}")
                        # kill Anywall?
                    if cont:
                        continue
                
                for same_window_list in split_list:
                    req_window, new_info = collectWindowChanges(same_window_list, )
                    
                    if req_window is not None:
                        updateRenderData(req_window.window_id, new_info)
                    
                    if "visualizzazione" in new_info:
                        handleViewModeChange(req_window)

                utils.applyDeltaChangesInWindows() # salvo in Windows

                
                last_api_call_dt_creation = timezone.localtime(current_api_call.created)
                logger.debug(f"last_api_call_dt_creation: {last_api_call_dt_creation}")
            
            state_prev_instance = state_instance
            
            # for p in screen_helper.processes:
            #     print(p)
            time.sleep(1)


        except (django_state.DoesNotExist, django_window.DoesNotExist, django_delta.DoesNotExist, django_api_calls.DoesNotExist, KeyboardInterrupt) as e:
            if (isinstance(e, django_state.DoesNotExist)
                or isinstance(e, django_window.DoesNotExist)
                or isinstance(e, django_delta.DoesNotExist)):
                init_windows_list()
            elif isinstance(e, django_api_calls.DoesNotExist):
                logger.warning("No django_api_calls object found with the latest 'created' timestamp.")
                utils.createMockedApiCallObject()
                last_api_call_dt_creation = timezone.localtime(timezone.now())
            elif isinstance(e, KeyboardInterrupt):
                logger.warning("Caught KeyboardInterrupt, terminating processes...")
                kill_all_win_processes()
                sys.exit(1)
        except Exception as e:
            logger.warning(e)
            pass

        connection.close()



# def run_monitor():
#     global monitor_process
#     def start_monitor():
#         import monitor
#         try:
#             monitor.execute()
#         except Exception as e:
#             print(e)
#             sys.exit(0)


            
#     monitor_process = Process(target=start_monitor)
#     monitor_process.start()
#     print("server process started")


# monitor_process = None
server_process = None
screen = None

def main(init, shared_dict):
    cur_dir = os.path.dirname(__file__) 
    logger.debug(f"cur_dir = os.path.dirname(__file__): {cur_dir}")
    global screen

    try:
        # run_monitor()
        execute(init, shared_dict)

    except OperationalError as e:
        logger.error(f"main(): DB connection error: {e}")
        # kill Anywall?
    except (ProgrammingError) as e:
        logger.warning("Mancano tabelle, django, main")
        make_migrations()
        execute(init, shared_dict)