# How PlaceRAM Works
PlaceRAM is a Python 3.6+ script based on Opendbpy that places instances on an input floor plan.

It is tied to a specific SRAM placement designs, but is designed pretty modularly so it can easily handle alterations to the design or similar designs for other PDKs.

## A. Sieve
The instance hierarchy has already been "flattened" by the time it's become a floor plan, so it becomes necessary to internally recreate this hierarchy. Luckily, a trace of the hierarchy remains in the form of the names:

```def
    - DIBUF\[17\] sky130_fd_sc_hd__clkbuf_16 ;
    - SLICE\[0\].RAM8x32.DEC.AND4 sky130_fd_sc_hd__and4bb_2 ;
    - SLICE\[0\].RAM8x32.WEBUF\[0\] sky130_fd_sc_hd__clkbuf_2 ;
    - SLICE\[0\].RAM8x32.WORD\[0\].W.B0.BIT\[0\].OBUF sky130_fd_sc_hd__ebufn_2 ;
```

Using regular expressions, the components are filtered into various components using a sieving algorithm, shown as follows:

![A diagram of the sieve algorithm](../img/sieve_algorithm.png)

The final hierarchy is returned as a tree-like structure of an abstract class `Placeable`, which also implements the sieve algorithm: to reconstruct the hierarchy, a placeable object would simply have to include this code in its constructor:


```python
S = Placeable.Sieve
class Slice(Placeable):
    def __init__(self, instances):
        # [...]
        self.sieve(instances, [
            S(variable="words", groups=["word"], custom_behavior=process_word),
            S(variable="decoders", groups=["port"], custom_behavior=process_decoder),
            S(variable="clkbuf"),
            S(variable="webufs", groups=["line"]),
        ])
        # [...]
```

Note that the order is significant, i.e., the largest subcomponents of a hierarchy should be first in a sieve. This is avoids some situations such as, for example, a clock buffer that is inside a word (with the name `WORD[0].CLKBUF`, for example) being mistakenly filtered by the `clkbuf` filter.

The regular expressions for the sieves are retrieved from `./placeram/rx.yml`, so for example, the sieve above would use the following regular expressions:

```yaml
Slice:
  clkbuf: "\\bCLKBUF\\b"
  webufs: "\\bWEBUF\\\\\\[(\\d+)\\\\\\]"
  words: "\\bWORD\\\\\\[(\\d+)\\\\\\]"
  decoders: "\\bDEC(\\d+)\\b"
```

The variables are stored in dictionaries which can be turned into arrays by invoking `self.dicts_to_lists()`. 

## B. Place
At the heart of the placement is the `Row` object. It acts as a kind of wrapper for opendbpy rows, keeping track of the x value automatically as well as adding taps when required.

When placing a new instance, the algorithm is as follows.

```
MAX_TAP_DISTANCE = 10

┌─────────────────┐
│ Row             │
│ Since Last Tap: │    < (New Instance: Width 7)
│ 3               │
└─────────────────┘

if incoming_cell_width + since_last_tap >= MAX_TAP_DISTANCE:
    place_tap()
    since_last_tap = 0
```

In this manner, taps do not have to be considered in the general structure of the design.

Placement is handled by passing a list of rows to the `.place` method on `Placeable` objects. The method also recieves a starting row index and returns the current row index. Meaning that if a placeable object takes up 8 rows, it should return `start_row + 8`.

The hierarchy from the sieve gets traversed and placed. The various `.place` functions are responsible for placing the cells in the desired order and across many rows. The fill cells function may be used to "cap off" a larger structure such as a Slice or a Block.