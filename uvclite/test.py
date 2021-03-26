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
import uvclite

import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    with uvclite.UVCContext() as context:
        devlist = context.get_device_list()
        #dev = context.find_device()
        logger.debug(len(devlist))

        for dev in devlist:
            devdesc = dev.get_device_descriptor()
            logger.info("Vendor ID: %d" % devdesc.idVendor)
            logger.info("Product ID: %d" % devdesc.idProduct)
            logger.info("UVC Standard: %d" % devdesc.bcdUVC)
            logger.info("Serial Number: %s" % devdesc.serialNumber)
            logger.info("Manufacturer: %s" % devdesc.manufacturer)
            logger.info("Product Name %s" % devdesc.product)
            dev.free_device_descriptor()
            logger.debug("Freed descriptor")

        devlist = context.get_device_list()
        #dev = context.find_device()
        logger.debug(len(devlist))

        for dev in devlist:
            dev.open()
            dev.print_diagnostics()
            dev.close()

        