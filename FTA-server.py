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
        sys.exit()
        
# Main  
def runServer():
    global sock
    global state
    
    if not (state == "LISTENING" or state == "CONNECTED"):
    	try:
    		try:
    			sock.listen()
    		except Exception as e:
    			log("Exceptino: " + str(e))
				sys.exit(0)
			log("Setting state to connected.\n")
			state = "CONNECTED"
		except Exception as e:
			log("Connection Failed: " + str(e))
			return



# ---------------------------------------------------------
checkArgs()

serverCRPport = int(sys.argv[1])

sock = crpSocket.CRPSocket(int(sys.argv[1]))
state = 'DISCONNECTED'

try:
    sock.bind("127.0.0.1", serverCRPport)
except Exception as e:
    print "Error: could not bind to port " + str(serverCRPport) + " on local host.\n"
    log("Exception: " + str(e))
    sys.exit(1)
    
while True:
	runServer()