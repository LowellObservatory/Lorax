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
from datetime import datetime, timezone

from QHY600CameraTalk import QHY600CameraTalk

# Set stomp so it only logs WARNING and higher messages. (default is DEBUG)
logging.getLogger("stomp").setLevel(logging.WARNING)


class QHY600CameraAgent:
    hosts = ""
    log_file = ""
    camera_host = ""
    camera_port = 0
    current_message = ""
    message_received = 0
    camera_status = {}
    wait_list = ["expose", "changefilter"]

    def __init__(self):

        self.camera_status = {}
        # Read the config file.
        with open("QHY600CameraAgent/configure.yaml", "r") as stream:
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
        self.camera_logger = logging.getLogger("qhy_camera_log")

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
            body="qhy600_camera_agent alive",
            destination="/topic/" + self.config["broadcast_topic"],
        )

        # Get the host and port for the connection to the camera.
        self.camera_host = self.config["camera_host"]
        self.camera_port = self.config["camera_port"]

        self.qhy600_camera_talk = QHY600CameraTalk(
            self, host=self.camera_host, port=self.camera_port
        )
        # self.qhy600_camera_talk.send_command_to_camera("status")
        # print("Getting camera status:")
        # time.sleep(2)
        # print(self.camera_status)

        """  # Connect to the mount.
        self.mount_logger.info("connecting to mount")
        self.planewave_mount_talk.connect_to_mount()

        time.sleep(2)

        # Disconnect from the mount.
        self.mount_logger.info("disconnecting from mount")
        self.planewave_mount_talk.disconnect_from_mount() """

    def get_status_and_broadcast(self):
        # print(self.camera_status)
        self.qhy600_camera_talk.send_command_to_camera("status")
        time.sleep(0.2)
        # print(self.camera_status)

        c_status = {
            "message_id": uuid.uuid4(),
            "timestamput": datetime.now(timezone.utc),
            "root": self.camera_status,
        }
        status = {"root": c_status}
        xml_format = xmltodict.unparse(status, pretty=True)

        self.conn.send(
            body=xml_format,
            destination="/topic/" + qca.config["broadcast_topic"],
        )

        # Just send the camera temperature to DTO
        self.conn.send(
            body=xmltodict.unparse(
                {
                    "root": {
                        "temp": self.camera_status["CCD_TEMPERATURE"],
                        "ccd_cooler": self.camera_status["CCD_COOLER"],
                        "ccd_cooler_mode": self.camera_status["CCD_COOLER_MODE"],
                        "ccd_cooler_power": self.camera_status["CCD_COOLER_POWER"],
                    }
                },
                pretty=True,
            ),
            destination="/topic/" + qca.config["dto_topic"],
        )

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
    qca = QHY600CameraAgent()

    while True:
        if qca.message_received:
            print(f"Message received:  {qca.current_message}")
            # if isca.current_message == "end":
            #     os._exit(0)
            # else:
            #     isca.indisim_camera_talk.send_command_to_camera(isca.current_message)
            qca.qhy600_camera_talk.send_command_to_camera(qca.current_message)
            qca.message_received = 0
            """ isca.conn.send(
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
                ) """
            # time.sleep(0.5)
            # time.sleep(0.1)
        else:
            time.sleep(0.5)
            qca.get_status_and_broadcast()
            # time.sleep(0.5)
