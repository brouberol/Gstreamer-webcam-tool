#!/usr/bin/env python

"""
This script sets up a video stream from internal or connected webcam using
Gstreamer.
"""

from os.path import exists
from sys import exit
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst
import argparse

class Webcam:
    
    def __init__(self, device, window_size, framerate):
        """
        Set up the GUI, the gstreamer pipeline and webcam<-->GUI communication bus.
        If any, the external webcam (/dev/video1) will be selected by default, otherwise, /dev/video0 will be used
        """
        # SET UP THE INTERFACE
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Webcam-Viewer")
        window.set_default_size(660, 500)
        window.connect("destroy", self.exit, "WM destroy")
        vbox = gtk.VBox()
        window.add(vbox)
        self.movie_window = gtk.DrawingArea()
        vbox.add(self.movie_window)
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False)
        hbox.set_border_width(10)
        hbox.pack_start(gtk.Label())
        self.button = gtk.Button("Quit")
        self.button.connect("clicked", self.exit)
        hbox.pack_start(self.button, False)
        hbox.add(gtk.Label())
        
        # SET UP THE GSTREAMER PIPELINE 
        self.device = device 
        self.W = window_size[0]
        self.H = window_size[1]
        self.framerate = framerate
        print 'v4l2src device={0} ! video/x-raw-yuv,width={1},height={2},framerate={3}/1 ! xvimagesink'.format(self.device, str(self.W), str(self.H), str(self.framerate))
        self.player = gst.parse_launch('v4l2src device={0} ! video/x-raw-yuv,width={1},height={2},framerate={3}/1 ! xvimagesink'.format(self.device, self.W, self.H, self.framerate))

        # input from webcam (v4l2src : video for linux 2), output : xvimagesink
        self.player.set_state(gst.STATE_PLAYING)
        # More information here : http://www.cin.ufpe.br/~cinlug/wiki/index.php/Introducing_GStreamer

        # SET UP WINDOW <--> WEBCAM STREAM COMMUNICATION BUS
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        bus.enable_sync_message_emission()
        bus.connect("sync-message::element", self.on_sync_message)
       
        # ROCK ON BABY \o/
        window.show_all()

        
            
    def exit(self, widget, data=None):
        """ Exit the program """
        self.player.set_state(gst.STATE_PAUSED) # Not sure if the PAUSE+READY steps are necessary, but when i use gst in bash, they are triggered.
        self.player.set_state(gst.STATE_READY)
        self.player.set_state(gst.STATE_NULL) 

        # Ugly hack : launch cheese to avoid empty webcam window next time, probably due to webcam driver problem
        from os import system
        gtk.main_quit()
        system("cheese")
        
    def on_message(self, bus, message):
        """ Gst message sink. Closes the pipeline in case of error or EOS (end of stream) message """
        t = message.type
        if t == gst.MESSAGE_EOS:
            print "MESSAGE EOS"
            self.player.set_state(gst.STATE_NULL)
        elif t == gst.MESSAGE_ERROR:
            print "MESSAGE ERROR"
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.player.set_state(gst.STATE_NULL)
                    
    def on_sync_message(self, bus, message):
        """ Webcam <--> GUI messages sink """
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            # Assign the viewport
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(self.movie_window.window.xid) # HERE I SEND THE WEBCAM STREAM TO THE MOVIE WINDOW

if __name__ == "__main__":

    if not exists('/dev/video0'):
        print "No webcam detected: /dev/video cannot be found.\n The program is now exiting."
        exit()

    # Argument parsing
    parser = argparse.ArgumentParser(description='Set video stream window parameters')
    parser.add_argument('--device', '-d',type=str, action='store', default='/dev/video0', help="Set the video input device path")
    parser.add_argument('--window-size', '-w', nargs='+', type=str,  default=['640', '480'], 
                        # choices = [[352, 288], [640, 480], [1024, 768], [1280, 720], [1280, 1024], [1600, 1200], [1920, 1080], [2048, 1536]],
                        # My webcam goes up to 1024x768
                        help="Set the video stream resolution. Of form 'W H'")
    parser.add_argument('--framerate', '-f', type=str, default=30, help="Set the video stream framerate") # --> CHOICES = ?

    args = vars(parser.parse_args())
    
    device = args['device']
    window_size = args['window_size']
    framerate = args['framerate']
        
    Webcam(device, window_size, framerate)
    gtk.gdk.threads_init()
    gtk.main()


# TODO : 
#     * Take a picture from the videostream
#     * Handle arguments passing. Possible arguments
#         * --device, -d: device (/dev/video0, etc)
#         * --window-size, -w : window dimensions --> W:H (in px)
#         * --framerate, -f : numbers of frame per second

# BUGS:
# BUG#1: ONLY DISPLAYS WEBCAM FEED AFTER I LAUNCHED & CLOSED CHEESE 
# When it works, I have a message "ON SYNC MESSAGE" --> call on_sync_message(self, bus, message) method
# see other source code, to see how exiting is handled webcam-wise --> HOW DO WE SHUT DOWN THE WEBCAM ?
# I tested it in the original (webcam.py.bckp) script : works fine the first time, but doesn't work
# another time after i hit "Stop"
