import subprocess
from math import sqrt
import re
import ctypes

import sys

from anywall_app.models import MODE

from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

processes = {}

MAX_WINDOWS = 16

def makeProcessWindow(process_manager, window, size_x, size_y, coord_x, coord_y, pos=None):
    delattr(window, "width")
    delattr(window, "height")
    delattr(window, "coord_x")
    delattr(window, "coord_y")

    process_manager.shared_dict[f"window_p_{window.window_id}"] = {  **(window.__dict__),
                                                                    "width": size_x,
                                                                    "height": size_y,
                                                                    "coord_x": coord_x,
                                                                    "coord_y": coord_y
                                                                 }

class Screen:
    def __init__(self, process_manager, state_instance, windows_list): # Default 16 finestre vuote
        global processes
        self.window_handler = None
        if state_instance.mode == MODE['TELECAMERE']:
            self.windows_list = windows_list
            self.win_number = state_instance.windows_number
            self.active_windows = state_instance.active_windows
            
            self.width, self.height = self.get_display_size()
            self.process_manager = process_manager
            self.createLayout(self.windows_list, self.win_number, self.active_windows)


    def createLayout(self, windows_list, win_number, active_windows):
        try:
            for window in windows_list:
                logger.info(f"Screen_helper: Finestra {window.window_id}: {window.width}x{window.height}, ({window.coord_x}, {window.coord_y}), {window.isActive}")
                makeProcessWindow(self.process_manager, window, window.width, window.height, window.coord_x, window.coord_y)
        except Exception as e: # if data is missing
            logger.error("Errore in screen.createLayout:")
            logger.error(e)
            if processes:
                processes.clear()
            self.createLayoutFrom0(windows_list, win_number, active_windows)
    
    def createLayoutFrom0(self, windows_list, win_number, active_windows):
        logger.debug("start createLayoutFrom0")
        try:
            coord_x = 0
            coord_y = 0
            win_per_line = int(sqrt(win_number))
            size_x = int(self.width / win_per_line)
            size_y = int(self.height / win_per_line)

            lines_in_offset = 0
            offset_multiplier = 0
            for i in range(MAX_WINDOWS):
                zoom = windows_list[i].zoom

                if zoom != 1:
                    lines_in_offset = zoom if lines_in_offset <= 0 else lines_in_offset
                    offset_multiplier = zoom

                makeProcessWindow(self.process_manager, windows_list[i], size_x, size_y, zoom, coord_x, coord_y)
                coord_x += size_x * zoom


                if coord_x >= self.width:
                    lines_in_offset -= 1 * zoom
                    if lines_in_offset <= 0:
                        offset_multiplier = 0
                    coord_x = size_x * offset_multiplier 
                    coord_y += size_y * zoom

        except KeyboardInterrupt:
            logger.warning("Caught KeyboardInterrupt, terminating processes...")
            for key, p in processes.items():
                logger.debug(p['process'])
                p['process'].terminate()
            for key, p in processes.items():
                p['process'].join()
            processes.clear()
            sys.exit(0)

    def get_display_size_linux(self):
        cmd = ['xrandr']
        cmd2 = ['grep', '+0+0']

        pattern = r'\b\d+x\d+\b'

        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            p2 = subprocess.Popen(cmd2, stdin=p.stdout, stdout=subprocess.PIPE)
            p.stdout.close()

            resolution_string, _ = p2.communicate()
            p2.stdout.close()
            resolution_string = resolution_string.decode("utf-8")
            logger.debug(f"resolution string: {resolution_string}")

                #Check if the expected pattern is found
            if "connected" in resolution_string:
                resolution = re.search(pattern, resolution_string).group(0)
                width, height = map(int, resolution.split('x'))
                return width, height
            else:
                raise ValueError("Resolution not found in xrandr output")
        except Exception as e:
          logger.warning(f"Failed to get display size: {e}")
        logger.warning("Setting widht and height to default 1920x1080")
        return 1920, 1080

    def get_display_size(self):
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()  # Enables high DPI awareness for accurate resolution
            width = user32.GetSystemMetrics(0)  # Screen width
            height = user32.GetSystemMetrics(1)  # Screen height

            logger.info(f"Screen_helper: Trovata display size: {width}x{height}")
            return width, height
        except Exception as e:
            logger.warning(f"Failed to get display size on Windows: {e}")
            return 1920, 1080