from ast import literal_eval


def parse_file(filename):
    """
    Parse a .kk file to a `Puzzle` object

    Args:
        filename (str): input .kk filename to open and read

    Returns: `Puzzle`

    """
    with open(filename, 'r') as f:
        return parse_string(f.read())


def parse_string(s):
    """
    Parse a string to a `Puzzle` object

    The string should be a dictionary that python
    can interpret literally. For example:

    {
      'width': 2,
       'cages': [
         {'value': 2, 'op': '/', 'cells': [(0,0), (0,1)]},
         {'value': 3, 'op': '+', 'cells': [(1,0), (1,1)]}
      ]
    }

    The 'op' value should be one of the following, the key set
    for VALUE_CONSTRAINTS

        '+' -> AddConstraint,
        '-' -> SubConstraint,
        '*' -> MulConstraint,
        '/' -> DivConstraint,
        '$' -> ConConstraint

    The exclusive row/column cages will be created automatically

    Args:
        s (str): input string to read

    Returns: `Puzzle` object

    """

    from puzzle import (
        Puzzle,
        Cell,
        AddConstraint,
        SubConstraint,
        MulConstraint,
        DivConstraint,
        ConConstraint,
        UniquenessConstraint,
        VALUE_CONSTRAINTS
    )

    constraint_factory = {
        AddConstraint.__name__: AddConstraint,
        SubConstraint.__name__: SubConstraint,
        MulConstraint.__name__: MulConstraint,
        DivConstraint.__name__: DivConstraint,
        ConConstraint.__name__: ConConstraint
    }

    d = literal_eval(s.strip())

    puzzle_width = d.get('width')
    puzzle_cages = d.get('cages')

    # ensure that both the puzzle width and a set of cages are provided
    if puzzle_width is None or puzzle_cages is None:
        raise SyntaxError(
            "Expected 'width' and 'cages'. Got `{0}`".format(d)
        )

    puzzle_cells = set()
    puzzle_constraints = []

    for cage in puzzle_cages:
        value = cage.get('value')
        cells = set(cage.get('cells'))

        # ensure both 'value' and 'cells' are provided
        if value is None or cells is None:
            raise Exception(
                "Expected 'value' and 'cells'. Got {0}".format(cage)
            )

        # ensure that none of these cells has already been parsed
        if cells.intersection(puzzle_cells):
            raise Exception('Some cells exist in another cage {0}'.format(cells))

        op = cage.get('op')

        # ensure that the cage operation is valid
        if op not in VALUE_CONSTRAINTS:
            raise Exception(
                "Expected {0} Got {1}".format(','.join(VALUE_CONSTRAINTS), op)
            )

        cells = [Cell(*cell) for cell in cells]

        # create a "ValueCage"
        _class = constraint_factory[VALUE_CONSTRAINTS[op]]
        puzzle_constraints.append(_class(cells, value))
        puzzle_cells = puzzle_cells.union(cells)

    # after looping over the puzzle cages, ensure all cells parsed
    if len(puzzle_cells) != puzzle_width * puzzle_width:
        raise Exception(
            'Expected {0} cells; parsed {1}'.format(
                puzzle_width * puzzle_width, puzzle_cells)
        )

    # add all unique constraints for the puzzle rows/columns
    for width in range(puzzle_width):
        puzzle_constraints.append(
            UniquenessConstraint(
                [cell for cell in puzzle_cells if cell.row == width]
            )
        )

        puzzle_constraints.append(
            UniquenessConstraint(
                [cell for cell in puzzle_cells if cell.col == width]
            )
        )

    return Puzzle(puzzle_width, puzzle_cells, puzzle_constraints)
