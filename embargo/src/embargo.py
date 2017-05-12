#!/usr/bin/python
import sys
import math
from random import randint

######################################################################

DEBUG         = 0
# L1 params
BLOCK_SIZE    = 32
CACHE_SIZE    = 1024
NUM_BLOCKS    = CACHE_SIZE / BLOCK_SIZE
OFFSET        = int(math.log(BLOCK_SIZE)/math.log(2)) # num offset bits
LRU_BITS      = 4

# LLC params
LLC_BLOCK_SIZE    = 64
LLC_CACHE_SIZE    = 4096
LLC_NUM_BLOCKS    = CACHE_SIZE / BLOCK_SIZE
LLC_OFFSET        = int(math.log(BLOCK_SIZE)/math.log(2)) # num offset bits
LLC_LRU_BITS      = 4

# General system params
ADDR_BITS     = 64
TAG_INDEX     = 0
VALID_INDEX   = 1
LRU_INDEX     = 2

######################################################################

# Assuming fully associative cache
# Assuming 64-bit address space
# So, size of tag and offset?
# Assume 64B block -> log2(64) = 6 bit offset
# 63:6 are for tag. 5:0 are offset.

def embargo(aTrace):
    print '================================'
    print '$ Parameters:'
    print 'BLOCK_SIZE = '+str(BLOCK_SIZE)
    print 'CACHE_SIZE = '+str(CACHE_SIZE)
    print 'NUM_BLOCKS = '+str(NUM_BLOCKS)
    print 'ADDR_BITS  = '+str(ADDR_BITS)
    print 'OFFSET     = '+str(OFFSET)
    print 'LLC_BLOCK_SIZE = '+str(LLC_BLOCK_SIZE)
    print 'LLC_CACHE_SIZE = '+str(LLC_CACHE_SIZE)
    print 'LLC_NUM_BLOCKS = '+str(LLC_NUM_BLOCKS)
    print 'LLC_OFFSET     = '+str(LLC_OFFSET)
    print '================================'

  
    # General dumb algorithm:
    # 0) Get address
    # 1) Check for $ hit.
    #    a. For each block, see if address fits in block
    # 2) If hit, great. Update statistics.
    # 3) If miss, crap. Evict based on LRU.
    l1 = l1Cache()
    l2 = l2Cache()

    fhandle = open(aTrace)
    counter = 0
    processA = True
    for line in fhandle:
        if counter % 100000 == 0:
            processA = not processA
            pass
        counter = counter + 1
        address = int(line, 16)

        hit = l1.query(address)
        if not hit:
            l2.query(address, processA)
            pass
        pass

# Used for initial bring-up/debugging
#    for index in range(500):
#        if DEBUG:
#            print 'Address: '+str(index)
#            pass
#        address = randint(0, 200000)
#        hit = l1.query(address)
#        if not hit:
#            l2.query(address)
#            pass
#        pass


    l1.dumpCacheState()
    l2.dumpCacheState()
    l1.dumpStats()
    l2.dumpStats()

    pass

class l1Cache:
    # $ info:
    # [tag, valid, num_hits] * number of blocks
    cache     = [[0,False,0] for x in xrange(NUM_BLOCKS)]
    numAccess = 0
    numHit    = 0
    numMiss   = 0

    def dumpStats(self):
        print '===================================='
        print 'Dumping stats of instance '+self.__class__.__name__
        print 'numAccess: '+str(self.numAccess)
        print 'numHit: '+str(self.numHit)
        print 'numMiss: '+str(self.numMiss)
        print 'Hit Rate: '+str((float(self.numHit)/self.numAccess)*100)+'%'
        print '===================================='
        pass

    def dumpCacheState(self):
        print '================================'
        print 'Dumping cache state...'
        print self.cache
        print '================================'
        pass

    def calcTag(self, address):
        return address >> OFFSET
        pass

    def query(self, address):
        self.numAccess = self.numAccess + 1

        reqTag = self.calcTag(address)
        
        foundHit = False
        hitIndex = -1
        for index in range(len(self.cache)):
            if self.cache[index][TAG_INDEX] == reqTag and self.cache[index][VALID_INDEX]:
                # We got a hit!
                foundHit = True
                hitIndex = index
                pass
            elif self.cache[index][VALID_INDEX]:
                # If miss, index LRU value. Keep capped at num bits we set. Higher -> less used.
                self.cache[index][LRU_INDEX] = min(2**LRU_BITS, self.cache[index][LRU_INDEX] + 1)
                pass
            pass

        if foundHit:
            assert(hitIndex != -1)
            self.serviceHit(hitIndex)
            pass
        else:
            self.serviceMiss(reqTag)
            pass
        return foundHit
        pass

    def serviceHit(self, hitIndex):
        self.numHit = self.numHit + 1
        # Reset LRU
        self.cache[hitIndex][LRU_INDEX] = 0
        pass

    def serviceMiss(self, tag):
        self.numMiss = self.numMiss + 1
        # If there are available blocks, allocate
        # Else evict according to LRU policy
        foundAvailableBlock = self.allocBlock(tag)

        if foundAvailableBlock == False:
            # Cache is full, need to evict
            self.doEvict()
            foundAvailableBlock = self.allocBlock(tag)
            assert(foundAvailableBlock) # evicted, but still not free block?
            pass
        pass

    def allocBlock(self, tag):
        foundAvailableBlock = False
        for index in range(len(self.cache)):
            if self.cache[index][VALID_INDEX] == False:
                # Allocate!
                self.cache[index][VALID_INDEX] = True
                self.cache[index][TAG_INDEX]   = tag
                self.cache[index][LRU_INDEX]   = 0
                foundAvailableBlock = True
                break
                pass
            pass
        # Function is time-consuming.
        # To compromise, only check like 5% of the time.
        if randint(0, 100) > 95:
            self.checkAllValidTagsUnique()
        return foundAvailableBlock
        pass

    def checkAllValidTagsUnique(self):
        # Sanity check: make sure all tags are unique between valid blocks
        validTags = []
        for index in range(len(self.cache)):
            if self.cache[index][VALID_INDEX]:
                validTags.append(self.cache[index][TAG_INDEX])
                pass
            pass
        if len(validTags) != len(set(validTags)):
            self.dumpCacheState()
            pass
        assert(len(validTags) == len(set(validTags))) # Tags in all valid blocks should be unique
        pass

    # Do some stupid LRU method
    def doEvict(self):
        minLru = -1
        evictIndex = -1

        # Should only do evict if everything is full
        for index in range(len(self.cache)):
            if self.cache[index][VALID_INDEX] == False:
                assert(0) # Trying to evict something despite a block being available?
                pass
            pass

        for index in range(len(self.cache)):
            # Find largest LRU value. That is least used, so evict.
            if self.cache[index][LRU_INDEX] > minLru and self.cache[index][VALID_INDEX]:
                evictIndex = index
                minLru = self.cache[index][LRU_INDEX]
                pass
            pass
        assert(minLru != -1)
        assert(evictIndex != -1)

        # Found block to evict. Now evict it.
        self.cache[evictIndex][VALID_INDEX] = 0
        pass

    def getCache(self):
        return self.cache
    pass

class l2Cache(l1Cache):
    # Add L2-specific paramters...
    cache     = [[0,False,0] for x in xrange(LLC_NUM_BLOCKS)]

    # Do some stupid LRU method
    # Currently from L1. Update for MRU or something.
    # Do some stupid LRU method
    def doEvict(self):
        minLru = -1
        evictIndex = -1

        # Should only do evict if everything is full
        for index in range(len(self.cache)):
            if self.cache[index][VALID_INDEX] == False:
                assert(0) # Trying to evict something despite a block being available?
                pass
            pass

        for index in range(len(self.cache)):
            # Find largest LRU value. That is least used, so evict.
            if self.cache[index][LRU_INDEX] > minLru and self.cache[index][VALID_INDEX]:
                evictIndex = index
                minLru = self.cache[index][LRU_INDEX]
                pass
            pass
        assert(minLru != -1)
        assert(evictIndex != -1)

        # Found block to evict. Now evict it.
        self.cache[evictIndex][VALID_INDEX] = 0
        pass

    # Currently from L1. Update to do like MRU
    def allocBlock(self, tag, processA):
        foundAvailableBlock = False
        for index in range(len(self.cache)):
            if self.cache[index][VALID_INDEX] == False:
                # Allocate!
                self.cache[index][VALID_INDEX] = True
                self.cache[index][TAG_INDEX]   = tag
                if processA:
                    self.cache[index][LRU_INDEX]   = 0
                    pass
                else:
                    if randint(0, 100) > 50:
                        self.cache[index][LRU_INDEX]   = (2**LLC_LRU_BITS)*0.50
                        pass
                    else:
                        self.cache[index][LRU_INDEX]   = 0
                        pass
                    pass
                foundAvailableBlock = True
                break
                pass
            pass
        # Function is time-consuming.
        # To compromise, only check like 5% of the time.
        if randint(0, 100) > 95:
            self.checkAllValidTagsUnique()
        return foundAvailableBlock
        pass

    def query(self, address, processA):
        self.numAccess = self.numAccess + 1

        reqTag = self.calcTag(address)
        
        foundHit = False
        hitIndex = -1
        for index in range(len(self.cache)):
            if self.cache[index][TAG_INDEX] == reqTag and self.cache[index][VALID_INDEX]:
                # We got a hit!
                foundHit = True
                hitIndex = index
                pass
            elif self.cache[index][VALID_INDEX]:
                # If miss, index LRU value. Keep capped at num bits we set. Higher -> less used.
                self.cache[index][LRU_INDEX] = min(2**LRU_BITS, self.cache[index][LRU_INDEX] + 1)
                pass
            pass

        if foundHit:
            assert(hitIndex != -1)
            self.serviceHit(hitIndex)
            pass
        else:
            self.serviceMiss(reqTag, processA)
            pass
        return foundHit
        pass

    def serviceMiss(self, tag, processA):
        self.numMiss = self.numMiss + 1
        # If there are available blocks, allocate
        # Else evict according to LRU policy
        foundAvailableBlock = self.allocBlock(tag, processA)

        if foundAvailableBlock == False:
            # Cache is full, need to evict
            self.doEvict()
            foundAvailableBlock = self.allocBlock(tag, processA)
            assert(foundAvailableBlock) # evicted, but still not free block?
            pass
        pass

    pass


#####################################################
# Main function, call the beast.
if __name__ == "__main__":
    # Call function, passing file name in.
    embargo(sys.argv[1])
    pass
