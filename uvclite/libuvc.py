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

# pylint: disable=no-member
# pylint: disable=W0511,W0622,W0613,W0603,R0902,C0103,W0614,W0401,W0212,R0903,C0111

from ctypes import *
import sys
import errno
from enum import Enum

import logging

logger = logging.getLogger(__name__)

__author__ = 'Eric Callahan'

# __all__ attribtue only includes basic functionality needed for uvclite.
__all__ = [
    'buffer_at',
    'str_error_map',
    'libuvc_errno_map',
    'uvc_error',
    'uvc_init',
    'uvc_exit',
    'uvc_find_device',
    'uvc_get_device_list',
    'uvc_free_device_list',
    'uvc_ref_device',
    'uvc_unref_device',
    'uvc_open',
    'uvc_close',
    'uvc_device_descriptor',
    'uvc_device_descriptor_p',
    'uvc_get_device_descriptor',
    'uvc_free_device_descriptor',
    'uvc_stream_ctrl',
    'uvc_get_stream_ctrl_format_size',
    'uvc_frame_callback',
    'uvc_null_frame_callback',
    'uvc_stream_open_ctrl',
    'uvc_stream_start',
    'uvc_start_streaming',
    'uvc_stream_stop',
    'uvc_stream_close',
    'uvc_stop_streaming',
    'uvc_frame',
    'uvc_frame_p',
    'uvc_stream_get_frame',
    'uvc_print_diag'
]

# TODO: create function for more robust library loading, that should hopefully
# work on all platforms
_libuvc = CDLL('libuvc.so')

class UVCError(IOError):
    """
    Exception wrapper for libuvc error codes
    """
    def __init__(self, strerror, errnum=None):
        IOError.__init__(self, strerror, errnum)

def _check_error(errcode):
    err = uvc_error(errcode)
    if err != uvc_error.UVC_SUCCESS:
        try:
            strerr = uvc_strerror(err.value).decode('utf8')
        except AttributeError:
            strerr = str_error_map[err]
        errnum = libuvc_errno_map[err]
        raise UVCError(strerr, errnum)

def buffer_at(address, length):
    """
    Similar to ctypes.string_at, but zero-copy and requires an integer address.
    """
    return bytearray((c_char * length).from_address(address))

# libuvc.h

# enum uvc_error (uvc_error_t) return codes
class uvc_error(Enum):
    UVC_SUCCESS = 0
    UVC_ERROR_IO = -1
    UVC_ERROR_INVALID_PARAM = -2
    UVC_ERROR_ACCESS = -3
    UVC_ERROR_NO_DEVICE = -4
    UVC_ERROR_NOT_FOUND = -5
    UVC_ERROR_BUSY = -6
    UVC_ERROR_TIMEOUT = -7
    UVC_ERROR_OVERFLOW = -8
    UVC_ERROR_PIPE = -9
    UVC_ERROR_INTERRUPTED = -10
    UVC_ERROR_NO_MEM = -11
    UVC_ERROR_NOT_SUPPORTED = -12
    UVC_ERROR_INVALID_DEVICE = -50
    UVC_ERROR_INVALID_MODE = -51
    UVC_ERROR_CALLBACK_EXISTS = -52
    UVC_ERROR_OTHER = -99

# map return codes to string messages
str_error_map = {
    uvc_error.UVC_SUCCESS:'Success (no error)',
    uvc_error.UVC_ERROR_IO:'Input/output error',
    uvc_error.UVC_ERROR_INVALID_PARAM:'Invalid parameter',
    uvc_error.UVC_ERROR_ACCESS:'Access denied',
    uvc_error.UVC_ERROR_NO_DEVICE:'No such device',
    uvc_error.UVC_ERROR_NOT_FOUND:'Not found',
    uvc_error.UVC_ERROR_BUSY:"Resource Busy",
    uvc_error.UVC_ERROR_TIMEOUT:'Operation timed out',
    uvc_error.UVC_ERROR_OVERFLOW:'Overflow',
    uvc_error.UVC_ERROR_PIPE:'Pipe Error',
    uvc_error.UVC_ERROR_INTERRUPTED:'System call interrupted (perhaps due to signal)',
    uvc_error.UVC_ERROR_NO_MEM:'Insufficient memory',
    uvc_error.UVC_ERROR_INVALID_DEVICE:'Invalid device',
    uvc_error.UVC_ERROR_INVALID_MODE:'Invalid mode',
    uvc_error.UVC_ERROR_CALLBACK_EXISTS:'Callback exists, cannot poll',
    uvc_error.UVC_ERROR_OTHER:'Unknown Error'
}

# map return codes to error numbers
libuvc_errno_map = {
    uvc_error.UVC_SUCCESS:None,
    uvc_error.UVC_ERROR_IO:errno.__dict__.get('EIO', None),
    uvc_error.UVC_ERROR_INVALID_PARAM:errno.__dict__.get('EINVAL', None),
    uvc_error.UVC_ERROR_ACCESS:errno.__dict__.get('EACCES', None),
    uvc_error.UVC_ERROR_NO_DEVICE:errno.__dict__.get('ENODEV', None),
    uvc_error.UVC_ERROR_NOT_FOUND:errno.__dict__.get('ENOENT', None),
    uvc_error.UVC_ERROR_BUSY:errno.__dict__.get('EBUSY', None),
    uvc_error.UVC_ERROR_TIMEOUT:errno.__dict__.get('ETIMEDOUT', None),
    uvc_error.UVC_ERROR_OVERFLOW:errno.__dict__.get('EOVERFLOW', None),
    uvc_error.UVC_ERROR_PIPE:errno.__dict__.get('EPIPE', None),
    uvc_error.UVC_ERROR_INTERRUPTED:errno.__dict__.get('EINTR', None),
    uvc_error.UVC_ERROR_NO_MEM:errno.__dict__.get('ENOMEM', None),
    uvc_error.UVC_ERROR_NOT_SUPPORTED:errno.__dict__.get('EOPNOTSUPP', None),
    uvc_error.UVC_ERROR_INVALID_DEVICE:errno.__dict__.get('EBADSLT', None),
    uvc_error.UVC_ERROR_INVALID_MODE:errno.__dict__.get('EBADR', None),
    uvc_error.UVC_ERROR_CALLBACK_EXISTS:errno.__dict__.get('EBADE', None),
    uvc_error.UVC_ERROR_OTHER:None
}

# enum uvc_frame_format
class uvc_frame_format(Enum):
    UVC_FRAME_FORMAT_UNKNOWN = 0
    UVC_FRAME_FORMAT_ANY = 0
    UVC_FRAME_FORMAT_UNCOMPRESSED = 1
    UVC_FRAME_FORMAT_COMPRESSED = 2
    UVC_FRAME_FORMAT_YUYV = 3
    UVC_FRAME_FORMAT_UYVY = 4
    UVC_FRAME_FORMAT_RGB = 5
    UVC_FRAME_FORMAT_BGR = 6
    UVC_FRAME_FORMAT_MJPEG = 7
    UVC_FRAME_FORMAT_GRAY8 = 8
    UVC_FRAME_FORMAT_BY8 = 9
    UVC_FRAME_FORMAT_COUNT = 10

# enum uvc_vs_des_subtype
class uvc_vs_des_subtype(Enum):
    UVC_VS_UNDEFINED = 0x00
    UVC_VS_INPUT_HEADER = 0x01
    UVC_VS_OUTPUT_HEADER = 0x02
    UVC_VS_STILL_IMAGE_FRAME = 0x03
    UVC_VS_FORMAT_UNCOMPRESSED = 0x04
    UVC_VS_FRAME_UNCOMPRESSED = 0x05
    UVC_VS_FORMAT_MJPEG = 0x06
    UVC_VS_FRAME_MJPEG = 0x07
    UVC_VS_FORMAT_MPEG2TS = 0x0a
    UVC_VS_FORMAT_DV = 0x0c
    UVC_VS_COLORFORMAT = 0x0d
    UVC_VS_FORMAT_FRAME_BASED = 0x10
    UVC_VS_FRAME_FRAME_BASED = 0x11
    UVC_VS_FORMAT_STREAM_BASED = 0x12

# IMPORTANT: C enums are mapped to c_int in python

class _format_union(Union):
    _fields_ = [('guidFormat', ARRAY(c_uint8, 16)),
                ('fourccFormat', ARRAY(c_uint8, 4))]

class _bit_union(Union):
    _fields_ = [('bBitsPerPixel', c_uint8),
                ('bmFlags', c_uint8)]

class uvc_format_desc(Structure):
    pass

uvc_format_desc_p = POINTER(uvc_format_desc)

class uvc_frame_desc(Structure):
    pass

uvc_frame_desc_p = POINTER(uvc_frame_desc)
uvc_frame_desc._fields_ = [('parent', uvc_format_desc_p),
                           ('prev', uvc_frame_desc_p),
                           ('next', uvc_frame_desc_p),
                           ('bDescriptorSubtype', c_int), # enum uvc_vs_desc_subtype
                           ('bFrameIndex', c_uint8),
                           ('bmCapabilities', c_uint8),
                           ('wWidth', c_uint16),
                           ('wHeight', c_uint16),
                           ('dwMinBitRate', c_uint32),
                           ('dwMaxBitRate', c_uint32),
                           ('dwMaxVideoFrameBufferSize', c_uint32),
                           ('dwDefaultFrameInterval', c_uint32),
                           ('dwMinFrameInterval', c_uint32),
                           ('dwMaxFrameInterval', c_uint32),
                           ('dwFrameIntervalStep', c_uint32),
                           ('bFrameIntervalType', c_uint8),
                           ('dwBytesPerLine', c_uint32),
                           ('intervals', POINTER(c_uint32))]

uvc_format_desc._anonymous_ = ('fmt', 'bit',)
uvc_format_desc._fields_ = [('parent', c_void_p),
                            ('prev', uvc_format_desc_p),
                            ('next', uvc_format_desc_p),
                            ('bDescriptorSubtype', c_int),      # enum uvc_vs_desc_subtype
                            ('bFormatIndex', c_uint8),
                            ('bNumFrameDescriptors', c_uint8),
                            ('fmt', _format_union),
                            ('bit', _bit_union),
                            ('bDefaultFrameIndex', c_uint8),
                            ('bAspectRatioX', c_uint8),
                            ('bAspectRatioY', c_uint8),
                            ('bmInterlaceFlags', c_uint8),
                            ('bCopyProtect', c_uint8),
                            ('bVariableSize', c_uint8),
                            ('frame_descs', uvc_frame_desc_p)]

# enum_uvc_req_code
class uvc_req_code(Enum):
    UVC_RC_UNDEFINED = 0x00
    UVC_SET_CUR = 0x01
    UVC_GET_CUR = 0x81
    UVC_GET_MIN = 0x82
    UVC_GET_MAX = 0x83
    UVC_GET_RES = 0x84
    UVC_GET_LEN = 0x85
    UVC_GET_INFO = 0x86
    UVC_GET_DEF = 0x87

# enum uvc_device_power_mode
class uvc_device_power_mode(Enum):
    UVC_VC_VIDEO_POWER_MODE_FULL = 0x000b
    UVC_VC_VIDEO_POWER_MODE_DEVICE_DEPENDENT = 0x001b

# TODO:
# enum uvc_ct_ctrl_selector
class uvc_ct_ctrl_selector(Enum):
    UVC_CT_CONTROL_UNDEFINED = 0x00
    UVC_CT_SCANNING_MODE_CONTROL = 0x01
    UVC_CT_AE_MODE_CONTROL = 0x02
    UVC_CT_AE_PRIORITY_CONTROL = 0x03
    UVC_CT_EXPOSURE_TIME_ABSOLUTE_CONTROL = 0x04
    UVC_CT_EXPOSURE_TIME_RELATIVE_CONTROL = 0x05
    UVC_CT_FOCUS_ABSOLUTE_CONTROL = 0x06
    UVC_CT_FOCUS_RELATIVE_CONTROL = 0x07
    UVC_CT_FOCUS_AUTO_CONTROL = 0x08
    UVC_CT_IRIS_ABSOLUTE_CONTROL = 0x09
    UVC_CT_IRIS_RELATIVE_CONTROL = 0x0a
    UVC_CT_ZOOM_ABSOLUTE_CONTROL = 0x0b
    UVC_CT_ZOOM_RELATIVE_CONTROL = 0x0c
    UVC_CT_PANTILT_ABSOLUTE_CONTROL = 0x0d
    UVC_CT_PANTILT_RELATIVE_CONTROL = 0x0e
    UVC_CT_ROLL_ABSOLUTE_CONTROL = 0x0f
    UVC_CT_ROLL_RELATIVE_CONTROL = 0x10
    UVC_CT_PRIVACY_CONTROL = 0x11
    UVC_CT_FOCUS_SIMPLE_CONTROL = 0x12
    UVC_CT_DIGITAL_WINDOW_CONTROL = 0x13
    UVC_CT_REGION_OF_INTEREST_CONTROL = 0x14

# enum uvc_pu_ctrl_selector
class uvc_pu_ctrl_selector(Enum):
    UVC_PU_CONTROL_UNDEFINED = 0x00
    UVC_PU_BACKLIGHT_COMPENSATION_CONTROL = 0x01
    UVC_PU_BRIGHTNESS_CONTROL = 0x02
    UVC_PU_CONTRAST_CONTROL = 0x03
    UVC_PU_GAIN_CONTROL = 0x04
    UVC_PU_POWER_LINE_FREQUENCY_CONTROL = 0x05
    UVC_PU_HUE_CONTROL = 0x06
    UVC_PU_SATURATION_CONTROL = 0x07
    UVC_PU_SHARPNESS_CONTROL = 0x08
    UVC_PU_GAMMA_CONTROL = 0x09
    UVC_PU_WHITE_BALANCE_TEMPERATURE_CONTROL = 0x0a
    UVC_PU_WHITE_BALANCE_TEMPERATURE_AUTO_CONTROL = 0x0b
    UVC_PU_WHITE_BALANCE_COMPONENT_CONTROL = 0x0c
    UVC_PU_WHITE_BALANCE_COMPONENT_AUTO_CONTROL = 0x0d
    UVC_PU_DIGITAL_MULTIPLIER_CONTROL = 0x0e
    UVC_PU_DIGITAL_MULTIPLIER_LIMIT_CONTROL = 0x0f
    UVC_PU_HUE_AUTO_CONTROL = 0x10
    UVC_PU_ANALOG_VIDEO_STANDARD_CONTROL = 0x11
    UVC_PU_ANALOG_LOCK_STATUS_CONTROL = 0x12
    UVC_PU_CONTRAST_AUTO_CONTROL = 0x13

# enum uvc_term_type
class uvc_term_type(Enum):
    UVC_TT_VENDOR_SPECIFIC = 0x0100
    UVC_TT_STREAMING = 0x0101

# enum uvc_it_type
class uvc_it_type(Enum):
    UVC_ITT_VENDOR_SPECIFIC = 0x0200
    UVC_ITT_CAMERA = 0x0201
    UVC_ITT_MEDIA_TRANSPORT_INPUT = 0x0202

# enum_uvc_ot_type
class uvc_ot_type(Enum):
    UVC_OTT_VENDOR_SPECIFIC = 0x0300
    UVC_OTT_DISPLAY = 0x0301
    UVC_OTT_MEDIA_TRANSPORT_OUTPUT = 0x0302

# enum_uvc_et_type
class uvc_et_type(Enum):
    UVC_EXTERNAL_VENDOR_SPECIFIC = 0x0400
    UVC_COMPOSITE_CONNECTOR = 0x0401
    UVC_SVIDEO_CONNECTOR = 0x0402
    UVC_COMPONENT_CONNECTOR = 0x0403

# struct uvc_input_terminal
class uvc_input_terminal(Structure):
    pass

uvc_input_terminal_p = POINTER(uvc_input_terminal)
uvc_input_terminal._fields_ = [('prev', uvc_input_terminal_p),
                               ('next', uvc_input_terminal_p),
                               ('bTerminalId', c_uint8),
                               ('wTerminalType', c_int),  # enum uvc_it_type
                               ('wObjectiveFocalLengthMin', c_uint16),
                               ('wObjectiveFocalLengthMax', c_uint16),
                               ('wOcularFocalLength', c_uint16),
                               ('bmControls', c_uint64)]

# struct uvc_output_terminal
# TODO: This isn't fully implemented by libuvc
class uvc_output_terminal(Structure):
    pass

uvc_output_terminal_p = POINTER(uvc_output_terminal)
uvc_output_terminal._fields_ = [('prev', uvc_output_terminal_p),
                                ('next', uvc_output_terminal_p)]

# struct uvc_processing_unit
class uvc_processing_unit(Structure):
    pass

uvc_processing_unit_p = POINTER(uvc_processing_unit)
uvc_processing_unit._fields_ = [('prev', uvc_processing_unit_p),
                                ('next', uvc_processing_unit_p),
                                ('bUnitId', c_uint8),
                                ('bSourceId', c_uint8),
                                ('bmControls', c_uint64)]
# struct_uvc_extension_unit
class uvc_extension_unit(Structure):
    pass

uvc_extension_unit_p = POINTER(uvc_extension_unit)
uvc_extension_unit._fields_ = [('prev', uvc_extension_unit_p),
                               ('next', uvc_extension_unit_p),
                               ('bUnitId', c_uint8),
                               # this is how you declare ctypes arrays
                               # https://docs.python.org/3/library/ctypes.html#arrays
                               ('guidExtensionCode', c_uint8 * 16), 
                               ('bmControls', c_uint64)]

# enum uvc_status_class
class uvc_status_class(Enum):
    UVC_STATUS_CLASS_CONTROL = 0x10
    UVC_STATUS_CLASS_CONTROL_CAMERA = 0x11
    UVC_STATUS_CLASS_CONTROL_PROCESSING = 0x12

# enum uvc_status_attribute
class uvc_status_attribute(Enum):
    UVC_STATUS_ATTRIBUTE_VALUE_CHANGE = 0x00
    UVC_STATUS_ATTRIBUTE_INFO_CHANGE = 0x01
    UVC_STATUS_ATTRIBUTE_FAILURE_CHANGE = 0x02
    UVC_STATUS_ATTRIBUTE_UNKNOWN = 0xff

# status callback
# typedef void(uvc_status_callback_t)(enum uvc_status_class status_class,
#                                     int event,
#                                     int selector,
#                                     enum uvc_status_attribute status_attribute,
#                                     void *data, size_t data_len,
#                                     void *user_ptr);
uvc_status_callback = CFUNCTYPE(None, c_int, c_int, c_int, c_int,
                                c_void_p, c_size_t, c_void_p)


# button callback
# typedef void(uvc_button_callback_t)(int button,
#                                     int state,
#                                     void *user_ptr);
uvc_button_callback = CFUNCTYPE(None, c_int, c_int, c_void_p)

# struct uvc_device_descriptor
class uvc_device_descriptor(Structure):
    _fields_ = [('idVendor', c_uint16),
                ('idProduct', c_uint16),
                ('bcdUVC', c_uint16),
                ('serialNumber', c_char_p),
                ('manufacturer', c_char_p),
                ('product', c_char_p)]

uvc_device_descriptor_p = POINTER(uvc_device_descriptor)

class _timeval(Structure):
    _fields_ = [('tv_sec', c_long),  #this is actually time_t, I assume its a long on linux
                ('tv_usec', c_long)]

class uvc_frame(Structure):
    _fields_ = [('data', c_void_p),
                ('data_bytes', c_size_t),
                ('width', c_uint32),
                ('height', c_uint32),
                ('frame_format', c_int),
                ('step', c_size_t),
                ('sequence', c_uint32),
                ('capture_time', _timeval),
                ('source', c_void_p),
                ('library_owns_data', c_uint8)]

uvc_frame_p = POINTER(uvc_frame)

#  typedef void(uvc_frame_callback_t)(struct uvc_frame *frame, void *user_ptr);
uvc_frame_callback = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)
uvc_null_frame_callback = cast(None, uvc_frame_callback)

class uvc_stream_ctrl(Structure):
    _fields_ = [('bmHint', c_uint16),
                ('bFormatIndex', c_uint8),
                ('bFrameIndex', c_int8),
                ('dwFrameInterval', c_int32),
                ('wKeyFrameRate', c_uint16),
                ('wPFrameRate', c_uint16),
                ('wCompQuality', c_uint16),
                ('wCompWindowSize', c_uint16),
                ('wDelay', c_uint16),
                ('dwMaxVideoFrameSize', c_uint32),
                ('dwMaxPayloadTransferSize', c_uint32),
                ('dwClockFrequency', c_uint32),
                ('bmFramingInfo', c_uint8),
                ('bPreferredVersion', c_uint8),
                ('bMinVersion', c_uint8),
                ('bMaxVersion', c_uint8),
                ('bInterfaceNumber', c_uint8)]

### Function prototypes###

# uvc_error_t uvc_init(uvc_context_t **ctx, struct libusb_context *usb_ctx);
uvc_init = _libuvc.uvc_init
uvc_init.argtypes = [POINTER(c_void_p), c_void_p]

# void uvc_exit(uvc_context_t *ctx);
uvc_exit = _libuvc.uvc_exit
uvc_exit.argtypes = [c_void_p]
uvc_exit.restype = None

# uvc_error_t uvc_get_device_list(uvc_context_t *ctx,
#                                 uvc_device_t ***list);
uvc_get_device_list = _libuvc.uvc_get_device_list
uvc_get_device_list.argtypes = [c_void_p, POINTER(POINTER(c_void_p))]

# void uvc_free_device_list(uvc_device_t **list, uint8_t unref_devices);
uvc_free_device_list = _libuvc.uvc_free_device_list
uvc_free_device_list.argtypes = [POINTER(c_void_p), c_uint8]
uvc_free_device_list.restype = None

# uvc_error_t uvc_get_device_descriptor(uvc_device_t *dev,
#                                       uvc_device_descriptor_t **desc);
uvc_get_device_descriptor = _libuvc.uvc_get_device_descriptor
uvc_get_device_descriptor.argtypes = [c_void_p, POINTER(uvc_device_descriptor_p)]


#void uvc_free_device_descriptor(uvc_device_descriptor_t *desc);
uvc_free_device_descriptor = _libuvc.uvc_free_device_descriptor
uvc_free_device_descriptor.argtypes = [uvc_device_descriptor_p]
uvc_free_device_descriptor.restype = None

# uint8_t uvc_get_bus_number(uvc_device_t *dev);
uvc_get_bus_number = _libuvc.uvc_get_bus_number
uvc_get_bus_number.argtypes = [c_void_p]
uvc_get_bus_number.restype = c_uint8

# uint8_t uvc_get_device_address(uvc_device_t *dev);
uvc_get_device_address = _libuvc.uvc_get_device_address
uvc_get_device_address.argtypes = [c_void_p]
uvc_get_device_address.restype = c_uint8

# uvc_error_t uvc_find_device(uvc_context_t *ctx,
#                             uvc_device_t **dev,
#                             int vid,
#                             int pid,
#                             const char *sn);
uvc_find_device = _libuvc.uvc_find_device
uvc_find_device.argtypes = [
    c_void_p,
    POINTER(c_void_p),
    c_int,
    c_int,
    c_char_p
]

# uvc_error_t uvc_open(uvc_device_t *dev, uvc_device_handle_t **devh);
uvc_open = _libuvc.uvc_open
uvc_open.argtypes = [c_void_p, POINTER(c_void_p)]

# void uvc_close(uvc_device_handle_t *devh);
uvc_close = _libuvc.uvc_close
uvc_close.argtypes = [c_void_p]
uvc_close.restype = None

# uvc_device_t *uvc_get_device(uvc_device_handle_t *devh);
uvc_get_device = _libuvc.uvc_get_device
uvc_get_device.argtypes = [c_void_p]
uvc_get_device.restype = c_void_p

# libusb_device_handle *uvc_get_libusb_handle(uvc_device_handle_t *devh);
uvc_get_libusb_handle = _libuvc.uvc_get_libusb_handle
uvc_get_libusb_handle.argtypes = [c_void_p]
uvc_get_libusb_handle.restype = c_void_p

# void uvc_ref_device(uvc_device_t *dev);
uvc_ref_device = _libuvc.uvc_ref_device
uvc_ref_device.argtypes = [c_void_p]
uvc_ref_device.restype = None

# void uvc_unref_device(uvc_device_t *dev);
uvc_unref_device = _libuvc.uvc_unref_device
uvc_unref_device.argtypes = [c_void_p]
uvc_unref_device.restype = None

# TODO:
# void uvc_set_status_callback(uvc_device_handle_t *devh,
#                              uvc_status_callback_t cb,
#                              void *user_ptr);
# const uvc_input_terminal_t *uvc_get_input_terminals(uvc_device_handle_t *devh);
# const uvc_output_terminal_t *uvc_get_output_terminals(uvc_device_handle_t *devh);
# const uvc_processing_unit_t *uvc_get_processing_units(uvc_device_handle_t *devh);
# const uvc_extension_unit_t *uvc_get_extension_units(uvc_device_handle_t *devh);
uvc_get_input_terminals = _libuvc.uvc_get_input_terminals
uvc_get_input_terminals.argtypes = [c_void_p]
uvc_get_input_terminals.restype = uvc_input_terminal_p
uvc_get_processing_units = _libuvc.uvc_get_processing_units
uvc_get_processing_units.argtypes = [c_void_p]
uvc_get_processing_units.restype = uvc_processing_unit_p
uvc_get_extension_units = _libuvc.uvc_get_extension_units
uvc_get_extension_units.argtypes = [c_void_p]
uvc_get_extension_units.restype = uvc_extension_unit_p

# uvc_error_t uvc_get_stream_ctrl_format_size(uvc_device_handle_t *devh,
#                                             uvc_stream_ctrl_t *ctrl,
#                                             enum uvc_frame_format format,
#                                             int width,
#                                             int height,
#                                             int fps);
uvc_get_stream_ctrl_format_size = _libuvc.uvc_get_stream_ctrl_format_size
uvc_get_stream_ctrl_format_size.argtypes = [
    c_void_p,
    POINTER(uvc_stream_ctrl),
    c_int,
    c_int,
    c_int,
    c_int
]

# const uvc_format_desc_t *uvc_get_format_descs(uvc_device_handle_t* );
uvc_get_format_descs = _libuvc.uvc_get_format_descs
uvc_get_format_descs.argtypes = [c_void_p]
uvc_get_format_descs.restype = uvc_format_desc_p

# uvc_error_t uvc_probe_stream_ctrl(uvc_device_handle_t *devh, uvc_stream_ctrl_t *ctrl);
uvc_probe_stream_ctrl = _libuvc.uvc_probe_stream_ctrl
uvc_probe_stream_ctrl.argtypes = [c_void_p, POINTER(uvc_stream_ctrl)]

# uvc_error_t uvc_start_streaming(uvc_device_handle_t *devh,
#                                 uvc_stream_ctrl_t *ctrl,
#                                 uvc_frame_callback_t *cb,
#                                 void *user_ptr,
#                                 uint8_t flags);
uvc_start_streaming = _libuvc.uvc_start_streaming
uvc_start_streaming.argtypes = [
    c_void_p,
    POINTER(uvc_stream_ctrl),
    uvc_frame_callback,
    c_void_p,
    c_uint8
]

# DEPRICATED:
# uvc_error_t uvc_start_iso_streaming(uvc_device_handle_t *devh,
#                                     uvc_stream_ctrl_t *ctrl,
#                                     uvc_frame_callback_t *cb,
#                                     void *user_ptr);

# void uvc_stop_streaming(uvc_device_handle_t *devh);
uvc_stop_streaming = _libuvc.uvc_stop_streaming
uvc_stop_streaming.argtypes = [c_void_p]
uvc_stop_streaming.restype = None

# uvc_error_t uvc_stream_open_ctrl(uvc_device_handle_t *devh,
#                                  uvc_stream_handle_t **strmh,
#                                  uvc_stream_ctrl_t *ctrl);
uvc_stream_open_ctrl = _libuvc.uvc_stream_open_ctrl
uvc_stream_open_ctrl.argtypes = [
    c_void_p,
    POINTER(c_void_p),
    POINTER(uvc_stream_ctrl)
]

# uvc_error_t uvc_stream_ctrl(uvc_stream_handle_t *strmh, uvc_stream_ctrl_t *ctrl);
uvc_stream_ctrl_f = _libuvc.uvc_stream_ctrl
uvc_stream_ctrl_f.argtypes = [c_void_p, POINTER(uvc_stream_ctrl)]

# uvc_error_t uvc_stream_start(uvc_stream_handle_t *strmh,
#                              uvc_frame_callback_t *cb,
#                              void *user_ptr,
#                              uint8_t flags);
uvc_stream_start = _libuvc.uvc_stream_start
uvc_stream_start.argtypes = [
    c_void_p,
    uvc_frame_callback,
    c_void_p,
    c_uint8
]

# DEPRICATED:
# uvc_error_t uvc_stream_start_iso(uvc_stream_handle_t *strmh,
#                                  uvc_frame_callback_t *cb,
#                                  void *user_ptr);

# uvc_error_t uvc_stream_get_frame(uvc_stream_handle_t *strmh,
#                                  uvc_frame_t **frame,
#                                  int32_t timeout_us);
uvc_stream_get_frame = _libuvc.uvc_stream_get_frame
uvc_stream_get_frame.argtypes = [
    c_void_p,
    POINTER(POINTER(uvc_frame)),
    c_int32
]

# uvc_error_t uvc_stream_stop(uvc_stream_handle_t *strmh);
uvc_stream_stop = _libuvc.uvc_stream_stop
uvc_stream_stop.argtypes = [c_void_p]

# void uvc_stream_close(uvc_stream_handle_t *strmh);
uvc_stream_close = _libuvc.uvc_stream_close
uvc_stream_close.argtypes = [c_void_p]
uvc_stream_close.restype = None

# int uvc_get_ctrl_len(uvc_device_handle_t *devh, uint8_t unit, uint8_t ctrl);
uvc_get_ctrl_len = _libuvc.uvc_get_ctrl_len
uvc_get_ctrl_len.argtypes = [c_void_p, c_uint8, c_uint8]

# int uvc_get_ctrl(uvc_device_handle_t *devh,
#                  uint8_t unit,
#                  uint8_t ctrl,
#                  void *data,
#                  int len,
#                  enum uvc_req_code req_code);
uvc_get_ctrl = _libuvc.uvc_get_ctrl
uvc_get_ctrl.argtypes = [
    c_void_p,
    c_uint8,
    c_uint8,
    c_void_p,
    c_int,
    c_int
]

class Control:

    def __init__(
            self,
            device_handle,
            unit_id,
            display_name,
            unit,
            control_id,
            offset,
            data_len,
            bit_mask,
            d_type,
            doc=None,
            buffer_len=None,
            min_val=None,
            max_val=None,
            step=None,
            def_val=None
        ):

        self.devh = device_handle
        self.display_name = display_name
        self.unit_id = unit_id
        self.unit = unit
        self.control_id = control_id
        self.offset = offset
        self.data_len = data_len
        self.bit_mask = bit_mask
        self.d_type = d_type
        self.doc = doc

        try:
            ret_buffer_len = uvc_get_ctrl_len(self.devh, self.unit_id, self.control_id)
            if ret_buffer_len < 1:
                _check_error(ret_buffer_len)
            self.buffer_len = ret_buffer_len
        except Exception as e:
            # print("WARNING: Could not get control length")
            # print("  Exception: {}".format(e))
            if buffer_len is not None:
                # print("  Setting given buffer_len of {}".format(buffer_len))
                self.buffer_len = buffer_len
            else:
                raise

        self.info_bit_mask = self._uvc_get(uvc_req_code["UVC_GET_INFO"].value)
        self._value = self._uvc_get(uvc_req_code["UVC_GET_CUR"].value)
        self.min_val = min_val if min_val != None else self._uvc_get(uvc_req_code["UVC_GET_MIN"].value)
        self.max_val = max_val if max_val != None else self._uvc_get(uvc_req_code["UVC_GET_MAX"].value)
        if self.min_val > self.max_val:
            logger.warning("WARNING! min > max")
            self.min_val = -1*self.max_val
        self.step    = step    if step    != None else self._uvc_get(uvc_req_code["UVC_GET_RES"].value)
        self.def_val = def_val if def_val != None else self._uvc_get(uvc_req_code["UVC_GET_DEF"].value)

        # I think if step = 0 then the control is a continuous function?
        if self.d_type == int and self.step != 0 and len(range(self.min_val,self.max_val+1,self.step)) == 2:
            self.d_type = bool
        #we could filter out unsupported entries but device dont always implement this correctly.
        #if type(self.d_type) == dict:
        #    possible_vals = range(self.min_val,self.max_val+1,self.step)
        #    print possible_vals
        #    filtered_entries = {}
        #    for key,val in self.d_type.iteritems():
        #        if val in possible_vals:
        #            filtered_entries[key] = val
        #    self.d_type = filtered_entries

    def __str__(self):
        return "%s"%self.display_name \
        + '\n\t value: %s'%self._value \
        + '\n\t min: %s'%self.min_val \
        + '\n\t max: %s'%self.max_val \
        + '\n\t step: %s'%self.step \
        + '\n\t default: %s'%self.def_val

    def _uvc_get(self, req_code):
        data = bytes(12)
        ret = uvc_get_ctrl(self.devh, self.unit_id, self.control_id, data, self.buffer_len, req_code)
        if ret < 1:
            _check_error(ret)
        value = int.from_bytes(data[0:ret], sys.byteorder, signed=True)
        return value

    def _uvc_set(self, value):
        data = value.to_bytes(self.buffer_len, sys.byteorder, signed=True)
        ret =  uvc_set_ctrl(self.devh, self.unit_id, self.control_id, data, self.buffer_len)
        if ret <= 0: #== self.buffer_len
            _check_error(ret)

    def refresh(self):
        try:
            self._value = self._uvc_get(uvc_req_code["UVC_GET_CUR"].value)
        except Exception as e:
            logger.error("Could not get {} value. Must be read disabled.".format(self.display_name))
            logger.error(e)

    @property
    def value(self):
        self.refresh()
        return self._value

    @value.setter
    def value(self, value):
        self._uvc_set(value)
        self.refresh()

# int uvc_set_ctrl(uvc_device_handle_t *devh,
#                  uint8_t unit,
#                  uint8_t ctrl,
#                  void *data,
#                  int len);
uvc_set_ctrl = _libuvc.uvc_set_ctrl
uvc_set_ctrl.argtypes = [
    c_void_p,
    c_uint8,
    c_uint8,
    c_void_p,
    c_int
]

# uvc_error_t uvc_get_power_mode(uvc_device_handle_t *devh,
#                                enum uvc_device_power_mode *mode,
#                                enum uvc_req_code req_code);
uvc_get_power_mode = _libuvc.uvc_get_power_mode
uvc_get_power_mode.argtypes = [
    c_void_p,
    POINTER(c_int),
    c_int
]

# uvc_error_t uvc_set_power_mode(uvc_device_handle_t *devh,
#                                enum uvc_device_power_mode mode);
uvc_set_power_mode = _libuvc.uvc_set_power_mode
uvc_set_power_mode.argtypes = [c_void_p, c_int]

# const char* uvc_strerror(uvc_error_t err);
uvc_strerror = _libuvc.uvc_strerror
uvc_strerror.argtypes = [c_int]
uvc_strerror.restype = c_char_p

# void uvc_print_diag(uvc_device_handle_t *devh, FILE *stream);
# Note: this implementation uses c_void_p as the FILE pointer,
# because it is only necessary to pass NULL to print to stderr
uvc_print_diag = _libuvc.uvc_print_diag
uvc_print_diag.argtypes = [c_void_p, c_void_p]
uvc_print_diag.restype = c_void_p


# TODO: Implement control accessors

# Not Implemented:
# Functions that print to stdout/stderr:
# uvc_perror, uvc_print_diag, uvc_print_stream_ctrl
#
# Functions that do color conversion, decompression or allocate frames.
# Use pyuvc if you need this functionality, as it is written in
# cython for speed
