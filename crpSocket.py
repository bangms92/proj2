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
        ackData, ackAddress = self.socket.recvfrom(self.receivingWindowSize)
        ackPacket = self._reconstructPacket(bytearray(ackData))
        
        log("self.seqNum is " + str(self.seqNum))
        if ackPacket.isAck() and ackPacket.header['ackNum'] == self.seqNum:
            print "Correct Ack recieved"
            
        #Send SYNC
        self._sendSYNC()
        
        #Established
        self.state = 'ESTABLISHED'

    def listen(self):
        self.state = 'LISTEN'
        
        #Receive REQ
        while True:
            reqData, reqAddress = self.socket.recvfrom(self.receivingWindowSize)
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
        syncData, syncAddress = self.socket.recvfrom(self.receivingWindowSize)
        syncPacket = self._reconstructPacket(bytearray(reqPacket))
        #Established
        state = 'ESTABLISHED'
        
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        