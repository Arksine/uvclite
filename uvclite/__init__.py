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

""" A ctypes wrapper around libuvc

"""

from ctypes import byref, POINTER, c_void_p
import sys
from . import libuvc
from .standard_control_units import standard_ctrl_units
if sys.version[0] == 2:
    from builtins import range


__author__ = 'Eric Callahan'

__all__ = [
    'UVCError', 'UVCFrame', 'UVCDevice', 'UVCContext', 'UVCFrameFormat'
]

# UVC Enums
UVCFrameFormat = libuvc.uvc_frame_format

class UVCError(IOError):
    """
    Exception wrapper for libuvc error codes
    """
    def __init__(self, strerror, errnum=None):
        IOError.__init__(self, strerror, errnum)


def _check_error(errcode):
    # print("UVCLITE ERROR INFO:")
    err = libuvc.uvc_error(errcode)
    # print("err = {}".format(err))
    # print("dir(err = {}".format(dir(err)))
    # print("err.name = {}".format(err.name))
    # print("err.value = {}".format(err.value))
    if err != libuvc.uvc_error.UVC_SUCCESS:
        try:
            strerr = libuvc.uvc_strerror(err.value).decode('utf8')
        except AttributeError:
            strerr = libuvc.str_error_map[err]
        errnum = libuvc.libuvc_errno_map[err]
        raise UVCError(strerr, errnum)


class UVCFrame(object):
    """
    Represents a Frame received from a UVC Device.

    Public Attributes:
    frame   - reference to an actual uvc_frame struct.
              This should only be accessed if some of the
              lesser required members of that struct are
              neccessary.  See uvc_frame for more details.
    size    - size of the frame in bytes
    width   - frame width in pixels
    height  - frame height in pixels
    data    - a Python bytearray referencing the frame bytes
    """
    def __init__(self, frame_p):
        self.frame = frame_p.contents
        self.size = self.frame.data_bytes
        self.width = self.frame.width
        self.height = self.frame.height
        self.data = libuvc.buffer_at(self.frame.data, self.size)


def uint_array_to_GuidCode(u):
    s = ''
    for x in range(16):
        s += "{0:0{1}x}".format(u[x],2) # map int to rwo digit hex without "0x" prefix.
    return '%s%s%s%s%s%s%s%s-%s%s%s%s-%s%s%s%s-%s%s%s%s-%s%s%s%s%s%s%s%s%s%s%s%s'%tuple(s)


class UVCDevice(object):
    """
    Represents a UVC device.  To make things less complex
    for the user, device handles and device streams are
    also tracked.  All basic device operations are handled
    by this class.
    """
    def __init__(self, dev_p, new_ref=False):
        self._device_p = dev_p
        self._handle_p = c_void_p()
        self._stream_handle_p = None
        self._dev_desc_p = None
        self._new_ref = new_ref
        self._is_open = False
        self._stream_ctrl = libuvc.uvc_stream_ctrl()
        self._format_set = False
        self._frame_callback = libuvc.uvc_null_frame_callback
        self._user_id = None
        self.controls = {}

    def open(self):
        """
        Opens a UVC device and stores its Handle.
        """
        if not self._is_open:
            if self._new_ref:
                libuvc.uvc_ref_device(self._device_p)

            ret = libuvc.uvc_open(self._device_p, byref(self._handle_p))
            _check_error(ret)
            self._enumerate_controls()
            self._is_open = True

    def _enumerate_controls(self):
        """
        Build out the self.controls list containing all control objects for this camera
        """

        input_terminal = libuvc.uvc_get_input_terminals(self._handle_p)
        # cdef uvc.uvc_output_terminal_t  *output_terminal = uvc.uvc_get_output_terminals(self._handle_p)
        processing_unit =  libuvc.uvc_get_processing_units(self._handle_p)
        extension_unit = libuvc.uvc_get_extension_units(self._handle_p)
        

        available_controls_per_unit = {}
        id_per_unit = {}
        extension_units = {}
        while extension_unit:
            guidExtensionCode = uint_array_to_GuidCode(extension_unit.contents.guidExtensionCode)
            # print("guidExtensionCode = {}".format(guidExtensionCode))
            id_per_unit[guidExtensionCode] = extension_unit.contents.bUnitId
            available_controls_per_unit[guidExtensionCode] = extension_unit.contents.bmControls
            extension_unit = extension_unit.contents.next

        while input_terminal:
            available_controls_per_unit['input_terminal'] = input_terminal.contents.bmControls
            id_per_unit['input_terminal'] = input_terminal.contents.bTerminalId
            input_terminal = input_terminal.contents.next

        while processing_unit:
            available_controls_per_unit['processing_unit'] = processing_unit.contents.bmControls
            id_per_unit['processing_unit'] = processing_unit.contents.bUnitId
            processing_unit = processing_unit.contents.next

        for std_ctl in standard_ctrl_units:
            if std_ctl['bit_mask'] & available_controls_per_unit[std_ctl['unit']]:
                # print('Adding "%s" control.'%std_ctl['display_name'])
                std_ctl['unit_id'] = id_per_unit[std_ctl['unit']]
                try:
                    control = libuvc.Control(self._handle_p, **std_ctl)
                except Exception as e:
                    print("Could not init '%s'! Error: %s" %(std_ctl['display_name'],e))
                    raise
                else:
                    self.controls[control.display_name] = control

    def print_controls(self):
        for c in self.controls.values():
            print(c)

    def set_control_defaults(self):
        """
        Set all controls to default values
        """
        for ctrl_name, control in self.controls.items():
            self.set_control(ctrl_name, control.def_val)
   
    def set_control(self, ctrl_name, value):
        # TODO: For Exposure Time and White Balance Temperature, we need to disable the
        # automatic mode setting before we can attempt to set them manually
        # When trying to set those values manually with automatic mode enabled, get an
        # ErrNo 32 Pipe Error
        ret = True
        try:
            control = self.controls[ctrl_name]
            control.value = value
            # print("SET {} SUCCESSFULLY".format(ctrl_name))
        except Exception as e:
            # print("SET {} FAILED".format(ctrl_name))
            print(e)
            ret = False
        return ret


    def get_control(self, ctrl_name):
        control = self.controls[ctrl_name]
        return control.value

    def close(self):
        """
        Closes the device and removes its reference.  A device
        cannot be reopened after it has been closed, you must
        request a new device from either find_device() or
        get_device_list() in the UVCContext class.
        """
        if self._stream_handle_p:
            self.stop_streaming()

        if self._dev_desc_p:
            libuvc.uvc_free_device_descriptor(self._dev_desc_p)

        if self._is_open:
            libuvc.uvc_close(self._handle_p)
            self._is_open = False
        libuvc.uvc_unref_device(self._device_p)

    def set_stream_format(self, frame_format=UVCFrameFormat.UVC_FRAME_FORMAT_MJPEG,
                          width=640, height=480, frame_rate=30):
        """
        Sets the stream parameters.

        Params:
        frame_format - the pixel/frame format expected from the UVC Device
                       See the enum uvc_frame_format for options
        width        - width of frame in pixels (int)
        height       - height of frame in pixels (int)
        frame_rate   - frame rate expected from device (int)
        """
        ret = libuvc.uvc_get_stream_ctrl_format_size(
            self._handle_p, byref(self._stream_ctrl), frame_format.value, width,
            height, frame_rate)

        _check_error(ret)
        self._format_set = True

    def set_callback(self, callback, user_id=None):
        """
        Sets the optional callback for asynchronous I/O. The
        device defaults to polling mode if no callback is
        set.  To reset back to polling mode send None as
        the callback parameter.

        Params:
        callback -  A function that will be called whenever
                    a frame is received.  The format should be:
                    callback(frame, userid)
        user_id -   An integer that identifies the user that
                    set the callback.  Any unique integer is ok
        """
        # don't set while streaming
        if not self._stream_handle_p:
            if not callback:
                self._frame_callback = libuvc.uvc_null_frame_callback
                self._user_id = None
            else:
                def _frame_cb(frame, user):
                    if frame:
                        new_frame = UVCFrame(frame)
                        callback(new_frame, user)

                self._frame_callback = libuvc.uvc_frame_callback(_frame_cb)
                self._user_id = user_id

    def start_streaming(self):
        """
        Start streaming video.  Video can either be polled by calling
        the get_frame() member or retreived through an optional
        callback
        """
        if not self._format_set:
            # if the format hasn't been set, use default values
            self.set_stream_format()

        # don't open a stream if we are already streaming
        if not self._stream_handle_p:
            # open the stream.  Polling mode if callback is not supplied
            self._stream_handle_p = c_void_p()
            # print("UVCLITE: open stream ctrl")
            ret = libuvc.uvc_stream_open_ctrl(self._handle_p, byref(self._stream_handle_p),
                                              byref(self._stream_ctrl))

            _check_error(ret)

            # print("UVCLITE: start stream")
            ret = libuvc.uvc_stream_start(self._stream_handle_p, self._frame_callback,
                                          self._user_id, 0)
            _check_error(ret)

    def stop_streaming(self):
        """
        Stops streaming video from the device and
        releases the stream handle.
        """
        # Dont close unless we are streaming
        if self._stream_handle_p:
            libuvc.uvc_stream_stop(self._stream_handle_p)
            libuvc.uvc_stream_close(self._stream_handle_p)
            self._stream_handle_p = None

    def get_frame(self, timeout=1000000):
        """
        When in polling mode, retreives the next frame in the buffer.
        When get_frame is called, the previous buffer is overrwitten,
        so make sure you have either copied the buffer or finished
        you work on the previous buffer before calling again.

        Timeout is in microseconds, default is a 1 second timeout.
        Set timeout to 0 to block indefinitely, -1 to return immediately.
        If the timeout is set it is a good idea to catch errors when
        attempting to call this function

        If this is called when a callback has been set, a UVCError will
        be raised.
        """

        frame = libuvc.uvc_frame_p()
        ret = libuvc.uvc_stream_get_frame(self._stream_handle_p, byref(frame), timeout)
        _check_error(ret)

        if frame:
            return UVCFrame(frame)
        else:
            raise UVCError("Null Frame", 500)

    def get_device_descriptor(self):
        """
        Retreives the device descriptor.

        This function returns the contents of the descriptor,
        so the user may access its fields:
        idVendor     - USB vendor Id (int)
        idProduct    - USB product Id (int)
        bcdUVC       - UVC compliance level (int)
        serialNumber - USB serial number (str if available, None if not)
        manufacturer - USB Manufacturer  (str if available, None if not)
        product      - USB Product name (str if available, None if not)

        Usage:

        desc = dev.get_device_descriptor()
        if desc.idVendor == 0x1234:
            # do something
        """
        if not self._dev_desc_p:
            self._dev_desc_p = libuvc.uvc_device_descriptor_p()
            ret = libuvc.uvc_get_device_descriptor(self._device_p, byref(self._dev_desc_p))
            _check_error(ret)
        return self._dev_desc_p.contents

    def free_device_descriptor(self):
        """
        Free's the device descriptor.  Only necessary when a descriptor
        request is made when the device is not to be opened (and thus
        closed)
        """
        if self._dev_desc_p:
            libuvc.uvc_free_device_descriptor(self._dev_desc_p)
            self._dev_desc_p = None

    def get_device_bus_number(self):
        if self._device_p:
            return libuvc.uvc_get_bus_number(self._device_p)

    def get_device_address(self):
        if self._device_p:
            return libuvc.uvc_get_device_address(self._device_p)

    def print_diagnostics(self):
        """
        Prints device information and diagnostics to stderr. Should
        only be called after device is opened.
        """
        if self._is_open:
            libuvc.uvc_print_diag(self._handle_p, None)

class DeviceList(object):
    """
    Presents a Python List representation of a UVCDevice list.
    """
    def __init__(self, dev_list_p):
        self._device_list_p = dev_list_p
        self._dev_count = 0

        # get device count.  The uvc get device list function
        # does not return a count, so I assume it is null terminated
        while True:
            if self._device_list_p[self._dev_count]:
                self._dev_count += 1
            else:
                break
    def __getitem__(self, key):
        if key >= 0 and key < self._dev_count:
            return UVCDevice(self._device_list_p[key], True)
        else:
            raise IndexError()

    def __iter__(self):
        for i in range(self._dev_count):
            yield UVCDevice(self._device_list_p[i], True)

    def __len__(self):
        return self._dev_count

class UVCContext(object):
    """
    Reprensents a libuvc context.  Every libuvc app must retreive a context
    prior to any operations.  It is recommended to use a with statement
    to retreive a context so resources are automatically cleaned up. For
    example:

    try:
        with UVCContext() as context:
            # find a device, do stuff

    except UVCError():
        # Handle your exception

    """
    def __init__(self):
        self._context_p = c_void_p()
        self._device_list_p = None

        # Retreive uvc context.
        ret = libuvc.uvc_init(byref(self._context_p), None)
        _check_error(ret)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """

        Releases UVC Context and frees up resources

        """
        if self._device_list_p:
            # free device list if it exists
            libuvc.uvc_free_device_list(self._device_list_p, 1)
            self._device_list_p = None

        if self._context_p:
            libuvc.uvc_exit(self._context_p)
            self._context_p = None

    def find_device(self, vendor_id=0, product_id=0, serial_number=None):
        """
        Attempts to find a device.  Returns the first UVC device found
        matching the given parameters.

        Params:
        vendor_id   Usb Vendor Id of the device to find. (integer)
        product_id  Usb Product Id of the the device to find (integer)
        serial_number Serial Number of the device to find (string)

        Returns:
        UVCDevice object

        Usage:
        All parameters are optional.  If any parameter is left out,
        the first device found matching the remaining parmeters will
        be returned.  If no device is found this function will raise
        a UVCError exception.

        Examples:
        Find the first uvc device on the System:
        context.find_device()

        Find device matching product id 0x1234:
        context.find_device(product_id=0x1234)
        """
        dev_p = c_void_p()
        if serial_number:
            ser = serial_number.encode('utf-8')
            ret = libuvc.uvc_find_device(self._context_p, byref(dev_p),
                                         vendor_id, product_id, ser)
        else:
            ret = libuvc.uvc_find_device(self._context_p, byref(dev_p),
                                         vendor_id, product_id, None)

        _check_error(ret)

        return UVCDevice(dev_p)

    def get_device_list(self):
        """
        Retreives a list of UVC devices on the system.  If a device list has
        already been allocated, it will be freed upon successive calls.  This
        is done to easily track device references as libuvc requires.
        The following example would fail:

        dev_list = context.get_device_list()
        device = list[0]
        new_list = context.get_device_list()
        device.open()

        In the situation above, the first call to device list allocates
        a reference to every device found on the system.  When the
        second call to device list is made, the reference that 'device'
        holds is destroyed.  If device.open() had been called prior
        to a new list request it would have increased the its ref
        count and everything would work okay.
        """
        if self._device_list_p:
            libuvc.uvc_free_device_list(self._device_list_p, 1)

        self._device_list_p = POINTER(c_void_p)()
        ret = libuvc.uvc_get_device_list(self._context_p, byref(self._device_list_p))
        # print("ret = {}".format(ret))
        _check_error(ret)

        return DeviceList(self._device_list_p)
