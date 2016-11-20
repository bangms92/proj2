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
	print "Invalid arguments\n"
	print "FTA-server Usage: \n"
	print "FTA-server X \n"
	print "X: port number to which FTA server's UDP socker should bind \n"
	print "Example: FTA-server 5000"
	sys.exit(1)

# def send_msg(socket, msg)
# def recv_msg(socket)

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
        packet = asocket.recv()
        if not packet:
            return None
        data += packet
        recvCallsMade += 1
    log("\n Calls to rcv() made: " + str(recvCallsMade) + "...\n")
    print str(len(data)) + " bytes received.\n"
    return data

# def recvall(socket, n)
# def window(size)
# def handleGet(filename)
# def handlePut(filename)
        
# Main  
def runServer():
    global sock
    global state
    

    if not (state == "LISTENING" or state == "CONNECTED"):
    	try:
    		log("Attempting to listen\n")
    		try:
    			sock.listen()
    		except Exception as e:
    			log("Exception: " + str(e))
    			sys.exit(0)
    		log("Setting state to CONNECTED.\n")
    		state = "CONNECTED"
    	except Exception as e:
    		log("Connection Failed: " + str(e))
    		return
    	
	log("Waiting for message from client") 
	message = recv_msg(sock)
	log("Message: " + str(message))
	if message is None:
		log("Client terminated")
		state = "DISCONNECTED"
	else:
		log("Message received\n")

    	# log(message)


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