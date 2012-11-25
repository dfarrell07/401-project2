#!/usr/bin/env python
# Implements reliable data transfer over UDP. See project spec for details.
# Usage: `python client.py <shost> <sport> <file_name> <N> <MSS>`
# Author: Daniel Farrell
# Usage: Use freely

import pdb
import time
import select
import socket
import errno
import sys
from struct import *
from collections import namedtuple

DEBUG = False
E_INVALID_PARAMS = 2 # Error code returned for invalid params
E_FILE_READ_FAIL = 69 # Error code returned if the target file can not be read
E_NO_SERVER = 70 # Error code returned if the target server can not be found
SPORT = 7735 # Well-known server port
CPORT = 7736 # Well-known client port
DATA_ID = 0b0101010101010101 # Well-known
ACK_ID = 0b1010101010101010 # Well-known
HEADER_LEN = 8 # Bytes
TIMEOUT = .1 # Seconds

# Find my IP
# Cite: http://is.gd/gLzpdS
stmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
stmp.connect(("gmail.com",80))
me = stmp.getsockname()[0]
stmp.close()

# Open UDP socket for communication with server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((me, CPORT))
sock.setblocking(0)

# Build data structure for representating packets
pkt = namedtuple("pkt", ["seq_num", "chk_sum", "pkt_type", "data", "acked"])
ack = namedtuple("pkt", ["seq_num", "chk_sum", "pkt_type"])

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
  print "CLIENT: shost:", shost, "\nCLIENT: sport:", sport, "\nCLIENT: file_name:",\
    file_name, "\nCLIENT: window_size:", window_size, "\nCLIENT: mss:", mss

# Cite: http://stackoverflow.com/questions/1767910/checksum-udp-calculation-python
def carry_around_add(a, b):
  """Helper function for checksum function"""
  c = a + b
  return (c & 0xffff) + (c >> 16)

# Cite: http://stackoverflow.com/questions/1767910/checksum-udp-calculation-python
def checksum(msg):
  """Compute and return a checksum of the given data"""
  # Force data into 16 bit chunks for checksum
  if (len(msg) % 2) != 0:
    msg += "0"

  s = 0
  for i in range(0, len(msg), 2):
    w = ord(msg[i]) + (ord(msg[i+1]) << 8)
    s = carry_around_add(s, w)
  return ~s & 0xffff

def send_pkt(pkt, sock):
  """
  Take a pkt named tuple, build the pkt and send it to the server
  """
  if DEBUG:
    print "CLIENT: Packing checksum", pkt.chk_sum, "seq_num", pkt.seq_num

  raw_pkt = pack('iHH' + str(len(pkt.data)) + 's', pkt.seq_num, int(pkt.chk_sum), \
    pkt.pkt_type, pkt.data)

  sock.sendto(raw_pkt, (shost, sport))

def parse_ack(pkt_raw):
  """Convert raw ACK pkt into a usable pkt named tuple"""
  new_pkt = ack._make(unpack('iHH', pkt_raw))
  
  return new_pkt

def build_pkts(file_data):
  """Takes raw data to be sent and builds a list of pkt named tuples"""
  seq_num = 0
  pkts = []

  sent = 0
  to_send = min(mss - HEADER_LEN, len(file_data) - sent)
  while to_send > 0:
    # Build a pkt named tuple and add it to the list of packets
    pkts.append(pkt(seq_num = seq_num, chk_sum = checksum(file_data[sent:sent \
      + to_send]), pkt_type = DATA_ID, data = file_data[sent:sent + to_send], \
      acked = False))
    if DEBUG:
      print "CLIENT: Built pkt with seq_num", seq_num
    sent += to_send
    to_send = min(mss - HEADER_LEN, len(file_data) - sent)
    seq_num += 1

  # Newly built list of pkts
  return pkts


def rdt_send(file_data):
  """Send passed data reliably, using an unreliable connection"""
  # Build packet list
  pkts = build_pkts(file_data)

  oldest_unacked = 0
  unacked = 0
  while oldest_unacked < len(pkts):

    # Can we send a packet, do we need to send pkt
    if unacked < window_size and (unacked + oldest_unacked) < len(pkts):
      send_pkt(pkts[oldest_unacked + unacked], sock)

      if DEBUG:
        print "CLIENT: Sent pkt to", str(shost) + ":" +  str(sport)

      unacked += 1
      continue
    else: # Can not send pkt
      # Listen for ACKs
      ready = select.select([sock], [], [], TIMEOUT)
      if ready[0]:
        pkt_recv_raw, addr = sock.recvfrom(4096)
        if DEBUG:
          print "CLIENT: Packet received from", addr
      else: # Window is full and no ACK received before timeout
        if DEBUG:
          print "CLIENT: No pkt received with timeout", TIMEOUT
          print "CLIENT: Go-back-N because of full window and no ACK after timeout"

        print "Timeout, sequence number =", oldest_unacked

        unacked = 0
        continue

      # Confirm that pkt is from the server
      if addr[0] != shost:
        if DEBUG:
          print "CLIENT: Unexpected pkt from", addr
        continue

      # Decode packet
      pkt_recv = parse_ack(pkt_recv_raw)

      # Confirm that pkt is indeed an ACK
      if pkt_recv.pkt_type != ACK_ID:
        if DEBUG:
          print "CLIENT: Unexpected pkt type", pkt_recv.pkt_type, ", dropping pkt"
        continue

      # If this is the pkt you're looking for
      if pkt_recv.seq_num == oldest_unacked:
        oldest_unacked += 1
        unacked -= 1

        if DEBUG:
          print "CLIENT: oldest_unacked updated, now", oldest_unacked
          print "CLIENT: unacked updated, now", unacked
      else:
        if DEBUG:
          print "CLIENT: Out of order pkt. Expected", oldest_unacked, \
            "received", pkt_recv.seq_num
          print "CLIENT: Go-back-N with unacked", unacked, "== window_size", \
            window_size
        unacked = 0
        continue

  # Close server connection and exit successfully
  print "CLIENT: File successfully transfered"
  sock.close()
  sys.exit(0)


# Open file passed from CLI
try:
  fd = open(file_name, 'r')
  file_data = fd.read()
  fd.close()
except:
  print "Failed to open file:", file_name
  sys.exit(E_FILE_READ_FAIL)

# Validate file data
if file_data == "":
  print "No data read from file. Is it empty?"
  sys.exit(E_FILE_READ_FAIL)

# Pass file data to reliable data transfer function
rdt_send(file_data)
