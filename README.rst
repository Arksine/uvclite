UVCLite - A ctypes python wrapper around libuvc
===============================================

This library implements a simple ctypes wrapper around libuvc.  It
excludes support for conversion or decompression, if you are looking
for this functionality see pyuvc by Pupil Labs.  The primary use
case for this library is to capture frames from a UVC device and
redirect them somewhere else.  Currently only linux is supported.
All versions of python from 2.7 up should work, but only 3.4 and 3.6
have been tested.

Requirements:
-------------
libuvc
::
    git clone https://github.com/ktossell/libuvc
    cd libuvc
    mkdir build
    cd build
    cmake ..
    make && sudo make install
    sudo ldconfig

NOTE: the current version of libuvc has a bug that can potentially cause a
hang when streaming is stopped.  See `Issue 16`_ and `Pull Request 59`_ 
for explanations and potential fixes. 

.. _Issue 16: https://github.com/ktossell/libuvc/issues/16#issuecomment-101653441
.. _Pull Request 59: https://github.com/ktossell/libuvc/pull/59

Usage:
-----

.. code:: python

    import uvclite

    capturing = True
    with uvclite.UVCContext() as context:
        device = context.find_device() # finds first device
        device.open()
        device.set_stream_format()  # sets default format (MJPEG, 640x480, 30fps)
        device.start_streaming()

        while capturing:
            frame = device.get_frame()
            print(frame.size)  # print size of frame in bytes
            # do something with frame.data, a bytearray referencing the actual bytes
        
        device.stop_streaming()
        device.close()

The examples in this reposity demonstrate basic usage of a UVC Camera
capturing MJPEG frames at 640x480 30fps and displaying them on a flask
server.  These examples require that Flask be installed.  The server
code is credit to Miguel Grinberg (see `MJPEG Video Streamer`_)

.. _MJPEG Video Streamer: https://github.com/miguelgrinberg/flask-video-streaming)

License
-------
Copyright 2017 Eric Callahan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
