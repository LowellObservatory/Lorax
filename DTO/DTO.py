"""
Created on March 11, 2022

@author: dlytle

"""

import time
import logging
import stomp
import yaml

# Set stomp so it only logs WARNING and higher messages. (default is DEBUG)
logging.getLogger("stomp").setLevel(logging.WARNING)


class DTO:
    hosts = ""
    log_file = ""
    command_input_file = ""

    def __init__(self):

        # Read the config file.
        with open("DTO/configure.yaml", "r") as stream:
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
        self.dto_logger = logging.getLogger("dto_log")

        # Tell em we've started.
        self.dto_logger.info("Initializing: logging started")

        # Get the broker host from the configuration.
        # Make a connection to the broker.
        self.hosts = [tuple(self.config["broker_hosts"])]
        self.dto_logger.info(
            "connecting to broker at " + str(self.config["broker_hosts"])
        )

        try:
            # Get a connection handle.s
            self.conn = stomp.Connection(host_and_ports=self.hosts)

            # Set up a listener and and connect.
            self.conn.set_listener("", self.MyListener(self))
            self.conn.connect(wait=True)
        except:
            self.dto_logger.error("Connection to broker failed")

        self.dto_logger.info("connected to broker")
        self.dto_logger.info(
            "subscribing to topic: " + self.config["mount_incoming_topic"]
        )

        # Subscribe to messages from "mount_incoming_topic"
        # and "camera_incoming_topic".
        self.conn.subscribe(
            id=1,
            destination="/topic/" + self.config["mount_incoming_topic"],
            headers={},
        )

        self.dto_logger.info(
            "subscribed to topic " + self.config["mount_incoming_topic"]
        )

        self.dto_logger.info(
            "subscribing to topic: " + self.config["camera_incoming_topic"]
        )

        self.conn.subscribe(
            id=1,
            destination="/topic/" + self.config["camera_incoming_topic"],
            headers={},
        )

        self.dto_logger.info(
            "subscribed to topic " + self.config["camera_incoming_topic"]
        )

        self.command_input_file = self.config["command_input_file"]

    def send_hello(self):
        self.conn.send(
            body="Hello World",
            destination="/topic/" + self.config["mount_incoming_topic"],
        )
        time.sleep(2)

    class MyListener(stomp.ConnectionListener):
        def __init__(self, parent):
            self.parent = parent
            pass

        def on_error(self, message):
            print('received an error "%s"' % message)

        def on_message(self, message):
            # print('received a message "%s"' % message)
            self.parent.dto_logger.info('received a message "%s"' % message.body)


if __name__ == "__main__":
    dto = DTO()
    dto.send_hello()

    print(dto.command_input_file)
    with open(dto.command_input_file) as fp:
        line = fp.readline()
        cnt = 1
        while line:
            print("Line {}: {}".format(cnt, line.strip()))
            dto.conn.send(
                body=line.strip(),
                destination="/topic/" + dto.config["mount_command_topic"],
            )
            time.sleep(0.1)
            line = fp.readline()
            cnt += 1
