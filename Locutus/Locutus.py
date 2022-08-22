"""
Created on Aug 22, 2022

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

from LocutusTalk import LocutusTalk

# Set stomp so it only logs WARNING and higher messages. (default is DEBUG)
logging.getLogger("stomp").setLevel(logging.WARNING)


class Locutus:
    hosts = ""
    log_file = ""
    current_message = ""
    current_destination = ""
    message_received = 0

    def __init__(self):

        # Read the config file.
        with open("Locutus/configure.yaml", "r") as stream:
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
        self.locutus_logger = logging.getLogger("locutus_log")

        # Tell em we've started.
        self.locutus_logger.info("Initializing: logging started")

        # Get the broker host from the configuration.
        # Make a connection to the broker.
        self.hosts = [tuple(self.config["broker_hosts"])]
        self.locutus_logger.info(
            "connecting to broker at " + str(self.config["broker_hosts"])
        )

        try:
            # Get a connection handle.s
            self.conn = stomp.Connection(host_and_ports=self.hosts)

            # Set up a listener and and connect.
            self.conn.set_listener("", self.MyListener(self))
            self.conn.connect(wait=True)
        except:
            self.locutus_logger.error("Connection to broker failed")

        self.locutus_logger.info("connected to broker")

        # Subscribe to broadcast topics from mount, camera, and weather.
        self.do_subscribe("incoming_mount_topic")
        self.do_subscribe("incoming_camera_topic")
        self.do_subscribe("incoming_weather_topic")

        # Send a message to "dictionary_broadcast_topic" that gives "alive" status.
        self.conn.send(
            body="locutus alive",
            destination="/topic/" + self.config["dictionary_broadcast_topic"],
        )

        self.locutus_talk = LocutusTalk(self)

        print("got here")
        # print(self.mount_status)

    def do_subscribe(self, topic):

        self.locutus_logger.info("subscribing to topic: " + topic)
        # Subscribe to messages from topic.
        self.conn.subscribe(
            id=1,
            destination="/topic/" + self.config[topic],
            headers={},
        )
        self.locutus_logger.info("subscribed to topic " + topic)

    def assemble_dictionary_and_broadcast(self, dict_requested):
        this_dict = self.gather_dictionary(dict_requested)
        xml_dictionary = self.dict_to_xml(this_dict)
        self.conn.send(
            body=xml_dictionary,
            destination="/topic/" + locutus.config["dictionary_broadcast_topic"],
        )

    def gather_dictionary(self, dict_requested):
        this_dict = dict_requested + "xyz"
        return this_dict

    def dict_to_xml(self, this_dict):
        xml_dict = this_dict + "xyz"
        return xml_dict

    class MyListener(stomp.ConnectionListener):
        def __init__(self, parent):
            self.parent = parent
            pass

        def on_error(self, message):
            print('received an error "%s"' % message)

        def on_message(self, message):
            # print('received a message "%s"' % message)

            self.parent.locutus_logger.info('received a message "%s"' % message.body)
            self.parent.current_destination = message.destination
            self.parent.current_message = message.body
            self.parent.message_received = 1


if __name__ == "__main__":
    locutus = Locutus()

    # -------------------------

    while True:
        if locutus.message_received:
            print(locutus.current_message)
            # if locutus.current_message == "end":
            #     os._exit(0)
            # else:
            #     put info in Redis
            locutus.message_received = 0

            if locutus.config["incoming_camera_topic"] in locutus.current_destination:
                # Store camera status in Redis.
                pass

            if locutus.config["incoming_mount_topic"] in locutus.current_destination:
                # Store mount status in Redis.
                pass

            if locutus.config["incoming_weather_topic"] in locutus.current_destination:
                # Store weather status in Redis.
                pass

            if (
                locutus.config["dictionary_request_topic"]
                in locutus.current_destination
            ):
                # A dictionary has been requested, get dictionary details,
                # assemble dictionary, translate to XML and broadcast.
                locutus.assemble_dictionary_and_broadcast(locutus.current_message)

            # Wait a bit for another message
            time.sleep(0.5)
