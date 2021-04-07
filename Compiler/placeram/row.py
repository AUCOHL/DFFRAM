class Row(object):
    sw = None
    sh = None
    
    create_tap = None
    tap_distance = None

    create_fill = None 

    # Assumptions:
    #   All fills are powers of 2.
    #   If fill 2^n is available, then for 0 <= i < n: 2^i is available.
    supported_fill_sizes = None

    max_fill_size = None

    def __init__(self, ordinal, row_obj):
        self.ordinal = ordinal
        self.obj = row_obj

        self.origin = self.obj.getOrigin()
        [self.x, self.y] = self.obj.getOrigin()
        self.max = self.obj.getBBox().xMax()

        self.orientation = self.obj.getOrient()

        self.cell_counter = 0
        self.tap_counter = 0
        self.fill_counter = 0
        self.since_last_tap = 0 if self.ordinal % 2 == 0 else Row.tap_distance

    def tap(self, width=0):
        location = self.x

        if self.since_last_tap + width > Row.tap_distance:
            self.place(Row.create_tap("tap_%i_%i" % (self.ordinal, self.tap_counter)), ignore_tap=True)
            self.tap_counter += 1
            self.since_last_tap = 0
        else:
            self.since_last_tap += width

    def place(self, instance, ignore_tap=False):
        width = instance.getMaster().getWidth()
        if not ignore_tap:
            self.tap(width)

        instance.setOrient(self.orientation)
        instance.setLocation(self.x, self.y)
        instance.setPlacementStatus("PLACED")

        self.x += width
        self.cell_counter += 1

    @staticmethod
    def from_odb(rows, regular_site, create_tap, max_tap_distance, create_fill, supported_fill_sizes):
        Row.create_tap = create_tap
        Row.sw, Row.sh = (regular_site.getWidth(), regular_site.getHeight())
        Row.tap_distance = max_tap_distance

        Row.create_fill = create_fill
        Row.supported_fill_sizes = supported_fill_sizes
        Row.max_fill_size = max(supported_fill_sizes)

        returnable = []
        for i, row in enumerate(rows):
            returnable.append(Row(i, row))
        return returnable

    @staticmethod
    def fill_rows(rows, from_index, to_index): # [from_index,to_index)
        """
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

        Technology's amazing, innit?

        """
        def bin_pack(remaining, max_fill_size):
            fills = []
            while remaining > max_fill_size:
                fills.append(max_fill_size)
                remaining -= max_fill_size

            # I'm using nature's bin-packing algorithm for base-2.
            # Binary representation.
            current_size = 1
            while remaining > 0:
                if remaining & 1:
                    fills.append(current_size)
                remaining >>= 1
                current_size <<= 1

            return fills
        max_sw = -1
        for i in range(from_index, to_index):
            r = rows[i]
            width = r.x
            width_sites = int(width / Row.sw)
            max_sw = max(max_sw, width_sites)
            
        for i in range(from_index, to_index):
            r = rows[i]
            width = r.x
            width_sites = int(width / Row.sw)

            empty = max_sw - width_sites

            remaining = empty

            fills = bin_pack(empty, Row.max_fill_size)
            
            for fill in fills:
                fill_cell = Row.create_fill("fill_%i_%i" % (i, r.fill_counter), fill)
                r.place(fill_cell, ignore_tap=True)
                r.fill_counter += 1
