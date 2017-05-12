#!/usr/bin/python

import sys

GRANULARITY = 100000

def interleaveAddresses(fileA, fileB, outputName):
    fhandleA = open(fileA, 'r')
    fhandleB = open(fileB, 'r')

    addressesA = []
    addressesB = []
    # Extract the data, put into a set. Each entry is an address.
    for line in fhandleA:
        if not line.startswith('#'):
            line = line.strip()
            addressesA.append(line[:line.find(':')])
        pass

    for line in fhandleB:
        if not line.startswith('#'):
            line = line.strip()
            addressesB.append(line[:line.find(':')])
        pass

    fhandleA.close()
    fhandleB.close()

    ###############################################
    # Have the lists of addresses. Now interleave.
    # Kludgey mess and I don't care.
    counter = 0 # inf loop counter
    pullFromA = False
    finalList = []
    while True:
        print counter
        print 'Len of A: '+str(len(addressesA))
        print 'Len of B: '+str(len(addressesB))
        if len(addressesA) == 0 and len(addressesB) == 0:
            break
        elif len(addressesA) == 0:
            pullFromA = False
            pass
        elif len(addressesB) == 0:
            pullFromA = True
            pass
        else:
            pullFromA = not pullFromA
            pass

        if pullFromA:
            # kludge fix off-by-one issue in the else
            if len(addressesA) == 1:
                finalList.append([addressesA[0]])
                del addressesA[0]
                pass
            else:
                finalList.append(addressesA[0:min(GRANULARITY, len(addressesA))])
                del addressesA[0:min(GRANULARITY-1, len(addressesA)-1)]
                pass
            pass
        else:
            # kludge fix off-by-one issue in the else
            if len(addressesB) == 1:
                finalList.append([addressesB[0]])
                del addressesB[0]
                pass
            else:
                finalList.append(addressesB[0:min(GRANULARITY, len(addressesB))])
                del addressesB[0:min(GRANULARITY-1, len(addressesB)-1)]
                pass
            pass
        
        counter = counter + GRANULARITY
        if counter > 100000000:
            print 'Len of A: '+str(len(addressesA))
            print 'Len of B: '+str(len(addressesB))            
            print 'pullFromA:'+str(pullFromA)
            assert(0) # probably infinite loop
        pass

    ####################################
    # Write out this garbage
    fhandleFinal = open(outputName, 'w')

    for entry in finalList:
        for address in entry:
            fhandleFinal.write(str(address)+'\n')
            pass
        pass
    
    fhandleFinal.close()
    pass

#####################################################
# Main function, call the beast.
if __name__ == "__main__":
    # Call function, passing file name in.
    interleaveAddresses(sys.argv[1], sys.argv[2], sys.argv[3])
    pass
