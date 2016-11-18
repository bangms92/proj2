DEBUG = True

def log(message):
    if DEBUG:
        print message

import sys
import struct
import socket
import crpSocket

# FTA-server X
# X: The port number at which the FTA-server's UDP socket should bind
def checkArgs():
    if len(sys.argv) != 2:
        print "Invalid arguments"
        sys.exit(1)
        
# Main  
def runServer():
    global sock
    global state
    
    sock.listen()

# ------------------Program Run-------------------- #

checkArgs()

serverCRPport = int(sys.argv[1])

sock = crpSocket.CRPSocket(serverCRPport)
state = 'DISCONNECTED'

try:
    sock.bind("172.17.0.3", serverCRPport)
except Exception as e:
    print "Error: could not bind to port " + str(serverCRPport) + " on local host.\n"
    log("Exception: " + str(e))
    sys.exit(1)
    
while True:
	runServer()