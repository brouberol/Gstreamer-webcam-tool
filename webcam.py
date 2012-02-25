#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ssGUI import Webcam

cam = Webcam(device='/dev/video1', resolution=(640,480), snap_format='jpg')
cam.run()
