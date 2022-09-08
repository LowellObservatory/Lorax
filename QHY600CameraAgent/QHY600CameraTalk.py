"""
Created on June 29, 2022

@author: dlytle
"""
# from asyncio.windows_events import NULL
import PyIndi
import psutil
import subprocess
import time
import os
import numpy as np
import sys
import threading
import io
import astropy.io.fits
from astropy.coordinates import SkyCoord, FK5
from astropy.time import Time


class IndiClient(PyIndi.BaseClient):
    def __init__(self, parent):
        super(IndiClient, self).__init__()
        self.parent = parent
        status = {}
        self.blobEvent = threading.Event()

    def newDevice(self, d):
        print("Receiving Device... " + d.getDeviceName())
        self.camera = d
        self.parent.camera = d

    def newProperty(self, p):
        # print(dir(p))
        # print("new property " + p.getName() + " for device " + p.getDeviceName())
        # print("type = " + str(p.getType()))
        # Go store the property in the appropriate status dictionary.
        prop_name = p.getName()
        if "CCD" in prop_name or "FILTER" in prop_name:
            self.store_prop(p)

    def removeProperty(self, p):
        pass

    def newBLOB(self, bp):
        print("new BLOB ", bp.name)
        self.blobEvent.set()
        pass

    def newSwitch(self, svp):
        prop_name = svp.name
        prop_type = 1
        prop_dict = {"prop_type": prop_type}
        prop_dict["length"] = len(svp)
        prop_vals = []
        for val in svp:
            prop_vals.append((val.name, val.s))
        prop_dict["vals"] = prop_vals
        self.parent.camera_status[prop_name] = prop_dict

    def newNumber(self, nvp):
        prop_name = nvp.name
        prop_type = 0
        prop_dict = {"prop_type": prop_type}
        prop_dict["length"] = len(nvp)
        prop_vals = []
        for val in nvp:
            prop_vals.append((val.name, val.value))
        prop_dict["vals"] = prop_vals
        self.parent.camera_status[prop_name] = prop_dict

    def newText(self, tvp):
        return
        prop_name = tvp.name
        prop_type = 2
        # Text type
        temp = tvp.getText()
        prop_dict = {"prop_type": prop_type}
        prop_dict["length"] = len(temp)
        prop_vals = []
        for val in temp:
            prop_vals.append((val.name, val.text))
        prop_dict["vals"] = prop_vals
        self.parent.camera_status[prop_name] = prop_dict

    def newLight(self, lvp):
        pass

    def newMessage(self, d, m):
        pass

    def serverConnected(self):
        pass

    def serverDisconnected(self, code):
        pass

    def store_prop(self, prop):
        prop_name = prop.getName()
        prop_type = prop.getType()

        if not prop_name in self.parent.camera_status:
            if prop_type == 0:
                # Number Type
                temp = prop.getNumber()
                prop_dict = {"prop_type": prop_type}
                prop_dict["length"] = len(temp)
                prop_vals = []
                for val in temp:
                    # print(dir(val))
                    prop_vals.append((val.name, val.value))
                prop_dict["vals"] = prop_vals
                self.parent.camera_status[prop_name] = prop_dict
            elif prop_type == 1:
                # Switch type
                temp = prop.getSwitch()
                prop_dict = {"prop_type": prop_type}
                prop_dict["length"] = len(temp)
                prop_vals = []
                for val in temp:
                    # print(dir(val))
                    prop_vals.append((val.name, val.s))
                    # print(val.name)
                prop_dict["vals"] = prop_vals
                self.parent.camera_status[prop_name] = prop_dict
            elif prop_type == 2:
                # Text type
                temp = prop.getText()
                # print(len(temp))
                # print(dir(temp[0]))
                prop_dict = {"prop_type": prop_type}
                prop_dict["length"] = len(temp)
                prop_vals = []
                for val in temp:
                    # print(dir(val))
                    prop_vals.append((val.name, val.text))
                # print(val.name)
                prop_dict["vals"] = prop_vals
                self.parent.camera_status[prop_name] = prop_dict
                # print(status[prop_name])
            elif prop_type == 3:
                # Light type
                temp = prop.getLight()
                prop_dict = {"prop_type": prop_type}
                prop_dict["length"] = len(temp)
                prop_vals = []
                for val in temp:
                    prop_vals.append((val.name, val.text))
                prop_dict["vals"] = prop_vals
                self.parent.camera_status[prop_name] = prop_dict

        # print(status)
        # print("       ")


class QHY600CameraTalk:
    """
    Communications with INDI QHY600 Camera.
    """

    def __init__(self, parent, host, port):

        self.parent = parent

        self.indiclient = IndiClient(self)
        print(f"Connecting with server at {host}:{port}")
        self.indiclient.setServer(host, port)
        self.camera_status = {}

        while not (retval := self.indiclient.connectServer()):
            print("  Waiting on connection to the INDI server...")
            time.sleep(0.5)

        print(f"I think we connected?  {self.indiclient.isServerConnected()}")


        devlist = self.indiclient.getDevices()
        print(f"This is the list of connected devices: {devlist}")

        self.ccd = "QHY CCD QHY600M-d0a5a44"
        device_ccd = self.indiclient.getDevice(self.ccd)
        while not (device_ccd):
            print("  Waiting on connection to the CMOS Camera...")
            time.sleep(0.5)
            device_ccd = self.indiclient.getDevice(self.ccd)

        self.device_ccd = device_ccd

        # temp = device_ccd.getNumber("CCD_TEMPERATURE")
        # print("temp = " + str(temp[0].value))

        # print("setting temp to -10")
        # temp = device_ccd.getNumber("CCD_TEMPERATURE")
        # temp[0].value = np.float(-10)  ### new temperature to reach
        # self.indiclient.sendNewNumber(temp)

        ccd_connect = device_ccd.getSwitch("CONNECTION")
        while not (ccd_connect):
            print("not connected")
            time.sleep(0.5)
            ccd_connect = device_ccd.getSwitch("CONNECTION")
        if not (device_ccd.isConnected()):
            print("still not connected")
            ccd_connect[0].s = PyIndi.ISS_ON  # the "CONNECT" switch
            ccd_connect[1].s = PyIndi.ISS_OFF  # the "DISCONNECT" switch
            self.indiclient.sendNewSwitch(ccd_connect)
        print(f"Are we connected yet? {device_ccd.isConnected()}")
        if not device_ccd.isConnected():
            sys.exit()
        # --------------------

        print(f"Result of device_ccd.isConnected(): {device_ccd.isConnected()}")
        print("QHY600CameraTalk: finished initialization")

    def send_command_to_camera(self, camera_command):
        # s = self.pwi4.status()
        # s = self.pwi4.camera_connect()
        # Strip off everything up to the first parenthesis
        if "(" in camera_command:
            mcom = camera_command[0 : camera_command.find("(")]
        else:
            mcom = camera_command
        # print(mcom)

        if mcom == "enablecamera":
            print("Enable the camera")

        elif mcom == "disablecamera":
            print("Disable the camera")

        elif mcom == "connectcamera":
            print("Connect the camera")

        elif mcom == "disconnectcamera":
            print("Disconnecting from camera...")

        elif mcom == "settemp":
            # Get the arguments.
            # setTemp(-45.0)
            temperature = float(
                camera_command[camera_command.find("(") + 1 : camera_command.find(")")]
            )
            print("setting temp to " + str(temperature))
            temp = self.device_ccd.getNumber("CCD_TEMPERATURE")
            temp[0].value = float(temperature)  ### new temperature to reach
            self.indiclient.sendNewNumber(temp)

        elif mcom == "status":
            # print("doing status")
            self.parent.camera_status = self.camera_status

        elif mcom == "expose":
            exptime = float(
                camera_command[camera_command.find("(") + 1 : camera_command.find(")")]
            )
            self.move_telescope()
            self.expose(exptime)

        elif mcom == "end":
            print("Ending...")

        else:
            print("Unknown command")

        # if command is x send this other command to pwi4
        # check status, send acknowledgement when done.
        return ()

    def expose(self, exptime):
        """expose _summary_

        _extended_summary_

        Parameters
        ----------
        exptime : `float`
            Desired exposure time
        """
        # Set a timer & say what we're up to
        t_start = time.time()
        print(f"Exposing for {exptime:.2f}s...")

        # Retrieve the CCD_EXPOSURE object from the camera
        ccd_exposure = self.device_ccd.getNumber("CCD_EXPOSURE")
        while not (ccd_exposure):
            time.sleep(0.5)
            ccd_exposure = self.device_ccd.getNumber("CCD_EXPOSURE")
 
         # Ensure the CCD simulator snoops the telescope simulator
        # otherwise you may not have a picture of vega
        ccd_active_devices = self.device_ccd.getText("ACTIVE_DEVICES")
        while not (ccd_active_devices):
            time.sleep(0.5)
            ccd_active_devices = self.device_ccd.getText("ACTIVE_DEVICES")
        ccd_active_devices[0].text = "Telescope Simulator"
        self.indiclient.sendNewText(ccd_active_devices)

        # Ensure the CCD simulator snoops the telescope simulator
        # otherwise you may not have a picture of vega
        ccd_active_devices = self.device_ccd.getText("ACTIVE_DEVICES")
        while not (ccd_active_devices):
            time.sleep(0.5)
            ccd_active_devices = self.device_ccd.getText("ACTIVE_DEVICES")
        ccd_active_devices[0].text = "Telescope Simulator"
        self.indiclient.sendNewText(ccd_active_devices)


        # we should inform the indi server that we want to receive the
        # "CCD1" blob from this device
        print(f"This is the CCD: {self.ccd}")
        self.indiclient.setBLOBMode(PyIndi.B_ALSO, self.ccd, "CCD1")
 
        # Get the BLOB
        print("Getting Blob")
        ccd_ccd1 = self.device_ccd.getBLOB("CCD1")
        while not (ccd_ccd1):
            time.sleep(0.5)
            ccd_ccd1 = self.device_ccd.getBLOB("CCD1")
            sys.stderr.write(".")
        print(
            f"Got blob; Info about ccd_ccd1:  type = {type(ccd_ccd1)}  size = {len(ccd_ccd1)}"
        )
        print(f"Elapsed time: {time.time() - t_start}")

        # Set up the list of desired exposure times
        exposures = [exptime, exptime * 5.0]

        # Set threading bit...
        self.indiclient.blobEvent.clear()
        i = 0
        ccd_exposure[0].value = exposures[i]
        self.indiclient.sendNewNumber(ccd_exposure)

        while i < len(exposures):
            # wait for the ith exposure
            self.indiclient.blobEvent.wait()#timeout=10)
            # we can start immediately the next one
            if i + 1 < len(exposures):
                ccd_exposure[0].value = exposures[i + 1]
                self.indiclient.blobEvent.clear()
                self.indiclient.sendNewNumber(ccd_exposure)
            # and meanwhile process the received one
            for blob in ccd_ccd1:
                print(
                    "name: ", blob.name, " size: ", blob.size, " format: ", blob.format
                )
                # pyindi-client adds a getblobdata() method to IBLOB item
                # for accessing the contents of the blob, which is a bytearray in Python
                fits = blob.getblobdata()
                print("fits data type: ", type(fits))


                blobFile = io.BytesIO(fits)
                hdulist = astropy.io.fits.open(blobFile)
                hdulist.writeto('simimage.fits', overwrite=True)
                # here you may use astropy.io.fits to access the fits data
            # and perform some computations while the ccd is exposing
            # but this is outside the scope of this tutorial
            i += 1



        # print("Sending exposure object...")
        # self.status = self.STATUS_EXPOSING

        # # Initial value, received from the camera
        # print(ccd_exposure[0].value)

        # self.getFrame()

        # # Update the value with what we want, then print to screen
        # ccd_exposure[0].value = exptime
        # print(ccd_exposure[0].value)

        # # Send the new expoure INDI object...
        # self.indiclient.sendNewNumber(ccd_exposure)
        # print("We were able to set the new number, right?")

        # print(f"Elapsed time: {time.time() - t_start}")

        # print("startExposure Complete")

        # print("got exposure object ")

        # # Now, wait for the event to complete...
        # self.indiclient.blobEvent.wait(timeout=10)
        # print("This prints after the blobEvent.wait() statement...")

        # print(f"Elapsed time: {time.time() - t_start}")

        # print(f"Return value of ccd_ccd1.getState(): {ccd_ccd1.getState()}")

        # for blob in ccd_ccd1:
        #     print("name: ", blob.name, " size: ", blob.size, " format: ", blob.format)
        #     # pyindi-client adds a getblobdata() method to IBLOB item
        #     # for accessing the contents of the blob, which is a bytearray in Python
        #     fits = blob.getblobdata()
        # print("fits data type: ", type(fits))
        # print("fits data size: ", len(fits))
        # # here you may use astropy.io.fits to access the fits data

        # print(f"Elapsed time: {time.time() - t_start}")

        # blobFile = io.BytesIO(fits)
        # hdulist = astropy.io.fits.open(blobFile)

        # hdulist.writeto("Pinhole_test.fits", overwrite=True)
        # # and perform some computations while the ccd is exposing
        # # but this is outside the scope of this tutorial

    def getFrame(self):
        """Populates this object with the current frame dimensions
        in the camera.
        """
        print("Getting CCD_INFO Object..")
        ccd_info = self.device_ccd.getNumber("CCD_INFO")
        while not (ccd_info):
            time.sleep(0.5)
            ccd_info = self.device_ccd.getNumber("CCD_INFO")
            sys.stderr.write(".")
            sys.stderr.flush()
        print("got ccd_info object: ")
        for n in ccd_info:
            print(n.name, " = ", n.value)
        self.frameSizeX = ccd_info[0].value
        self.frameSizeY = ccd_info[1].value
        print("getFrame Complete")


    def move_telescope(self):
        # connect the scope
        telescope = "Telescope Simulator"
        device_telescope = None
        telescope_connect = None

        # get the telescope device
        device_telescope = self.indiclient.getDevice(telescope)
        while not (device_telescope):
            time.sleep(0.5)
            device_telescope = self.indiclient.getDevice(telescope)

        # wait CONNECTION property be defined for telescope
        telescope_connect = device_telescope.getSwitch("CONNECTION")
        while not (telescope_connect):
            time.sleep(0.5)
            telescope_connect = device_telescope.getSwitch("CONNECTION")

        # if the telescope device is not connected, we do connect it
        if not (device_telescope.isConnected()):
            # Property vectors are mapped to iterable Python objects
            # Hence we can access each element of the vector using Python indexing
            # each element of the "CONNECTION" vector is a ISwitch
            telescope_connect[0].s = PyIndi.ISS_ON  # the "CONNECT" switch
            telescope_connect[1].s = PyIndi.ISS_OFF  # the "DISCONNECT" switch
            self.indiclient.sendNewSwitch(telescope_connect)  # send this new value to the device

        # Now let's make a goto to vega
        # Beware that ra/dec are in decimal hours/degrees
        vega = SkyCoord.from_name("Vega").transform_to(FK5(equinox=Time.now()))

        # We want to set the ON_COORD_SET switch to engage tracking after goto
        # device.getSwitch is a helper to retrieve a property vector
        telescope_on_coord_set = device_telescope.getSwitch("ON_COORD_SET")
        while not (telescope_on_coord_set):
            time.sleep(0.5)
            telescope_on_coord_set = device_telescope.getSwitch("ON_COORD_SET")
        # the order below is defined in the property vector, look at the standard Properties page
        # or enumerate them in the Python shell when you're developing your program
        telescope_on_coord_set[0].s = PyIndi.ISS_ON  # TRACK
        telescope_on_coord_set[1].s = PyIndi.ISS_OFF  # SLEW
        telescope_on_coord_set[2].s = PyIndi.ISS_OFF  # SYNC
        self.indiclient.sendNewSwitch(telescope_on_coord_set)
        # We set the desired coordinates
        telescope_radec = device_telescope.getNumber("EQUATORIAL_EOD_COORD")
        while not (telescope_radec):
            time.sleep(0.5)
            telescope_radec = device_telescope.getNumber("EQUATORIAL_EOD_COORD")
        telescope_radec[0].value = vega.ra.hour
        telescope_radec[1].value = vega.dec.degree
        self.indiclient.sendNewNumber(telescope_radec)
        # and wait for the scope has finished moving
        while telescope_radec.getState() == PyIndi.IPS_BUSY:
            print("Scope Moving ", telescope_radec[0].value, telescope_radec[1].value)
            time.sleep(2)

