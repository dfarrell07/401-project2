#!/usr/bin/env python

import socket
from collections import namedtuple

DEBUG = True
SPORT = 7735 # Well-known server port

pkt = namedtuple("pkt", [""])

# Read data from CLI
prob_loss = .5


def rdt_send(file_data):
  return True

# Open file passed from CLI
file_data = ""

# Pass file data to reliable data transfer function
rdt_send(file_data)


