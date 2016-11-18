import socket
import crpPacket
from crpPacket import import CRPPacket

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
        
    def bind(self, addr):
        self.socket.bind(addr)
        
    def connect(self, ipAddress, portNum):
        self.destAddr = ipAddress
        self.udpDestPort = portNum
        
        #Send REQ
        self._sendREQ()
        
        #Receive ACK
        #Send SYNC
        #Established
        
    def listen(self):
        #Receive REQ
        while True:
            rcData, address = self.socket.recvFrom(self.receivingWindowSize)
            rcPacket = self._reconstructPacket(bytearray(rcData))
            break
        
        #Send ACK
        self.ackNum = rcPacket.header['seqNum'] + 1
        #Receive SYNC
        #Established
            
    def _sendREQ(self):
        reqPacket = CRPPacket.getREQ(self.udpSrcPort, self.udpDestPort, self.seqNum, self.ackNum, self.receivingWindowSize)
        
        self.seqNum = self.seqNum + 1 #Increment sequence number
        self.socket.sendto(reqPacket, (self.destAddr self.udpDestPort))
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        