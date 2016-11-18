import socket
import sys
import struct
import crpSocket

DEBUG = True

def log(message):
    if DEBUG:
        print message

def checkArgs():
    if len(sys.argv) != 3:
        print "Invalid arguments"
        sys.exit(1)

def send_msg(asocket, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    asocket.send(msg)

def recv_msg(asocket):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(asocket, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(asocket, msglen)

def recvall(asocket, n):
    log("Preparing to receive " + str(n) + " bytes...\n")

    # Helper function to recv n bytes or return None if EOF is hit
    data = ''
    recvCallsMade = 0;
    while len(data) < n:
       log("message length is : " + str(n) + " | "+ "data length is : " + str(len(data)))
        packet = asocket.recv(n - len(data))
        if not packet:
            return None
        data += packet
        recvCallsMade += 1
    log("\n Calls to rcv() made: " + str(recvCallsMade) + "...\n")
    print str(len(data)) + " bytes received.\n"
    return data

def connect():
    log("Client: Connect()\n")
    global sock
    global state
        
    if state != 'DISCONNECTED':
        print "Already Connected"
        log("sending message...")
        #send_msg(sock, "test")
    
    else:
        sock.connect(ftaServerIP, ftaServerPort)
        state = 'CONNECTED'
        
checkArgs()

# FTA-client A P
# A: The IP address of FTA-server
# P: The UDP port number of FTA-server

clientCRPPort = 7001
ftaServerIP = sys.argv[1]
ftaServerPort = int(sys.argv[2])

#Create Client socket
sock = crpSocket.CRPSocket(clientCRPPort)
state = 'DISCONNECTED'

try:
    sock.bind('172.17.0.2', clientCRPPort)
except Exception as e:
    print "Error during binding" + str(e)
    sys.exit(1)

connect()