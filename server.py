#!/usr/bin/env python

import socket
import sys
import random
from collections import namedtuple

DEBUG = True
E_INVALID_PARAMS = 2
SPORT = 7735 # Well-known server port

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

def valid_checksum():
  """Check the validity of a data/checksum pair"""
  return True

def parse_pkt(pkt_raw):
  """Convert raw pkt data into a usable pkt named tuple"""
  return "stub"

def send_ack(seq_num):
  """ACK the given seq_num pkt"""
  return True

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
    continue

  # Compute checksum
  if not valid_checksum():
    continue

  # Check sequence number

  # Send ACK
  #send_ack(pkt_recv.seq_num)

  # Write data to file 


