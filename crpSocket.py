import socket
import crpPacket
from crpPacket import CRPPacket

DEBUG = True

def log(message):
    if DEBUG:
        print message

class CRPSocket:
    def __init__(self, sourceCRPPort):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receivingWindowSize = CRPPacket.maxWindowSize()
        self.sendWindowSize = 1
        
        self.destAddr = None
        self.srcAddr = None
        
        self.udpDestPort = None
        self.udpSrcPort = sourceCRPPort
        
        self.seqNum = 0
        self.ackNum = 0
        
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
        self.ackNum = reqPacket.header['seqNum'] + 1
        self.udpDestPort = int(reqPacket.header['desPort'])
        self.destAddr = reqAddress[0]
        self.udpDestPort = reqAddress[1]
        
        #Send ACK
        ackPacket = CRPPacket(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, (False, True, False, False), self.receivingWindowSize)
        self.socket.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))
        self.state = 'REQ-RCVD'
        log("ACK Packet Sent")
        
        #Receive SYNC
        syncData, syncAddress = self.recvfrom(self.receivingWindowSize)
        syncPacket = self._reconstructPacket(bytearray(syncData))
        log("Received SYNC")
        #Established
        self.state = 'ESTABLISHED'
        
    def _reconstructPacket(self, data):
        packet = CRPPacket.fromByteArray(data)
        #include checksum here
        return packet
    
    def _sendREQ(self):
        log("Creating REQ Packet")
        reqPacket = CRPPacket.getREQ(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
        
        log("Increment Seq Num")
        self.seqNum = self.seqNum + 1 #Increment sequence number
        self.socket.sendto(reqPacket.toByteArray(), (self.destAddr, self.udpDestPort))
    
    def _sendSYNC(self):
        log("Creating SYNC Packet")
        syncPacket = CRPPacket.getSYNC(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
        
        log("Increment Seq Num")
        self.seqNum = self.seqNum + 1 #Increment sequence number
        self.socket.sendto(syncPacket.toByteArray(), (self.destAddr, self.udpDestPort))
        

    def send(self, msg):
        if self.udpSrcPort is None:
            raise Exception("Socket not bound")

        if self.state != 'ESTABLISHED':
            raise Exception("Connection not established")

        dataQueue = deque()
        packetQueue = deque()
        sentQueue = deque()
        lastSeqNum = self.seqNum

        #fragment data and add it to data queue
        for i in range(stop = len(msg), step = CRPPacket.getDataLength()):
            if (i + CRPPacket.getDataLength() > len(msg)):
                dataQueue.append(bytearray(msg[i : ]))
            else:
                dataQueue.append(bytearray(msg[i : i + CRPPacket.getDataLength()]))

        #construct packet queue from data queue
        for data in dataQueue:
            if data == dataQueue[0]:
                flags = (False, False, False, False, True, False)
            if data == dataQueue[-1]:
                flags = (False, False, False, False, False, True)
            else:
                flags = (False, False, False, False, False, False)

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

        resetsLeft = self.maxReset
        while packetQueue and resetsLeft:
            #send packets in send window
            window = self.sendWindowSize
            while window and packetQueue:
                packetToSend = packetQueue.popLeft()
                self.sendto(packet.toByteArray(), (self.destAddr, self.desUDPPort))
                lastSeqNum = packet.header['seqNum']

                window -= 1
                sentQueue.append(packet)

            try:
                data, address = self.recvfrom(self.receivingWindowSize)
                handShakeFinishedCheck = self.__reconstructPacket(bytearray(data))
                packet = self.__reconstructPacket(data = bytearray(data),  checkAckNum = lastSeqNum)

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
                elif handShakeFinishedCheck.isAck() and handShakeFinishedCheck.header['ackNum'] == self.finalCnctAckNum:

                    flags = (False, False, True, False, False, False)
                    ackPacket = CRPPacket(
                                srcPort = self.udpSrcPort,
                                desPort = self.udpDestPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = flags,
                                winSize = self.receivingWindowSize,
                                )
                    self.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))

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
        
        
    def recv(self):
        log("source port is " + str(self.udpSrcPort))
        if self.udpSrcPort is None:
            log("Socket already closed")
        log("state: " + self.state)
        if self.state != 'ESTABLISHED':
            log("Socket already closed")

        message = bytes()

        redoLeft = self.maxReset
        while redoLeft:
            try:
                data, address = self.recvfrom(self.receivingWindowSize)

            except socket.timeout:
                redoLeft -= 1
                continue

            packet = self.__reconstructPacket(bytearray(data))

            if not packet:
                redoLeft -= 1
                continue

            else:
                self.ackNum = packet.header['seqNum'] + 1
                if self.ackNum > RxPacket.maxAckNum():
                    self.ackNum = 0
                message += packet.data

                flags = (False, False, True, False, False, False)
                ackPacket = CRPPacket(
                            srcPort = self.udpSrcPort,
                            desPort = self.udpDestPort,
                            seqNum = self.seqNum,
                            ackNum = self.ackNum,
                            flagList = flags,
                            winSize = self.receivingWindowSize,
                            )
                self.sendto(ackPacket.toByteArray(), (self.destAddr, self.udpDestPort))

                if (packet.isEndOfMessage()):
                    break

                if (packet.isFin()):
                    flags = (False, False, True, False, False, False)
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

                return message


        if not redoLeft:
            raise Exception('Socket timeout')

        return message
        
    def recvfrom(self, recvWindow):
        while True:
            log("Trying to recieve")
            try:
                packet = self.socket.recvfrom(recvWindow)
                log("Recied message from " + str(packet[1]) + "\n")
            except socket.error as error:
                if error.errno is 35:
                    continue
                else:
                    raise e
            log("Returning recvfrom packet")
            return packet
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        