import ctypes
import sys
import socket
import math
import struct
import random
from functools import reduce

DEBUG = True

def log(message):
    if DEBUG:
        print message

class CRPacket:

    uint16 = ctypes.c_uint16
    uint32 = ctypes.c_uint32

    # Global decs
    global MAX_SEQUENCE_NUM
    global MAX_ACK_NUM
    global MAX_WINDOW_SIZE
    global HEADER_LENGTH
    global DATA_LEN
    global HEADER_FIELDS


    # based on bit count for each value
    MAX_SEQUENCE_NUM = int(math.pow(2, 32) - 1)
    MAX_ACK_NUM = int(math.pow(2, 32) - 1)
    MAX_WINDOW_SIZE = int(math.pow(2, 16) - 1)
    HEADER_LENGTH = 20 # number of bytes in header
    DATA_LEN = 1004

    # assign size to each header field
    HEADER_FIELDS = (
                    ('srcPort', uint16, 2),
                    ('desPort', uint16, 2),
                    ('seqNum', uint32, 4),
                    ('ackNum', uint32, 4),
                    ('flags', uint32, 4),
                    ('winSize', uint16, 2),
                    ('checksum', uint16, 2)
                    )

    # static methods
    @staticmethod
    def maxSeqNum():
        log("Returning max sequence number...\n")
        return MAX_SEQUENCE_NUM

    @staticmethod
    def maxAckNum():
        log("Returning max ack number...\n")
        return MAX_ACK_NUM

    @staticmethod
    def maxWinSize():
        log("Returning max window size...\n")
        return MAX_WINDOW_SIZE

    @staticmethod
    def getHeaderLeangth():
        log("Returning header length...\n")
        return HEADER_LENGTH

    @staticmethod
    def getDataLength():
        log("Returning data length...\n")
        return DATA_LEN

    # Returns a simple REQ packet.
    @staticmethod
    def getReq(srcPort, desPort, seqNum, ackNum, winSize):
        log("Returning an REQ packet...\n")
        return CRPacket(srcPort, desPort, seqNum, ackNum, (True, False, False, False), winSize)

    # Returns a simple SYNC packet.
    @staticmethod
    def getSync(srcPort, desPort, seqNum, ackNum, winSize):
        log("Returning a SYNC packet...\n")
        return CRPacket(srcPort, desPort, seqNum, ackNum, (False, True, False, False), winSize)


    # returns an CRPacket given a byteArray as an input
    @staticmethod
    def fromByteArray(byteArray):
        log("Creating an empty CRPacket in fromByteArray...\n")
        p = CRPacket()
        log("Unpicking byteArray to packet...\n")
        p.__unpickle(byteArray)
        log("Returning unpickled packet...\n")
        return p
    # end static methods

    # constructor
    def __req__(self, srcPort = 0, desPort = 0, seqNum = 0, ackNum = 0, flagList = None, winSize = MAX_WINDOW_SIZE, data = None):
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

        self.header['checksum'] = self.__computeChecksum()

    # instance methods

    # checks if the internet checksum provided is equal to what is
    # calculated on this side
    def isValid(self):
        givenChecksum = self.header['checksum']
        calculatedChecksum = self.__computeChecksum()
        return givenChecksum == calculatedChecksum

    # checks if it is an req packet
    def isReq(self):
        return header['flags'][0]

    def isSync(self):
        return header['flags'][1]

    def isAck(self):
        return header['flags'][2]

    def isFin(self):
        return header['flags'][3]

    def isEndOfMessage(self):
        return header['flags'][5]

    def toByteArray(self):
        packet = bytearray()
        log("Pickling header.....\n")
        packet.extend(self.__pickleHeader())
        log("Done pickling header.....\n")
        if self.data:
            log("adding data.....\n")
            packet.extend(self.data)
            log("done adding data.....\n")
        return packet


    # http://stackoverflow.com/a/1769267
    def __computeChecksum(self):
        log("Computing checksum...\n")
        self.header['checksum'] = 0

        log("Converting packet to byteArray...\n")
        packet = str(self.toByteArray())
        log("Packet converted to byteArray...\n")

        sum = 0
        for i in range(0, len(packet), 2):

            #16 bit carry-around addition
            value = ord(packet[i]) + (ord(packet[i + 1]) << 8)
            temp = sum + value
            sum = (temp & 0xffff) + (temp >> 16)

        return ~sum & 0xffff #16-bit one's complement

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
        isReq = ((value & 0x1) == 1)
        isSync = (((value & 0x2) >> 1) == 1)
        isAck = (((value & 0x4) >> 2) == 1)
        isFin = (((value & 0x8) >> 3) == 1)
        isNM = (((value & 0x16) >> 4) == 1)
        isEOM = (((value & 0x32) >> 5) == 1)
        return (isReq, isSync, isAck, isFin)

    #converts the header to a length 20 bytearray
    def __pickleHeader(self):
        byteArray = bytearray()

        for (fieldName, dataType, size) in HEADER_FIELDS:
            log("pickling header field " + fieldName + "....\n")
            value = self.header[fieldName]

            if (fieldName != 'flags'):
                log("pickling flags")
                byteArray.extend(bytearray(dataType(value)))
            else:
                byteArray.extend(self.__pickleFlags())

        return byteArray

    #converts a flag list to a length 4 bytearray
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
        if flags[4] == True:
            value = value | (0x1 << 4)
        if flags[5] == True:
            value = value | (0x1 << 5)
        return bytearray(uint32(value))

    #end instance methods
