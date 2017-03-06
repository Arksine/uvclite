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

app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        try:
            frame = camera.get_frame()
        except uvclite.UVCError as err:
            print(err.args)
            if err.errno == 110 or err.errno == 500:
                # 110 = read timeout, 500 = Null Frame
                continue
            else:
                raise err
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.data + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(cap_dev),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':

    with uvclite.UVCContext() as context:
        cap_dev = context.find_device()
        cap_dev.open()
        cap_dev.start_streaming()
        app.run(host='0.0.0.0', debug=False, threaded=True)
        print("Exiting...")
        cap_dev.stop_streaming()
        print("Closing..")
        cap_dev.close()
        print("Clear Context")
