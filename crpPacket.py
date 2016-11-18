import sys
import socket
import struct
import ctypes
import math

class CRPPacket:
    uint16 = ctypes.c_uint16
    uint32 = ctypes.c_uint32
    uint8 = ctypes.c_uint8
    
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
                    ('flags', uint8, 1),
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
    
    # returns an crpPacket given a byteArray as an input
    @staticmethod
    def fromByteArray(byteArray):
        p = CRPPacket()
        p.__unpickle(byteArray)
        return p
    
    #adds byteArray to object
    def __unpickle(self, byteArray):
        if byteArray:
            headerBytes = byteArray[0 : HEADER_LENGTH]
            self.__unpickleHeader(headerBytes)

            if (len(byteArray) != HEADER_LENGTH):
                dataBytes = byteArray[HEADER_LENGTH : ]
            else:
                dataBytes = None
            self.data = dataBytes

    def __unpickleHeader(self, headerBytes):
        base = 0
        #for each header field, get values
        for (fieldName, dataType, size) in HEADER_FIELDS:
            # Get the bytes from byteArray, convert to int
            bytes = headerBytes[base : base + size]
            value = dataType.from_buffer(bytes).value

            #add specific field, done differently for flags
            if (fieldName == 'flags'):
                value = self.__unpickleFlags(value)

            #add value to header
            self.header[fieldName] = value

            # increment base
            base = base + size
            
    def __unpickleFlags(self, value):
        # checks if each individual bit is present
        isInit = ((value & 0x1) == 1)
        isCnct = (((value & 0x2) >> 1) == 1)
        isAck = (((value & 0x4) >> 2) == 1)
        isFin = (((value & 0x8) >> 3) == 1)
        return (isInit, isCnct, isAck, isFin)
    
    def toByteArray(self):
        packet = bytearray()
        packet.extend(self.__pickleHeader())
        if self.data:
            packet.extend(self.data)
        return packet
    
    
    
    #converts the header to a length 20 bytearray
    def __pickleHeader(self):
        byteArray = bytearray()

        for (fieldName, dataType, size) in HEADER_FIELDS:
            value = self.header[fieldName]

            if (fieldName != 'flags'):
                byteArray.extend(bytearray(dataType(value)))
            else:
                byteArray.extend(self.__pickleFlags())

        return byteArray
    
    def __pickleFlags(self):
        value = 0
        flags = self.header['flags']
        if flags[0] == True:
            value = value | 0x1
        if flags[1] == True:
            value = value | (0x1 << 1)
        if flags[2] == True:
            value = value | (0x1 << 2)
        if flags[3] == True:
            value = value | (0x1 << 3)
        return bytearray(uint8(value))
    
    # Returns a simple REQ packet.
    @staticmethod
    def getREQ(srcPort, desPort, seqNum, ackNum, winSize):
        return CRPPacket(srcPort, desPort, seqNum, ackNum, (False, False, False, True), winSize)

    # Returns a simple SYNC packet.
    @staticmethod
    def getSYNC(srcPort, desPort, seqNum, ackNum, winSize):
        return CRPPacket(srcPort, desPort, seqNum, ackNum, (False, False, True, False), winSize)
    
    def isInit(self):
        return header['flags'][3]

    def isCnct(self):
        return header['flags'][2]

    def isAck(self):
        return header['flags'][1]

    def isFin(self):
        return header['flags'][0]
    
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