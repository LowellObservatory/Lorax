"""
Created on Aug 22, 2022

@author: dlytle
"""

import psutil
import subprocess
import time
import os


class LocusTalk(object):
    """
    Communications with PlaneWave Mount.
    """

    def __init__(self, parent, host, port):
        self.parent = parent
        print("finished initialization")
