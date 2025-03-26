
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GObject, Gtk, Gdk

from anywall_app.logger import setup_logger
logger = setup_logger(__name__)

class GStreamerHandler:
    """
    Handles video streams using GStreamer.
    """
    
    def __init__(self, window, url):
        """Initialize the GStreamer pipeline for video streaming."""
        try:
            Gst.init(None)
            self.window = window
            self.url = url
            
            # Build and setup pipeline
            self.pipeline_str = self.build_pipeline(url)
            self.pipeline = Gst.parse_launch(self.pipeline_str)
            
            if not self.pipeline:
                logger.error(f"Failed to create pipeline for window {window.window_id}")
                return
                
            # Set up bus for pipeline messages
            self.bus = self.pipeline.get_bus()
            self.bus.add_signal_watch()
            self.bus.connect('message::eos', self.on_eos)
            self.bus.connect('message::error', self.on_error)
            
            logger.info(f"GStreamer initialized for window {window.window_id} with URL: {url}")
        except Exception as e:
            logger.error(f"Failed to initialize GStreamer for window {window.window_id}: {e}")

    def play(self):
        """Start playing the video stream."""
        try:
            if self.pipeline:
                state_change = self.pipeline.set_state(Gst.State.PLAYING)
                if state_change == Gst.StateChangeReturn.FAILURE:
                    logger.error(f"Failed to start pipeline for window {self.window.window_id}")
                else:
                    logger.info(f"Started pipeline for window {self.window.window_id}")
        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")

    def on_eos(self, bus, message):
        """Handle end-of-stream message."""
        logger.info(f"End of stream for window {self.window.window_id}")
        try:
            self.pipeline.set_state(Gst.State.NULL)
            # Attempt to restart the pipeline after a brief delay
            GObject.timeout_add(1000, self.restart_pipeline)
        except Exception as e:
            logger.error(f"Error handling EOS: {e}")

    def on_error(self, bus, message):
        """Handle error message."""
        err, debug = message.parse_error()
        logger.error(f"GStreamer error for window {self.window.window_id}: {err} ({debug})")
        try:
            self.pipeline.set_state(Gst.State.NULL)
            # Attempt to restart the pipeline after a brief delay
            GObject.timeout_add(3000, self.restart_pipeline)
        except Exception as e:
            logger.error(f"Error handling pipeline error: {e}")

    def restart_pipeline(self):
        """Attempt to restart the pipeline."""
        try:
            logger.info(f"Attempting to restart pipeline for window {self.window.window_id}")
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline.set_state(Gst.State.PLAYING)
            return False  # Don't repeat the timeout
        except Exception as e:
            logger.error(f"Failed to restart pipeline: {e}")
            return False

    def update_url(self, url):
        """Update the stream URL."""
        if url == self.url:
            return  # No change needed
            
        try:
            logger.info(f"Updating URL for window {self.window.window_id} to: {url}")
            self.url = url
            # Stop current pipeline
            self.pipeline.set_state(Gst.State.NULL)
            
            # Create new pipeline with updated URL
            self.pipeline_str = self.build_pipeline(url)
            self.pipeline = Gst.parse_launch(self.pipeline_str)
            
            # Set up bus for new pipeline
            self.bus = self.pipeline.get_bus()
            self.bus.add_signal_watch()
            self.bus.connect('message::eos', self.on_eos)
            self.bus.connect('message::error', self.on_error)
            
            # Start new pipeline
            self.play()
        except Exception as e:
            logger.error(f"Failed to update URL: {e}")

    def quit(self):
        """Clean up and stop the pipeline."""
        try:
            if self.pipeline:
                self.pipeline.set_state(Gst.State.NULL)
                logger.info(f"Pipeline stopped for window {self.window.window_id}")
        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")
    
    def build_pipeline(self, url):
        """Build the GStreamer pipeline string."""
        try:
            win = self.window
            pipeline_str = (
                f'rtspsrc location={url} ! '
                f'decodebin ! videoconvert ! videoscale ! '
                f'video/x-raw,width={win.width},height={win.height} ! '
                f'glimagesink'
            )
            
            logger.debug(f"Pipeline for window {win.window_id}: {pipeline_str}")
            return pipeline_str
        except Exception as e:
            logger.error(f"Failed to build pipeline: {e}")
            return "videotestsrc ! videoconvert ! glimagesink"  # Fallback pipeline
