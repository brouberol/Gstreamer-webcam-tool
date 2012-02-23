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
import Image
from time import sleep

class Webcam:
    
    def __init__(self, device, resolution, framerate, snap_format):
        """
        Set up the GUI, the gstreamer pipeline and webcam<-->GUI communication bus.
        If any, the external webcam (/dev/video1) will be selected by default, otherwise, /dev/video0 will be used
        """

        # OBJECT ARGUMENTS
        self.device = device         
        self.W = resolution[0].split(':')[0]
        self.H = resolution[0].split(':')[1]
        self.framerate = framerate
        self.snap_format = snap_format
        if self.snap_format == 'png':
            self.image_enc = 'pngenc'
        elif self.snap_format in ['jpg','jpeg']:
            self.image_enc = 'jpegenc'

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
        self.button = gtk.Button("Snap")
        self.button.connect("clicked", self.get_snapshot)
        hbox.pack_start(self.button, False)
        hbox.add(gtk.Label())
        
        # SET UP THE GSTREAMER VIDEO PIPELINE 
        print 'v4l2src device={0} ! video/x-raw-yuv,width={1},height={2},framerate={3}/1 ! xvimagesink '.format(self.device, str(self.W), str(self.H), str(self.framerate))
        self.video_player = gst.parse_launch('v4l2src device=%s ! video/x-raw-yuv,width=%s,height=%s,framerate=%s/1 ! xvimagesink' %(self.device, self.W, self.H, self.framerate))
        # input from webcam (v4l2src : video for linux 2), output : xvimagesink
        self.video_player.set_state(gst.STATE_PLAYING)
        # More information here : http://www.cin.ufpe.br/~cinlug/wiki/index.php/Introducing_GStreamer

        # SET UP WINDOW <--> WEBCAM STREAM COMMUNICATION BUS
        bus = self.video_player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        bus.enable_sync_message_emission()
        bus.connect("sync-message::element", self.on_sync_message)
       
        # ROCK ON BABY \o/
        window.show_all()
                   
    def exit(self, widget, data=None):
        """ Exit the program """
        self.video_player.set_state(gst.STATE_NULL) 
        gtk.main_quit()
        
    def on_message(self, bus, message):
        """ Gst message sink. Closes the pipeline in case of error or EOS (end of stream) message """
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
        """ Webcam <--> GUI messages sink """
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            # Assign the viewport
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(self.movie_window.window.xid) # Sending video stream to gtk DrawingArea

    def get_snapshot(self, e):
        """ Capture a snapshot from webcam input """
        # We close video stream
        self.video_player.set_state(gst.STATE_NULL)
        # Open a image capture pipeline
        snap_pipeline = "v4l2src device=/dev/video1 ! video/x-raw-yuv,width=%s,height=%s ! ffmpegcolorspace  ! %s ! filesink location=snapshot.%s" %(self.W, self.H, self.image_enc, self.snap_format)
        print snap_pipeline
        self.image_capture= gst.parse_launch(snap_pipeline)
        self.image_capture.set_state(gst.STATE_PLAYING)
        # Picture capture : Hack : it needs some time to take the picture, otherwise, the snaphsot is empty
        print "taking picture !"
        sleep(0.5)
        # Killing image capture pipeline
        self.image_capture.set_state(gst.STATE_NULL)
        # restoring video pipeline
        self.video_player.set_state(gst.STATE_PLAYING)

if __name__ == "__main__":

    # Before anything, let's be sure that we have a webcam plugged in
    if not exists('/dev/video0'):
        print "No webcam detected: /dev/video cannot be found.\n The program is now exiting."
        exit()

    # Argument parsing
    parser = argparse.ArgumentParser(description='Set video stream window parameters')
    parser.add_argument('--device', '-d',type=str, action='store', default='/dev/video0', help="Set the video input device path")
    parser.add_argument('--resolution', '-r', nargs='+', type=str,  default=['800:600'], 
                        choices = ['352:288', '640:480', '800:600', '960:720', '1280:720'],
                        help="Set the video stream resolution. Of form 'W H'")
    parser.add_argument('--framerate', '-f', type=str, default=30, help="Set the video stream framerate") # --> CHOICES = ?
    parser.add_argument('--output-format', '-o', type=str, action='store', default='png', choices=['png','jpeg','jpg'], help="Set the snapshot format")

    args = vars(parser.parse_args())
    device = args['device']
    resolution = args['resolution']
    framerate = args['framerate']
    snap_format = args['output_format']

    # Let the show begin 
    Webcam(device, resolution, framerate, snap_format)
    gtk.gdk.threads_init()
    gtk.main()
