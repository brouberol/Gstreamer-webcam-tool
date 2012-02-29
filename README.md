<h1>Webcam viewer + snapshot using pyGTK and Gstreamer</h1>

<p>The idea of this project was to implement an interface allowing you to display a webcam live feed and to take snapshot from it.</p>

<h2>How do I use it?</h2>
<p>Type in
<pre>python demo.py</pre></p>
The possible (and optional) arguments are :
<ul>
  <li><code>-d</code> / <code>--device</code>: the device used for video input. Default:<code>/dev/video0</code>
  <li><code>-r</code> / <code>--resolution</code>: the webcam resolution. Format: W:H. Default: 640:480
  <li><code>-o</code> / <code>--ouput-format</code> the snapshot format. Available: jpeg & png. Default: jpeg
</ul>

<h2>What do I need ?</h2>
<p>This project uses gstreamer & pygtk. Consequently, the following modules are required:
<ul>
  <li><code>gst</code>
  <li><code>pygst</code>
  <li><code>gtk</code>
  <li><code>pygtk</code>
</ul></p>
