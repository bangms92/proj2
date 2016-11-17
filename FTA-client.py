import socket
import sys
import struct

def checkArgs():
    if len(sys.argv) != 2:
        print "Invalid arguments"
        sys.exit()
    
    try:
        int(sys.argv[1]) #The port number at which the FTA-server's UDP socket should bind
        
        
checkArgs()

localUDPPort = sys.argv[1]