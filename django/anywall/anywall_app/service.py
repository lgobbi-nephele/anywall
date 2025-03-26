
import datetime
import numpy as np
import traceback

from anywall_app.models import *
from rest_framework.response import Response
from math import sqrt, ceil
from django.utils import timezone
from django.db import connection
from .logger import setup_logger

from config import MAX_WINDOWS
from config import DEFAULT_DISPLAY_SIZE as SCREEN_SIZE

logger = setup_logger(__name__)


def resetWinIds(windows_state_list):
    #reset window_ids with indexes
    for i in range(len(windows_state_list)):
        windows_state_list[i].window_id = i
    return windows_state_list

def closest_square(n):
    return int(ceil(sqrt(n))) ** 2

def cloneDjangoDict(instance, **kwargs):
    """
    Clone the current Window instance.

    kwargs: Override fields for the new instance.
    """
    # Copy all fields from the current instance
    cloned_fields = {}

    cloned_fields.update(**(instance.__dict__))
    cloned_fields.update(kwargs)
    # Remove the id so Django knows this is a new object
    logger.debug("removing _state and id")
    cloned_fields.pop('_state', None)
    cloned_fields.pop('id', None)

    # Update with kwargs if any field needs to be overridden
    return cloned_fields

def makeDeltaRows(state, req_window, api_call):
    delta = Delta()
    del delta._state
    delta.call_id = api_call.id

    if req_window is not None:
        delta.readState = False
        delta.window_id = req_window.window_id
        last_window_entry = Window.objects.get(window_id=req_window.window_id)
        connection.close()
        for field in req_window._meta.fields:
            field_name = field.name
            previous_window_value = getattr(last_window_entry, field_name)
            req_window_value = getattr(req_window, field_name)
            if previous_window_value != req_window_value:
                delta.windows_column_name = field_name
                Delta.objects.create(**(delta.__dict__))

    if state is not None:
        delta.window_id = -1
        delta.readState = True
        delta.call_id = api_call.id
        delta = cloneDjangoDict(delta, readState=True, call_id=api_call.id)
        Delta.objects.create(**delta)

    connection.close()

def createMockedWindowObject(window_id):
    try:
        win, created = Window.objects.update_or_create(
            window_id=window_id,
            defaults={"coord_x": 480 * (window_id % 4), 
                      "coord_y": 270 * (window_id // 4),
                      }
            )
        connection.close()
        return win
    except Exception as e:
        logger.warning(f"Error creating/updating Window object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def createMockedReqWindowObject(window_id, **kwargs):
    try:
        win, created = RequestedWindow.objects.update_or_create(
            window_id=window_id,
            defaults={"coord_x": 480 * (window_id % 4),
                      "coord_y": 270 * (window_id // 4),
                      **kwargs
                      }
            )
        connection.close()
        return win
    except Exception as e:
        logger.warning(f"Error creating/updating RequestedWindow object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def createMockedBackupWindowObject(window_id):
    try:
        win, created = BackupWindow.objects.update_or_create(
            window_id=window_id,
            defaults={"coord_x": 480 * (window_id % 4),
                      "coord_y": 270 * (window_id // 4),
                      }
            )
        logger.debug(win.__dict__.copy())
        connection.close()
        return win
    except Exception as e:
        logger.warning(f"Error creating/updating RequestedWindow object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def resetMockedReqWindowObject(window_id, **kwargs):
    try:
        win, created= RequestedWindow.objects.filter(pk=window_id).update_or_create(
            window_id=window_id,
            defaults={"stream":'',
                "labelText":'',
                "zoom":1,
                "isZoom":False,
                "width":480,
                "height":270,
                "coord_x":480 * (window_id % 4),
                "coord_y":270 * (window_id // 4),
                "isBrowser":False,
                "urlBrowser":'',
                "isActive":True,
                "isAlarm":False,
                "isRolling":False,
                "timerRolling":5,
                "timeout":None,
                "visualizzazione":0,
                **kwargs
                }
            )
        connection.close()
        return win
    except Exception as e:
        logger.warning(f"Error reset RequestedWindow object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()


def resetMockedWindowObject(window_id, **kwargs):
    try:
        win, created= Window.objects.filter(pk=window_id).update_or_create(
            window_id=window_id,
            defaults={"stream":'',
                "labelText":'',
                "zoom":1,
                "isZoom":False,
                "width":480,
                "height":270,
                "coord_x":480 * (window_id % 4),
                "coord_y":270 * (window_id // 4),
                "isBrowser":False,
                "urlBrowser":'',
                "isActive":True,
                "isAlarm":False,
                "isRolling":False,
                "timerRolling":5,
                "timeout":None,
                "visualizzazione":0,
                **kwargs
                }
            )
        connection.close()
        return win
    except Exception as e:
        logger.warning(f"Error reset Window object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def resetMockedBackupWindowObject(window_id, **kwargs):
    try:
        win, created= BackupWindow.objects.filter(pk=window_id).update_or_create(
            window_id=window_id,
            defaults={"stream":'',
                "labelText":'',
                "zoom":1,
                "isZoom":False,
                "width":480,
                "height":270,
                "coord_x":480 * (window_id % 4), 
                "coord_y":270 * (window_id // 4),
                "isBrowser":False,
                "urlBrowser":'',
                "isActive":True,
                "isAlarm":False,
                "isRolling":False,
                "timerRolling":5,
                "timeout":None,
                "visualizzazione":0,
                **kwargs
                }
            )
        connection.close()
        return win
    except Exception as e:
        logger.warning(f"Error reset BackupWindow object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def resetMockedStateObject(window_id):
    try:
        win, created= State.objects.create(
           defaults={"created":'',
               "window_number":16,
               "active_windows":16,
               "alarm_windows":16,
               "mode":0,
               "browserUrl":'',
               "isActive":True,
               "id":''
                }
            )
        connection.close()
        return win
    except Exception as e:
        logger.warning(f"Error reset State table object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def createMockedStateObject(mode=MODE['TELECAMERE']):
    try:
        state = State.objects.create(
            mode=mode,
            )
        connection.close()
        return state
    except Exception as e:
        logger.warning(f"Error creating State object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def createMockedDeltaObject():
    try:
        last_api_call = Api_calls.objects.latest('created')

        delta = Delta.objects.create(
            call_id = last_api_call.id,
            window_id = 0,
            windows_column_name = 'stream',
            readState = False
        )
        connection.close()
        return delta
    except Exception as e:
        logger.warning(f"Error creating Delta object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def createMockedApiCallObject():
    try:
        api_call = Api_calls.objects.create(
            name = 'first-call',
            data = {"name":'first-call'},
        )
        connection.close()
        return api_call
    except Exception as e:
        logger.warning(f"Error creating ApiCall object: {e}")
        # Log the full traceback for debugging purposes
        traceback.print_exc()

def read_state():
    state = State.objects.latest('created')
    connection.close()
    return state

def read_windows():
    windows_list = list(Window.objects.all())
    connection.close()
    logger.debug("Window.objects.all(): ")
    for win in windows_list:
        logger.debug(win.__dict__)
    return windows_list

def read_requested_windows():
    windows_list = list(RequestedWindow.objects.all())
    connection.close()
    logger.debug("Window.objects.all(): ")
    for win in windows_list:
        logger.debug(win.__dict__)
    return windows_list


def read_backup_windows():
    windows_list = list(BackupWindow.objects.all())
    connection.close()
    logger.debug("Window.objects.all(): ")
    for win in windows_list:
        logger.debug(win.__dict__)
    return windows_list

def reset_backup_windows():
    new_backup_windows = []
    for i in range(MAX_WINDOWS):
        new_backup_windows.append(createMockedBackupWindowObject(i))
    
    return new_backup_windows

def uploadRequestedWindows(windows_list):
    requested_windows = []
    for el in windows_list:
        req_window_data = el.__dict__
        req_win, created = RequestedWindow.objects.update_or_create(window_id=el.window_id, defaults={**req_window_data})
        connection.close()
        requested_windows.append(req_win)

    return requested_windows

def uploadBackupWindows(windows_list):
    for el in windows_list:
        backup_window_data = el.__dict__
        BackupWindow.objects.update_or_create(window_id=el.window_id, defaults={**backup_window_data})
        connection.close()

def getTime(timer=0):
    # Get the current date and time in UTC
    current_time = datetime.datetime.now()

    # Add the timedelta to the current UTC datetime
    timeout = current_time + datetime.timedelta(seconds=timer)

    timeout = timezone.make_aware(timeout, timezone.get_current_timezone())
    # Format the datetime to show year, month, day, hour, minute, and second
    # formatted_timeout = timeout.strftime("%Y-%m-%d %H:%M:%S")

    return timeout


def createLayout(windows_list, win_number):
    coord_x = 0
    coord_y = 0
    win_per_line = int(sqrt(win_number))
    size_x = int(SCREEN_SIZE[0] / win_per_line)
    size_y = int(SCREEN_SIZE[1] / win_per_line)

    lines_in_offset = 0
    offset_multiplier = 0
    logger.debug(f"Service: win_number: {win_number}")
    for i in range(win_number):

        windows_list[i].width = size_x
        windows_list[i].height = size_y
        windows_list[i].coord_x = coord_x
        windows_list[i].coord_y = coord_y

        logger.debug(f"window {i} in service createLayout:")
        logger.debug(windows_list[i].__dict__)

        coord_x += size_x


        if coord_x >= SCREEN_SIZE[0]:
            lines_in_offset -= 1
            if lines_in_offset <= 0:
                offset_multiplier = 0
            coord_x = size_x * offset_multiplier 
            coord_y += size_y 

    return windows_list


def calculateExpansion(window, windows_number, zoom):
    prev_windows = read_windows()

    win_per_line = int(sqrt(windows_number))  # Assuming a square grid
    if windows_number < 9 and any(prev_window.isZoom == True for idx, prev_window in enumerate(prev_windows) if idx != window.window_id):
        return Response({"message": f"Cannot zoom more than one window in {win_per_line}x{win_per_line} layout"}), None, None


    if zoom > 2 and any(prev_window.zoom > 1 for idx, prev_window in enumerate(prev_windows) if idx != window.window_id):
        return Response({"message": f"Cannot zoom more than 2x with other windows zoomed"}, status=400), None, None
    # funziona per zoom da 1 a N, ma non per zoom da >1 a N.
    # trovare modo di calcolare solo differenza rispetto a zoom precedente

    prev_windows_matrix = np.array(prev_windows[:windows_number]).reshape(win_per_line, win_per_line)

    for i in range(win_per_line):
        if not prev_windows_matrix[0, i].isZoom and prev_windows_matrix[1, i].isZoom:
              prev_windows_matrix[0, i].isZoom = True
        if not prev_windows_matrix[win_per_line - 1, i].isZoom and prev_windows_matrix[win_per_line - 2, i].isZoom:
              prev_windows_matrix[win_per_line - 1, i].isZoom = True

    for i in range(win_per_line):
        if not prev_windows_matrix[i, 0].isZoom and prev_windows_matrix[i, 1].isZoom:
            prev_windows_matrix[i, 0].isZoom = True
        if not prev_windows_matrix[i, win_per_line - 1].isZoom and prev_windows_matrix[i, win_per_line - 2].isZoom:
            prev_windows_matrix[i, win_per_line - 1].isZoom = True

    busy_rows = []
    for i in range(win_per_line):
        if not any(el.isZoom == False for el in prev_windows_matrix[i]):
            busy_rows.append(i)

    t_prev_windows_matrix = prev_windows_matrix.T # Transpose the matrix

    busy_columns = []
    for j in range(win_per_line):
        if not any(el.isZoom == False  for el in t_prev_windows_matrix[j]):  # Check each column (now rows in transposed_matrix)
            busy_columns.append(j)


    if (len(busy_rows) > win_per_line - 1 or len(busy_columns) > win_per_line - 1) and zoom < (win_per_line/2 + 1):
        return Response({"message": f"No space left for zoom"}), None, None

    initial_index = window.window_id if window.shifted_index is None else window.shifted_index
    initial_row = initial_index // win_per_line
    initial_col = initial_index % win_per_line
    covered_indices = []

    if window.shifted_index == None and (initial_row in busy_rows or initial_col in busy_columns):
        return Response({"message": f"No space left for zooming window {window.window_id}"}), None, None

    row = initial_row
    col = initial_col

    # expanding or reducing
    if zoom > window.zoom:
        exp = True
    else:
        exp = False

    dx = 1
    dy = 1

    # caso base, giù e destra.
    if col + zoom - 1 < win_per_line: # direzione dx, no bounce sul bordo
        logger.debug("col no bounce")
    else:
        logger.debug("col bounce")
        col = (win_per_line - 1) - (zoom -1) # direzione sx, bounce sul bordo
        dx = -1

    rv = col + zoom - 1

    logger.debug(f"col: {col}")
    logger.debug(f"rv: {rv}")

    logger.debug(f"col after busy check: {col}")


    if row + zoom - 1  < win_per_line: # direzione giù, no bounce sul bordo
        logger.debug("row no bounce")

    else:
        logger.debug("row bounce")
        row = (win_per_line - 1) - (zoom -1) # direzione su, bounce sul bordo
        dy = -1

    dv = row + zoom - 1

    logger.debug(f"row: {row}")
    logger.debug(f"dv: {dv}")

    logger.debug(f"row after busy check: {row}")

    logger.debug(f"dx: {dx}")
    logger.debug(f"dy: {dy}")
    if exp and zoom < (win_per_line/2 + 1):
        while rv in busy_columns or prev_windows_matrix[row, rv].isZoom:
            col += -dx
            rv += -dx
        while dv in busy_rows or prev_windows_matrix[dv, col].isZoom:
            row += -dy
            dv += -dy
        logger.debug(f"col e rv dopo busy exp: {col} {rv}")
        logger.debug(f"row e dv dopo busy exp: {row} {dv}")

    if row < 0 or col < 0:
        return Response({"message": f"Cannot zoom window {window.window_id} at this moment"}), None, None

    new_coord_x = col * SCREEN_SIZE[0] / win_per_line
    new_coord_y = row * SCREEN_SIZE[1] / win_per_line
    new_position = (new_coord_x, new_coord_y)


    # copri posizioni trovate
    for r_exp in range(row, dv+1):
        for c_exp in range(col, rv+1):
            covered_indices.append(r_exp*win_per_line + c_exp)

    # rimuovo la mia finestra iniziale
    if initial_index in covered_indices:
        covered_indices.remove(initial_index)
    if window.window_id in covered_indices:
        covered_indices.remove(window.window_id)
    logger.debug(f"covered_indices: {covered_indices}")

    if exp and zoom < (win_per_line/2 + 1):
        for el in covered_indices:
            if prev_windows[el].isZoom:
                covered_indices.clear()
                col -=1
                logger.debug(f"cleared covered_indices: {covered_indices}")
                break

        for r_exp in range(row, dv+1):
            for c_exp in range(col, rv):
                covered_indices.append(r_exp*win_per_line + c_exp)

        # rimuovo la mia finestra iniziale
        if initial_index in covered_indices:
            covered_indices.remove(initial_index)

        new_coord_x = col * SCREEN_SIZE[0] / win_per_line
        new_coord_y = row * SCREEN_SIZE[1] / win_per_line
        new_position = (new_coord_x, new_coord_y)
        logger.debug(f"covered_indices: {covered_indices}")

    new_shifted_index = row*win_per_line + col

    # comportarsi in modo diverso per rimpicciolimento

    return covered_indices, new_position, new_shifted_index

def calculateReduction(window, windows_number, zoom):
    read_windows()
    win_per_line = int(sqrt(windows_number))  # Assuming a square grid

    previous_zoom = window.zoom

    shifted_index = window.shifted_index

    logger.debug(f"shifted_index: {shifted_index}")

    original_row = window.window_id // win_per_line
    original_col = window.window_id % win_per_line
    logger.debug(f"original_row: {original_row}")
    logger.debug(f"original_col: {original_col}")
    logger.debug(f"previous_zoom: {previous_zoom}")
    logger.debug(f"zoom: {zoom}")
    uncover_windows = []
    counter = 0

    while previous_zoom != zoom:
        logger.debug(f"ciclo {counter}")

        row = shifted_index // win_per_line
        col = shifted_index % win_per_line

        top_left = [row, col]
        logger.debug(f"row: {row}")
        logger.debug(f"col: {col}")

        if row - original_row < 0:
            dy = -1
            row = row + previous_zoom - 1
        else:
            dy = 1

        if col - original_col < 0:
            dx = -1 # direzione delle fienstre da riattivare rispetto all'originale
            col = col + previous_zoom - 1
        else:
            dx = 1

        logger.debug(f"row: {row}")
        logger.debug(f"col: {col}")
        logger.debug(f"dx: {dx}")
        logger.debug(f"dy: {dy}")
        for i in range(0,previous_zoom - 1):
            uncover_windows.append((row + i*dy) * win_per_line + col + (previous_zoom-1)*dx)
            uncover_windows.append((row +(previous_zoom-1)*dy) * win_per_line + col+i*dx)
        uncover_windows.append(((row +(previous_zoom-1)*dy) * win_per_line + col + (previous_zoom-1)*dx))

        logger.debug(f"uncovered_windows: {uncover_windows}")

        previous_zoom -=1
        if dy < 0:
            top_left[0] += 1
        if dx < 0:
            top_left[1] += 1
        shifted_index = top_left[0] * win_per_line + top_left[1]
        logger.debug(f"shifted_index: {shifted_index}")
        # uncover_windows.append(shifted_index)
        counter +=1

    if zoom == 1:
        col = original_col
        row = original_row
        shifted_index = None

    new_coord_x = top_left[1] * SCREEN_SIZE[0] / win_per_line
    new_coord_y = top_left[0] * SCREEN_SIZE[1] / win_per_line
    new_position = (new_coord_x, new_coord_y)



    return uncover_windows, new_position, shifted_index




def updateWindowsForLayout(windows_list, windows_number, active_windows):
    for i in range(windows_number):
        if i in range(active_windows):
            windows_list[i].isActive = True
        else:
            windows_list[i].isActive = False
        windows_list[i].zoom = 1
        windows_list[i].isZoom = False
        windows_list[i].shifted_index = None

    for i in range(windows_number, MAX_WINDOWS):
        windows_list[i].isActive = False
        windows_list[i].zoom = 1
        windows_list[i].isZoom = False
        windows_list[i].shifted_index = None

    windows_list = createLayout(windows_list, windows_number)

    return windows_list

def getZoomedWindowSize(zoom, windows_number):
    win_per_line = int(sqrt(windows_number))  # Assuming a square grid
    width = int(SCREEN_SIZE[0] / win_per_line * zoom)
    height = int(SCREEN_SIZE[1] / win_per_line * zoom)
    return (width, height)

def calculateZoom(window, last_state_entry, new_zoom):
    new_windows = []
    if new_zoom > window.zoom:
        # ogni finestra coperta dev'essere segnata come isZoom
        # se una di queste finestre è gia isZoom, bisogna rifiutare la chiamata
        covered_indices, new_position, new_shifted_index = calculateExpansion(window, last_state_entry.windows_number, new_zoom)
        if isinstance(covered_indices, Response):
            return covered_indices

        logger.debug(f"covered_indices: {covered_indices}")
        size = getZoomedWindowSize(new_zoom, last_state_entry.windows_number)
        wins_to_cover = []

        requested_window_data = cloneDjangoDict(window, isZoom=True, zoom=new_zoom, width=size[0], height=size[1], coord_x=new_position[0], coord_y=new_position[1], shifted_index=new_shifted_index)
        wins_to_cover.append(requested_window_data)


        for el in covered_indices:
            last_window_entry = Window.objects.get(window_id=el)
            if not last_window_entry.isActive: # già nascosta e coperta da zoom, non aggiungere a calcoli
                logger.debug(f"FINESTRA {last_window_entry.window_id} già nascosta e coperta da zoom, non aggiungere a calcoli")

                continue
            if last_window_entry.isZoom:
                return Response({"message": f"Cannot zoom window {window.window_id}: window {last_window_entry.window_id} is preventing it"})

            requested_window_data = cloneDjangoDict(last_window_entry, isActive=False, isZoom=True)
            wins_to_cover.append(requested_window_data)

        for win in wins_to_cover:
            req_window, created = RequestedWindow.objects.update_or_create(window_id=win.get("window_id", None), defaults={**win})
            new_windows.append(req_window)
        connection.close()
        return new_windows
    else:
        # come calculateExpansion(), ma calcolando differenza (negativa) dello zoom precedente 
        uncovered_indices, new_position, new_shifted_index = calculateReduction(window, last_state_entry.windows_number, new_zoom)

        if isinstance(uncovered_indices, Response):
            return uncovered_indices
        uncovered_indices = set(uncovered_indices)
        uncovered_indices = list(uncovered_indices)
        logger.debug(f"uncovered indices: {uncovered_indices}")


        size = getZoomedWindowSize(new_zoom, last_state_entry.windows_number)

        requested_window_data = cloneDjangoDict(window, zoom=new_zoom, width=size[0], height=size[1], coord_x=new_position[0], coord_y=new_position[1], shifted_index=new_shifted_index)
        req_window, created = RequestedWindow.objects.update_or_create(window_id=window.window_id, defaults={**requested_window_data})
        new_windows.append(req_window)

        for el in uncovered_indices:
            last_window_entry = Window.objects.get(window_id=el)
            requested_window_data = cloneDjangoDict(last_window_entry, isActive=True, isZoom=False)
            req_window, created = RequestedWindow.objects.update_or_create(window_id=el, defaults={**requested_window_data})
            new_windows.append(req_window)
        connection.close()
        return new_windows

def updateLayoutInDB(prev_windows, windows_number, active_windows, api_call):
    prev_windows = updateWindowsForLayout(prev_windows, windows_number, active_windows)
    uploadRequestedWindows(prev_windows)

    for i in range(MAX_WINDOWS):
        makeDeltaRows(None, prev_windows[i], api_call)

def alarmClear(api_call=None):
    logger.debug("Chiamato alarmClear")
    last_telecamere_state_entry = State.objects.filter(mode=MODE['TELECAMERE']).latest('created')
    last_telecamere_state_entry = cloneDjangoDict(last_telecamere_state_entry)
    last_telecamere_state_entry = State.objects.create(**last_telecamere_state_entry)
    connection.close()

    makeDeltaRows(last_telecamere_state_entry, None, api_call)

    backup_windows = read_backup_windows()

    requested_windows = uploadRequestedWindows(backup_windows)

    for win in requested_windows:
        makeDeltaRows(None, win, api_call)

    reset_backup_windows()

    return last_telecamere_state_entry


# API services section

def alarmClearAPIService(data, api_call):
    clear = data['clear']

    if not clear:
        return Response({'status': 'success', 'message': f"No action"})

    try:
        last_state_entry = State.objects.latest('created')
        connection.close()
    except State.DoesNotExist:
        last_state_entry = mockedStateInstance('TELECAMERE')
        pass # handle chiamata senza stato

    if last_state_entry.mode != MODE['ALLARME']:
        return Response({"message": "must be in ALARM mode to clear alarms"}, status=400)

    alarmClear(api_call)


    return Response({'status': 'success', 'message': f"Alarm cleared"})

def alarmAPIService(data, api_call):
    alarm_window_data = data.get("alarm_window")
    alarm_state_data = data.get("alarm_state")

    stream = alarm_window_data['stream']
    labelText = alarm_window_data['labelText']
    timer = alarm_window_data['timer']
    enableAlarmIcon = alarm_window_data['enableAlarmIcon']

    alarm_border_color = alarm_state_data['alarm_border_color']
    alarm_border_thickness = alarm_state_data['alarm_border_thickness']

    # read current windows
    prev_state = read_state()
    prev_windows = read_windows()


    if prev_state.mode != MODE['ALLARME'] and not any(window.isAlarm for window in prev_windows):
        uploadBackupWindows(prev_windows)
        for i in range(MAX_WINDOWS):
            mocked_data_window = RequestedWindow(window_id=i)
            mocked_data_window = mocked_data_window.__dict__.copy()
            mocked_data_window.pop('window_id', None)
            # metto isActive false?
            prev_windows[i] = createMockedReqWindowObject(i, **mocked_data_window)


    logger.debug(f"service.py: stato precedente ALLARME")

    # update timeout se stream uguale
    try:
        first_matching_stream = next(el for el in prev_windows if el.stream == stream)
    except StopIteration:
        first_matching_stream = None  # Or any other default value you prefer

    logger.debug(f"service.py first_matching_stream: {first_matching_stream}")

    timeout = getTime(timer)

    logger.debug(f"timeout in service.py: {timeout}")

    if first_matching_stream:
        requested_window_data = cloneDjangoDict(first_matching_stream, timeout=timeout)
        req_window, created = RequestedWindow.objects.update_or_create(window_id=requested_window_data.get('window_id', None), defaults={**requested_window_data})
        makeDeltaRows(None, req_window, api_call)
        return Response({"message": f"service.py: Alarm {stream} timer updated."})

    # costruisco stato
    wins_in_alarm = len([el for el in prev_windows if el.isAlarm]) + 1
    windows_number = closest_square(wins_in_alarm)
    active_windows = wins_in_alarm
    mode = MODE['ALLARME']

    new_alarm_window = cloneDjangoDict(prev_windows[wins_in_alarm - 1], stream=stream, labelText=labelText, isAlarm=True, enableAlarmIcon=enableAlarmIcon, timeout=timeout)
    new_alarm_window = RequestedWindow(**new_alarm_window)
    prev_windows[wins_in_alarm -1] = new_alarm_window

    new_state = cloneDjangoDict(
                                prev_state,
                                windows_number=windows_number,
                                active_windows=active_windows,
                                alarm_windows=wins_in_alarm,
                                mode=mode,
                                alarm_border_color=alarm_border_color,
                                alarm_border_thickness=alarm_border_thickness
                                )
    State.objects.create(**new_state)
    connection.close()

    logger.debug(f"service.py new_state: {new_state}")

    makeDeltaRows(new_state, None, api_call)

    updateLayoutInDB(prev_windows, windows_number, active_windows, api_call)

    return Response({'status': 'success', 'message': 'Alarm updated successfully.'})

def isAlarmExpired(timeout):
    if timezone.localtime(timezone.now()) > timezone.localtime(timeout):
        logger.debug(f"timeout: {timezone.localtime(timeout)}")
        logger.debug(f"timezone.localtime(timezone.now()): {timezone.localtime(timezone.now())}")
        logger.debug(timezone.localtime(timezone.now()) > timezone.localtime(timeout))
        return True
    return False

def alarmExpiredAPIService(data, api_call):
    state_instance = State.objects.latest('created')

    if state_instance.mode != MODE['ALLARME']:
        return Response({"message": "must be in ALARM mode to check expired alarms"}, status=400)

    requested_windows = read_requested_windows()
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
        return Response({'status': 'success', 'message': 'No expired alarms.'})

    for el in expired_alarms:
        logger.debug("in expired_alarms")
        logger.debug(f"el: {el.__dict__}")
        logger.debug(f"el.window_id: {el.window_id}")
        expired = createMockedReqWindowObject(el.window_id,
                                    isAlarm=False,
                                    stream='',
                                    isActive=False,
                                    timeout=None,
                                    )

        requested_windows[el.window_id] = expired 


    state_instance.alarm_windows = len([win for win in requested_windows if win.isAlarm])
    logger.debug(f"new alarm_windows number: {state_instance.alarm_windows}")

    sorted_windows = sorted(requested_windows, key=lambda window: not window.isAlarm)
    sorted_windows = resetWinIds(sorted_windows)
    windows_number = closest_square(state_instance.alarm_windows)

    logger.debug(f"windows_number: {windows_number}")
    if windows_number > 0:

        new_state = cloneDjangoDict(state_instance, windows_number=windows_number, active_windows=state_instance.alarm_windows, alarm_windows=state_instance.alarm_windows)

        State.objects.create(**new_state)

        makeDeltaRows(new_state, None, api_call)


        updateLayoutInDB(sorted_windows, windows_number, state_instance.alarm_windows, api_call)
    else:
        alarmClear(api_call)

    connection.close()
    return Response({'status': 'success', 'message': 'Expired alarms updated successfully.'})

def browserWindowAPIService(data, api_call):
    window_id = data['window_id']
    urlBrowser = data['urlBrowser']

    last_state_entry = State.objects.latest('created')
    if last_state_entry.mode != MODE['TELECAMERE']:
        return Response({"message": "must be in mode TELECAMERE to add a browser window"}, status=400)

    try:
        last_window_entry = Window.objects.get(window_id=window_id)

    except Window.DoesNotExist:
        last_window_entry = createMockedWindowObject()

    except Window.MultipleObjectsReturned:
        last_window_entry = Window.objects.filter(window_id=window_id).first()

    visualizzazione = VISUALIZZAZIONE['BROWSERWINDOW']

    requested_window_data = cloneDjangoDict(last_window_entry, urlBrowser=urlBrowser, isBrowser=True, visualizzazione=visualizzazione)
    req_window, created = RequestedWindow.objects.update_or_create(window_id=window_id, defaults={**requested_window_data})
    connection.close()
    makeDeltaRows(None, req_window, api_call)
    return Response({"message": "Updated browser_window"})

# non completa, per il momento la desktop window utilizza la stessa logica temporanea di clock view
def screenShareWindowAPIService(data, api_call):
    window_id = data['window_id']

    last_state_entry = State.objects.latest('created')
    if last_state_entry.mode != MODE['TELECAMERE']:
        return Response({"message": "must be in mode TELECAMERE to add a screen share window"}, status=400)

    try:
        last_window_entry = Window.objects.get(window_id=window_id)

    except Window.DoesNotExist:
        last_window_entry = createMockedWindowObject()

    except Window.MultipleObjectsReturned:
        last_window_entry = Window.objects.filter(window_id=window_id).first()

    visualizzazione = VISUALIZZAZIONE['DESKTOP']

    requested_window_data = cloneDjangoDict(last_window_entry, isBrowser=True, visualizzazione=visualizzazione)
    req_window, created = RequestedWindow.objects.update_or_create(window_id=window_id, defaults={**requested_window_data})
    connection.close()
    makeDeltaRows(None, req_window, api_call)
    return Response({"message": "Updated browser_window"})

def changeStreamAPIService(data, api_call):
    window_id = data['window_id']
    stream = data['stream']
    labelText = data['labelText']
    enableLogo = data['enableLogo']
    enableWatermark = data['enableWatermark']

    last_state_entry = State.objects.latest('created')
    if last_state_entry.mode != MODE['TELECAMERE']:
        return Response({"message": "must be in mode TELECAMERE to changeStream"}, status=400)

    try:
        last_window_entry = Window.objects.get(window_id=window_id)

    except Window.DoesNotExist:
        last_window_entry = createMockedWindowObject(window_id)

    except Window.MultipleObjectsReturned:
        last_window_entry = Window.objects.filter(window_id=window_id).first()


    if labelText == '':
        labelText = last_window_entry.labelText

    requested_window_data = cloneDjangoDict(last_window_entry, 
                                                stream=stream,
                                                labelText=labelText,
                                                enableLogo=enableLogo,
                                                enableWatermark=enableWatermark,
                                                visualizzazione=VISUALIZZAZIONE['OPENGL'],
                                                isBrowser=False,
                                                )
    req_window, created = RequestedWindow.objects.update_or_create(window_id=window_id, defaults={**requested_window_data})
    connection.close()
    makeDeltaRows(None, req_window, api_call)
    return Response({"message": "Stream and label changed"})


def switchAPIService(data, api_call):
    mode = int(data['mode'])
    try:
        if mode == MODE['TELECAMERE']:
            logger.debug("in telecamere")
            last_state_entry = State.objects.filter(mode=MODE['TELECAMERE']).order_by('-created').first()
            new_state = last_state_entry.clone()

            State.objects.create(**new_state)
            makeDeltaRows(new_state, None, api_call)
            return Response({"message": "Switched to normal mode"})
        elif mode == MODE['BROWSER']:
            logger.debug("in browser")
            last_state_entry = State.objects.filter(mode=MODE['BROWSER']).order_by('-created').first()
            new_state = last_state_entry.clone()

            State.objects.create(**new_state)
            makeDeltaRows(new_state, None, api_call)
            return Response({"message": "Switched to browser mode"})
        elif mode == MODE['DESKTOP']:
            logger.debug("in desktop")
            last_state_entry = State.objects.filter(mode=MODE['DESKTOP']).order_by('-created').first()
            new_state = last_state_entry.clone()

            State.objects.create(**new_state)
            makeDeltaRows(new_state, None, api_call)
            return Response({"message": "Switched to browser mode"})

        connection.close()
        return Response({"message": "Not a valid mode"}, status=400)
    except State.DoesNotExist:
        last_window_entry = createMockedStateObject(mode)
        return Response({"message": f"Previous state {mode} missing, creating a default one"})

def zoomAPIService(data, api_call):
    window_id = data['window_id']
    zoom = data['zoom']

    last_state_entry = State.objects.latest('created')

    if last_state_entry.mode != MODE['TELECAMERE']:
        return Response({"message": "must be in mode TELECAMERE to issue zoom"}, status=400)

    if zoom < 1:
        return Response({"message": "Zoom must be a positive integer"}, status=400)
    # Retrieve the existing window or create a new one if it doesn't exist
    try:
        last_window_entry = Window.objects.get(window_id=window_id)
    except Window.DoesNotExist:
        last_window_entry = createMockedWindowObject()
    connection.close()

    if last_window_entry.zoom == zoom: # stesso zoom di prima, nessun'azione
        return Response({"message": f"Zoom level for window {window_id} is already {zoom}"}, status=400)

    if not last_window_entry.isActive:
        return Response({"message": f"Window {window_id} is not active and cannot be zoomed"}, status=400)

    if zoom > 1:
        isZoom = True
    else:
        isZoom = False

    if (zoom > int(sqrt(last_state_entry.windows_number))):
        return Response({"message": f"Not valid zoom for this layout"}, status=400)

    last_window_entry.isZoom = isZoom
    # Update the zoom level of the window
    windows = calculateZoom(last_window_entry, last_state_entry, zoom)

    # se errore/zoom non aggiornato, calculateZoom ritorna un oggestto Response
    if isinstance(windows, Response):
        return windows

    # aggiornare anche stato con nuovo numero finestre attive

    if len(windows) > 0:
        logger.debug(f"windows changed: {len(windows)}")
        for win in windows:
            makeDeltaRows(None, win, api_call)


    return Response({"message": f"Zoom level for window {window_id} updated to {zoom}"})

def restartAPIService(data):
    reset = data['isReset']
    if reset:

        return Response({"message": "Restart succeded"})
    else:
        return Response({"message": "Restart value was False"})

def resetAPIService(data, api_call):
    reset = data['isReset']
    if reset:
        new_state = createMockedStateObject()

        makeDeltaRows(new_state, None, api_call)
        clearRequestWindow(api_call)
        clearWindow(api_call)
        clearBackupWindow(api_call)

        return Response({"message": "Reset succeded"})
    else:
        return Response({"message": "Reset value was False"})

def clearRequestWindow(api_call):
    for i in range(16):

            mocked_data_window = RequestedWindow(window_id=i)
            mocked_data_window = mocked_data_window.__dict__.copy()
            mocked_data_window.pop('window_id', None)
            mocked_data_window.pop('coord_x', None)
            mocked_data_window.pop('coord_y', None)

            req_window = resetMockedReqWindowObject(i, **mocked_data_window)

            makeDeltaRows(None, req_window, api_call)

def clearWindow(api_call):
    for i in range(16):

            mocked_data_window = Window(window_id=i)
            mocked_data_window = mocked_data_window.__dict__.copy()
            mocked_data_window.pop('window_id', None)
            mocked_data_window.pop('coord_x', None)
            mocked_data_window.pop('coord_y', None)

            window = resetMockedWindowObject(i, **mocked_data_window)

            makeDeltaRows(None, window, api_call)

def clearBackupWindow(api_call):
    for i in range(16):

            mocked_data_window = BackupWindow(window_id=i)
            mocked_data_window = mocked_data_window.__dict__.copy()
            mocked_data_window.pop('window_id', None)
            mocked_data_window.pop('coord_x', None)
            mocked_data_window.pop('coord_y', None)

            backup_window = resetMockedBackupWindowObject(i, **mocked_data_window)

            makeDeltaRows(None, backup_window, api_call)

def browserAPIService(data, api_call):
    mode = BROWSER
    last_state_entry = State.objects.filter(mode!=ALLARME).order_by('-created').first() # if an alarm is going and browser is called, it should stop

    new_state = last_state_entry.clone(mode = BROWSER)
    State.objects.create(**new_state)
    connection.close()
    makeDeltaRows(new_state, None, api_call)
    return Response({"message": "Success"})

def changeLayoutAPIService(data, api_call):
    def is_perfect_square(n):
        """Check if n is a perfect square."""
        sqrt_n = int(n**0.5)
        return sqrt_n*sqrt_n == n

    windows_number = data['windows_number']

    try:
        last_state_entry = State.objects.latest('created')
        if last_state_entry.mode != MODE['TELECAMERE']:
            return Response({"message": "must be in normal mode to changeStream"}, status=400)

    except State.DoesNotExist:
        last_state_entry = mockedStateInstance('TELECAMERE')
        pass # handle chiamata senza stato

    if windows_number > MAX_WINDOWS or not is_perfect_square(n=windows_number):
        return Response({'status': 'error', 'message': 'Invalid windows number'}, status=400)

    if last_state_entry.windows_number == windows_number:
        return Response({'status': 'success', 'message': f"State not changed. Windows number: {windows_number}"})

    new_state = cloneDjangoDict(last_state_entry, windows_number=windows_number, active_windows=windows_number)
    State.objects.create(**new_state)
    connection.close()

    windows_list = read_requested_windows()
    windows_list = updateWindowsForLayout(windows_list, windows_number, windows_number)
    uploadRequestedWindows(windows_list)

    makeDeltaRows(new_state, None, api_call)

    for i in range(MAX_WINDOWS):
        makeDeltaRows(None, windows_list[i], api_call)

    return Response({'status': 'success', 'message': 'Window changed successfully.'})