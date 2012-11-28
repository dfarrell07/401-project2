#!/usr/bin/env python
# Implements reliable data transfer over UDP. See project spec for details.
# Usage: `python server.py <sport> <file_name> <prob_loss>`
# Author: Daniel Farrell
# Usage: Use freely

import pdb
import socket
import sys
import random
import select
from struct import *
from collections import namedtuple

E_FILE_READ_FAIL = 69
DEBUG = False
E_INVALID_PARAMS = 2
SPORT = 7735 # Well-known server port
CPORT = 7736 # Well-known client port
HEADER_LEN = 8 # Bytes
ACK_ID = 0b1010101010101010
TIMEOUT = 2

# Find my IP
# Cite: http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
stmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
stmp.connect(("gmail.com",80))
me = stmp.getsockname()[0]
stmp.close()


# Build data structure for representing packets
pkt = namedtuple("pkt", ["seq_num", "chk_sum", "pkt_type", "data", "acked"])

# Validate number of passed arguments
# Spec: Must have form <sport> <file_name> <prob_loss> 
if len(sys.argv) != 4:
  print "Usage: ./server <sport> <file_name> <prob_loss>"
  sys.exit(E_INVALID_PARAMS)

# Read data from CLI
sport = int(sys.argv[1])
file_name = str(sys.argv[2])
prob_loss = float(sys.argv[3])

# Only port 7735 is allowed for this project. Turn this on if you want that limit.
#if not DEBUG and sport != SPORT:
#  print "Sorry, the use of port", SPORT, "is required for this project"
#  sport = SPORT

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

def parse_pkt(pkt_raw):
  """Convert raw pkt data into a usable pkt named tuple"""
  pkt_unpacked = unpack('iHH' + str(len(pkt_raw) - HEADER_LEN) + 's', pkt_raw) + (False,)

  return pkt._make(pkt_unpacked)

def send_ack(seq_num, chost):
  """ACK the given seq_num pkt"""
  raw_ack = pack('iHH', seq_num, 0, ACK_ID)

  if DEBUG:
    print "SERVER: Sending ACK with seq_num", seq_num

  sock.sendto(raw_ack, (chost, CPORT))

expected_seq_num = 0

# Open output file 
try:
  fd = open(file_name, 'w')
except:
  print "Failed to open file:", file_name
  sys.exit(E_FILE_READ_FAIL)

# Listen for connections on sport TODO: Try/catch
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((me, sport))
sock.setblocking(0)
if DEBUG:
  print "SERVER: Listening on " + me + ":" + str(sport)
while True:
  # Receive packet
  try:
      if DEBUG:
        print "SERVER: Ready for data, timeout started..."
      ready = select.select([sock], [], [], TIMEOUT)
      if ready[0]:
        pkt_recv_raw, addr = sock.recvfrom(4096)
        if DEBUG:
          print "SERVER: Packet received from", addr
      elif expected_seq_num == 0: # If no pkt has been received
        if DEBUG:
          print "SERVER: No data yet"
        continue
      else: # Assume client done sending, since we have no FIN (per spec)
        if DEBUG:
          print "Client seems to be done sending. Timeout is", TIMEOUT, "seconds."
        sock.close
        fd.close()
        sys.exit(0)
  except socket.error:
      if DEBUG:
        # TODO: Add more error info
        print "SERVER: Error, dropping pkt"
      continue
  except KeyboardInterrupt:
    print "\nSERVER: Shutting down"
    sock.close
    fd.close()
    sys.exit(0)

  # Parse pkt into named tuple
  pkt_recv = parse_pkt(pkt_recv_raw)

  if DEBUG:
    print "SERVER: Received pkt with seq_num", pkt_recv.seq_num, "chk_sum", \
      pkt_recv.chk_sum

  # Compute checksum
  if pkt_recv.chk_sum != checksum(pkt_recv.data):
    if DEBUG:
      print "SERVER: Invalid checksum, pkt dropped"
    continue

  # Check sequence number
  if expected_seq_num != pkt_recv.seq_num:
    if DEBUG:
      print "SERVER: Unexpected sequence number", pkt_recv.seq_num, ", expected", \
        expected_seq_num
    continue

  # Generate artificial packet loss
  r = random.random()
  if r <= prob_loss:
    print "Packet loss, sequence number =", pkt_recv.seq_num
    if DEBUG:
      print "SERVER: Artificial pkt loss at p =", prob_loss, "with r =", r
    continue

  # Send ACK
  send_ack(pkt_recv.seq_num, addr[0])
  expected_seq_num += 1

  # Write data to file 
  try:
    fd.write(pkt_recv.data)
  except:
    print "Failed to open file:", file_name
    sys.exit(E_FILE_READ_FAIL)
