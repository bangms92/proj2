import sys
import socket
import struct
import ctypes
import math

class CRPPacket:
    uint16 = ctypes.c_uint16
    uint32 = ctypes.c_uint32
    uint4 = ctypes.c_uint8
    
    global MAX_SEQUENCE_NUM
    global MAX_ACK_NUM
    global MAX_WINDOW_SIZE
    global HEADER_LENGTH
    
    MAX_SEQUENCE_NUM = int(math.pow(2, 32) - 1) #32 bits
    MAX_ACK_NUM = int(math.pow(2, 32) - 1) #32 bits
    MAX_WINDOW_SIZE = int(math.pow(2, 16) - 1) #16 bits
    
    HEADER_LENGTH = 16 #16 Bytes
    
    HEADER_FIELDS = (
                    ('srcPort', uint16, 2),
                    ('desPort', uint16, 2),
                    ('seqNum', uint32, 4),
                    ('ackNum', uint32, 4),
                    ('flags', c_uint8, 1),
                    ('winSize', uint16, 2),
                    ('checksum', uint16, 2)
                    )
    
    @staticmethod
    def maxSeqNum():
        return MAX_SEQUENCE_NUM

    @staticmethod
    def maxAckNum():
        return MAX_ACK_NUM

    @staticmethod
    def maxWindowSize():
        return MAX_WINDOW_SIZE

    @staticmethod
    def getHeaderLeangth():
        return HEADER_LENGTH

    # Returns a simple INIT packet.
    @staticmethod
    def getInit(srcPort, desPort, seqNum, ackNum, winSize):
        return CRPPacket(srcPort, desPort, seqNum, ackNum, (True, False, False, False), winSize)

    # Returns a simple CNCT packet.
    @staticmethod
    def getCnct(srcPort, desPort, seqNum, ackNum, winSize):
        return CRPPacket(srcPort, desPort, seqNum, ackNum, (False, True, False, False), winSize)
    
    def __init__(self, srcPort = 0, desPort = 0, seqNum = 0, ackNum = 0, flagList = None, winSize = MAX_WINDOW_SIZE, data = None):
        self.header = {}

        if srcPort:
            self.header['srcPort'] = srcPort
        if desPort:
            self.header['desPort'] = desPort

        if seqNum:
            self.header['seqNum'] = seqNum

        if ackNum:
            self.header['ackNum'] = ackNum

        if flagList:
            self.header['flagList'] = flagList

        if winSize > MAX_WINDOW_SIZE:
            self.header['winSize'] = MAX_WINDOW_SIZE
        else:
            self.header['winSize'] = winSize

        if data:
            self.data = bytearray(data)

        self.header['checksum'] = self.__computeChecksum()