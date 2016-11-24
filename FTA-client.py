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

def get(filename):
    getRequest = 'GET ' + filename

    #Send file request message
    send_msg(sock, getRequest)
    log("get " + filename + ". Request sent")

    receivedFile = recv_msg(sock)

    if receivedFile != None:
        log("Recevied File contet: " + str(receivedFile))
    ##
    newFileName = 'received file ' + filename
    try:
        with file(newFileName, "wb") as afile:
        # File is open. Send as bytestream.
            afile.write(receivedFile)
    except IOError as e:
        # File doe snot exist. Send error message.
        eMessage = "ERROR : File does not exist."
        log("Exception: " + str(e) + "...\n")
        log("Sending error message to cleint...\n")
        send_msg(sock, bytearray(eMessage))
    ##

def post(filename):
    postRequest = 'POST ' + filename

    send_msg(sock, postRequest)
    log("POST request sent")
    response = recv_msg(sock)
    if (str(response) == "ACCEPTED"):
        log("Received accepted message. Sending file")
        try:
            log("Attempting to open file " + filename + "...\n")
            with open(filename, "rb") as afile:
            # File is open. Send as bytestream.
                log("File opened - now attempting to read it in.\n")
                toSend = afile.read()
                bytesToSend = bytearray(toSend)
                log("File imported as byteArray...\n")
                log("Sending file to server...\n")
                send_msg(sock, bytesToSend)
                print "File sent!"
        except IOError as e:
            # File does not exist. Send error message.
            eMessage = "ERROR : File does not exist."
            log("Exception: " + str(e) + "...\n")

        # Make sure server got the file
        completeMessage = recv_msg(sock)
        log("Complete Message received")
        if str(completeMessage) == "COMPLETE":
            log("File upload complete")

def window(size):
    global sock

    sock.setWindowSize(size)
    log("Window size set to " + str(size))

def send_msg(asocket, msg):
    # Prefix each message with a 4-byte length (network byte order)
    #msg = struct.pack('>I', len(msg)) + msg
    asocket.send(msg)

def recv_msg(asocket):
    # Read message length and unpack it into an integer
    # this is packet structure
    raw_msglen = recvall(asocket, 4)
    if not raw_msglen:
        return None
    #msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return raw_msglen

def recvall(asocket, n):
    recvCallsMade = 0;
    packet = asocket.recv()

    if not packet:
        return None

    return packet

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

def disconnect():
    global sock
    global state

    if sock is None:
        print "No connection\n"
        return
    if state == 'CONNECTED':
            # Tell server we're about to disconnect.
            send_msg(sock, "DISCONNECTING")
            sock.close()
            state = 'DISCONNECTED'
            print "Terminating...Thank you"
            sys.exit(0)

def runClient():
    userInput = raw_input('\n\nEnter a command:\n')
    splitInput = userInput.split(' ', 1)

    if splitInput[0] == 'connect':
        connect()
    elif splitInput[0] == 'get':
        if len(splitInput) == 2:
            if state == 'DISCONNECTED':
                print ("You are not connected\n")
            elif state == 'CONNECTED':
                get(splitInput[1])
        else:
            print("Invalid command")
    elif splitInput[0] == 'post':
        if len(splitInput) == 2:
            if state == 'DISCONNECTED':
                print ("You are not connected\n")
            elif state == 'CONNECTED':
                post(splitInput[1])
        else:
            print("Invalid command")
    elif splitInput[0] == 'window':
        if len(splitInput) == 2:
            if state == 'DISCONNECTED':
                print ("You are not connected\n")
            elif state == 'CONNECTED':
                window(int(splitInput[1]))
    elif splitInput[0] == 'disconnect':
        print "Client request for disconnect"
        disconnect()

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

while True:
    runClient()