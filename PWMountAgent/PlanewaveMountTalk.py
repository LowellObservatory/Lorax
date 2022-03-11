"""
Created on Feb 7, 2022

@author: dlytle
"""

from extern.pwi4_client import PWI4


class PlanewaveMountTalk(object):
    """
    Communications with PlaneWave Mount.
    """

    def __init__(self, parent, host, port):
        self.pwi4 = PWI4(host=host, port=port)
        self.parent = parent

    def connect_to_mount(self):
        s = self.pwi4.status()
        # print("Mount connected:", s.mount.is_connected)

        if not s.mount.is_connected:
            # print("Connecting to mount...")
            s = self.pwi4.mount_connect()
            # print("Mount connected:", s.mount.is_connected)
        return ()

    def disconnect_from_mount(self):
        s = self.pwi4.mount_disconnect()

    def send_command_to_mount(self, mount_command):
        s = self.pwi4.status()
        s = self.pwi4.mount_connect()
        # Strip off everything up to the first parenthesis
        mcom = mount_command[0 : mount_command.find("(")]

        if mcom == "mount_enable":
            print("Enable the Mount")

        elif mcom == "mount_disable":
            print("Disable the Mount")

        elif mcom == "mount_goto_ra_dec_j2000":
            print("Mount to RA,DEC, J2000")

        else:
            print("Unknown command")

        # if command is x send this other command to pwi4
        # check status, send acknowledgement when done.
        return ()
