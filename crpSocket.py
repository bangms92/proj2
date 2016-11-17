import socket
import crpPacket
from crpPacket import import CRPPacket

class CRPSocket:
    def __init__(self, sourceCRPPort):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receivingWindowSize = CRPPacket.maxWindowSize()
        
        self.sourceCRPPort = sourceCRPPort
        
        self.udpDestPort = None
        self.udpSrcPort = None
        
    def SetUDPDestination(self, destPortNum):
        self.udpDestPort = destPortNum
        
    def SetUDPSource(self, srcPortNum):
        self.udpSrcPort = srcPortNum
        
    def bindLocal(self, portNum):
        try:
            if portNum:
                self.socket.