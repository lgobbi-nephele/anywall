import time
from django.utils import timezone
import sys
import os
import psutil
from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, freeze_support

MAX_WINDOWS = 16
processes = {}

if getattr(sys, 'frozen', False):
    # Running as a bundled executable
    BASE_DIR = sys._MEIPASS
else:
    # Running as a script
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Add Django project to sys.path
    sys.path.append(os.path.join(BASE_DIR, 'django', 'anywall'))



from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

current_pid = os.getpid()

"""
Import e init Django 
"""
import django
from django.test.runner import DiscoverRunner

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anywall.settings")

test_runner = DiscoverRunner()

django.setup(test_runner)

django.setup()

from anywall_app.models import Api_calls as django_api_calls
from anywall_app.models import VISUALIZZAZIONE
from django.db.utils import ProgrammingError
from django.db import OperationalError


def start_server():
    try:
        from daphne.server import Server
        from daphne.endpoints import build_endpoint_description_strings
        from anywall.asgi import application

        if getattr(sys, 'frozen', False):
            asgi_dir = BASE_DIR
        else:
            # Running as a script
            asgi_dir = os.path.join(BASE_DIR, 'django', 'anywall')

        sys.path.append(asgi_dir)
        os.chdir(asgi_dir)

        # Start the Daphne server programmatically
        endpoints = build_endpoint_description_strings(host="0.0.0.0", port="8000")
        server = Server(application=application, endpoints=endpoints)
        server.run()

    except Exception as e:
        logger.error(e)
        # logger.error("Traceback: %s", traceback.format_exc())
        sys.exit(0)

def run_django_server():
    global server_process
    p = Process(target=start_server)  # Using the top-level start_server function
    p.start()
    processes['server_process'] = p
    logger.debug("server process started")

def start_manager(init, shared_dict):
    import manager
    try:
        manager.main(init, shared_dict)
    except Exception as e:
        logger.error(e)
        sys.exit(0)


def run_manager(init):
    logger.debug(f"init: {init}")
    p = Process(target=start_manager, args=(init, pm.shared_dict, ))
    p.start()
    processes['manager_process'] = p
    logger.debug("Manager process started")



def check_pid_running(p, pm):
    # Check if a PID exists and if the process is alive
    try:
        if not p.is_alive():
            raise psutil.NoSuchProcess(p.pid)

        # Use psutil to check if the process is still running on Windows
        process = psutil.Process(p.pid)
        if not process.is_running():
            raise psutil.NoSuchProcess(p.pid)

    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.warning(f"Process {p.pid} error: {e}")  # Not a real error
        if "switchView" in pm.shared_dict:
            window_id = pm.shared_dict.pop("switchView")

            if f"window_p_{window_id}" in processes:
                processes[f"window_p_{window_id}"].terminate()
                processes[f"window_p_{window_id}"].join()
                processes[f"window_p_{window_id}"] = None

            if f"window_p_{window_id}" in pm.shared_dict:
                data = pm.shared_dict.pop(f"window_p_{window_id}")
            else:
                # reset?
                data = None

            if window_id in pm.shared_dict:
                pm.shared_dict.pop(window_id)

            add_single_window(pm, f"window_p_{window_id}", data)
            return True

        p.terminate()
        p.join()
        return False

    else:
        return True



def check_pid_running_linux(p):
    try:
        # Try to send signal 0 to the PID (does not kill the process)
        os.kill(p.pid, 0)
        if not p.is_alive():
            raise OSError
    except OSError as e:
        logger.warning(f"process {p} OSError: {e}") # not a real error
        logger.warning(e)
        if "switchView" in ProcessManager.shared_dict:
            window_id = ProcessManager.shared_dict.pop("switchView")

            processes[f"window_p_{window_id}"].terminate()
            processes[f"window_p_{window_id}"].join()
            processes[f"window_p_{window_id}"] = None

            if f"window_p_{window_id}" in ProcessManager.shared_dict:
                data = ProcessManager.shared_dict.pop(f"window_p_{window_id}")
            else:
                # reset?
                pass
            if window_id in ProcessManager.shared_dict:
                ProcessManager.shared_dict.pop(window_id)

            add_single_window(pm, f"window_p_{window_id}", data)
            return True
        p.terminate()
        p.join()
        return False
    else:
        return True

# approccio corrente, solo PM.shared_dict.
# Se cade shared dict?
# Dovrei avere sempre una copia di shared dict in locale in questo modulo?
def restartPM(pm, force_restart=False):
        # se caduto, riavvio lo shared dict prima di riavviare i processi 
        if (force_restart or processes['PM_process'] is None
            or not check_pid_running(processes['PM_process'], pm)):
            logger.info("PM down")
            logger.info("Restarting PM...")
            processes['PM_process'] = None
            pm.deleteInstance()
            pm = ProcessManager.getInstance()
            processes['PM_process'] = pm.p
            return True



def restartServer():
    if (processes['server_process'] is None
        or not check_pid_running(processes['server_process'], pm)):
        logger.info("Restarting server...")
        processes['server_process'] = None
        run_django_server()

def restartManager(init='noinit'):
    if (processes['manager_process'] is None
        or not check_pid_running(processes['manager_process'], pm)):
        logger.info("Restarting manager...")
        processes['manager_process'] = None
        run_manager(init)

def restartWindows(force_restart=False):
    global reset_windows

    # killa finestre se processi esistono
    window_processes = {key: value for key, value in processes.items() if key.startswith('window_p_') and value is not None}

    if force_restart or len(window_processes) < MAX_WINDOWS:

        # prima di killare le finestre, le disabilito se possibile, per evitare errori
        for i in range(len(window_processes)):
            pm.shared_dict[i] = {"close": True}

        for key, p in window_processes.items():
            p.terminate()
            p.join()

        pm.shared_dict.clear()

        for i in range(16):
            processes[f"window_p_{i}"] = None

        reset_windows = True
        # starto manager con init finestre e starto finestre
        if processes['manager_process'] is not None:
            os.kill(processes['manager_process'].pid, 15)
        restartManager('init_windows')
        return True

def kill_manager_and_windows():
    if processes['manager_process'] is not None:
        processes['manager_process'].terminate()
        processes['manager_process'].join()
        processes['manager_process'] = None

def total_restart(pm):
    restartPM(pm=pm, force_restart=True)
    kill_manager_and_windows()
    restartWindows(force_restart=True)
    restartServer()
    restartManager()

def restart_processes():

    logger.debug("in restart processes")

    if restartPM(pm):
        kill_manager_and_windows()
        restartWindows(force_restart=True)
        restartServer()
        return

    restartServer()

    if restartWindows():
        return

    restartManager()
    pm.shared_dict.clear()

def add_single_window(pm, el, data):
    global processes
    p = Process(target=create_window, args=(pm.shared_dict, ), kwargs=data)
    p.start()
    processes[el] = p


def start_windows():
    global processes
    global reset_windows

    try:

        if check_pid_running(processes['PM_process'], pm):
            logger.debug(f"Finestre ready?: {'ready' in pm.shared_dict}")
            while "ready" not in pm.shared_dict:
                logger.debug("start_windows: dentro while")
                if not check_pid_running(processes["manager_process"], pm):
                    logger.debug("start_windows: dentro if")
                    processes["manager_process"] = None
                    reset_windows = False
                    return
                time.sleep(0.5)

            pm.shared_dict.pop("ready")

            for el in pm.shared_dict.keys():
                if isinstance(el, str):
                    if el.startswith("window_p_"):
                        data = pm.shared_dict.pop(el)
                        add_single_window(pm, el, data)
            reset_windows = False
            logger.debug(f"processes: {processes}")
            return

        raise BrokenPipeError
    except BrokenPipeError:
        pm.deleteInstance()
        processes['PM_process'] = None
        reset_windows = False

def create_window(shared_dict, **kwargs):
    from window_handler import WindowHandler
    from multiprocessing import current_process
    from process_manager import ProcessManager
    process_manager = ProcessManager(shared_dict=shared_dict, pid=os.getpid(), p=current_process())
    visualizzazione = kwargs.get("visualizzazione")

    if visualizzazione == VISUALIZZAZIONE['BROWSERWINDOW'] or visualizzazione == VISUALIZZAZIONE['DESKTOP']:
        app = QApplication(sys.argv)
        WindowHandler(**kwargs, process_manager=process_manager)
        sys.exit(app.exec_())
    else:
        WindowHandler(**kwargs, process_manager=process_manager)

    logger.debug("window created")

def execute():
    logger.info("Application started")

    global reset_windows
    reset_windows = True
    logger.debug(f"Parent Process PID: {os.getpid()}")

    run_django_server()
    run_manager('init_windows')

    from utils import getReceivedApiCalls

    last_api_call_dt_creation=timezone.localtime(timezone.now())

    try:

        while True:
            gotReset = False

            if reset_windows:
                logger.info("Starting windows after reset")
                start_windows()

            count_read_api = 0

            while count_read_api < 5:

                api_calls = []
                try:
                    api_calls = getReceivedApiCalls(last_api_call_dt_creation)
                except OperationalError as e:
                    logger.error(f"monitor.py: getReceivedApiCalls 293: DB connection error: {e}")
                except django_api_calls.DoesNotExist as e:
                    logger.error(e)
                    time.sleep(5)


                while api_calls:
                    current_api_call = api_calls.pop(0)
                    if current_api_call.name == 'reset':
                        logger.info("Restarting windows only...")
                        restartWindows(force_restart=True)
                        last_api_call_dt_creation = timezone.localtime(current_api_call.created)
                        gotReset = True
                        break
                    last_api_call_dt_creation = timezone.localtime(current_api_call.created)
                if gotReset:
                    break

                count_read_api += 1
                time.sleep(1)
            if gotReset:
                continue

            toRestart = False

            # in caso di reset, updatare qui last_api_call_dt_creation

            # caso 1: PM o main caduti
            # caso 2:
            # django va giù, main verifica PID dajngo server, si autokilla, viene riavviato da monitor
            try:
                for key, el in processes.items():
                    # print(PM.shared_dict)
                    if el is None or not check_pid_running(el, pm):
                        processes[key] = None
                        if el is None:
                            logger.debug(f"{key} nullo")
                        else:
                            logger.debug(f"{key} killato")
                        toRestart = True
            except RuntimeError as e:
                logger.error(e)
                continue

            if toRestart:
                restart_processes()
                continue

            # caso 3:
            # arriva chiamata di reset dall'utente, main rileva chiamata (come attualmente sotto) e si spegne da solo
            # poi verrà ricreato da monitor

            # if 'reset' in PM.shared_dict and PM.shared_dict['reset'] == True:
            #     restart_processes()



            # elapsed_time = time.time() - start_time
            # print(elapsed_time)
            # if elapsed_time >= 15:
            #     start_time = time.time()
            #     ProcessManager.exit()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
        logger.info("Cleaning up processes...")
        for key, process in processes.items():
            if process is not None:
                logger.info(f"Terminating process {key} with PID {process.pid}")
                process.terminate()
                process.join()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    from multiprocessing import Manager
    from process_manager import ProcessManager

    freeze_support()
    logger.debug(f"Monitor current process PID is: {current_pid}")
    manager = Manager()
    shared_dict = manager.dict()
    global pm
    pm = ProcessManager(shared_dict, manager._process.pid, manager._process)
    processes['PM_process'] = pm.p

    execute()




# RIAVVIO
# va giù server:
    # catcho l'exception qui, riavvio processo server
    # catcho eccezioni di lettura DB in manager, le gestiamo in modo che il manager rimanga up, così che non vada in errore

# va giù manager:

# va giù PM:

# vanno giù finestre:




# ECCEZIONI CHIAMATA restart_processes() IN CLASSE MONITOR
# Deve portarmi automaticamente a un riavvio di tutti i processi (meno process manager)


# ECCEZIONI NEL RESTO DEL SOFTWARE
# Studio più approfondito su tipo di eccezione, per il momento feedback all'utente, più tardi implementeremo con cliente casi in cui safetyconf viene chiamata automaticamente


# ricevuta chiamata safetyconf da utente:
    # riavvio tutto meno che server django
    # faccio clear di PM.shared_dict