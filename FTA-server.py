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
        usage()
    try:
    	int(sys.argv[1])
    except:
        usage()

def usage():
	print "Invalid arguments"
    print "FTA-server Usage: \n"
    print "FTA-server X\n"
    print "X: port number to which FTA server's UDP socker should bind\n"
    print "Example: FTA-server 5000"
    sys.exit(1)

# def send_msg(socket, msg)
# def recv_msg(socket)
# def recvall(socket, n)
# def window(size)
# def handleGet(filename)
# def handlePut(filename)
        
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