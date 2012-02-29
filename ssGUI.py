#!/usr/bin/env python

"""
This module sets up a video stream from internal or connected webcam using Gstreamer.
You can then take snapshots.
"""

import pygtk, gtk
import pygst
pygst.require("0.10")
import gst

from os.path import exists, relpath
from sys import exit

window_w  = 660
window_h  = 543
framerate = 30

# Gstreamer constants. 
# More infos about Gstreamer here : 
#  * http://www.cin.ufpe.br/~cinlug/wiki/index.php/Introducing_GStreamer
#  * http://www.oz9aec.net/index.php/gstreamer/345-a-weekend-with-gstreamer
gst_src             = 'v4l2src device=' # VideoForLinux driver asociated with specified device 
gst_src_format      = 'video/x-raw-yuv' # colorspace specific to webcam
gst_videosink       = 'xvimagesink'     # sink habilitated to manage images
sep                 = ' ! '             # standard gstreamer pipe. Don't change that

class WebcamManager:    
    def __init__(self, device, resolution, snap_format):
        """
        Set up the GUI, the gstreamer pipeline and webcam<-->GUI communication bus.
        When everything is created, display.
        """
        # Before anything, let's be sure that we have a webcam plugged in
        if not exists('/dev/video0'):
            print "No webcam detected: /dev/video0 cannot be found.\n The program is now exiting."
            exit()
        if not exists(device):
            print device, 'not detected. Fall back to default camera (/dev/video0)'
            self.device = '/dev/video0'
        else:
            self.device = device             # device used for video input
        self.W = int(resolution[0])               # resolution: width
        self.H = int(resolution[1])               # resolution: height
        self.framerate = str(framerate)+'/1' # number of frames per second
        self.snap_format = snap_format       # format of snapshot (png, jpg, ...)

        self.create_gui()
        self.create_video_pipeline()
        self.window.show_all()

    def create_gui(self):
        """Set up the GUI"""
        # Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Smile or be killed.")
        self.window.set_default_size(window_w, window_h)
        self.window.connect("destroy", self.exit, "WM destroy")
        self.window.set_geometry_hints(min_width=window_w, 
                                       min_height=window_h, 
                                       max_width=window_w, 
                                       max_height=window_h,)
        self.window.set_position(gtk.WIN_POS_CENTER)

        # Video screen
        vbox = gtk.VBox()
        self.window.add(vbox)
        self.movie_window = gtk.DrawingArea()
        vbox.add(self.movie_window)

        # Button
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False)
        hbox.set_border_width(10)
        hbox.pack_start(gtk.Label())
        self.button = gtk.Button("Snap")
        self.button.connect("clicked", self.take_snapshot)
        hbox.pack_start(self.button, False)
        hbox.add(gtk.Label())
       
    def create_video_pipeline(self):
        """Set up the video pipeline and the communication bus bewteen the video stream and gtk DrawingArea """
        src = gst_src + self.device # video input
        src_format = gst_src_format +',width='+ str(self.W) + ',height=' + str(self.H) +',framerate='+ self.framerate # video parameters
        videosink = gst_videosink # video receiver
        video_pipeline = src + sep  + src_format + sep + videosink 
        # print 'gstreamer video pipeline :', video_pipeline
        self.video_player = gst.parse_launch(video_pipeline) # create pipeline
        self.video_player.set_state(gst.STATE_PLAYING)       # start video stream

        bus = self.video_player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        bus.enable_sync_message_emission()
        bus.connect("sync-message::element", self.on_sync_message)        
                   
    def exit(self, widget, data=None):
        """ Exit the program """
        self.video_player.set_state(gst.STATE_NULL) 
        gtk.main_quit()
        
    def on_message(self, bus, message):
        """ Gst message bus. Closes the pipeline in case of error or EOS (end of stream) message """
        t = message.type
        if t == gst.MESSAGE_EOS:
            print "MESSAGE EOS"
            self.video_player.set_state(gst.STATE_NULL)
        elif t == gst.MESSAGE_ERROR:
            print "MESSAGE ERROR"
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.video_player.set_state(gst.STATE_NULL)
                    
    def on_sync_message(self, bus, message):
        """ Set up the Webcam <--> GUI messages bus """
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            # Assign the viewport
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(self.movie_window.window.xid) # Sending video stream to gtk DrawingArea

    def take_snapshot(self, e):
        """ Capture a snapshot from DrawingArea and save it into a image file """
        drawable = self.movie_window.window
        colormap = drawable.get_colormap()
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 0, 8, *drawable.get_size())
        pixbuf = pixbuf.get_from_drawable(drawable, colormap, 0,0,0,0, *drawable.get_size()) 
        pixbuf = pixbuf.scale_simple(self.W, self.H, gtk.gdk.INTERP_HYPER) # resize
        # We resize from actual window size to wanted resolution
        # gtk.gdk.INTER_HYPER is the slowest and highest quality reconstruction function
        # More info here : http://developer.gnome.org/pygtk/stable/class-gdkpixbuf.html#method-gdkpixbuf--scale-simple
        filename = snapshot_name() + '.' + self.snap_format
        filepath = relpath(filename)
        pixbuf.save(filename, self.snap_format)
        return filepath
            
    def run(self):
        """ Main loop """
        gtk.gdk.threads_init()
        gtk.main()

def snapshot_name():
    """ Return a string of the form yyyy-mm-dd-hms """
    from datetime import datetime
    today = datetime.today()
    y = str(today.year)
    m = str(today.month)
    d = str(today.day)
    h = str(today.hour)
    mi= str(today.minute)
    s = str(today.second)
    return '%s-%s-%s-%s%s%s' %(y, m, d, h, mi, s)
