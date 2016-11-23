import socket
import crpPacket
from collections import deque
from crpPacket import CRPPacket

DEBUG = True

def log(message):
	if DEBUG:
		print message

class CRPSocket:
	def __init__(self, sourceCRPPort):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.receivingWindowSize = CRPPacket.maxWindowSize()
		self.sendWindowSize = 20
		
		self.destAddr = None
		self.srcAddr = None
		
		self.udpDestPort = None
		self.udpSrcPort = sourceCRPPort
		
		self.seqNum = 1
		self.ackNum = 1
		
		self.state = 'CLOSED'

		self.maxReset = 50
		
	def bind(self, addr, portNum):
		self.socket.bind((addr, portNum))
		
	def connect(self, ipAddress, portNum):
		log("Client connect()")
		self.destAddr = ipAddress
		self.udpDestPort = portNum
		
		#Send REQ
		self._sendREQ()
		log("REQ Packet Sent")
		self.state = 'REQ-SENT'
		
		#Receive ACK
		log("Waiting to receive ACK...")
		ackData, ackAddress = self.recvfrom(self.receivingWindowSize)
		ackPacket = self._reconstructPacket(bytearray(ackData))
		
		log("self.seqNum is " + str(self.seqNum))
		if ackPacket.isAck() and ackPacket.header['ackNum'] == self.seqNum:
			print "Correct Ack recieved"
			
		#Send SYNC
		self._sendSYNC()
		log("SYNC is sent")
		#Established
		self.state = 'ESTABLISHED'

	def listen(self):
		log("listen()")
		self.state = 'LISTENING'
		
		#Receive REQ
		while True:
			reqData, reqAddress = self.recvfrom(self.receivingWindowSize)
			reqPacket = self._reconstructPacket(bytearray(reqData))
			break
		self.udpDestPort = int(reqPacket.header['desPort'])
		self.destAddr = reqAddress[0]
		self.udpDestPort = reqAddress[1]
		
		#Send ACK
		ackPacket = CRPPacket(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, (False, False, True, False, False), self.receivingWindowSize)
		self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
		self.state = 'REQ-RCVD'
		log("ACK Packet Sent")
		
		#Receive SYNC
		syncData, syncAddress = self.recvfrom(self.receivingWindowSize)
		syncPacket = self._reconstructPacket(bytearray(syncData))
		log("Received SYNC")
		#Established
		self.state = 'ESTABLISHED'
		
	def _reconstructPacket(self, data, checkAckNum = False):
		packet = CRPPacket.fromByteArray(data)
		#include checksum here
		if checkAckNum:
			packetAckNum = packet.header['seqNum']
			log("Comparing seqNum: " + str(packetAckNum) + " with " + str(checkAckNum))

			if packetAckNum != checkAckNum:
				log("ack mismatch")
				return None
		return packet
	
	def _sendREQ(self):
		log("Creating REQ Packet")
		reqPacket = CRPPacket.getREQ(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
		
		log("Increment Seq Num")
		#self.seqNum = self.seqNum + 1 #Increment sequence number
		self.socket.sendto(reqPacket.toByteArray(), (self.destAddr, self.udpDestPort))
	
	def _sendSYNC(self):
		log("Creating SYNC Packet")
		syncPacket = CRPPacket.getSYNC(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
		
		log("Increment Seq Num")
		#self.seqNum = self.seqNum + 1 #Increment sequence number
		self.socket.sendto(syncPacket.toByteArray(), (self.destAddr, self.udpDestPort))
		

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
		#    if data == dataQueue[0]:
		#        flags = (False, False, False, False, True, False)
		#    if data == dataQueue[-1]:
		#        flags = (False, False, False, False, False, True)
		#    else:
			#log("Data in dataQueue: " + str(data))
			count = count + 1
			if data == dataQueue[-1]:
				log("# " + str(count) + " Last Packet, 1:0:0:0:0 flag set")
				flags = (True, False, False, False, False)
			else:
				log("# " + str(count) + " Normal Packet, 0:0:0:0:0 flag set")
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

			# Handle ack
			log("Receiving ACK Package in send()")
			data, address = self.recvfrom(self.receivingWindowSize)
			packet = self._reconstructPacket(bytearray(data))
			if not packet:
				log("Something wrong, send form base again")
					
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
		"""
		while packetQueue and resetsLeft:
			#send packets in send window
			window = self.sendWindowSize
			while window and packetQueue:

				packetToSend = packetQueue.popleft()
				#log("Sending message: " + str(packetToSend.data))
				self.socket.sendto(packetToSend.toByteArray(), (self.destAddr, self.udpDestPort))
				log("Sent a packet")
				lastSeqNum = packetToSend.header['seqNum']

				window -= 1
				sentQueue.append(packetToSend)

			try:
				log("Waiting to receive ack Packet")
				data, address = self.recvfrom(self.receivingWindowSize)
				handShakeFinishedCheck = self._reconstructPacket(bytearray(data))
				packet = self._reconstructPacket(bytearray(data),  lastSeqNum)
				if not packet:
					sentQueue.reverse()
					packetQueue.extendleft(sentQueue)
					sentQueue.clear()
					resetsLeft -= 1
					continue

			except socket.timeout:
				window = 1
				resetsLeft -= 1
				sentQueue.reverse()
				packetQueue.extendleft(sentQueue)
				sentQueue.clear()

			
			else:
				window += 1
				if (isinstance(packet, int)):
					while packet < 0:
						packetQueue.appendleft(sentQueue.pop())
						packet += 1
				elif handShakeFinishedCheck.isAck():

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

					resetsLeft = self.maxReset

					sentQueue.reverse()
					packetQueue.extendleft(sentQueue)
					sentQueue.clear()
				elif packet.isAck():
					self.seqNum = packet.header['ackNum']
					resetsLeft = self.maxReset
					sentQueue.clear()
			
		if not resetsLeft:
			raise Exception('socket timeout')
		"""
	# Returns the packet that was received in packet structure
	def recv(self):
		log("recv() entered")
		if self.udpSrcPort is None:
			log("Socket already closed")
		if self.state != 'ESTABLISHED':
			log("Socket already closed")

		message = bytes()

		redoLeft = self.maxReset
		isLast = False
		while redoLeft and not isLast:
			windowCount = self.sendWindowSize
			log("Window Size: " + str(windowCount))
			while windowCount:
				try:
					log("==============Waiting to recieve a packet==============")
					data, address = self.recvfrom(self.receivingWindowSize)
				except socket.timeout:
					log("Timed out")
					redoLeft -= 1
					continue
				packetP = self._reconstructPacket(bytearray(data))
				log("Recevied Packet SeqNum: " + str(packetP.header['seqNum']) + " ackNum: " + str(self.ackNum))
				packet = self._reconstructPacket(bytearray(data), self.ackNum)

				if not packet:
					log("Receive out of order or irrelevant packet")
					continue

				message += packet.data
				self.ackNum = packet.header['seqNum'] + 1
				if self.ackNum > CRPPacket.maxAckNum():
					self.ackNum = 0

				if (packet.isLastPacket()):
					log("Last Packet")
					isLast = True
					break
				windowCount -= 1

			#log("Data received: " + str(packet.data))
			if packet.data != None:
				
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
		"""
		while redoLeft:
			try:
				log("Attempt to receive packet")
				data, address = self.recvfrom(self.receivingWindowSize)
				log("Packet received")
			except socket.timeout:
				redoLeft -= 1
				continue

			packet = self._reconstructPacket(bytearray(data))
			log("packet reconstructed")
			log("Flag List: " + str(packet.header['flagList']) + "\n")
			log("Sequence Number " + str(packet.header['seqNum']))
			if not packet:
				redoLeft -= 1
				continue
			else:
				self.ackNum = packet.header['seqNum'] + 1
				if self.ackNum > CRPPacket.maxAckNum():
					self.ackNum = 0

				#log("Data received: " + str(packet.data))
				if packet.data != None:
					message += packet.data

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
				log("Ack Packet sent")

				if (packet.isLastPacket()):
					log("Last Packet")
					break

				if (packet.isFin()):
					log("Finish Packet received.")
					flags = (False, True, False, False, False)
					ackPacket = RxPacket(
								srcPort = self.udpSrcPort,
								desPort = self.udpDestPort,
								seqNum = self.seqNum,
								ackNum = self.ackNum,
								flagList = flags,
								winSize = self.receivingWindowSize,
								)
					self.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
					self.__closePassive(ackPacket)
					break

				#return message
		return message
		"""
		if not redoLeft:
			raise Exception('Socket timeout')

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
					raise e
			return packet
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		