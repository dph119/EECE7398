#!/usr/bin/python

import sys
import matplotlib
matplotlib.use('agg')
import pylab as plt

#################################
#
# Parse address trace
# and figure out working
# set over time.
# Written to parse the output of
# "pinatrace" Pin tool.
#
#################################

INSTRUCTION_WINDOW = 10000
BLOCK_SIZE_BYTES = [16] # Must be list

def deriveWorkingSet(fileName):
    print 'File name: '+fileName

    plt.figure
    plt.hold(True)
    plt.xlabel('Time Slice Index')
    plt.ylabel('# Unique Blocks Accessed')
    plt.title('Evolution of Number of Unique Block Sizes Accessed for cp Command')

    for blockSize in BLOCK_SIZE_BYTES:
        fhandle = open(fileName, 'r')
        memoryAccesses = []
        for line in fhandle:
            # Skip commented out lines
            if line.startswith('#'):
                continue
            line = line.strip()
            line = line.split(' ') 
            lineValues = []
            for element in line:
                if element != '':
                    lineValues.append(element)
                    pass
                pass
        
            # Line will now be of this format:
            # ['0x387440fc3e:', 'R', '0x7f8330508b20', '8', '0']
            # We care about element 2 (i.e. the memory access).
            memoryAccesses.append(lineValues[2])
            pass

        uniqueBlocksAccessed = []
        # We now have all of the memory accesses for each instruction.
        # Walk at the specified instruction granularity
        # Carve out the slices we will be working on.
        endOfList = False
        sliceCount = 0
        print 'Size of memoryAccesses = '+str(len(memoryAccesses))
        print 'Total slices = '+str(len(memoryAccesses)/INSTRUCTION_WINDOW)
        while (endOfList == False):
            if (sliceCount + 1) * INSTRUCTION_WINDOW > len(memoryAccesses):
                endOfList = True
                sliceOfAddresses = memoryAccesses[sliceCount*INSTRUCTION_WINDOW:-1]     
                pass
            else:
                sliceOfAddresses = memoryAccesses[sliceCount*INSTRUCTION_WINDOW:(sliceCount+1)*INSTRUCTION_WINDOW]     
                pass
            sliceCount = sliceCount + 1

            # Convert hex values to int
            for index in range(len(sliceOfAddresses)):
                sliceOfAddresses[index] = int(sliceOfAddresses[index], 16)
                pass
            maxVal = max(sliceOfAddresses)
            minVal = min(sliceOfAddresses)
            
            blockIndex = {}
            # Use a dictionary. We know minimum address. Calculate offset,
            # divide by block size to get index value (which will be a key)
            # If key exists, increment total in value. Else create key/value
            # pair and initialize value to 1 since it's first access.
            # Number of keys will be number of unique blocks.
            for address in sliceOfAddresses:
                addressOffset = address - minVal

                assert(addressOffset > -1)
                addressIndex = addressOffset / blockSize
                if addressIndex in blockIndex:
                    blockIndex[addressIndex] = blockIndex[addressIndex] + 1
                    pass
                else:
                    blockIndex[addressIndex] = 1
                    pass
                pass
            # Finished processing slice. 
            uniqueBlocksAccessed.append(len(blockIndex.keys()))
            pass
        print 'Stopped after sliceCount = '+str(sliceCount)
            
        print uniqueBlocksAccessed

        x_series = range(len(uniqueBlocksAccessed))
        y_series = uniqueBlocksAccessed
        plt.plot(x_series, y_series, label=str(blockSize)+'B block size')
        fhandle.close()
        pass
    plt.legend(loc='upper right')
    plt.savefig('working_set_'+str(BLOCK_SIZE_BYTES)+'_window_size_'+str(INSTRUCTION_WINDOW)+'.png')
    pass

if __name__ == "__main__":
    # Call function, passing file name in.
    deriveWorkingSet(sys.argv[1])
    pass

