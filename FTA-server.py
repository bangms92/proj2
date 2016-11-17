import sys
import struct
import socket

def checkArgs():
    if len(sys.argv) != 3:
        print "Invalid arguments"
        sys.exit()
    
    try:
        socket.inet_aton(sys.argv[1]])#The IP address of FTA-server
        int(sys.argv[2]) #The UDP port number of FTA-server
        
        
checkArgs()