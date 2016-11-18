import sys
import socket
import struct
import ctypes
import math

DEBUG = True

def log(message):
    if DEBUG:
        print message

class CRPPacket:
    global uint16
    global uint32
    global uint8

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
    
    global HEADER_FIELDS
    HEADER_FIELDS = (
                    ('srcPort', uint16, 2),
                    ('desPort', uint16, 2),
                    ('seqNum', uint32, 4),
                    ('ackNum', uint32, 4),
                    ('flagList', uint16, 4),
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
            log("Unpicked " + fieldName + " Value is " + str(value))
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
        log("converting to ByteArray")
        packet = bytearray()
        packet.extend(self.__pickleHeader())
        log("Header added to Packet")
        if self.data != 0:
            packet.extend(self.data)
            log("data added to the packet")
        return packet
    
    #converts the header to a length 20 bytearray
    def __pickleHeader(self):
        log("Packing header to the packet")
        byteArray = bytearray()

        for (fieldName, dataType, size) in HEADER_FIELDS:
            log("crpPacket __pickleHeader: fieldName " + fieldName)
            value = self.header[fieldName]

            if (fieldName != 'flagList'):
                byteArray.extend(bytearray(dataType(value)))
            else:
                byteArray.extend(self.__pickleFlags())
            log("After Packet " + fieldName + " length is " + str(len(byteArray)))
        return byteArray
    
    def __pickleFlags(self):
        value = 0
        flags = self.header['flagList']
        if flags[3] == True:
            value = value | 0x1
        if flags[2] == True:
            value = value | (0x1 << 1)
        if flags[1] == True:
            value = value | (0x1 << 2)
        if flags[0] == True:
            value = value | (0x1 << 3)
        return bytearray(uint16(value))
    
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
    
    def __init__(self, srcPort = 99, desPort = 99, seqNum = 0, ackNum = 0, flagList = (False, False, False, False), winSize = MAX_WINDOW_SIZE, data = None):
        self.header = {}

        if srcPort:
            self.header['srcPort'] = srcPort
        if desPort:
            self.header['desPort'] = desPort

        if seqNum > MAX_SEQUENCE_NUM:
            self.header['seqNum'] = seqNum - MAX_SEQUENCE_NUM #Restart the sequence numbers??
        else:
            self.header['seqNum'] = seqNum

        if ackNum > MAX_ACK_NUM:
            self.header['ackNum'] = ackNum - MAX_ACK_NUM
        else:
            self.header['ackNum'] = ackNum

        if flagList:
            self.header['flagList'] = flagList

        if winSize > MAX_WINDOW_SIZE:
            self.header['winSize'] = MAX_WINDOW_SIZE
        else:
            self.header['winSize'] = winSize

        if data:
            self.data = bytearray(data)
        else:
            self.data = 0

        self.header['checksum'] = self._computeChecksum()

    def _computeChecksum(self):
        log("Computing checksum...\n")
        self.header['checksum'] = 0

        log("Converting packet to byteArray...\n")
        packet = str(self.toByteArray())
        log("Packet converted to byteArray...\n")
        log("Length of the packet is " + str(len(packet)))
        sum = 0
        for i in range(0, len(packet), 2):
            log(str(i) + '\n')
            #16 bit carry-around addition
            value = ord(packet[i]) + (ord(packet[i + 1]) << 8)
            temp = sum + value
            sum = (temp & 0xffff) + (temp >> 16)

        return ~sum & 0xffff #16-bit one's complement