import sys
import struct
import socket

def checkArgs():
    if len(sys.argv) != 2:
        print "Invalid arguments"
        sys.exit()
        
        
def listen():
    gloabl sock
    
    sock.listen()
    
checkArgs()

# FTA-server X
# X: The port number at which the FTA-server's UDP socket should bind

state = "CLOSED"

try:
    sock.bind(' ', int(sys.argv[1]))
except:
    print "Error during binding"
    sys.exit(1)
    