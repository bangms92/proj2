import socket
import sys
import struct
import crpSocket

def checkArgs():
    if len(sys.argv) != 3:
        print "Invalid arguments"
        sys.exit(1)

def connect():
    global sock
    global state
        
    if state != 'DISCONNECTED':
        print "Already Connected"
    
    else:
        sock.connect(ftaServerIP, ftaServerPort)
        state = 'CONNECTED'
        
checkArgs()

# FTA-client A P
# A: The IP address of FTA-server
# P: The UDP port number of FTA-server

clientCRPPort = 7001
ftaServerIP = socket.inet_aton(sys.argv[1]])
ftaServerPort = int(sys.argv[2])

#Create Client socket
sock = crpSocket.CRPSocket(clientCRPPort)
state = 'DISCONNECTED'

try:
    sock.bind((' ', clientCRPPort))
except:
    print "Error during binding"
    sys.exit(1)