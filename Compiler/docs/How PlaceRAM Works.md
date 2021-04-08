# How PlaceRAM Works
PlaceRAM is a Python 3.8+ script based on Opendbpy that places instances on an input floor plan.

It is tied to a specific SRAM placement designs, but is designed pretty modularly so it can easily handle alterations to the design or similar designs for other PDKs.

## A. Sieve
The instance hierarchy has already been "flattened" by the time it's become a floor plan, so it becomes necessary to internally recreate this hierarchy. Luckily, a trace of the hierarchy remains in the form of the names:

```def
    - DIBUF\[17\] sky130_fd_sc_hd__clkbuf_16 ;
    - SLICE\[0\].RAM8x32.DEC.AND4 sky130_fd_sc_hd__and4bb_2 ;
    - SLICE\[0\].RAM8x32.WEBUF\[0\] sky130_fd_sc_hd__clkbuf_2 ;
    - SLICE\[0\].RAM8x32.WORD\[0\].W.B0.BIT\[0\].OBUF sky130_fd_sc_hd__ebufn_2 ;
```

The sieve process mandates that the names of the various objects already be known. For example, see the following sieve:

```def
    TOP
    [SIEVE: SLICE]
    [SIEVE: DEC] ; [SIEVE: WORD ]
```

For example, let's look at the passing of `SLICE\[0\].RAM8x32.WEBUF\[0\]` through the sieve:


```def
    SLICE\[0\].RAM8x32.WEBUF\[0\]

    V

    [SIEVE: SLICE] (Contains "SLICE". Proceed.)

    [SIEVE: DEC] ; [SIEVE: WORD ]

    ---
    
    [SIEVE: SLICE] > {SLICE\[0\].RAM8x32.WEBUF\[0\]} (Does not contain either DEC or WORD. Not passed to any internal objects.)

    [SIEVE: DEC] ; [SIEVE: WORD ]
```

Typically, when using a sieve, you filter the larger components first. Perhaps a bit counterintuitively to that analog, the longer names actually go first. The items go through the sieve until they're where they're supposed to be. By the end, the components should be filtered as follows:

```def
    TOP > { DIBUF\[17\] }
    [SIEVE: SLICE] > { SLICE\[0\].RAM8x32.WEBUF\[0\] }
    [SIEVE: DEC] > { SLICE\[0\].RAM8x32.DEC.AND4 } ; [SIEVE: WORD] > { SLICE\[0\].RAM8x32.WORD\[0\].W.B0.BIT\[0\].OBUF }
```

The sieve is implemented as a series of object constructors in `data.py`. By the end, the hierarchy is returned as a tree-like structure of an abstract class `Placeable`, indicating that this object is placeable.

## B. Place
At the heart of the placement is the `Row` object. It acts as a kind of wrapper for opendbpy rows, keeping track of the x value automatically as well as adding taps when required.

When placing a new instance, the algorithm is as follows.

```
MAX_TAP_DISTANCE = 10

┌─────────────────┐
│ Row              │
│ Since Last Tap:  │    < (New Instance: Width 7)
│ 3                │
└─────────────────┘

if incoming_cell_width + since_last_tap >= MAX_TAP_DISTANCE:
    place_tap()
    since_last_tap = 0
```

In this manner, taps do not have to be considered in the general structure of the design.

The `Row` object also offers a fill cells function, which achieves a square shape for a series of rows.

```
-- Before this function --

[A][B][C][D]
[C][S]
[F][X][N]
[V]

-- After this function --

[A][B][C][D]
[C][S][ F  ]
[F][X][N][F]
[V][ F  ][F]

( where [F] are fill rows of various widths. This function performs bin-packing so that the least amount of instances is used.)
```

Placement is handled by passing a list of rows to the `.place` method on `Placeable` objects. The method also recieves a starting row index and returns the current row index. Meaning that if a placeable object takes up 8 rows, it should return `start_row + 8`.

The hierarchy from the sieve gets traversed and placed. The various `.place` functions are responsible for placing the cells in the desired order and across many rows. The fill cells function may be used to "cap off" a larger structure such as a Slice or a Block.