import socket
import crpacket
from crpacket import CRPacket

class CRPSocket:

    def log(self, message):
        if DEBUG:
            print message

    # Initliazation of class vars. Local to current instantiated class.
    def __init__(self, srcCRPPort, debug = True):
        self.state = 'CLOSED'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvWindowSize = CRPacket.maxWinSize()  # Receive Window size in bytes
        self.sendWindowSize = 1 # Send window size in bytes
        self.buffer = None      # Actual memory space for the buffer
        self.srcCRPPort = srcCRPPort  # Local CRP port, not UDP port
        self.desCRPPort = None     # Destination CRP Port, not UDP port
        self.desAddr = None
        self.srcAddr = "127.0.0.1"
        self.srcUDPPort = None
        self.desUDPPort = None
        self.timeout = None
        self.resetLimit = 50
        self.finalSyncAckNum = 2
        self.debug = debug

        # Note on Sequence and Acknoledgment numbers: The sequence number should
        #  increase every time you SEND data, by the number of bytes. This should be
        #  the entire packet size, not just the data size. The acknowldgement number
        #  should increase every time we RECEIVED data, by the number of bytes. This
        #  should also be the entire packet size, for continuity.

        self.seqNum = 0
        self.ackNum = 0

    def UDPdesSet(self, UDPdesport):
        self.log("Setting destination UDP port...\n")
        self.desUDPPort = UDPdesport

    def UDPbind(self, UDPsrcport):
        self.log("Setting source UDP port...\n")
        self.srcUDPPort = UDPsrcport

    def log(self, message):
        if self.debug:
            print message

    def gettimeout(self):
        return self.socket.gettimeout()

    def settimeout(self, val):
        return self.socket.settimeout()

    # Bind the socket to a specific local CRP port.
    # Set the object's port var.
    def bind(self, aPort):
        self.log("Attempting to bind to CRP port " + str(aPort))
        try:
            if aPort:
                self.socket.bind((self.srcAddr, aPort))
                self.bindPort = aPort
        except Exception as e:
            print("The socket could not be bound to " + aPort + ".")
            self.log(str(e))

    # Listen for incoming connectins, and accepts them.
    # Uses the CRP handshake as described in the CRP state diagram.
    # Once connection is established, sets up memory and window.
    def listen(self):
        if self.bindPort is None:
            self.log("An attempt to listen an un unbound port was made...\n")
            raise Exception("Socket not bound")
            sys.exit(1)

        self.state = 'LISTENING'

        waitLimit = self.resetLimit * 100

        self.log("Waiting for req packet...\n")
        while waitLimit:

            #receive REQ
            try:
                self.log("Calling recvfrom to see if we have anything...\n")
                theBytes, address = self.recvfrom(self.recvWindowSize)
                self.log("Recvfrom called....\n")
                packet = self.__reconstructPacket(data = bytearray(theBytes))

                if packet is None:
                    waitLimit -= 1
                    continue

            except socket.timeout:
                waitLimit -= 1
                continue

            else:
                if (packet.isReq()):
                    break
                else:
                    waitLimit -= 1


        if not waitLimit:
            log("Socket timed out!\n")
            raise Exception('socket timeout')

        self.ackNum = packet.header['seqNum'] + 1
        self.log("Setting destination CRP Port to " + packet.header['desPort'])
        self.desCRPPort = packet.header['desPort']
        self.desAddr = addr[0]
        self.log("Setting destination UDP port to " + str(addr[1]))
        self.desUDPPort = addr[1]

        #Send Ack 1
        waitLimit = self.resetLimit * 100
        while waitLimit:

            try:
                #create packet
                flags = (False, False, True, False, False, False)
                reqPacket = CRPacket(
                            srcPort = self.srcCRPPort,
                            desPort = self.desCRPPort,
                            seqNum = self.seqNum,
                            ackNum = self.ackNum,
                            flagList = flags,
                            winSize = self.recvWindowSize,
                            )
                self.sendto(reqPacket.toByteArray(), (self.desAddr, self.desUDPPort))


                data, address = bytearray(self.recvfrom(self.rcvWindowSize))
                packet = self.__reconstructPacket(data = bytearray(data))
                if not packet:
                    resetsLeft -= 1
                    continue
            except socket.timeout:
                resetsLeft -= 1
            else:
                if packet.isSync():
                    break
                else:
                    resetsLeft -= 1

        if not waitLimit:
            raise Exception('socket timeout')

        self.ackNum = packet.header['seqNum'] + 1
        self.finalSyncAckNum = self.ackNum

        #send the second ACK
        flags = (False, False, True, False, False, False)
        reqPacket = CRPacket(
                    srcPort = self.srcCRPPort,
                    desPort = self.desCRPPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = flags,
                    winSize = self.recvWindowSize,
                    )
        self.sendto(reqPacket.toByteArray(), (self.desAddr, self.desUDPPort))

        self.state = 'ESTABLISHED'


    # Connects to the specified host on the specified port.
    # Uses the CRP handshake as described in the CRP state diagram.
    # Once connection is estabilshed, sets up memory and window.
    def connect(self, (ip, port)):
        if port == None:
            self.log("Socket not bound\n")
            raise Exception("Socket not bound")
            sys.exit(1)

        self.desAddr = ip
        self.desCRPPort = port

        try:
            self.log("Sending REQ packet....\n")
            # Create an Req packet and send it off to the host we wish to connect to.
            ack1 = self.__sendReq()

            # Create a Sync packet and send it off to the other host
            self.log("Sending SYNC packet...\n")
            ack2 = __sendSync()
        except Exception:
            self.log("Could not connect...\n")
            raise Exception("Could not connect")
        else:
            self.log("Connection established\n")
            self.state = 'ESTABLISHED'



    def send(self, msg):
        if self.srcCRPPort is None:
            raise Exception("Socket not bound")

        if self.state != 'ESTABLISHED':
            raise Exception("Connection not established")

        dataQueue = deque()
        packetQueue = deque()
        sentQueue = deque()
        lastSeqNum = self.seqNum

        #fragment data and add it to data queue
        for i in range(stop = len(msg), step = CRPacket.getDataLength()):
            if (i + CRPacket.getDataLength() > len(msg)):
                dataQueue.append(bytearray(msg[i : ]))
            else:
                dataQueue.append(bytearray(msg[i : i + CRPacket.getDataLength()]))

        #construct packet queue from data queue
        for data in dataQueue:
            if data == dataQueue[0]:
                flags = (False, False, False, False, True, False)
            if data == dataQueue[-1]:
                flags = (False, False, False, False, False, True)
            else:
                flags = (False, False, False, False, False, False)

            packet = CRPacket(
                    srcPort = self.srcCRPPort,
                    desPort = self.desCRPPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = flags,
                    winSize = self.recvWindowSize,
                    data = data
                    )

            self.seqNum += 1
            if self.seqNum >= CRPacket.maxSeqNum():
                self.seqNum = 0

            packetQueue.append(packet)

        resetsLeft = self.resetLimit
        while packetQueue and resetsLeft:
            #send packets in send window
            window = self.sendWindowSize
            while window and packetQueue:
                packetToSend = packetQueue.popLeft()
                self.sendto(packet.toByteArray(), (self.desAddr, self.desUDPPort))
                lastSeqNum = packet.header['seqNum']

                window -= 1
                sentQueue.append(packet)

            try:
                data, address = self.recvfrom(self.recvWindowSize)
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
                elif handShakeFinishedCheck.isAck() and handShakeFinishedCheck.header['ackNum'] == self.finalSyncAckNum:

                    flags = (False, False, True, False, False, False)
                    ackPacket = CRPacket(
                                srcPort = self.srcCRPPort,
                                desPort = self.desCRPPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = flags,
                                winSize = self.recvWindowSize,
                                )
                    self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desUDPPort))

                    resetsLeft = self.resetLimit

                    sentQueue.reverse()
                    packetQueue.extendleft(sentQueue)
                    sentQueue.clear()
                elif packet.isAck():
                    self.seqNum = packet.header['ackNum']
                    resetsLeft = self.resetLimit
                    sentQueue.clear()

        if not resetsLeft:
            raise Exception('socket timeout')

    def recv(self):
        if self.srcCRPPort is None:
            self.log("Socket already closed")

        if self.state != 'ESTABLISHED':
            self.log("Socket already closed")

        message = bytes()

        resetsLeft = self.resetLimit
        while resetsLeft:
            try:
                data, address = self.recvfrom(self.recvWindowSize)

            except socket.timeout:
                resetsLeft -= 1
                continue

            packet = self.__reconstructPacket(bytearray(data))

            if not packet:
                resetsLeft -= 1
                continue

            else:
                self.ackNum = packet.header['seqNum'] + 1
                if self.ackNum > CRPacket.maxAckNum():
                    self.ackNum = 0
                message += packet.data

                flags = (False, False, True, False, False, False)
                ackPacket = CRPacket(
                            srcPort = self.srcCRPPort,
                            desPort = self.desCRPPort,
                            seqNum = self.seqNum,
                            ackNum = self.ackNum,
                            flagList = flags,
                            winSize = self.recvWindowSize,
                            )
                self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desUDPPort))

                if (packet.isEndOfMessage()):
                    break

                if (packet.isFin()):
                    flags = (False, False, True, False, False, False)
                    ackPacket = CRPacket(
                                srcPort = self.srcCRPPort,
                                desPort = self.desCRPPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = flags,
                                winSize = self.recvWindowSize,
                                )
                    self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desUDPPort))
                    self.__closePassive(ackPacket)
                    break

                return message


        if not resetsLeft:
            raise Exception('Socket timeout')


        return message

    def sendto(self, data, address):
        self.log("Sending packet to " + str(address) + "\n")
        self.socket.sendto(data, address)

    def recvfrom(self, recvWindow):
        while True:
            try:
                packet = self.socket.recvfrom(recvWindow)
                self.log("Recieving message from " + str(packet[1]) + "\n")
            except socket.error as error:
                if error.errno is 35:
                    continue
                else:
                    raise e

        return packet

    def close(self):
        if self.srcCRPPort is None:
            self.socket.close()
            raise CRPException("Socket not bound")


        if self.state != 'ESTABLISHED':
            self.socket.close()
            raise Exception("Connection not established")

        fin_flags = (False, False, False, True, False, False)
        finPacket = CRPacket(
                    srcPort = self.srcCRPPort,
                    desPort = self.desCRPPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = fin_flags,
                    winSize = self.recvWindowSize,
                    )

        self.seqNum += 1
        if self.seqNum > CRPacket.maxSeqNum():
            self.seqNum = 0

        resetsLeft = self.resetLimit()

        waitingForHostB = True
        isFinAcked = False

        while resetsLeft and (not isFinAcked or waitingForHostB):
            self.sendto(finPacket.toByteArray(), (self.desAddr, self.desUDPPort))

            try:
                data, address = self.recvfrom(self.recvWindowSize)
                packet = self.__reconstructPacket(data)

                if not packet:
                    resetsLeft -= 1
            except socket.timeout:
                resetsLeft -= 1
                continue
            else:
                if (packet.isAck() and packet.header['ackNum'] == self.seqNum):
                    isFinAcked = True

                if (packet.isFin()):
                    ack_flags = (False, False, False, True, False, False)
                    finPacket = CRPacket(
                                srcPort = self.srcCRPPort,
                                desPort = self.desCRPPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = fin_flags,
                                winSize = self.recvWindowSize,
                                )

                    self.sendto(finPacket.toByteArray(), (self.desAddr, self.desUDPPort))
                    waitingForHostB = False

        self.socket.close()
        self = RxSocket(self.srcCRPPort, self.debug)
        self.state = 'CLOSED'

    def __closePassive(self, ackPacket):
        if self.srcCRPPort is None:
            self.socket.close()
            raise CRPException("Socket not bound")


        if self.state != 'ESTABLISHED':
            self.socket.close()
            raise Exception("Connection not established")

        fin_flags = (False, False, False, True, False, False)
        finPacket = CRPacket(
                    srcPort = self.srcCRPPort,
                    desPort = self.desCRPPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = fin_flags,
                    winSize = self.recvWindowSize,
                    )

        self.seqNum += 1
        if self.seqNum > CRPacket.maxSeqNum():
            self.seqNum = 0

        resetsLeft = self.resetLimit()

        isFinAcked = False

        while resetsLeft and (not isFinAcked):
            self.sendto(finPacket.toByteArray(), (self.desAddr, self.desUDPPort))

            try:
                data, address = self.recvfrom(self.recvWindowSize)
                packet = self.__reconstructPacket(data)

                if not packet:
                    resetsLeft -= 1
            except socket.timeout:
                resetsLeft -= 1
                continue
            else:
                if (packet.isAck() and packet.header['ackNum'] == self.seqNum):
                    isFinAcked = True

                if (packet.isFin()):
                    ack_flags = (False, False, False, True, False, False)
                    finPacket = CRPacket(
                                srcPort = self.srcCRPPort,
                                desPort = self.desCRPPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = fin_flags,
                                winSize = self.recvWindowSize,
                                )

                    self.sendto(finPacket.toByteArray(), (self.desAddr, self.desUDPPort))

        self.socket.close()
        self = CRPSocket(self.srcCRPPort, self.debug)
        self.state = 'CLOSED'


    def __sendReq(self):

        #create packet
        self.log("Creating req packet......\n")

        try:
            self.log("Setting flags...\n")
            flags = (True, False, False, False, False, False)
        except Exception as e:
            self.log("Exception: " + str(e))
            sys.exit(0)
        self.log("Flags created...\n")

        try:
            reqPacket = CRPacket.getReq(
                        srcPort = self.srcCRPPort,
                        desPort = self.desCRPPort,
                        seqNum = self.seqNum,
                        ackNum = self.ackNum,
                        winSize = self.recvWindowSize,
                        )
        except Exception as e:
            self.log("Exception: " + str(e))
            sys.exit(0)

        #increment seq num
        self.log("Incrementing sequence number......\n")
        self.seqNum = self.seqNum + 1 #increment by number of bytes (20 byte header only)
        if self.seqNum > CRPacket.maxSeqNum():
            self.seqNum = 0

        #transfer packet
        resetsLeft = self.resetLimit
        self.log("entering send loop for REQ packet......\n")
        while resetsLeft:
            self.log("Sending req......\n")
            self.sendto(reqPacket.toByteArray(), (self.desAddr, self.desUDPPort))

            try:
                self.log("waiting for ack......\n")
                data, address = bytearray(self.recvfrom(self.rcvWindowSize))
                packet = self.__reconstructPacket(data = bytearray(data))

                if not packet:
                    self.log("Checksum failed......\n")
                    resetsLeft -= 1
                    continue
            except socket.timeout:
                resetsLeft -= 1
            else:
                if packet.isAck() and packet.header['ackNum'] == self.seqNum:
                    self.log("req has been acked......\n")
                    break
                else:
                    self.log("Wrong packet recieved, restarting req loop......\n")
                    resetsLeft -= 1

        if not resetsLeft:
            self.log("socket timeout......\n")
            raise Exception('socket timeout')

        return packet

    def __sendSync(self):

        #create packet
        self.log("Creating sync packet......\n")
        flags = (False, True, False, False, False, False)
        syncPacket = CRPacket.getSync(
                    srcPort = self.srcCRPPort,
                    desPort = self.desCRPPort,
                    seqNum = self.seqNum,
                    winSize = self.recvWindowSize,
                    )

        #increment seq num
        self.seqNum = self.seqNum + 1 #increment by number of bytes (20 byte header only)
        if self.seqNum > CRPacket.maxSeqNum():
            self.seqNum = 0


        #transfer packet
        resetsLeft = self.resetLimit
        self.log("entering send loop for REQ packet......\n")
        while resetsLeft:
            self.log("Sending req......\n")
            self.sendto(syncPacket.toByteArray(), (self.desAddr, self.desUDPPort))

            try:
                self.log("waiting for ack......\n")
                data, address = bytearray(self.recvfrom(self.rcvWindowSize))
                packet = self.__reconstructPacket(data = bytearray(data))

                if not packet:
                    self.log("Checksum failed......\n")
                    resetsLeft -= 1
                    continue
            except socket.timeout:
                resetsLeft -= 1
            else:
                if packet.isAck() and packet.header['ackNum'] == self.seqNum:
                    self.log("req has been acked......\n")
                    break
                else:
                    self.log("Wrong packet recieved, restarting req loop......\n")
                    resetsLeft -= 1

        if not resetsLeft:
            self.log("socket timeout......\n")
            raise Exception('socket timeout')

        return packet


    def __reconstructPacket(self, data, checkAckNum = False):
        packet = CRPacket.fromByteArray(data)

        if not packet.isValid():
            return None

        if checkAckNum:

			packetAckNum = packet.header['ackNum']

			ackMismatch = (int(packetAckNum) - checkAckNum - 1)

			if packetAckNum and ackMismatch:
				return ackMismatch

        return packet
