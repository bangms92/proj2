import sys
import struct
import socket
import crpSocket

def checkArgs():
    if len(sys.argv) != 2:
        print "Invalid arguments"
        sys.exit()
        
        
def listen():
    global sock
    
    sock.listen()
    
checkArgs()

# FTA-server X
# X: The port number at which the FTA-server's UDP socket should bind

#Create Client socket
sock = crpSocket.CRPSocket(int(sys.argv[1]))
state = 'DISCONNECTED'

try:
    sock.bind("127.0.0.1", int(sys.argv[1]))
except Exception as e:
    print "Error during binding" + str(e)
    sys.exit(1)
    

listen()