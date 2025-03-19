import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GObject, Gtk, Gdk

class GStreamerHandler:
    def __init__(self, window, url):
        Gst.init(None)
        self.window = window
        self.pipeline = None
        self.pipeline_str = self.pipeline_builder(url)
        
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.on_eos)
        self.bus.connect('message::error', self.on_error)

    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, message):
        print("End of Stream")
        self.pipeline.set_state(Gst.State.NULL)

    def on_error(self, bus, message):
        err, debug = message.parse_error()
        print("Error: %s" % err, debug)

    def quit(self):
        self.pipeline.set_state(Gst.State.NULL)
    
    def pipeline_builder(self, url):


        # # Initialize GTK+
        # Gtk.init(None)

        # # Create a new GTK+ window
        # window = Gtk.Window(title="GStreamer GLImagesink Example")
        # window.connect("destroy", Gtk.main_quit)

        # # Show the window
        # window.show_all()

        # # Start the GTK+ main loop
        # Gtk.main()

        # At this point, the GTK+ main loop is running, and the window is displayed.
        # You would typically set up your GStreamer pipeline here and start it.
        # However, since we're focusing on creating the window and getting its handle,
        # let's assume you've already set up your GStreamer pipeline elsewhere.

        # Get the window handle
        #window_handle = window.get_window().get_xid()

        #print(f"Window handle: {window_handle}")

        # Now, you can use `window_handle` in your GStreamer pipeline setup
        # For example, setting it as the window handle for glimagesink:
        # glimagesink.set_property("window-handle", window_handle)

        # implementare logica per test stream, identificazione problemi, utilizzo condizionale ffmpeg (?)
        win = self.window
        win_coordinates = (win.coordinates[0], win.coordinates[1], win.coordinates[0] + win.width, win.coordinates[1] + win.height)
        pipeline_str = f'rtspsrc location={url} ! decodebin ! videoconvert ! videoscale ! video/x-raw,width={win.width},height={win.height} ! glimagesink' 
        
        self.pipeline = Gst.parse_launch(pipeline_str)
        
        # glimagesink = self.pipeline.get_by_name("glimagesink")

        # # Set the window handle
        # # Replace 'window_handle' with the actual handle of your window
        # glimagesink.set_property("window-handle", window_handle)

        # glimagesink.set_property("render-x", win_coordinates[0])
        # glimagesink.set_property("render-y", win_coordinates[1])
        # glimagesink.set_property("render-width", win_coordinates[2])
        # glimagesink.set_property("render-height", win_coordinates[3])
        
        print(pipeline_str)
        return pipeline_str
    