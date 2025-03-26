
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import os
import cv2
import time
import signal
import logging
import numpy as np
import subprocess
import ctypes
from dotenv import load_dotenv
from math import floor
from threading import Thread, Event
from datetime import datetime
from config import CONFIG_FILE

from manager import callAlarmExpired
from django.db import connection

from anywall_app.logger import setup_logger
from anywall_app.models import VISUALIZZAZIONE, IMAGE_SCOPE
from anywall_app.models import State as django_state
from anywall_app.models import ImageModel as django_image
from anywall_app.models import RequestedWindow as django_requested_window

logger = setup_logger(__name__)

OpenGL.ERROR_CHECKING = True
os.environ["SDL_VIDEO_X11_FORCE_EGL"] = "1"

DISPLAY_SIZE = (1920, 1080)


class OpenGLError(Exception):
    """Base exception for OpenGL-related errors"""
    pass


def check_for_errors():
    """Check for OpenGL errors and log them if found"""
    err = glGetError()
    if err != GL_NO_ERROR:
        error_message = f"OpenGL error detected: {gluErrorString(err)}"
        logger.error(error_message)
        return error_message
    return None


def check_opengl_errors(func):
    """Decorator to check for OpenGL errors after function execution"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        check_for_errors()
        return result
    return wrapper


class RTSPStreamCaptureConfig:
    """Configuration settings for RTSP stream capture"""
    def __init__(self, max_buffer_size=100, target_fps=15):
        self.max_buffer_size = max_buffer_size
        self.target_fps = target_fps


class RTSPStreamCapture:
    """
    Captures frames from an RTSP stream using FFmpeg.
    Handles stream buffering, reconnection, and frame delivery.
    """
    def __init__(self, rtsp_url, width, height, config=None):
        self.rtsp_url = rtsp_url
        self.config = config if config else RTSPStreamCaptureConfig()
        self.frame_queue = []
        self.stop_event = Event()
        self.last_read_time = datetime.now()

        self.width = width
        self.height = height

        self.logger = logging.getLogger(__name__)

        self.ready = False
        self.delay = 0
        self.skip = 0
        self.current_fps = self.config.target_fps
        self.increase_fps = 0

        self.frame_size = self.width * self.height * 3  # bgr24

        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3000000
        self.reconnect_interval = 5  # seconds
        self.is_reconnecting = False  # Flag per indicare la riconnessione in corso

        self.no_connection_frame = self._create_no_connection_frame()
        self.process = None
        self.capture_thread = None

    def start(self):
        """Start the capture process and thread"""
        self.stop_event.clear()
        self._start_stream()

        self.capture_thread = Thread(target=self._capture_loop)
        self.capture_thread.daemon = True  # Make thread exit when main thread exits
        self.capture_thread.start()
        self.logger.info(f"Started capturing from {self.rtsp_url} at resolution {self.width}x{self.height}")

    def _start_stream(self):
        """Start FFmpeg subprocess for stream decoding"""
        # Configure ffmpeg command for RTSP stream processing
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', self.rtsp_url,
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-vf', f'scale={self.width}:{self.height}',
            '-r', '15',
            '-an',  # no audio
            'pipe:1'
        ]
        try:
            self.process = subprocess.Popen(
                ffmpeg_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.DEVNULL, 
                bufsize=10**7
            )
        except Exception as e:
            self.logger.error(f"Failed to start FFmpeg process: {e}")
            raise

    def _capture_loop(self):
        """Main capture loop that reads frames from FFmpeg output"""
        while not self.stop_event.is_set():
            try:
                timestamp = datetime.now()
                raw_frame = self.process.stdout.read(self.frame_size)
                if not raw_frame or len(raw_frame) < self.frame_size:
                    self.logger.warning("No more frames or incomplete frame received from ffmpeg.")
                    self.frame_queue.append((self.no_connection_frame, timestamp))
                    self.ready = True
                    raise ConnectionError("Stream interrupted")

                frame = np.frombuffer(raw_frame, np.uint8).reshape((self.height, self.width, 3))
                self.frame_queue.append((frame, timestamp))
                while len(self.frame_queue) > self.config.max_buffer_size:
                    self.frame_queue.pop(0)

                self.ready = True
                self.is_reconnecting = False  # Connessione OK, flag riconnessione disattivato
                time.sleep(1 / (self.current_fps * 1.1))

            except Exception as e:
                self.logger.error(f"Capture loop error: {e}")
                self.is_reconnecting = True  # Flag riconnessione attivato
                self._attempt_reconnect()

        self.logger.info("Exiting capture loop")
        # Cleanup ffmpeg process if still running
        self._cleanup_process()

    def _cleanup_process(self):
        """Clean up the FFmpeg subprocess"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception as e:
                self.logger.warning(f"Error terminating FFmpeg process: {e}")
                # Force kill if termination fails
                try:
                    self.process.kill()
                except Exception as e:
                    self.logger.error(f"Failed to kill FFmpeg process: {e}")

    def _attempt_reconnect(self):
        """Try to reconnect to the stream after disconnection"""
        self.logger.info("Attempting to reconnect...")
        self.reconnect_attempts = 0
        while self.reconnect_attempts < self.max_reconnect_attempts and not self.stop_event.is_set():
            try:
                self.logger.info(f"Reconnect attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts}")
                self._cleanup_process()  # Clean up old process before starting new one
                self._start_stream()
                self.reconnect_attempts += 1

                # Test if the connection is valid
                time.sleep(self.reconnect_interval)
                raw_frame = self.process.stdout.read(self.frame_size)
                if raw_frame and len(raw_frame) == self.frame_size:
                    self.logger.info("Reconnected successfully.")
                    self.is_reconnecting = False
                    self.reconnect_attempts = 0
                    return
            except Exception as e:
                self.logger.warning(f"Reconnect attempt failed: {e}")
                time.sleep(self.reconnect_interval)

        self.logger.error("Failed to reconnect after maximum attempts. Stopping stream.")
        self.stop_event.set()
        self.is_reconnecting = False

    def _create_no_connection_frame(self):
        """Create a 'NO CONNECTION' message frame for display when stream is unavailable"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        text = "NO CONNECTION"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 2
        thickness = 3
        color = (0, 0, 255)  # Red in BGR
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = (frame.shape[0] + text_size[1]) // 2
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness, lineType=cv2.LINE_AA)
        return frame

    def read_frame(self):
        """Read a frame from the frame queue with error handling"""
        if self.stop_event.is_set():
            self.logger.info("Frame None due to Stop event")
            return None

        if self.is_reconnecting:
            # Show the "NO CONNECTION" frame during reconnection
            return self.no_connection_frame

        if not self.frame_queue:
            # If the frame queue is empty, return None
            return None

        frame, timestamp = self.frame_queue.pop(0)
        self.last_read_time = datetime.now()

        # Calculate frame delay
        self.delay = (self.last_read_time - timestamp).total_seconds()

        # Skip frames if needed to catch up
        if self.skip > 0:
            counter = 0
            while self.skip > counter:
                counter += 1
                if self.frame_queue:
                    frame, timestamp = self.frame_queue.pop(0)
                    if self.delay < 0.2:
                        self.skip = 0
                else:
                    self.skip = 0
                    self.increase_fps = -0.1

        if self.delay > 0.2 and self.skip == 0:
            self.skip = floor(self.delay / 0.2)
            self.increase_fps = 0.1

        return frame

    def stop(self):
        """Stop the capture thread and cleanup resources"""
        self.stop_event.set()
        if self.capture_thread:
            self.capture_thread.join(timeout=1)
        self._cleanup_process()
        self.logger.info("Stopped capturing")


class ImageUtility:
    """Utility class for image processing operations"""
    
    @staticmethod
    def hex_to_bgr(hex_color):
        """Convert hex color string to BGR tuple"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (rgb[2], rgb[1], rgb[0])
    
    @staticmethod
    def get_inside_sizes(frame, area_sizes):
        """Calculate dimensions to maintain aspect ratio when resizing"""
        f_height, f_width, channels = frame.shape
        frame_aspect_ratio = f_width / f_height
        window_aspect_ratio = area_sizes[0] / area_sizes[1]

        if frame_aspect_ratio >= window_aspect_ratio:
            new_width = area_sizes[0]
            new_height = int(f_height * (area_sizes[0] / f_width))
        else:
            new_width = int(f_width * (area_sizes[1] / f_height))
            new_height = area_sizes[1]
        return f_height, f_width, channels, frame_aspect_ratio, window_aspect_ratio, new_width, new_height
    
    @staticmethod
    def alpha_composting(four_channel_frame, canvas_frame, x_offset, o_width, y_offset, o_height):
        """Alpha composite a 4-channel frame onto a background"""
        frame_bgr = four_channel_frame[:, :, :3]
        frame_alpha = four_channel_frame[:, :, 3]
        frame_alpha_mask = frame_alpha / 255.0
        frame_inv_alpha_mask = 1.0 - frame_alpha_mask

        roi = canvas_frame[y_offset:y_offset+o_height, x_offset:x_offset+o_width]

        for c in range(3):
            roi[:, :, c] = (frame_alpha_mask * frame_bgr[:, :, c] +
                            frame_inv_alpha_mask * roi[:, :, c])

        canvas_frame[y_offset:y_offset+o_height, x_offset:x_offset+o_width] = roi
        return canvas_frame
    
    @staticmethod
    def rescale_frame(frame, width, height, keep_ratio=False):
        """Resize a frame with optional aspect ratio preservation"""
        if not keep_ratio:
            return cv2.resize(frame, (width, height))
        
        # If we need to keep the aspect ratio
        original_height, original_width, channels = frame.shape
        
        # Calculate new dimensions
        if original_width / original_height > width / height:
            # Image is wider than the target area
            new_width = width
            new_height = int(original_height * (width / original_width))
        else:
            # Image is taller than the target area
            new_height = height
            new_width = int(original_width * (height / original_height))
            
        # Resize the image
        resized = cv2.resize(frame, (new_width, new_height))
        
        # Create a white background
        base_image = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Calculate offsets to center the image
        x_offset = (width - new_width) // 2
        y_offset = (height - new_height) // 2
        
        # Handle transparent images (4 channels)
        if channels == 4:
            return ImageUtility.alpha_composting(resized, base_image, x_offset, new_width, y_offset, new_height)
        
        # For RGB images, just place them on the white background
        base_image[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized
        return base_image


class SystemMonitor:
    """Utility class for system monitoring and display detection"""
    
    @staticmethod
    def get_monitors():
        """Detect and return information about connected monitors"""
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()

            monitors = []

            def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
                monitor_info = ctypes.create_string_buffer(40)
                ctypes.windll.user32.GetMonitorInfoA(hMonitor, monitor_info)
                rect = ctypes.cast(lprcMonitor, ctypes.POINTER(ctypes.wintypes.RECT)).contents
                monitors.append({
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top
                })
                return True

            monitor_enum_proc_type = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                ctypes.c_void_p, ctypes.c_void_p,
                ctypes.POINTER(ctypes.wintypes.RECT), ctypes.c_double
            )
            monitor_enum_proc_cb = monitor_enum_proc_type(monitor_enum_proc)

            ctypes.windll.user32.EnumDisplayMonitors(0, 0, monitor_enum_proc_cb, 0)

            for i, monitor in enumerate(monitors):
                logger.debug(f"Monitor {i + 1}: {monitor}")

            return monitors
        except Exception as e:
            logger.error(f"Failed to get monitors: {e}")
            return [{"x": 0, "y": 0, "width": 1920, "height": 1080}]


class OpenGLHandler:
    """
    Handles OpenGL window creation and rendering.
    Manages video frames, overlays, and window state.
    """
    def __init__(self, window, url, process_manager):
        try:
            # Set up signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            # Get current application state
            try:
                state_instance = django_state.objects.latest('created')
                connection.close()
            except Exception:
                logger.warning(f"Could not get django state in OpenGL window {window.window_id}")
                state_instance = None

            # Initialize basic properties
            self.process_manager = process_manager
            self.window = window
            self.stream = window.stream
            self.labelText = window.labelText
            self.stop = False

            # Stream capture initialization
            self.cap = None
            self.target_fps = 25  # Default target FPS
            self.rtsp_config = RTSPStreamCaptureConfig(max_buffer_size=100, target_fps=self.target_fps)
            self.reconnect_flag = False
            self.reconnect_thread = None

            # Window properties
            self.isActive = window.isActive
            self.width = window.width
            self.height = window.height
            self.coord_x = window.coordinates[0]
            self.coord_y = window.coordinates[1]
            self.isAlarm = window.isAlarm

            # Visual elements
            self.watermark_path = None
            self.logo_path = window.logoPath
            self.alarm_icon_path = window.alarmIconPath
            self.placeholder_path = None
            self.fetch_all_images()

            # UI configuration
            self.newRenderInfo = True
            self.enable_logo = window.enableLogo
            self.enable_alarm_icon = window.enableAlarmIcon
            self.enable_watermark = window.enableWatermark

            # Region sizes and positions for overlays
            self.configure_regions()

            # Initialize overlay caches
            self.watermark = None
            self.logo = None
            self.alarm_icon = None

            self.updateWatermark = False
            self.updatePlaceholder = False

            # Configure alarm border
            self.configure_alarm_settings(state_instance)

            # Red border blink timing
            self.blink_state = False
            self.start_time = time.time()
            self.blink_interval = 0.6

            # Text rendering variables
            self.text_height = 0
            self.fontsize = 0
            self.label_pos = None
            self.font_thickness = 0
            self.text_cache_key = None

            # GLUT window properties
            self.glutWidth = 0
            self.glutX = 0
            self.glutY = 0
            self.updateCap = True
            self.counter = 0

            # For texture updating optimization
            self.current_texture_width = None
            self.current_texture_height = None

            # Store the last known good frame
            self.last_good_frame = None

            # Load environment configuration
            load_dotenv(CONFIG_FILE, override=True)

            # Configure monitor settings
            self.configure_monitors()

            # Initialize OpenGL window
            self.initialize_opengl_window()

        except Exception as e:
            logger.error(f"Error initializing OpenGL window: {e}")
            self.close()

    def configure_regions(self):
        """Configure sizes and positions for overlay regions"""
        self.watermark_region_size = (self.width, self.height)
        self.watermark_region_position = (0, 0)
        
        # Logo size and position (37% of window height, positioned in top-left corner)
        self.logo_region_size = (int(self.height * 0.37), int(self.height * 0.37))
        self.logo_region_position = (int(self.height * 0.07), int(self.height * 0.07))
        self.logo_keep_ratio = True
        
        # Alarm icon size and position (37% of window height, positioned in top-right corner)
        self.alarm_icon_region_size = (int(self.height * 0.37), int(self.height * 0.37))
        self.alarm_icon_region_position = (
            self.width - int(self.height * 0.37) - int(self.height * 0.07),
            int(self.height * 0.07)
        )
        self.alarm_icon_keep_ratio = True

    def configure_alarm_settings(self, state_instance):
        """Configure alarm border settings from state"""
        if state_instance is not None:
            self.alarm_border_color = ImageUtility.hex_to_bgr(str(state_instance.alarm_border_color))
            self.alarm_border_thickness = state_instance.alarm_border_thickness
        else:
            self.alarm_border_color = (0, 0, 255)  # Default to red in BGR
            self.alarm_border_thickness = 5

    def configure_monitors(self):
        """Configure monitor settings based on environment"""
        self.monitors = SystemMonitor.get_monitors()
        self.target_monitor_index = int(os.getenv("MONITOR_INDEX", 0))
        if self.target_monitor_index >= len(self.monitors):
            logger.warning(f"Monitor index {self.target_monitor_index} out of range, using 0")
            self.target_monitor_index = 0
        self.target_monitor = self.monitors[self.target_monitor_index]

    def initialize_opengl_window(self):
        """Initialize the OpenGL/GLUT window"""
        glutInit()
        glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_BORDERLESS | GLUT_CAPTIONLESS)
        glutInitWindowSize(self.width, self.height)
        glutInitWindowPosition(self.target_monitor["x"] + self.coord_x, self.target_monitor["y"] + self.coord_y)
        window_name = str(self.window.window_id).encode('utf-8')
        self.window_glut_id = glutCreateWindow(window_name)

        if not self.isActive:
            glutHideWindow()
            self.stop = True

        glutDisplayFunc(self.render_frame)
        glutTimerFunc(1000, self.timer, 0)
        glutKeyboardFunc(self.keyboard)
        glutWMCloseFunc(self.close)
        self.setup_opengl()

        glutMainLoop()
        logger.debug("Main loop started")

    def setup_opengl(self):
        """Set up OpenGL rendering environment"""
        # Clear background to black
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # Disable depth test for simple 2D rendering
        glDisable(GL_DEPTH_TEST)

        # Enable alpha blending for overlays with transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Setup orthographic projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Generate texture ID
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def fetch_image(self, scope=None, new_window_data=None):
        """Fetch image path based on scope"""
        if scope is None:
            return None

        if scope == IMAGE_SCOPE['LOGO']:
            return new_window_data if new_window_data else self.logo_path
        elif scope == IMAGE_SCOPE['ALARM_ICON']:
            return new_window_data if new_window_data else self.alarm_icon_path
        else:
            try:
                image = list(django_image.objects.filter(scope=scope, selected=True))
                connection.close()
                if not image:
                    logger.warning(f"No selected image found for scope {scope}")
                    return None
                return image[0].image.path
            except Exception as e:
                logger.warning(f"Error fetching image for scope {scope}: {e}")
                return None

    def fetch_all_images(self, new_window_data=None):
        """Fetch all required images"""
        self.watermark_path = self.fetch_image(IMAGE_SCOPE['WATERMARK'])
        if new_window_data:
            self.logo_path = self.fetch_image(IMAGE_SCOPE['LOGO'], new_window_data.get('logoPath', None))
            self.alarm_icon_path = self.fetch_image(IMAGE_SCOPE['ALARM_ICON'], new_window_data.get('alarmIconPath', None))
        else:
            self.logo_path = self.fetch_image(IMAGE_SCOPE['LOGO'])
            self.alarm_icon_path = self.fetch_image(IMAGE_SCOPE['ALARM_ICON'])
        self.placeholder_path = self.fetch_image(IMAGE_SCOPE['PLACEHOLDER'])

    def signal_handler(self, sig, frame):
        """Handle signals for clean shutdown"""
        logger.error('Signal received, cleaning up...')
        self.close()

    def keyboard(self, key, x, y):
        """Handle keyboard input"""
        logger.info(f"Window {self.window.window_id}: ({self.coord_x}, {self.coord_y})")
        glutPositionWindow(self.target_monitor["x"] + self.coord_x, self.target_monitor["y"] + self.coord_y)

    def timer(self, value):
        """Timer callback to handle window management and updates"""
        self.glutWidth = glutGet(GLUT_WINDOW_WIDTH)
        self.glutX = glutGet(GLUT_WINDOW_X)
        self.glutY = glutGet(GLUT_WINDOW_Y)

        self.correct_window_size_position()
        self.handle_process_manager_updates()
        self.handle_reconnection_attempts()

        glutTimerFunc(1000, self.timer, 0)

    def correct_window_size_position(self):
        """Ensure window has the correct size and position"""
        if self.width > self.glutWidth:
            if self.glutWidth != self.width:
                self.custom_resize(self.width, self.height)
                check_for_errors()
            if self.glutX != self.coord_x or self.glutY != self.coord_y:
                glutPositionWindow(self.target_monitor["x"] + self.coord_x, self.target_monitor["y"] + self.coord_y)
                check_for_errors()
        else:
            if self.glutX != self.coord_x or self.glutY != self.coord_y:
                glutPositionWindow(self.target_monitor["x"] + self.coord_x, self.target_monitor["y"] + self.coord_y)
                check_for_errors()

    def handle_process_manager_updates(self):
        """Handle updates from the process manager"""
        try:
            if self.window.window_id in self.process_manager.shared_dict:
                new_window_data = self.process_manager.shared_dict.pop(self.window.window_id)
                logger.info(f"new_window_data for window {self.window.window_id}: {new_window_data}")
                self.apply_updates(new_window_data)
                glutPostRedisplay()
        except BrokenPipeError as e:
            logger.error(f"Broken pipe when accessing process_manager: {e}")
            self.close()
        except ConnectionRefusedError as e:
            logger.warning(f"Connection refused: {e}")
            self.log_process_manager_state()
        except Exception as e:
            logger.error(f"Error handling process manager updates: {e}")
            self.close()

    def apply_updates(self, new_window_data):
        """Apply updates to window properties"""
        # If a new stream is provided and it's different from the current one
        if "stream" in new_window_data:
            new_stream = new_window_data['stream']
            if new_stream != self.stream:
                # Stop the current capture first (close old ffmpeg)
                if isinstance(self.cap, RTSPStreamCapture):
                    self.cap.stop()
                    self.cap = None

                # Update the stream URL
                self.stream = new_stream
                self.window.stream = new_stream

                # Mark that we need to restart capture with the new stream
                self.updateCap = True

        if "labelText" in new_window_data:
            self.labelText = new_window_data['labelText']

        if "enableLogo" in new_window_data:
            self.enable_logo = new_window_data['enableLogo']
            self.newRenderInfo = True

        if "enableAlarmIcon" in new_window_data:
            self.enable_alarm_icon = new_window_data['enableAlarmIcon']
            self.newRenderInfo = True

        if "enableWatermark" in new_window_data:
            self.enable_watermark = new_window_data['enableWatermark']
            self.newRenderInfo = True

        if "logoPath" in new_window_data or "alarmIconPath" in new_window_data:
            self.fetch_all_images(new_window_data)
            self.updateCap = True
            self.newRenderInfo = True

        if "PLACEHOLDER" in new_window_data:
            self.placeholder_path = self.fetch_image(IMAGE_SCOPE['PLACEHOLDER'])
            self.updateCap = True

        if "WATERMARK" in new_window_data:
            self.watermark_path = self.fetch_image(IMAGE_SCOPE['WATERMARK'])
            self.updateCap = True
            self.newRenderInfo = True

        if "width" in new_window_data and "height" in new_window_data:
            self.width = new_window_data['width']
            self.height = new_window_data['height']
            self.newRenderInfo = True
            self.current_texture_width = None
            self.current_texture_height = None

            # Restart stream with new dimensions
            if isinstance(self.cap, RTSPStreamCapture):
                self.cap.stop()
                self.cap = None
                self.updateCap = True

            if self.width < self.glutWidth:
                self.custom_resize(new_window_data['width'], new_window_data['height'])

        if "coord_x" in new_window_data or "coord_y" in new_window_data:
            if "coord_x" in new_window_data:
                self.coord_x = new_window_data["coord_x"]
            if "coord_y" in new_window_data:
                self.coord_y = new_window_data["coord_y"]
            check_for_errors()

        if "isActive" in new_window_data:
            self.isActive = new_window_data["isActive"]
            if self.isActive:
                glutShowWindow()
                check_for_errors()
                self.stop = False
            else:
                glutHideWindow()
                check_for_errors()
                self.stop = True

        if "isAlarm" in new_window_data:
            self.isAlarm = new_window_data['isAlarm']
            self.update_alarm_state()

        if "visualizzazione" in new_window_data or "close" in new_window_data:
            if new_window_data.get("visualizzazione", VISUALIZZAZIONE['OPENGL']) != VISUALIZZAZIONE['OPENGL'] \
                    or new_window_data.get("close", None):
                self.close()

    def update_alarm_state(self):
        """Update alarm border settings when alarm state changes"""
        try:
            state_instance = django_state.objects.latest('created')
            connection.close()
            
            if state_instance is not None:
                self.alarm_border_color = ImageUtility.hex_to_bgr(str(state_instance.alarm_border_color))
                self.alarm_border_thickness = state_instance.alarm_border_thickness
            else:
                self.alarm_border_color = (0, 0, 255)  # Default to red in BGR
                self.alarm_border_thickness = 5
                
            # Reset blink state when alarm state changes
            if self.isAlarm:
                self.blink_state = True
                self.start_time = time.time()
            
            self.newRenderInfo = True
            logger.info(f"Alarm state updated for window {self.window.window_id}, isAlarm={self.isAlarm}")
            
        except Exception as e:
            logger.error(f"Could not update alarm state in OpenGL window {self.window.window_id}: {e}")
            self.alarm_border_color = (0, 0, 255)  # Default to red in BGR 
            self.alarm_border_thickness = 5

    def log_process_manager_state(self):
        """Log the current state of the process manager"""
        logger.warning(f"ProcessManager pid: {self.process_manager.pid}")
        logger.warning(f"ProcessManager p: {self.process_manager.p}")
        for key, value in self.process_manager.shared_dict.items():
            logger.warning(f"{key}:{value}")

    def handle_reconnection_attempts(self):
        """Handle reconnection to streams if needed"""
        # If needed, implement logic for restarting the ffmpeg pipeline
        if self.stream == "" and self.window.stream != "":
            # Stream URL was empty but now has a value - schedule reconnection
            self.stream = self.window.stream
            self.updateCap = True

    def updateRenderInfo(self):
        """Update cached rendering information for overlays"""
        # Update region sizes based on current window dimensions
        self.watermark_region_size = (self.width, self.height)
        self.logo_region_size = (int(self.height * 0.37), int(self.height * 0.37))
        self.alarm_icon_region_position = (
            self.width - int(self.height * 0.37) - int(self.height * 0.07),
            int(self.height * 0.07)
        )
        self.alarm_icon_region_size = (int(self.height * 0.37), int(self.height * 0.37))

        # Load and resize overlay images
        if self.enable_watermark and self.watermark_path:
            self.watermark = self.get_picture_info(self.watermark_region_size, self.watermark_path)
        else:
            self.watermark = None

        if self.enable_logo and self.logo_path:
            self.logo = self.get_picture_info(self.logo_region_size, self.logo_path, keep_ratio=self.logo_keep_ratio)
        else:
            self.logo = None

        if self.enable_alarm_icon and self.alarm_icon_path:
            self.alarm_icon = self.get_picture_info(self.alarm_icon_region_size,
                                                  self.alarm_icon_path,
                                                  keep_ratio=self.alarm_icon_keep_ratio)
        else:
            self.alarm_icon = None

    def update_capture_objects(self):
        """Initialize or update the stream capture object"""
        if self.stream:
            try:
                # Reset texture dimensions to force re-initialization
                self.current_texture_width = None
                self.current_texture_height = None
                self.newRenderInfo = True

                # Create and start a new capture with the current stream URL
                self.cap = RTSPStreamCapture(self.stream, self.width, self.height, config=self.rtsp_config)
                self.cap.start()
                return True
            except Exception as e:
                logger.error(f"Failed to create stream capture for {self.stream}: {e}")
                return False
        return False

    def render_frame(self):
        """Main frame rendering function"""
        if self.stop:
            return

        if self.stream:
            if self.updateCap:
                self.reset_capture()
            if self.newRenderInfo:
                self.updateRenderInfo()
                self.newRenderInfo = False

            self.play()
            time.sleep(1 / max(1, self.target_fps))
            glutPostRedisplay()
        else:
            if self.updateCap:
                self.reset_placeholder()
            self.show_placeholder()

    def reset_capture(self):
        """Reset and reinitialize the stream capture"""
        if isinstance(self.cap, RTSPStreamCapture):
            self.cap.stop()
        elif isinstance(self.cap, np.ndarray):
            self.cap = None

        if self.update_capture_objects():
            self.updateCap = False
        else:
            self.updateCap = True
            glutPostRedisplay()

    def reset_placeholder(self):
        """Reset to placeholder image when no stream is available"""
        if isinstance(self.cap, RTSPStreamCapture):
            self.cap.stop()
        elif isinstance(self.cap, np.ndarray):
            self.cap = None

        if self.placeholder_path:
            self.cap = cv2.imread(self.placeholder_path, cv2.IMREAD_UNCHANGED)
        else:
            self.cap = cv2.imread("C:\\Anywall\\resources\\placeholder.png",
                                  cv2.IMREAD_COLOR)
        self.updateCap = False

    def disable_alarm(self):
        """Mark alarm as expired in database"""
        try:
            django_requested_window.objects.update_or_create(
                window_id=self.window.window_id,
                defaults={"timeout": datetime.now(), "isAlarm": False}
            )
            callAlarmExpired()
            connection.close()
            logger.info(f"Alarm for window {self.window.window_id} disabled successfully")
        except Exception as e:
            logger.error(f"Error disabling alarm for window {self.window.window_id}: {e}")

    def custom_resize(self, new_width, new_height):
        """Resize the OpenGL viewport and window"""
        glViewport(0, 0, new_width, new_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glutReshapeWindow(new_width, new_height)

        # Reset text rendering cache
        self.text_height = 0
        self.fontsize = 0
        self.label_pos = None
        self.font_thickness = 0
        self.text_cache_key = None

    def close(self):
        """Close the window and cleanup resources"""
        self.stop = True
        if isinstance(self.cap, RTSPStreamCapture):
            self.cap.stop()
        elif isinstance(self.cap, np.ndarray):
            self.cap = None

        if getattr(self, 'texture_id', None) is not None:
            glDeleteTextures([self.texture_id])

        glutLeaveMainLoop()
        logger.info(f"Window {self.window.window_id} closed")
        return

    def get_picture_info(self, sizes, picture_path, keep_ratio=False):
        """Load and prepare image for overlay"""
        picture = cv2.imread(picture_path, cv2.IMREAD_UNCHANGED)
        if picture is None:
            return None

        if not keep_ratio:
            picture = cv2.resize(picture, sizes)
            picture_h, picture_w = sizes[1], sizes[0]
        else:
            _, _, picture_channels, _, _, picture_w, picture_h = ImageUtility.get_inside_sizes(picture, sizes)
            picture = cv2.resize(picture, (picture_w, picture_h))

        return self.prepare_picture_dict(picture, picture_w, picture_h)

    def prepare_picture_dict(self, picture, picture_w, picture_h):
        """Prepare image data for overlay rendering"""
        picture_channels = picture.shape[2]

        if picture_channels == 4:
            picture_bgr = picture[:, :, :3]
            picture_alpha = picture[:, :, 3]
            picture_alpha_mask = picture_alpha / 255.0
            picture_inv_alpha_mask = 1.0 - picture_alpha_mask

            return {
                "channels": picture_channels,
                "bgr": picture_bgr,
                "alpha": picture_alpha,
                "alpha_mask": picture_alpha_mask,
                "inv_alpha_mask": picture_inv_alpha_mask,
                "height": picture_h,
                "width": picture_w,
            }
        else:
            return {
                "channels": picture_channels,
                "bgr": picture[:, :, :3],
                "alpha": None,
                "alpha_mask": None,
                "inv_alpha_mask": None,
                "height": picture_h,
                "width": picture_w,
            }

    def draw_picture(self, frame, picture, position):
        """Draw an overlay picture onto a frame"""
        overlay_x = position[0]
        overlay_y = position[1]
        size_w = picture["width"]
        size_h = picture["height"]

        # Make sure the overlay is within frame bounds
        if overlay_x + size_w > frame.shape[1] or overlay_y + size_h > frame.shape[0]:
            logger.warning(f"Overlay out of bounds: pos={position}, size={size_w}x{size_h}, frame={frame.shape}")
            return frame

        if picture["channels"] == 4:
            # Alpha blending for transparent images
            roi = frame[overlay_y:overlay_y+size_h, overlay_x:overlay_x+size_w]
            for c in range(3):
                roi[:, :, c] = (picture["alpha_mask"] * picture["bgr"][:, :, c] +
                                picture["inv_alpha_mask"] * roi[:, :, c])
            frame[overlay_y:overlay_y+size_h, overlay_x:overlay_x+size_w] = roi
        else:
            # Direct overlay for opaque images
            frame[overlay_y:overlay_y+size_h, overlay_x:overlay_x+size_w] = picture["bgr"]

        return frame

    def draw_alarm_border(self, frame, color, thickness):
        """Draw a border around the frame for alarm indication"""
        cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), color, thickness)

    def draw_text(self, frame, text, color, fontsize, background=True):
        """Draw text overlay on the frame"""
        # Use cache for text rendering settings to avoid recalculating
        cache_key = (text, self.width, self.height, fontsize)
        if cache_key != self.text_cache_key:
            self.text_cache_key = cache_key
            font = cv2.FONT_HERSHEY_SIMPLEX
            border_height = int(DISPLAY_SIZE[1] * 0.02)
            wanted_height = int(border_height - border_height * 0.2)
            self.font_thickness = 2
            text_size, _ = cv2.getTextSize(text, font, fontsize, self.font_thickness)
            _, text_height = text_size
            position = (0, int(frame.shape[0] - wanted_height))

            # Binary search for optimal font size
            diff = 1
            dir_sign = -1 if text_height > wanted_height else 1

            while text_height != wanted_height:
                if text_height > wanted_height:
                    if dir_sign < 0:
                        dir_sign = 1
                        diff = diff / 2
                    fontsize = fontsize - diff
                elif text_height < wanted_height:
                    if dir_sign > 0:
                        dir_sign = -1
                        diff = diff / 2
                    fontsize = fontsize + diff

                text_size, _ = cv2.getTextSize(text, font, fontsize, 1)
                _, text_height = text_size

            self.text_height = text_height
            self.fontsize = fontsize
            self.label_pos = position

        # Draw background rectangle for text if enabled
        if background:
            cv2.rectangle(frame,
                          (0, int(self.label_pos[1] + DISPLAY_SIZE[1] * 0.02)),
                          (frame.shape[1], int(self.label_pos[1] - DISPLAY_SIZE[1] * 0.02)),
                          (101, 68, 17),
                          -1)

        # Draw the text
        cv2.putText(frame, text, self.label_pos, cv2.FONT_HERSHEY_SIMPLEX,
                    self.fontsize, color, self.font_thickness, lineType=cv2.LINE_AA)
        return frame

    def play(self):
        """Render video frame with overlays"""
        if not self.cap or not self.cap.ready:
            time.sleep(1/max(1, self.target_fps))
            glutPostRedisplay()
            return

        # Get a frame from the capture
        frame = self.cap.read_frame()
        max_attempts = max(1, self.target_fps) * 3
        attempts = 0
        
        # Update FPS based on stream performance
        self.target_fps += self.cap.increase_fps
        self.cap.current_fps = self.target_fps
        if self.cap.increase_fps != 0:
            self.cap.increase_fps = 0

        # Try to get a valid frame
        while frame is None and attempts < max_attempts:
            time.sleep(1/max(1, self.target_fps))
            frame = self.cap.read_frame()
            attempts += 1

        # Handle case where no frame is available
        if frame is None and self.last_good_frame is None:
            self.clear_window()
            self.stream = ""
            self.updateCap = True
            
            # Handle alarm state properly
            if self.isAlarm:
                logger.info(f"No frame available for alarm window {self.window.window_id}, disabling alarm")
                self.disable_alarm()
                self.isAlarm = False
                
            glutPostRedisplay()
            return

        # Use last good frame if current frame is not available
        if frame is None:
            if attempts >= max_attempts and self.isAlarm:
                logger.warning(f"Max attempts reached for alarm window {self.window.window_id}, may need to disable alarm")
            frame = self.last_good_frame

        # Resize frame to fit window
        frame = ImageUtility.rescale_frame(frame.astype(np.uint8), self.width, self.height, keep_ratio=False)
        if frame is None:
            self.clear_window()
            return

        # Draw overlays
        if self.enable_logo and self.logo:
            frame = self.draw_picture(frame, self.logo, self.logo_region_position)

        if self.isAlarm and self.enable_alarm_icon and self.alarm_icon:
            frame = self.draw_picture(frame, self.alarm_icon, self.alarm_icon_region_position)

        if self.enable_watermark and self.watermark:
            frame = self.draw_picture(frame, self.watermark, self.watermark_region_position)

        # Generate and draw text caption
        text = ''
        if not self.isAlarm:
            text = f'Camera {self.window.window_id}'
            if self.labelText:
                text += ' - '
        if self.labelText:
            text += f'{self.labelText}'

        frame = self.draw_text(frame, text, (255, 255, 255), 1)

        # Draw blinking alarm border if in alarm state
        if self.isAlarm and self.blink_state:
            self.draw_alarm_border(frame, self.alarm_border_color, self.alarm_border_thickness)

        if frame is None:
            self.clear_window()
            return

        # Store last good frame
        self.last_good_frame = frame

        # Upload frame to texture and render
        self.upload_texture(frame)
        glEnable(GL_TEXTURE_2D)
        glClear(GL_COLOR_BUFFER_BIT)

        # Draw textured quad
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-1,  1, 0)
        glTexCoord2f(1, 0); glVertex3f( 1,  1, 0)
        glTexCoord2f(1, 1); glVertex3f( 1, -1, 0)
        glTexCoord2f(0, 1); glVertex3f(-1, -1, 0)
        glEnd()

        glFlush()
        glFinish()
        glutSwapBuffers()

        # Handle alarm border blinking
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= self.blink_interval:
            self.blink_state = not self.blink_state
            self.start_time = time.time()

    def upload_texture(self, frame):
        """Upload a frame to OpenGL texture"""
        # Convert BGR (OpenCV) to RGB for standard GL_RGB usage
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        h, w, c = frame_rgb.shape

        # If size changed, reinitialize texture
        if (self.current_texture_width != w) or (self.current_texture_height != h):
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, frame_rgb)
            self.current_texture_width = w
            self.current_texture_height = h
        else:
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, frame_rgb)

    def show_placeholder(self):
        """Display placeholder image when no stream is available"""
        retry_counter = 0
        frame = self.cap
        while frame is None and retry_counter < 5:
            time.sleep(1)
            frame = self.cap
            retry_counter += 1

        if frame is None and self.last_good_frame is None:
            self.clear_window()
            return

        if frame is None:
            frame = self.last_good_frame

        frame = ImageUtility.rescale_frame(frame.astype(np.uint8), self.width, self.height, keep_ratio=True)
        if frame is None:
            self.clear_window()
            return

        text = f'Camera {self.window.window_id}'
        frame = self.draw_text(frame, text, (255, 255, 255), 1)

        if frame is None:
            self.clear_window()
            return

        self.last_good_frame = frame

        self.upload_texture(frame)
        glEnable(GL_TEXTURE_2D)
        glClear(GL_COLOR_BUFFER_BIT)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-1,  1, 0)
        glTexCoord2f(1, 0); glVertex3f( 1,  1, 0)
        glTexCoord2f(1, 1); glVertex3f( 1, -1, 0)
        glTexCoord2f(0, 1); glVertex3f(-1, -1, 0)
        glEnd()

        glFlush()
        glFinish()
        glutSwapBuffers()

    def switch_to_placeholder(self):
        """Switch rendering to placeholder mode"""
        self.display_foo = glutDisplayFunc(self.show_placeholder)

    def switch_to_stream(self):
        """Switch rendering to stream mode"""
        self.display_foo = glutDisplayFunc(self.play)

    def clear_window(self):
        """Clear the window with solid black background"""
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glFlush()
        glFinish()
        glutSwapBuffers()

    def __del__(self):
        """Destructor for cleanup"""
        self.close()