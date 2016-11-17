DEBUG = True

def log(message):
    if DEBUG:
        print message

import socket
import sys
import struct
import crpsocket

def validateSysArgs():
	if len(sys.argv) != 2:
		usage()
	try:
		int(sys.argv[1])
	except:
		usage()

def usage():
	print "FTA-server Usage:"
	print "FTA-server.py X"
	print "X: port number at which the FTA-server's UDP socket should bind"
	print "Example: FTA-server.py 5000"
	sys.exit(1)

def validCommand(command):
    theFirstWord = command.split(' ', 1)[0]
    if theFirstWord == 'window':
        return True
    elif theFirstWord == 'terminate':
        print "Terminating"
        sys.exit(0)
    else:
        return False


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
        # Only show progress if we're downloading a file bigger than 200 bytes.
        if n > 200:
            # Show download progress.
            sys.stdout.write('\r')
            sys.stdout.write('>>>> Downloading file... ' + str(float(int(100 * (len(data) / float(n))))) + "% <<<<")
            sys.stdout.flush()
        packet = asocket.recv(n - len(data))
        if not packet:
            return None
        data += packet
        recvCallsMade += 1
    sys.stdout.write('\r')
    sys.stdout.write('>>>> Downloading file... 100% <<<<')
    log("\n Calls to rcv() made: " + str(recvCallsMade) + "...\n")
    print str(len(data)) + " bytes successuflly received.\n"
    return data

#def window(size):

def handleGet(filename):
    try:
        log("Attempting to open file " + filename + "...\n")
        with open(filename, "rb") as afile:
        # File is open. Send as bytestream.
            log("File opened - now attempting to read it in.\n")
            toSend = afile.read()
            bytesToSend = bytearray(toSend)
            log("File imported as byteArray...\n")
            log("Sending file to client...\n")
            send_msg(sock, bytesToSend)
            if DEBUG:
                print "Sent file!"
    except IOError as e:
        # File doe snot exist. Send error message.
        eMessage = "ERROR : File does not exist."
        log("Exception: " + str(e) + "...\n")
        log("Sending error message to cleint...\n")
        send_msg(sock, eMessage)

def handlePut(filename):
    # Send ready message.
    log("Sending READY message to client...\n")
    rMessage = "READY"
    send_msg(sock, "READY")

    log("Ready message sent...\n")
    theFile = recv_msg(sock)

    log("Received file!\n")
    log("Sending OKAY message...\n")
    send_msg(sock, "OKAY")

    log("Writing file...\n")
    f = open(filename, 'wb')
    f.write(theFile)
    f.close()
    print "File written!\n"

# Main
def runServer():
    log("-------TOP OF RUN LOOP------------------")

    # Globals
    global sock
    global state

    # Listen and accept incoming connections, if we're not already connected.
    # Blocks until we're connected.

    #if not sock.connected():

    # If socket isn't listening, listen!
    log("State is currently " + state + "...\n")
    if not (state == "Listening" or state == "Connected"):
        try:
            log("Attempting to listen...\n")
            try:
                sock.listen()
            except Exception as e:
                log("Exception: " + str(e))
                sys.exit(0)
            log("Setting state to connected.\n")
            state = "Connected"
        except Exception as e:
            log("Connection Failed: " + str(e))
            return

    # Once we're connected, wait for a GET or PUT request.
    log("Waiting for message from client...\n")
    message = recv_msg(sock)

    # We've got something from the recv call.

    # Client closed connection.
    if message is None:
        log("Client terminated connection.")
        state = 'NotConnected'
    else:
        log("Message received!...\n")
        command = message.split(' ', 1)[0]
        filename = message.split(' ', 1)[1]
        log("Message command: " + command + "...\n")
        log("Message filename: " +  filename + "...\n")

        # If get, send to handler.
        if command == 'GET':
            log("Calling GET handler for file " + filename + "...\n")
            handleGet(filename)

            # IF put, send to handler.
        elif command == 'PUT':
            log("Calling PUT handler for file " + filename + "...\n")
            handlePut(filename)

            # Invalid command! Send error.
        else:
            log("Invalid command received...\n")
            print "Command that was not GET or PUT received. Exiting."
            sys.exit(1)

# ------------PROGRAM RUN LOOP-------------------- #
print("\n")

log("Validating arguments...\n")
validateSysArgs()

serverCRPPort = int(sys.argv[1])

log("Creating empty socket...\n")
sock = crpsocket.CRPSocket(serverCRPPort)
state = 'NotConnected'

try:
	log("Binding server CRPport: " + str(serverCRPPort))
	sock.bind(serverCRPPort)
	log("FTA src port bound...\n")
except Exception as e:
	print "ERROR: Could not bind to port " + str(serverCRPPort) + " on local host.\n"
	log("Exception: " + str(e))
	sys.exit(1)

log("Running server...\n")
while True:
    runServer()

# ------------END PROGRAM RUN LOOP-------------------- #





















