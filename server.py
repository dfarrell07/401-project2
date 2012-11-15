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

# Listen for connections on sport
s = socket.socket()
host = socket.gethostname()
s.bind((me, sport))
s.listen(5)
print "SERVER: Listening on " + me + ":" + str(sport)
while True:
  # Receive packet
  try:
      con, addr = s.accept()
  except socket.error:
      continue
  except KeyboardInterrupt:
    print "\nSERVER: Shutting down"
    s.close
    sys.exit(0)
  pkt_raw = con.recv(4096)
  pkt = parse_pkt(pkt_raw)

  # Generate artificial packet loss
  if random.random() <= prob_loss:
    continue

  # Compute checksum
  if not valid_checksum():
    continue

  # Check sequence number

  # Send ACK
  seq_num = 0
  send_ack(seq_num)

  # Write data to file 

