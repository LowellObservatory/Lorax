"""
Created on June 29, 2022

@author: dlytle

"""

import time
import logging
from typing_extensions import Self
import stomp
import yaml
import os
import xmltodict
import uuid
import datetime

from IndiSimCameraTalk import IndiSimCameraTalk

# Set stomp so it only logs WARNING and higher messages. (default is DEBUG)
logging.getLogger("stomp").setLevel(logging.WARNING)


class IndiSimCameraAgent:
    hosts = ""
    log_file = ""
    camera_host = ""
    camera_port = 0
    current_message = ""
    message_received = 0
    camera_status = ""
    wait_list = ["expose", "changefilter"]

    def __init__(self):

        # Read the config file.
        with open("INDISimCameraAgent/configure.yaml", "r") as stream:
            try:
                self.config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        # Get the log file name from the configuration.
        # Set up the logger.
        self.log_file = self.config["log_file"]
        logging.basicConfig(
            filename=self.log_file,
            format="%(asctime)s %(levelname)-8s %(message)s",
            level=logging.DEBUG,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.camera_logger = logging.getLogger("indisim_camera_log")

        # Tell em we've started.
        self.camera_logger.info("Initializing: logging started")

        # Get the broker host from the configuration.
        # Make a connection to the broker.
        self.hosts = [tuple(self.config["broker_hosts"])]
        self.camera_logger.info(
            "connecting to broker at " + str(self.config["broker_hosts"])
        )

        try:
            # Get a connection handle.s
            self.conn = stomp.Connection(host_and_ports=self.hosts)

            # Set up a listener and and connect.
            self.conn.set_listener("", self.MyListener(self))
            self.conn.connect(wait=True)
        except:
            self.mount_logger.error("Connection to broker failed")

        self.camera_logger.info("connected to broker")
        self.camera_logger.info(
            "subscribing to topic: " + self.config["incoming_topic"]
        )

        # Subscribe to messages from "incoming_topic"
        self.conn.subscribe(
            id=1,
            destination="/topic/" + self.config["incoming_topic"],
            headers={},
        )

        self.camera_logger.info("subscribed to topic " + self.config["incoming_topic"])

        # Send a message to "outgoing_topic" that gives "alive" status.
        self.conn.send(
            body="indisim_camera_agent alive",
            destination="/topic/" + self.config["broadcast_topic"],
        )

        # Get the host and port for the connection to mount.
        self.camera_host = self.config["camera_host"]
        self.camera_port = self.config["camera_port"]

        self.indisim_camera_talk = IndiSimCameraTalk(
            self, host=self.camera_host, port=self.camera_port
        )
        print("got here")
        # print(self.camera_status)

        """  # Connect to the mount.
        self.mount_logger.info("connecting to mount")
        self.planewave_mount_talk.connect_to_mount()

        time.sleep(2)

        # Disconnect from the mount.
        self.mount_logger.info("disconnecting from mount")
        self.planewave_mount_talk.disconnect_from_mount() """

    def get_status_and_broadcast(self):
        self.indisim_camera_talk.send_command_to_camera("status")
        time.sleep(0.2)
        for key, value in self.camera_status.items():
            print(key, " : ", value)
        """ mydict = {
            "camera_status": {
                "message_id": uuid.uuid4(),
                "timestamput": self.mount_status.response.timestamp_utc,
                "telescope": "TiMo",
                "device": {"type": "mount", "vendor": "planewave"},
                "is_slewing": self.mount_status.mount.is_slewing,
                "is_tracking": self.mount_status.mount.is_tracking,
                "azimuth": self.mount_status.mount.azimuth_degs,
                "altitude": self.mount_status.mount.altitude_degs,
                "RA-J2000": self.mount_status.mount.ra_j2000_hours,
                "dec-j2000": self.mount_status.mount.dec_j2000_degs,
                "rotator-angle": self.mount_status.rotator.field_angle_degs,
            }
        }
        xml_format = xmltodict.unparse(mydict, pretty=True)
        self.conn.send(
            body=xml_format,
            destination="/topic/" + pwma.config["broadcast_topic"],
        ) """

    class MyListener(stomp.ConnectionListener):
        def __init__(self, parent):
            self.parent = parent
            pass

        def on_error(self, message):
            print('received an error "%s"' % message)

        def on_message(self, message):
            # print('received a message "%s"' % message)

            self.parent.camera_logger.info('received a message "%s"' % message.body)
            self.parent.current_message = message.body
            self.parent.message_received = 1


if __name__ == "__main__":
    isca = IndiSimCameraAgent()

    """ while True:
        if isca.message_received:
            print(isca.current_message)
            if isca.current_message == "end":
                os._exit(0)
            else:
                isca.indisim_camera_talk.send_command_to_mount(isca.current_message)

            isca.message_received = 0
            isca.conn.send(
                body="Wait",
                destination="/topic/" + isca.config["broadcast_topic"],
            )

            if "camera" in isca.current_message:
                isca.conn.send(
                    body="Wait",
                    destination="/topic/" + isca.config["dto_topic"],
                )
                time.sleep(2.0)
                isca.conn.send(
                    body="Go",
                    destination="/topic/" + pwma.config["dto_topic"],
                )

            # If command in wait_list, send "Wait" to DTO, check status
            # until is_slewing is false, then send "Go" to DTO.
            if any(s in isca.current_message for s in pwma.wait_list):
                # print("we are in a wait loop")
                # Send mount status back to DTO.
                isca.conn.send(
                    body="Wait",
                    destination="/topic/" + isca.config["dto_topic"],
                )
                # time.sleep(0.5)
                while True:
                    isca.get_status_and_broadcast()
                    # print("is_slewing: ", pwma.mount_status.mount.is_slewing)
                    if not isca.mount_status.mount.is_slewing:
                        break

                isca.conn.send(
                    body="Go",
                    destination="/topic/" + isca.config["dto_topic"],
                )
                # time.sleep(0.5)
            # time.sleep(0.1)
        else:
        time.sleep(0.5)
        isca.get_status_and_broadcast()
        time.sleep(0.5)
        pass """


# Request status from Mount, broadcast to broker
