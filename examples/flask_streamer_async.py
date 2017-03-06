#!/usr/bin/python

# Copyright 2017 Eric Callahan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from flask import Flask, render_template, Response

import uvclite
import time
import queue

app = Flask(__name__)
frame_queue = queue.Queue(5)
user_check = True

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        try:
            frame = frame_queue.get(timeout=.5)
        except queue.Empty:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.data + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(cap_dev),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def frame_callback(in_frame, user):
    global user_check
    if user_check:
        print("User id: %d" % user)
        user_check = False
    try:
        # Dont block in the callback!
        frame_queue.put(in_frame, block=False)
    except queue.Full:
        pass

if __name__ == '__main__':

    with uvclite.UVCContext() as context:
        cap_dev = context.find_device()
        cap_dev.set_callback(frame_callback, 12345)
        cap_dev.open()
        cap_dev.start_streaming()
        app.run(host='0.0.0.0', debug=False, threaded=True)
        print("Exiting...")
        cap_dev.stop_streaming()
        print("Closing..")
        cap_dev.close()
        print("Clear Context")
