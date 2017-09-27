from abc import ABC, abstractmethod


class PuzzleFormatter(ABC):
    """
    Base class for formatting a puzzle for display

    Contains utilities that can be used to draw the puzzle
    Subclasses should implement `format`, which can be called
    to return a string representation of the puzzle.

    Args:
        puzzle (Puzzle): the puzzle object to format

    """

    def __init__(self, puzzle):
        from puzzle import ValueConstraint

        self.cages = {}
        for constraint in puzzle.constraints:
            if isinstance(constraint, ValueConstraint):
                for cell in constraint.cells:
                    self.cages[cell] = constraint

        self.ordering = sorted(puzzle.cells)
        self.puzzle = puzzle

    def cell(self, row, col):
        """
        Returns the cell at the given row/column coordinate

        Args:
            row (int): puzzle row
            col (int): puzzle column

        Returns: Cell object

        """
        return self.ordering[row * self.puzzle.width + col]

    def left_boundary(self, cell):
        """
        Returns whether or not to include a cell's left boundary

        Args:
            cell (Cell): given cell

        Returns: bool

        """
        return self.boundary(cell, cell.row, cell.col - 1)

    def bottom_boundary(self, cell):
        """
        Returns whether or not to include a cell's bottom boundary

        Args:
            cell (Cell): given cell

        Returns: bool

        """
        return self.boundary(cell, cell.row + 1, cell.col)

    def top_boundary(self, cell):
        """
        Returns whether or not to include a cell's top boundary

        Args:
            cell (Cell): given cell

        Returns: bool

        """
        return self.boundary(cell, cell.row - 1, cell.col)

    def right_boundary(self, cell):
        """
        Returns whether or not to include a cell's right boundary

        Args:
            cell (Cell): given cell

        Returns: bool

        """
        return self.boundary(cell, cell.row, cell.col + 1)

    def boundary(self, cell, row, col):
        """
        Returns whether or not to include a cell's boundary in the
        given direction

        Args:
            cell (Cell): given cell
            row (int): row direction
            col (int): column direction

        Returns: bool

        """
        return not any(
            other for other in self.cages[cell].cells
            if other.row == row and other.col == col
        )

    @abstractmethod
    def format(self, *args, **kwargs) -> str:
        pass


class AsciiPuzzleFormatter(PuzzleFormatter):
    """
    Class for pretty printing an ASCII representation of a puzzle
    
    Args:
        puzzle (Puzzle): the puzzle object to format
        display_width (int): drawn box width
        display_height (int): drawn box height

    Example of format output:

        #--------------#--------------#--------------#
        |3$            |6+                           |
        |              |                             |
        |      3       |     None           None     |
        |              |                             |
        |              |             1             12|
        #--------------#              #--------------#
        |3+            |              |4+            |
        |              |              |              |
        |     None     |     None     |     None     |
        |              |              |              |
        |            12|            13|           123|
        #              #--------------#              #
        |              |2$            |              |
        |              |              |              |
        |     None     |      2       |     None     |
        |              |              |              |
        |             1|              |            13|
        #--------------#--------------#--------------#
    """

    EMPTY = ''
    SPACE = ' '
    NEWLINE = '\n'
    PIPE = '|'
    HYPHEN = '-'
    SHARP = '#'

    def __init__(self, puzzle, display_width=14, display_height=5):
        super().__init__(puzzle)
        self.display_width = display_width
        self.display_height = display_height

    def pad(self, spaces_left, text, spaces_right):
        """
        Applies space padding left/right of the given text

        Args:
            spaces_left (int): left offset
            text (str): text to format
            spaces_right: right offset

        Returns: str

        """
        left_space = self.SPACE*spaces_left
        right_space = self.SPACE*spaces_right
        return left_space + text + right_space

    def position_left(self, text):
        """
        Helper to position text to the absolute left

        Args:
            text (str): what to position 

        Returns: str

        """
        return self.pad(0, text, self.display_width - len(text))

    def position_right(self, text):
        """
        Helper to position text to the absolute right

        Args:
            text (str): what to position 

        Returns: str

        """
        return self.pad(self.display_width - len(text), text, 0)

    def position_center(self, text):
        """
        Helper to center text

        Args:
            text (str): what to position 

        Returns: str

        """
        spaces_left = (self.display_width - len(text)) // 2
        spaces_right = self.display_width - (spaces_left + len(text))
        return self.pad(spaces_left, text, spaces_right)

    def header(self, cell):
        """
        Helper to get the header text to draw for the given cell
        
        This will be the cage constraint/value if the cell is the
        upper-left most cell in its ValueConstraint's cells

        Args:
            cell (Cell): cell object

        Returns: str

        """
        cage = self.cages.get(cell)
        if not cage or cell != min(cage.cells):
            return self.EMPTY

        return str(cage)

    def footer(self, cell):
        """
        Helper to get the footer text to draw for the given cell

        Args:
            cell (Cell): cell object

        Returns: str

        """
        return ''.join(map(str, cell.candidates))

    def format_cell(self, cell, height):
        """
        Helper to format a cell at the given "box height"

        This function is called as we iterate over this object's
        display_height

        Args:
            cell (Cell): cell object
            height (int): should be between 0 and self.display_height

        Returns: str

        """

        s = self.EMPTY
        if cell.col == 0:
            s += self.PIPE

        if height == 0:
            s += self.position_left(self.header(cell))
        elif height == (self.display_height // 2):
            s += self.position_center(str(cell.value))
        elif height == self.display_height - 1:
            s += self.position_right(self.footer(cell))
        else:
            s += self.SPACE * self.display_width

        if self.right_boundary(cell):
            s += self.PIPE
        else:
            s += self.SPACE
        return s

    def format_row(self, row):
        """
        Formats a puzzle row
        
        The algorithm proceeds by formatting the columns in the cell
        for each height in the display height

        Args:
            row (int): row whose cell's should are to be formatted 

        Returns: str

        """

        s = self.EMPTY
        if row == 0:
            s += self.SHARP
            for _ in range(self.puzzle.width):
                s += self.HYPHEN * self.display_width + self.SHARP
            s += self.NEWLINE

        for height in range(self.display_height):
            for col in range(self.puzzle.width):
                s += self.format_cell(self.cell(row, col), height)

            s += self.NEWLINE
            if height == self.display_height - 1:
                s += self.SHARP
                for col in range(self.puzzle.width):
                    if self.bottom_boundary(self.cell(row, col)):
                        s += self.HYPHEN * self.display_width
                    else:
                        s += self.SPACE * self.display_width
                    s += self.SHARP
        return s

    def format(self) -> str:
        return self.NEWLINE.join(
            map(self.format_row, range(self.puzzle.width))
        )
