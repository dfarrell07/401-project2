#!/usr/bin/env python

import socket
import sys
import random
import select
from struct import *
from collections import namedtuple

E_FILE_READ_FAIL = 69
DEBUG = True
E_INVALID_PARAMS = 2
SPORT = 7735 # Well-known server port
CPORT = 7736 # Well-known client port
HEADER_LEN = 8 # Bytes
ACK_ID = 0b1010101010101010
TIMEOUT = 3

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

# Cite: http://stackoverflow.com/questions/1767910/checksum-udp-calculation-python
def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

# Cite: http://stackoverflow.com/questions/1767910/checksum-udp-calculation-python
def checksum(msg):
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

# Listen for connections on sport TODO: Try/catch?
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((me, sport))
sock.setblocking(0)
print "SERVER: Listening on " + me + ":" + str(sport)
while True:
  # Receive packet
  try:
      # TODO: Remove magic number
      ready = select.select([sock], [], [], TIMEOUT)
      if ready[0]:
        pkt_recv_raw, addr = sock.recvfrom(4096)
        if DEBUG:
          print "SERVER: Packet recieved from", addr
      elif expected_seq_num == 0: # If no pkt has been recieved
        continue
      else: # Assume client done sending, since we have no FIN (per spec)
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
    print "SERVER: Recieved pkt with seq_num", pkt_recv.seq_num, "chk_sum", pkt_recv.chk_sum

  # Generate artificial packet loss
  if random.random() <= prob_loss:
    if DEBUG:
      print "SERVER: Artificial pkt loss at p =", prob_loss
    continue

  # Compute checksum
  if pkt_recv.chk_sum != checksum(pkt_recv.data):
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
  expected_seq_num += 1

  # Write data to file 
  try:
    fd.write(pkt_recv.data)
  except:
    print "Failed to open file:", file_name
    sys.exit(E_FILE_READ_FAIL)

