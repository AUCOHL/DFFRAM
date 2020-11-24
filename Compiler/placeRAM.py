import opendbpy as odb
import math
import os 
import pprint

tapCounter = 0

# A function to place a tap cell at a given point on a row
def createTapCell(currnetRow, startingPoint):

    global tapCounter
    tapCounter = tapCounter + 1
    # create tapCell
    currentTapCell = odb.dbInst_create(block, tapCell, "tap_cell_" + str(tapCounter))
    

    rowOrientation = currnetRow.getOrient()
    currentTapCell.setOrient(rowOrientation)
    currentTapCell.setLocation(startingPoint[0], startingPoint[1])
    currentTapCell.setPlacementStatus("PLACED")
    startingPoint[0] = startingPoint[0] + siteWidth * math.ceil(currentTapCell.getMaster().getWidth() / siteWidth )

    return startingPoint


# A function that places the cells representing the words in a cluster
# These cells will be placed on 16 rows where each row would have: 8 flipflops, 
# 8 tristate buffers, an inverter and 1 or 2 AND gates
def placeWordsInCluster(words, currentRowIndex, clusterNumber):


    for i in range(16):

        wordIdentifier = "WORD\[" + str(i) + "\]"
        currentRow = rows[currentRowIndex]
        rowOrigin = currentRow.getOrigin()
        rowOrientation = currentRow.getOrient()
        currentPoint = rowOrigin

        currentPoint = placeWord(words[wordIdentifier], currentRowIndex, currentPoint)

        level0 = 2 * clusterNumber + int(i / 8)
        level1 = i % 8
        decoder0Identifier = "DEC.DEC_L0.AND" + str(level0) 
        decoder1Identifier = "DEC.DEC_L1\[" + str(level0) + "\].U.AND" + str(level1)

        # check if 1 or 2 buffers will be placed in this row:
        if i % 8 == 0:
            decoder0Name = ".".join(decoders[decoder0Identifier])
            decoder1Name = ".".join(decoders[decoder1Identifier])

            decoderInstanceNames = [decoder1Name, decoder0Name]
            for decoderName in decoderInstanceNames:

                currentInstance = block.findInst(decoderName)
                currentInstance.setOrient(rowOrientation)
                currentInstance.setLocation(currentPoint[0], currentPoint[1])
                currentInstance.setPlacementStatus("PLACED")

                currentPoint[0] = currentPoint[0] + siteWidth * math.ceil(currentInstance.getMaster().getWidth() / siteWidth )

        # place 1 AND gate for decoder
        else:
            decoder1Name = ".".join(decoders[decoder1Identifier])

            decoderInstanceNames = [decoder1Name]
            for decoderName in decoderInstanceNames:

                currentInstance = block.findInst(decoderName)
                currentInstance.setOrient(rowOrientation)
                currentInstance.setLocation(currentPoint[0], currentPoint[1])
                currentInstance.setPlacementStatus("PLACED")


                currentPoint[0] = currentPoint[0] + siteWidth * math.ceil(currentInstance.getMaster().getWidth() / siteWidth )

        currentRowIndex = currentRowIndex + 1
    return currentRowIndex


# A function that takes a list of cells and places them on a row next to one another
# This is used for 2 tasks:
#       1- Place the buffers required for each cluster
#       2- Place all the remaining cells that are not part of a single cluster.
def placeBuffers(listOfBuffers, currentRowIndex):
 
    row = rows[currentRowIndex]
    rowOrigin = row.getOrigin()
    rowOrientation = row.getOrient()

    currentPoint = rowOrigin

    rowOrientation = row.getOrient()
    for i in range(len(listOfBuffers)):

        if(i%9 == 0) and (currentRowIndex % 2 == 0):
            currentPoint = createTapCell(row, currentPoint)

        if(i%9 == 1) and (currentRowIndex % 2 == 1):
            currentPoint = createTapCell(row, currentPoint)
        bufferInstance = listOfBuffers[i]
        currentInstance = block.findInst(bufferInstance)
        currentInstance.setOrient(rowOrientation)
        currentInstance.setLocation(currentPoint[0], currentPoint[1])
        currentInstance.setPlacementStatus("PLACED")
        currentPoint[0] = currentPoint[0] + siteWidth * math.ceil(currentInstance.getMaster().getWidth() / siteWidth)


# A function that places a cluster given its number
def placeCluster(clusterNumber, currentRowIndex):
    
    clusterName = 'C' + str(clusterNumber)
    cluster = clusters[clusterName]
    buffersList = []

    buffersList.append(".".join(cluster['clkbufs'][0]))
    for buf in cluster['dibufs']:
        buffersList.append(".".join(buf))
    for buf in cluster['webufs']:
        buffersList.append(".".join(buf))

    placeBuffers(buffersList, currentRowIndex)

    currentRowIndex = placeWordsInCluster(cluster['words'], currentRowIndex + 1, clusterNumber)

    return currentRowIndex

# A function that places all cells in a word given a list of the cells in the word
# It firstly splits the word into 4 bytes and then places them in sequence
def placeWord(word, currentRowIndex, currentPoint):

    row = rows[currentRowIndex]
    B0 = [".".join(word[i]) for i in range(len(word)) if word[i][3] == 'B0']
    B1 = [".".join(word[i]) for i in range(len(word)) if word[i][3] == 'B1']
    B2 = [".".join(word[i]) for i in range(len(word)) if word[i][3] == 'B2']
    B3 = [".".join(word[i]) for i in range(len(word)) if word[i][3] == 'B3']

    B0.sort()
    B1.sort()
    B2.sort()
    B3.sort()

    # Define the order of the cells in the word
    order = [-2, -1, -3, 14, 15, 12, 13, 10, 11, 8, 9, 6, 7, 4, 5, 2, 3, 0, 1]
    B0 = [B0[i] for i in order]
    B1 = [B1[i] for i in order]
    B2 = [B2[i] for i in order]
    B3 = [B3[i] for i in order]

    bytesInWord = [B3, B2, B1, B0]

    rowOrientation = row.getOrient()

    for byte in bytesInWord:   
        for i in range(len(byte)):
            # These 2 IF statements are used to place tap cells every 2 consecutive cells while
            # trying to prevent tap cells in consecutive rows from touching one another.
            if(i%2 == 0) and (currentRowIndex % 2 == 0):
                currentPoint = createTapCell(row, currentPoint)

            if(i%2 == 1) and (currentRowIndex % 2 == 1):
                currentPoint = createTapCell(row, currentPoint)
            instanceName = byte[i]
            currentInstance = block.findInst(instanceName)
            currentInstance.setOrient(rowOrientation)
            currentInstance.setLocation(currentPoint[0], currentPoint[1])
            currentInstance.setPlacementStatus("PLACED")
            currentPoint[0] = currentPoint[0] + siteWidth * math.ceil(currentInstance.getMaster().getWidth() / siteWidth)
    return currentPoint



# A function that loops over the 4 clusters and places them with all their cells
def placeClusters():

    currentRowIndex = 0
    for i in range(4):
        currentRowIndex = placeCluster(i, currentRowIndex)
        currentRowIndex = currentRowIndex + 2

    return currentRowIndex


# A function that places all the cells in the DEF file.
def place():

    currentRowIndex = placeClusters()
    currentRowIndex = currentRowIndex +  2

    remianingCells = [x[0] for x in remaining] + decoderBuffers + [outputs[key][0][0] for key in outputs] + [floatbuffers[key][0][0] for key in floatbuffers]
    
    placeBuffers(remianingCells, currentRowIndex)
    
    



# create a database
db = odb.dbDatabase.create()

# read LEF files
tech_lef = odb.read_lef(db, "sky130_fd_sc_hd/techlef/sky130_fd_sc_hd.tlef")
macro_lef = odb.read_lef(db, "sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef")

# read and empty def file with an initialized diearea
def_file = odb.read_def(db, "floorplan.def")

# get technology
tech = db.getTech()
lef_units = tech.getDbUnitsPerMicron()



# get site dimensions from LEF
sites = tech_lef.getSites()
regular_site = sites[0]
double_height_site = sites[1]

# I will use double height sites for now
siteWidth = regular_site.getWidth()
siteHeight = regular_site.getHeight()

# get the chip from the def file
chip = db.getChip()

# get the block designfrom the chip
block = chip.getBlock()

clusters = {}
decoders = {}
decoderBuffers = []
floatbuffers = {}
outputs = {}


remaining = []

# Get all the instances in the DEF file
instances = block.getInsts()


# Loop over the instances and parse them to be stored in accessible data structures 
for inst in instances:

    nameNotSplit = inst.getName()
    name = nameNotSplit.split('.')
    if 'DEC.DEC' in nameNotSplit:
        if nameNotSplit not in decoders:
            decoders[nameNotSplit] = []
        decoders[nameNotSplit].append(nameNotSplit)

    elif 'DEC.ABUF' in nameNotSplit:
        decoderBuffers.append(nameNotSplit)


    elif (name[0] == 'C0') or (name[0] == 'C1') or (name[0] == 'C2') or (name[0] == 'C3'):
        if name[0] not in clusters:
            clusters[name[0]] = {}
        
        if 'WORD' in name[1]:
            if 'words' not in clusters[name[0]]:
                clusters[name[0]]['words'] = {}

            if name[1] not in clusters[name[0]]['words']:
                clusters[name[0]]['words'][name[1]] = []
            clusters[name[0]]['words'][name[1]].append(name)

        elif 'WEBUF' in name[1]:
            if 'webufs' not in clusters[name[0]]:
                clusters[name[0]]['webufs'] = []

            clusters[name[0]]['webufs'].append(name)

        elif 'DIBUF' in name[1]:
            if 'dibufs' not in clusters[name[0]]:
                clusters[name[0]]['dibufs'] = []

            clusters[name[0]]['dibufs'].append(name)

        elif 'CLKBUF' in name[1]:
            if 'clkbufs' not in clusters[name[0]]:
                clusters[name[0]]['clkbufs'] = []

            clusters[name[0]]['clkbufs'].append(name)

    elif 'FLOATBUF' in name[0]:
        if name[0] not in floatbuffers:
            floatbuffers[name[0]] = []
        floatbuffers[name[0]].append(name)
    elif 'OUT' in name[0]:
        if name[0] not in outputs:
            outputs[name[0]] = []
        outputs[name[0]].append(name)
    else:
        remaining.append(name)


# Get all the rows in the floorplan
rows = block.getRows()

# Reverse the order of the rows so that placement starts at the top instead of the bottom
rows.reverse()

cells = macro_lef.getMasters()

# Extract the tap cell
tapCellName = "sky130_fd_sc_hd__tapvpwrvgnd_1"
tapCell = [cell for cell in cells if cell.getName() == tapCellName]
tapCell = tapCell[0]


# Place the cells in the DEF file
place()

# Right the new DEF file.
result = odb.write_def(chip.getBlock(), "placedSRAM64x32.def")



