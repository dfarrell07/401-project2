#!/usr/bin/env python

import socket
import sys
import random
from struct import *
from collections import namedtuple

DEBUG = True
E_INVALID_PARAMS = 2
SPORT = 7735 # Well-known server port
CPORT = 7736 # Well-known client port
HEADER_LEN = 8 # Bytes
ACK_ID = 0b1010101010101010

me = socket.gethostbyname(socket.gethostname())

# Build data structure for repersentating packets
pkt = namedtuple("pkt", ["seq_num", "chk_sum", "pkt_type", "data", "acked"])

# Validate number of passed argumnets
# Spec: Must have form <sport> <file_name> <prob_loss> 
if len(sys.argv) != 4:
  print "Usage: ./server <sport> <file_name> <prob_loss>"
  sys.exit(E_INVALID_PARAMS)

# Read data from CLI
sport = int(sys.argv[1])
file_name = str(sys.argv[2])
prob_loss = float(sys.argv[3])

# Only port 7735 is allowed for this project
if sport != SPORT:
  print "Sorry, the use of port", SPORT, "is required for this project"
  sport = SPORT

def valid_checksum(chk_sum, data):
  """Check the validity of a data/checksum pair"""
  return True

def parse_pkt(pkt_raw):
  """Convert raw pkt data into a usable pkt named tuple"""
  pkt_unpacked = unpack('iHH' + str(len(pkt_raw) - HEADER_LEN) + 's', pkt_raw) + (False,)

  if DEBUG:
    print "SERVER: Unpacked pkt", pkt_unpacked

  new_pkt = pkt._make(pkt_unpacked)
  
  if DEBUG:
    print "SERVER: New pkt tuple", new_pkt

  return new_pkt

def send_ack(seq_num, chost):
  """ACK the given seq_num pkt"""
  raw_ack = pack('iHH', seq_num, 0, ACK_ID)

  #if DEBUG:
  #  print "SERVER: Sending:", raw_ack

  sock.sendto(raw_ack, (chost, CPORT))

expected_seq_num = 0

# Listen for connections on sport TODO: Try/catch?
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((me, sport))
print "SERVER: Listening on " + me + ":" + str(sport)
while True:
  # Receive packet
  try:
      # TODO: Remove magic number
      pkt_recv_raw, addr = sock.recvfrom(4096)
      if DEBUG:
        print "SERVER FROM CLIENT:", addr
        print "SERVER FROM CLIENT:", pkt_recv_raw
  except socket.error:
      if DEBUG:
        # TODO: Add more error info
        print "SERVER: Error, dropping pkt"
      continue
  except KeyboardInterrupt:
    print "\nSERVER: Shutting down"
    sock.close
    sys.exit(0)

  # Parse pkt into named tuple
  pkt_recv = parse_pkt(pkt_recv_raw)

  # Generate artificial packet loss
  if random.random() <= prob_loss:
    if DEBUG:
      print "SERVER: Artificial pkt loss at p =", prob_loss
    continue

  # Compute checksum
  if not valid_checksum(pkt_recv.chk_sum, pkt_recv.data):
    if DEBUG:
      print "SERVER: Invalid checksum, pkt dropped"
    continue

  # Check sequence number
  if expected_seq_num != pkt_recv.seq_num:
    if DEBUG:
      print "SERVER: Unexpected sequence number", pkt_recv.seq_num, ", expected", expected_seq_num
    continue

  # Send ACK
  send_ack(pkt_recv.seq_num, addr[0])

  # TODO Write data to file 


