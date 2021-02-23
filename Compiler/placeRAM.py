import opendbpy as odb

import os 
import math
import pprint
import argparse

class Placer:
    def __init__(self, lef_file_name, tech_lef_file_name, def_file_name):
         # create a database
        self.db = odb.dbDatabase.create()
        # read LEF files
        self.tech_lef = odb.read_lef(self.db, tech_lef_file_name)
        self.macro_lef = odb.read_lef(self.db, lef_file_name)
        # read and empty def file with an initialized diearea
        self.def_file = odb.read_def(self.db, def_file_name)
        # get technology
        self.tech = self.db.getTech()
        # get site dimensions from LEF
        self.sites = self.tech_lef.getSites()
        self.regular_site = self.sites[0]
        self.siteWidth = self.regular_site.getWidth()
        self.siteHeight = self.regular_site.getHeight()
        # get the chip from the def file
        self.chip = self.db.getChip()
        # get the block designfrom the chip
        self.block = self.chip.getBlock()
        self.clusters = {}
        self.decoders = {}
        self.decoderBuffers = []
        self.floatbuffers = {}
        self.outputs = {}
        self.remaining = []
        # Get all the instances in the DEF file
        self.instances = self.block.getInsts()
        self.tapCounter = 0
        # Get all the rows in the floorplan
        self.rows = self.block.getRows()
        # Reverse the order of the rows so that placement starts at the top instead of the bottom
        self.rows.reverse()
        self.cells = self.macro_lef.getMasters()
        
        # Extract the tap cell
        self.tapCellName = "sky130_fd_sc_hd__tapvpwrvgnd_1"
        self.tapCell = [cell for cell in self.cells if cell.getName() == self.tapCellName]
        self.tapCell = self.tapCell[0]

    def writeDef(self, file):
        result = odb.write_def(self.chip.getBlock(), file)
        assert result==1, "DEF not written"

    def parse(self):
        # Loop over the instances and parse them to be stored in accessible data structures 
        for inst in self.instances:

            nameNotSplit = inst.getName()
            name = nameNotSplit.split('.')
            if 'DEC.DEC' in nameNotSplit:
                if nameNotSplit not in self.decoders:
                    self.decoders[nameNotSplit] = []
                self.decoders[nameNotSplit].append(nameNotSplit)

            elif 'DEC.ABUF' in nameNotSplit:
                self.decoderBuffers.append(nameNotSplit)


            elif (name[0] == 'C0') or (name[0] == 'C1') or (name[0] == 'C2') or (name[0] == 'C3'):
                if name[0] not in self.clusters:
                    self.clusters[name[0]] = {}
                
                if 'WORD' in name[1]:
                    if 'words' not in self.clusters[name[0]]:
                        self.clusters[name[0]]['words'] = {}

                    if name[1] not in self.clusters[name[0]]['words']:
                        self.clusters[name[0]]['words'][name[1]] = []
                    self.clusters[name[0]]['words'][name[1]].append(name)

                elif 'WEBUF' in name[1]:
                    if 'webufs' not in self.clusters[name[0]]:
                        self.clusters[name[0]]['webufs'] = []

                    self.clusters[name[0]]['webufs'].append(name)

                elif 'DIBUF' in name[1]:
                    if 'dibufs' not in self.clusters[name[0]]:
                        self.clusters[name[0]]['dibufs'] = []

                    self.clusters[name[0]]['dibufs'].append(name)

                elif 'CLKBUF' in name[1]:
                    if 'clkbufs' not in self.clusters[name[0]]:
                        self.clusters[name[0]]['clkbufs'] = []

                    self.clusters[name[0]]['clkbufs'].append(name)

            elif 'FLOATBUF' in name[0]:
                if name[0] not in self.floatbuffers:
                    self.floatbuffers[name[0]] = []
                self.floatbuffers[name[0]].append(name)
            elif 'OUT' in name[0]:
                if name[0] not in self.outputs:
                    self.outputs[name[0]] = []
                self.outputs[name[0]].append(name)
            else:
                self.remaining.append(name)

    # A function to place a tap cell at a given point on a row
    def createTapCell(self, currnetRow, startingPoint):
        self.tapCounter = self.tapCounter + 1
        # create tapCell
        currentTapCell = odb.dbInst_create(self.block, self.tapCell, "tap_cell_" + str(self.tapCounter))

        rowOrientation = currnetRow.getOrient()
        currentTapCell.setOrient(rowOrientation)
        currentTapCell.setLocation(startingPoint[0], startingPoint[1])
        currentTapCell.setPlacementStatus("PLACED")
        startingPoint[0] = startingPoint[0] + self.siteWidth * math.ceil(currentTapCell.getMaster().getWidth() / self.siteWidth)

        return startingPoint

    # A function that places the cells representing the words in a cluster
    # These cells will be placed on 16 rows where each row would have: 8 flipflops, 
    # 8 tristate buffers, an inverter and 1 or 2 AND gates
    def placeWordsInCluster(self, words, currentRowIndex, clusterNumber):
        for i in range(16):
            wordIdentifier = "WORD\[" + str(i) + "\]"
            currentRow = self.rows[currentRowIndex]
            rowOrigin = currentRow.getOrigin()
            rowOrientation = currentRow.getOrient()
            currentPoint = rowOrigin

            currentPoint = self.placeWord(words[wordIdentifier], currentRowIndex, currentPoint)

            level0 = 2 * clusterNumber + int(i / 8)
            level1 = i % 8
            decoder0Identifier = "DEC.DEC_L0.AND" + str(level0) 
            decoder1Identifier = "DEC.DEC_L1\[" + str(level0) + "\].U.AND" + str(level1)

            # check if 1 or 2 buffers will be placed in this row:
            if i % 8 == 0:
                decoder0Name = ".".join(self.decoders[decoder0Identifier])
                decoder1Name = ".".join(self.decoders[decoder1Identifier])

                decoderInstanceNames = [decoder1Name, decoder0Name]
                for decoderName in decoderInstanceNames:

                    currentInstance = self.block.findInst(decoderName)
                    currentInstance.setOrient(rowOrientation)
                    currentInstance.setLocation(currentPoint[0], currentPoint[1])
                    currentInstance.setPlacementStatus("PLACED")

                    currentPoint[0] = currentPoint[0] + self.siteWidth * math.ceil(currentInstance.getMaster().getWidth() / self.siteWidth )

            # place 1 AND gate for decoder
            else:
                decoder1Name = ".".join(self.decoders[decoder1Identifier])

                decoderInstanceNames = [decoder1Name]
                for decoderName in decoderInstanceNames:

                    currentInstance = self.block.findInst(decoderName)
                    currentInstance.setOrient(rowOrientation)
                    currentInstance.setLocation(currentPoint[0], currentPoint[1])
                    currentInstance.setPlacementStatus("PLACED")
                    currentPoint[0] = currentPoint[0] + self.siteWidth * math.ceil(currentInstance.getMaster().getWidth() / self.siteWidth )

            currentRowIndex = currentRowIndex + 1
        return currentRowIndex

    # A function that takes a list of cells and places them on a row next to one another
    # This is used for 2 tasks:
    #       1- Place the buffers required for each cluster
    #       2- Place all the remaining cells that are not part of a single cluster.
    def placeBuffers(self, listOfBuffers, currentRowIndex):
    
        row = self.rows[currentRowIndex]
        rowOrigin = row.getOrigin()
        rowOrientation = row.getOrient()

        currentPoint = rowOrigin

        rowOrientation = row.getOrient()
        for i in range(len(listOfBuffers)):

            if(i%9 == 0) and (currentRowIndex % 2 == 0):
                currentPoint = self.createTapCell(row, currentPoint)

            if(i%9 == 1) and (currentRowIndex % 2 == 1):
                currentPoint = self.createTapCell(row, currentPoint)
            bufferInstance = listOfBuffers[i]
            currentInstance = self.block.findInst(bufferInstance)
            currentInstance.setOrient(rowOrientation)
            currentInstance.setLocation(currentPoint[0], currentPoint[1])
            currentInstance.setPlacementStatus("PLACED")
            currentPoint[0] = currentPoint[0] + self.siteWidth * math.ceil(currentInstance.getMaster().getWidth() / self.siteWidth)

    # A function that places a cluster given its number
    def placeCluster(self, clusterNumber, currentRowIndex):
        
        clusterName = 'C' + str(clusterNumber)
        cluster = self.clusters[clusterName]
        buffersList = []
        buffersList.append(".".join(cluster['clkbufs'][0]))
        for buf in cluster['dibufs']:
            buffersList.append(".".join(buf))
        for buf in cluster['webufs']:
            buffersList.append(".".join(buf))

        self.placeBuffers(buffersList, currentRowIndex)
        currentRowIndex = self.placeWordsInCluster(cluster['words'], currentRowIndex + 1, clusterNumber)
        return currentRowIndex

    # A function that places all cells in a word given a list of the cells in the word
    # It firstly splits the word into 4 bytes and then places them in sequence
    def placeWord(self, word, currentRowIndex, currentPoint):

        row = self.rows[currentRowIndex]
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
                    currentPoint = self.createTapCell(row, currentPoint)

                if(i%2 == 1) and (currentRowIndex % 2 == 1):
                    currentPoint = self.createTapCell(row, currentPoint)
                instanceName = byte[i]
                currentInstance = self.block.findInst(instanceName)
                currentInstance.setOrient(rowOrientation)
                currentInstance.setLocation(currentPoint[0], currentPoint[1])
                currentInstance.setPlacementStatus("PLACED")
                currentPoint[0] = currentPoint[0] + self.siteWidth * math.ceil(currentInstance.getMaster().getWidth() / self.siteWidth)
        return currentPoint
    
    # A function that loops over the 4 clusters and places them with all their cells
    def placeClusters(self):
        currentRowIndex = 0
        for i in range(4):
            currentRowIndex = self.placeCluster(i, currentRowIndex)
            currentRowIndex = currentRowIndex + 2
        return currentRowIndex


    # A function that places all the cells in the DEF file.
    def place(self):
        currentRowIndex = self.placeClusters()
        currentRowIndex = currentRowIndex +  2
        remianingCells = [x[0] for x in self.remaining] + self.decoderBuffers + [self.outputs[key][0][0] for key in self.outputs]
        remianingCells = remianingCells + [self.floatbuffers[key][0][0] for key in self.floatbuffers]
        self.placeBuffers(remianingCells, currentRowIndex)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A python script that customly places the cells for 64x32 DFFRAM')

    parser.add_argument('--lef', '-l', dest="lef_file", required=True, help='Input LEF file')

    parser.add_argument('--tech-lef', '-t', dest="tech_lef_file", required=True, help='Input Technology LEF file')

    parser.add_argument('--def', '-d',  dest="def_file", required=True, help='Input DEF file')

    parser.add_argument('--output-def', '-o', dest="output_def_file", required=True, help='Output DEF file')

    args = parser.parse_args()

    lef_file_name = args.lef_file
    tech_lef_file_name = args.tech_lef_file
    def_file_name = args.def_file

    output_file_name = args.output_def_file

    placement = Placer(lef_file_name, tech_lef_file_name, def_file_name)
    placement.parse()
    placement.place()
    placement.writeDef(output_file_name)
