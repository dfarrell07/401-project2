#!/usr/bin/env python

import socket
import errno
import sys
from collections import namedtuple

DEBUG = True
E_INVALID_PARAMS = 2
E_FILE_READ_FAIL = 69
E_NO_SERVER = 70
SPORT = 7735 # Well-known server port
DATA_ID = 0b0101010101010101 # Well-known
HEADER_LEN = 8 # Bytes
me = socket.gethostbyname(socket.gethostname())

# Build data structure for repersentating packets
pkt = namedtuple("pkt", ["seq_num", "chk_sum", "pkt_type", "data", "acked"])

# Validate the number of passed arguments
# Spec: Must have form <shost> <sport> <file_name> <N> <MSS> 
if len(sys.argv) != 6:
  print "Usage: ./client <shost> <sport> <file_name> <N> <MSS>"
  sys.exit(E_INVALID_PARAMS)

# Read data from CLI
shost = str(sys.argv[1])
sport = int(sys.argv[2])
file_name = str(sys.argv[3])
window_size = int(sys.argv[4])
mss = int(sys.argv[5])

if DEBUG:
  print "shost:", shost, "\nsport:", sport, "\nfile_name:", file_name, "\nwindow_size:", window_size, "\nmss:", mss

# Only port 7735 is allowed for this project
if sport != SPORT:
  print "Sorry, the use of port", SPORT, "is required for this project"
  sport = SPORT

def get_chk_sum(data):
  """
  Compute and return the check sum of the given data
  TODO: Stub
  """
  return 0

def send_pkt(data, seq_num, s):
  """
  Take a pkt named tuple, build the pkt and send it to the server
  TODO: Modify to work with named tuple pkts
  """
  try:
    # Send packet to server
    s.send(str('%08X'%(seq_num)) + str('%04X'%(get_chk_sum(data))) \
      + str('%04X'%(DATA_ID)) + data)
  except IOError, e:
    if e.errno == errno.EPIPE:
      print "CLIENT ERROR: There is no server on", str(shost) + ":" \
        + str(sport)
    else:
      print "CLIENT ERROR: There was an IOError", e.errno
    s.close()
    sys.exit(1)

def build_pkts(file_data):
  """Takes raw data to be sent and builds a list of pkt named tuples"""
  seq_num = 0
  pkts = []

  sent = 0
  to_send = min(mss - HEADER_LEN, len(file_data) - sent)
  while to_send > 0:
    # Build a pkt named tuple and add it to the list of packets
    pkts.append(pkt(seq_num = seq_num, chk_sum = get_chk_sum(file_data), \
      pkt_type = DATA_ID, data = file_data[sent:sent + to_send], acked = False))
    sent += to_send
    to_send = min(mss - HEADER_LEN, len(file_data) - sent)
    seq_num += 1

  # Newly built list of pkts
  return pkts


def rdt_send(file_data):
  """Send passed data reliabally, using an unreliable connection"""
  # Build packet list
  pkts = build_pkts(file_data)

  if DEBUG:
    print pkts

  # Open server connection
  s = socket.socket()
  try:
    s.connect((shost, sport))
  except socket.error, e:
    if e.errno == errno.ECONNREFUSED:
      print "CLIENT ERROR: There is no server on", str(shost) + ":" \
        + str(sport)
      s.close()
      sys.exit(E_NO_SERVER)
    else:
      print "CLIENT ERROR: There was an IOError", e.errno

  if DEBUG:
    print "CLIENT: Connected to server", str(shost) + ":" + str(sport)

  # Close server connection and exit sucessfully
  s.close()
  sys.exit(0)


# Open file passed from CLI
try:
  fd = open(file_name, 'r')
  file_data = fd.read()
  fd.close()
except:
  print "Failed to open file:", file_name
  sys.exit(E_FILE_READ_FAIL)

if DEBUG:
  print file_name, "contents:\n", file_data

# Pass file data to reliable data transfer function
rdt_send(file_data)


