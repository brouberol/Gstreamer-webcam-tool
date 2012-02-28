#!/usr/bin/env python

import argparse
from ssGUI import StrongsteamGUI

if __name__ == "__main__":

    # Argument parsing
    parser = argparse.ArgumentParser(description='Set video stream window parameters')
    parser.add_argument('--device', '-d',type=str, action='store', default='/dev/video0', help="Set the video input device path : /dev/videoX")
    parser.add_argument('--resolution', '-r', nargs='+', type=str,  default=['640:480'], 
                        choices = ['352:288', '640:480', '800:600', '960:720', '1280:720'],
                        help="Set the video stream resolution. Of the form W:H")
    parser.add_argument('--output-format', '-o', type=str, action='store', default='jpeg', choices=['png','jpeg'], help="Set the snapshot format")

    args = vars(parser.parse_args())
    device = args['device']
    resolution = args['resolution'][0].split(':')
    snap_format = args['output_format']

    # Let the show begin
    cam = StrongsteamGUI(device, resolution, snap_format)
    cam.run()
