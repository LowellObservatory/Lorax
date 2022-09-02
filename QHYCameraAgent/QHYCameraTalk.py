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


class IndiClient(PyIndi.BaseClient):
    def __init__(self, parent):
        super(IndiClient, self).__init__()
        self.parent = parent
        status = {}

    def newDevice(self, d):
        # print("Receiving Device... " + d.getDeviceName())
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
        global blobEvent
        print("new BLOB ", bp.name)
        blobEvent.set()
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


class QHYCameraTalk:
    """
    Communications with INDI QHY Camera.
    """

    def __init__(self, parent, host, port):

        self.parent = parent

        self.indiclient = IndiClient(self)
        self.indiclient.setServer(host, port)
        self.camera_status = {}

        self.indiclient.connectServer()

        ccd = "QHY600M"
        device_ccd = self.indiclient.getDevice(ccd)
        while not (device_ccd):
            time.sleep(0.5)
            device_ccd = self.indiclient.getDevice(ccd)

        self.device_ccd = device_ccd

        # temp = device_ccd.getNumber("CCD_TEMPERATURE")
        # print("temp = " + str(temp[0].value))

        # print("setting temp to -10")
        # temp = device_ccd.getNumber("CCD_TEMPERATURE")
        # temp[0].value = np.float(-10)  ### new temperature to reach
        # self.indiclient.sendNewNumber(temp)

        """ ccd_connect = device_ccd.getSwitch("CONNECTION")
        while not (ccd_connect):
            print("not connected")
            time.sleep(0.5)
            ccd_connect = device_ccd.getSwitch("CONNECTION")
        if not (device_ccd.isConnected()):
            print("still not connected")
            ccd_connect[0].s = PyIndi.ISS_ON  # the "CONNECT" switch
            ccd_connect[1].s = PyIndi.ISS_OFF  # the "DISCONNECT" switch
            indiclient.sendNewSwitch(ccd_connect) """
        # --------------------
        print("QHYCameraTalk: finished initialization")

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
            temp[0].value = np.float(temperature)  ### new temperature to reach
            self.indiclient.sendNewNumber(temp)

        elif mcom == "status":
            # print("doing status")
            self.parent.camera_status = self.camera_status

        else:
            print("Unknown command")

        # if command is x send this other command to pwi4
        # check status, send acknowledgement when done.
        return ()
