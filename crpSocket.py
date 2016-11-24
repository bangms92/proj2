import socket
import crpPacket
from collections import deque
from crpPacket import CRPPacket
import math

DEBUG = True

def log(message):
	if DEBUG:
		print message

class CRPSocket:
	def __init__(self, sourceCRPPort):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.settimeout(1)
		self.receivingWindowSize = CRPPacket.maxWindowSize()
		self.recievingWindowSizeInt = 6
		self.sendWindowSize = 6
		
		self.destAddr = None
		self.srcAddr = None
		
		self.udpDestPort = None
		self.udpSrcPort = sourceCRPPort
		
		self.seqNum = 1
		self.ackNum = 1
		
		self.state = 'CLOSED'

		self.maxReset = 100

	def setWindowSize(self, size):
		self.receivingWindowSize = int(math.pow(2, size) - 1)
		self.recievingWindowSizeInt = size
		
	def bind(self, addr, portNum):
		self.socket.bind((addr, portNum))
		
	def connect(self, ipAddress, portNum):
		log("Client connect()")
		self.destAddr = ipAddress
		self.udpDestPort = portNum
		
		#Send REQ


		log("Creating REQ Packet")
		reqPacket = CRPPacket.getREQ(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
		
		self.seqNum = self.seqNum + 1 #Increment sequence number
		self.socket.sendto(reqPacket.toByteArray(), (self.destAddr, self.udpDestPort))

		log("REQ Packet Sent")
		self.state = 'REQ-SENT'
		
		timeoutCount = 0
		#Receive ACK
		log("Waiting to receive ACK...")
		while True:
			try:
				ackData, ackAddress = self.recvfrom(self.receivingWindowSize)
				ackPacket = self._reconstructPacket(bytearray(ackData), self.ackNum)
			except:
				log("Timed out, listening again for ACK in connect()")
				timeoutCount += 1

				if timeoutCount >= 3:
					log("Send REQ again")
					self.socket.sendto(reqPacket.toByteArray(), (self.destAddr, self.udpDestPort))
					log("REQ Packet Sent")
					timeoutCount = 0

				continue
			if ackPacket != None:
				self.ackNum = ackPacket.header['seqNum'] + 1
				break;
			
		log("self.seqNum is " + str(self.seqNum))
		if ackPacket.isAck() and ackPacket.header['ackNum'] == self.seqNum:
			print "Correct Ack recieved"
			
		#Send SYNC
		log("Creating SYNC Packet")
		syncPacket = CRPPacket.getSYNC(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
		
		log("Increment Seq Num")
		self.seqNum = self.seqNum + 1 #Increment sequence number
		self.socket.sendto(syncPacket.toByteArray(), (self.destAddr, self.udpDestPort))
		log("SYNC is sent")
		#Established
		self.state = 'ESTABLISHED'

	def listen(self):
		log("listen()")
		self.state = 'LISTENING'
		
		#Receive REQ
		while True:
			try:
				reqData, reqAddress = self.recvfrom(self.receivingWindowSize)
				reqPacket = self._reconstructPacket(bytearray(reqData), self.ackNum)
			except:
				log("Most likely Timed out")
				continue
			if reqPacket != None:
				log("Received REQ")
				self.ackNum = reqPacket.header['seqNum'] + 1
				break

		self.udpDestPort = int(reqPacket.header['desPort'])
		self.destAddr = reqAddress[0]
		self.udpDestPort = reqAddress[1]
		
		log("Sending back ACK")
		#Send ACK
		ackPacket = CRPPacket(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, (False, False, True, False, False), self.receivingWindowSize)
		self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
		self.seqNum = self.seqNum + 1 #Increment sequence number
		self.state = 'REQ-RCVD'
		log("ACK Packet Sent")
		
		timeoutCount = 0
		#Receive SYNC
		while True:
			try:
				syncData, syncAddress = self.recvfrom(self.receivingWindowSize)
				syncPacket = self._reconstructPacket(bytearray(syncData), self.ackNum)
			except:
				log("Most likely Timed out")
				timeoutCount += 1
				if timeoutCount >= 3:
					log("Send ACK again")
					self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
					log("ACK Packet Sent")
					timeoutCount = 0
				continue
			if syncPacket != None:
				log("Received SYNC")
				self.ackNum = syncPacket.header['seqNum'] + 1
				break
			
		log("Connection Established")
		#Established
		self.state = 'ESTABLISHED'
		
	def _reconstructPacket(self, data, checkAckNum = False):
		packet = CRPPacket.fromByteArray(data)

		#include checksum here
		if checkAckNum:
			#Check for checksum
			givenChecksum = packet.header['checksum']
			calculatedChecksum = packet._computeChecksum()

			log("Given Check Sum: " + str(givenChecksum))
			log("calculatedChecksum: " + str(calculatedChecksum))

			if givenChecksum != calculatedChecksum:
				log("#### corrupted packet ####")
				return None

			packetAckNum = packet.header['seqNum']
			log("Comparing seqNum: " + str(packetAckNum) + " with " + str(checkAckNum))

			if packetAckNum != checkAckNum:
				log("#### ack mismatch ####")
				return None
		return packet

	def send(self, msg):
		if len(msg) < 100:
			log("send(" + msg + "), length is " + str(len(msg)))
		if self.udpSrcPort is None:
			raise Exception("Socket not bound")

		if self.state != 'ESTABLISHED':
			raise Exception("Connection not established")

		dataQueue = deque()
		packetQueue = deque()
		sentQueue = deque()
		windowQueue = deque()
		lastSeqNum = self.seqNum
		baseNum = self.seqNum
		nextSeqNum = self.seqNum

		log("baseNum set to " + str(baseNum))

		#fragment data and add it to data queue
		log("Trying to send message length " + str(len(msg)))
		for i in range(0, len(msg), CRPPacket.getDataLength()):
			#log("i = " + str(i))
			if (i + CRPPacket.getDataLength() > len(msg)):
				dataQueue.append(bytearray(msg[i : ]))
			else:
				dataQueue.append(bytearray(msg[i : i + CRPPacket.getDataLength()]))

		#construct packet queue from data queue
		log("Queue size: " + str(len(dataQueue)))
		count = 0
		for data in dataQueue:
			#log("Data in dataQueue: " + str(data))
			count = count + 1
			if data == dataQueue[-1]:
				#log("# " + str(count) + " Last Packet, 1:0:0:0:0 flag set")
				flags = (True, False, False, False, False)
			else:
				#log("# " + str(count) + " Normal Packet, 0:0:0:0:0 flag set")
				flags = (False, False, False, False, False)

			packet = CRPPacket(
					srcPort = self.udpSrcPort,
					desPort = self.udpDestPort,
					seqNum = self.seqNum,
					ackNum = self.ackNum,
					flagList = flags,
					winSize = self.receivingWindowSize,
					data = data
					)

			self.seqNum += 1
			if self.seqNum >= CRPPacket.maxSeqNum():
				self.seqNum = 0

			packetQueue.append(packet)
		log("packetQueue size " + str(len(packetQueue)))
		resetsLeft = self.maxReset

		#Initial Window
		windowCount = self.sendWindowSize
		log("Window Size: " + str(windowCount))
		while windowCount and packetQueue:
			log("Packet aded to Window Queue")
			packetToSend = packetQueue.popleft()
			windowQueue.append(packetToSend)
			windowCount -= 1

		while (windowQueue or packetQueue) and resetsLeft:
			log("Sending Mode in send()")
			for pack in windowQueue:
				#Send the packet
				self.socket.sendto(pack.toByteArray(), (self.destAddr, self.udpDestPort))
				log("Packet sent, seqNum: " + str(pack.header['seqNum']))
				sentQueue.append(pack)
				nextSeqNum = self.seqNum + 1

			correctlyReceivedAck = False
			count = 0
			# Handle ack
			while True:
				packet = None
				try:
					log("Receiving ACK Package in send()")
					data, address = self.recvfrom(self.receivingWindowSize)
					packet = self._reconstructPacket(bytearray(data), self.ackNum)
				except:
					log("Timed out while trying to receive ACK in send()")
					count += 1
					if count >= 3:
						break
					continue
				if not packet:
					log("Something wrong with ACK packet received")
					#for pack in windowQueue:
						#Send the packet
					#   self.socket.sendto(pack.toByteArray(), (self.destAddr, self.udpDestPort))
					#   log("Packet sent, seqNum: " + str(pack.header['seqNum']))
					break
				if packet:
					log("Successfully received uncorrupted ACK Package")
					correctlyReceivedAck = True
					break

			if correctlyReceivedAck:
				change = packet.header['ackNum'] - baseNum
				baseNum = baseNum + change
				log("ackNum received: " + str(packet.header['ackNum']))
				log("chagnge: " + str(change))
				while change:
					if len(packetQueue) >= 1:
						windowQueue.append(packetQueue.popleft())
					if len(windowQueue) >= 1:
						windowQueue.popleft()
					change -= 1
				log("windowQueue left: " + str(len(windowQueue)) + " packetQueue left: " + str(len(packetQueue)) + " self.seq: " + str(self.seqNum) + " self.ack: " + str(self.ackNum))
		
	# Returns the packet that was received in packet structure
	def recv(self):
		recieveOrder = ""
		firstReceving = True
		log("recv() entered")
		if self.udpSrcPort is None:
			log("Socket already closed")
		if self.state != 'ESTABLISHED':
			log("Socket already closed")

		message = bytes()

		redoLeft = self.maxReset
		isLast = False
		while redoLeft and not isLast:
			justSendAck = False
			windowCount = self.receivingWindowSize
			log("Receiving Window Size: " + str(windowCount))
			packet = None
			while windowCount:
				try:
					log("==============Waiting to recieve a packet==============")
					data, address = self.recvfrom(self.receivingWindowSize)
				except socket.timeout:
					log("Timed out, just send ACK")
					redoLeft -= 1
					justSendAck = True
					break
				packetP = self._reconstructPacket(bytearray(data))
				log("Recevied Packet SeqNum: " + str(packetP.header['seqNum']) + " ackNum: " + str(self.ackNum))
				packet = self._reconstructPacket(bytearray(data), self.ackNum)

				if not packet:
					log("*******************Receive out of order or irrelevant packet, ignore****************")
					justSendAck = True
					windowCount -= 1
					break

				if packet.data != None:
					log("Recieved Packet, is First? " + str(firstReceving))
					recieveOrder = recieveOrder + ", " + str(packet.header['seqNum'])
					firstReceving = False
					message += packet.data
					self.ackNum = packet.header['seqNum'] + 1
					if self.ackNum > CRPPacket.maxAckNum():
						self.ackNum = 0
					windowCount -= 1

				if (packet.isLastPacket()):
					log("Last Packet")
					isLast = True
					break

				if (packet.isFin()):
					log("Finish Packet received")
					flags = (False, False, True, False, False)
					ackPacket = CRPPacket(
								srcPort = self.udpSrcPort,
								desPort = self.udpDestPort,
								seqNum = self.seqNum,
								ackNum = self.ackNum,
								flagList = flags,
								winSize = self.receivingWindowSize,
								)
					self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
					break

			#log("Data received: " + str(packet.data))
			if (firstReceving == False and justSendAck == True) or packet != None and packet.data != None:
				if justSendAck:
					log("Send due to socket time out")
				flags = (False, False, True, False, False)
				ackPacket = CRPPacket(
							srcPort = self.udpSrcPort,
							desPort = self.udpDestPort,
							seqNum = self.seqNum,
							ackNum = self.ackNum,
							flagList = flags,
							winSize = self.receivingWindowSize,
							)
				self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
				log("Ack Packet sent: #" + str(self.ackNum))
			log(" self.seq: " + str(self.seqNum) + " self.ack: " + str(self.ackNum))
		if not redoLeft:
			raise Exception('Socket timeout')

		log("Order: " + recieveOrder)
		return message
		
	def recvfrom(self, recvWindow):
		while True:
			try:
				packet = self.socket.recvfrom(recvWindow)
				log("Recieved message from " + str(packet[1]) + "\n")
			except socket.error as error:
				if error.errno is 35:
					continue
				else:
					raise error
			return packet
		
	def close(self):
		log("CLOSING REQUESTED")
		log("creating FIN Packet")
		fin_flags = (False, True, False, False, False)
		finPacket = CRPPacket(srcPort = self.udpSrcPort, desPort = self.udpDestPort,
					seqNum = self.seqNum, ackNum = self.ackNum, flagList = fin_flags, winSize = self.receivingWindowSize,
					)
		self.seqNum += 1
		self.socket.sendto(finPacket.toByteArray(), (self.destAddr, self.udpDestPort))
		log("FIN packet Sent")

		timeoutCount = 0
		log("waiting to receive ACK..")
		while True:
			try:
				ackData, ackAddress = self.recvfrom(self.receivingWindowSize)
				ackPacket = self._reconstructPacket(bytearray(ackData), self.ackNum)
			except:
				log("Timed out, listening again for ACK in connect()")
				timeoutCount += 1

				if timeoutCount >= 3:
					log("Send FIN again")
					self.socket.sendto(finPacket.toByteArray(), (self.destAddr, self.udpDestPort))
					log("FIN Packet Sent")
					timeoutCount = 0
				continue
			if ackPacket != None:
				self.ackNum = ackPacket.header['seqNum'] + 1
				break;
		self.socket.close()
		self.state = 'CLOSED'
	
		
		
		
		
		
		
