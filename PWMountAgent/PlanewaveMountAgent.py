"""
Created on Feb 3, 2022

@author: dlytle

"""

import time
import logging
import stomp
import yaml
import os

from PlanewaveMountTalk import PlanewaveMountTalk

# Set stomp so it only logs WARNING and higher messages. (default is DEBUG)
logging.getLogger("stomp").setLevel(logging.WARNING)


class PlanewaveMountAgent:
    hosts = ""
    log_file = ""
    mount_host = ""
    mount_port = 0
    current_message = ""

    def __init__(self):

        # Read the config file.
        with open("PWMountAgent/configure.yaml", "r") as stream:
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
        self.mount_logger = logging.getLogger("pw_mount_log")

        # Tell em we've started.
        self.mount_logger.info("Initializing: logging started")

        # Get the broker host from the configuration.
        # Make a connection to the broker.
        self.hosts = [tuple(self.config["broker_hosts"])]
        self.mount_logger.info(
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

        self.mount_logger.info("connected to broker")
        self.mount_logger.info("subscribing to topic: " + self.config["incoming_topic"])

        # Subscribe to messages from "incoming_topic"
        self.conn.subscribe(
            id=1,
            destination="/topic/" + self.config["incoming_topic"],
            headers={},
        )

        self.mount_logger.info("subscribed to topic " + self.config["incoming_topic"])

        # Send a message to "outgoing_topic" that gives "alive" status.
        self.conn.send(
            body="pw_mount_agent alive",
            destination="/topic/" + self.config["broadcast_topic"],
        )

        # Get the host and port for the connection to mount.
        self.mount_host = self.config["mount_host"]
        self.mount_port = self.config["mount_port"]

        """ self.planewave_mount_talk = PlanewaveMountTalk(
            self, host=self.mount_host, port=self.mount_port
        )

        # Connect to the mount.
        self.mount_logger.info("connecting to mount")
        self.planewave_mount_talk.connect_to_mount()

        time.sleep(2)

        # Disconnect from the mount.
        self.mount_logger.info("disconnecting from mount")
        self.planewave_mount_talk.disconnect_from_mount() """

    def send_hello(self):
        self.conn.send(
            body="Hello World", destination="/topic/" + self.config["incoming_topic"]
        )
        time.sleep(2)
        # print(self.config["incoming_topic"])
        # self.conn.disconnect()

    class MyListener(stomp.ConnectionListener):
        def __init__(self, parent):
            self.parent = parent
            pass

        def on_error(self, message):
            print('received an error "%s"' % message)

        def on_message(self, message):
            print('received a message "%s"' % message)
            self.parent.mount_logger.info('received a message "%s"' % message.body)
            self.parent.current_message = message.body
            # self.parent.planewave_mount_talk.send_command_to_mount(message.body)


if __name__ == "__main__":
    pwma = PlanewaveMountAgent()
    # pwma.send_hello()

    while True:
        if pwma.current_message == "end":
            os._exit(0)
"""

Request status from Mount, broadcast to broker

Loop {
    Listen to broker messages from DTO
    Interprete message, command mount
    Log commands to log file
    Broadcast status messages when things
        change and when requested.
    If command is exit
        exit
} """
