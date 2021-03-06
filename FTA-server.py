DEBUG = True

def log(message):
	if DEBUG:
		print message

import sys
import struct
import socket
import crpSocket
import os

# FTA-server X
# X: The port number at which the FTA-server's UDP socket should bind

def checkArgs():
	if len(sys.argv) == 2 or len(sys.argv) == 3 :
		print "Valid arguments"
	else:
		print "Invalid arguments"
		sys.exit(1)

def usage():
	print "Invalid arguments\n"
	print "FTA-server Usage: \n"
	print "FTA-server X \n"
	print "X: port number to which FTA server's UDP socker should bind \n"
	print "Example: FTA-server 5000"
	sys.exit(1)

def send_msg(asocket, msg):
	asocket.send(msg)

def recv_msg(asocket):
	# Read message length and unpack it into an integer
	raw_msglen = recvall(asocket, 4)
	if not raw_msglen:
		return None
	return raw_msglen

def recvall(asocket, n):
	recvCallsMade = 0;
	packet = asocket.recv()

	if not packet:
		return None

	return packet

# Main  
def runServer():
	global sock
	global state

	log("Top of the server, state: " + state)
	if (state != "CONNECTED"):
		try:
			log("Listening...")
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
		command = str(message).split(' ', 1)[0]
		filename = str(message).split(' ', 1)[1]
		log("Command: " + command)
		log("Command: " + filename)
		if command == 'GET':
			log("GET requets received")
			handleGet(filename)
		if command == 'POST':
			log("POST request received")
			handlePost(filename)
		if command == 'terminate':
			log("Exiting, Thank you!")
			sys.exit(0)

def handlePost(filename):
	log("Sending ACCEPTED message to the client")
	send_msg(sock, "ACCEPTED")
	log("Accepted message sent")

	recievedFilePacket = recv_msg(sock)
	log("Received uploading file")
	send_msg(sock, "COMPLETE")
	log("Complete message sent")
	newFileName = 'uploaded file ' + filename
	try:	
		with file(newFileName, "wb") as afile:
		# File is open. Send as bytestream.
			afile.write(recievedFilePacket)
	except IOError as e:
		# File doe snot exist.
		log("ERROR : File failed to be created.")


def handleGet(filename):
	log("Dir list: " + str(os.listdir(os.path.dirname(os.path.abspath(__file__)))))
	try:
		log("Attemping to send " + filename + "...\n")
		with file(filename.strip(), "rb") as afile:
		# File is open. Send as bytestream.
			log("File opened - now attempting to read it in.\n")
			toSend = afile.read()
			bytesToSend = bytearray(toSend)
			log("File imported as byteArray...\n")
			send_msg(sock, bytesToSend)
			log("Sending file to client...\n")
			log("File sent")
	except IOError as e:
		# File doe snot exist. Send error message.
		eMessage = "ERROR : File does not exist."
		log("Exception: " + str(e) + "...\n")
		log("Sending error message to cleint...\n")
		send_msg(sock, eMessage)


# ------------------Program Run-------------------- #

checkArgs()

serverCRPport = int(sys.argv[1])
debugFlag = False

if len(sys.argv) == 3:
	if sys.argv[2] != None:
		log("Flag set to True")
		debugFlag = True

sock = crpSocket.CRPSocket(serverCRPport, debugFlag)
state = 'DISCONNECTED'

try:
	sock.bind("172.17.0.3", serverCRPport)
except Exception as e:
	print "Error: could not bind to port " + str(serverCRPport) + " on local host.\n"
	log("Exception: " + str(e))
	sys.exit(1)

while True:
	runServer()