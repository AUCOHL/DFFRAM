# Using Opendbpy
First of all, start by importing the module:

```python
import odb
```

## Creating a database
You need to start by creating a database. This database will be linked to all of your calls to opendbpy directly or indirectly from now on.

```python 
db = odb.dbDatabase.create()
```

## Reading LEF files
```python
lef = odb.read_lef(db, lef_file_path)
tlef = odb.read_lef(db, tech_lef_file_path)
```

Note that the lef object contains a reference to db.

You can just extract information from the lef files as follows:

```python
cells = lef.getMasters()
sites = tlef.getSites()
```

## Dealing with Cell Masters
```python
cell = cells[0]

name = cell.getName()
width = cell.getWidth()
```

## Reading DEF files
```python
df = odb.read_def(db, def_file_path)
```

## Getting data from block: Rows, Existing Instances and DEF units
```python
chip = db.getChip() # Note how the db has been affected by the def_read imperatively.
block = chip.getBlock()

rows = block.getRows()
one_micron = block.getDefUnits()
existing_instances = block.getInsts()
```

## Getting data from Rows
The OpenDB row object is not particularly interesting other than for extracting data. placeram creates its own Row object that offers placement functions.

```python
for row in rows:
    [x, y] = row.getOrigin()
    [xMax, yMax] = [row.getBBox().xMax(), row.getBBox().yMax()]
    orientation = row.getOrient()
```

## Interacting with Instances
```python
MASTER_NAME = "sky130_fd_sc_hd__tapvpwrvgnd_1" # for example

row = rows[0] # You do not want to practically place everything on the first row, of course
x = row.getBBox().xMax()
y = row.getBBox().yMax()

# Create new instance
new_instance = odb.dbInst_create(block, MASTER_NAME, "tap_cell_x")

for i in existing_instances + [new_instance]:
    master = i.getMaster()
    width = master.getWidth()
    master_name = master.getName()

    i.setOrient(row.getOrient()) # Set Orientation
    i.setLocation(x, y) # Set X and Y locations of a cell
    i.setPlacementStatus("PLACED") # Set status as placed

    # Let's say we want to not place fill cells, for visual inspection, as an example
    if master_name == "sky130_fd_sc_hd__fill_1": 
        i.setPlacementStatus("UNPLACED") # Set status as unplaced

    x += width
```

## Writing result
```python
odb.write_def(block, output_def_path) # Returns 1 on success
```

These are all the basics you need to know when using opendbpy.
