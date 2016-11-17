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
        
        self.sourceCRPPort = sourceCRPPort
        self.destinationCRPPort = None
        
        self.udpDestPort = None
        self.udpSrcPort = None
        
    def SetUDPDestinationPort(self, destPortNum):
        self.udpDestPort = destPortNum
        
    def SetUDPSourcePort(self, srcPortNum):
        self.udpSrcPort = srcPortNum
        
    def bind(self, ipAddres, portNum):
        self.socket.bind(addr)