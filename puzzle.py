import argparse
import glob

from abc import ABC, abstractmethod
from formatter import AsciiPuzzleFormatter
from parsing import parse_file
from solver import backtrack_solve
from utils import product


class Puzzle:
    """
    Models a kenken puzzle

    See https://en.wikipedia.org/wiki/KenKen for more information

    Args:
        width (int): puzzle size
        cells (list): `Cell` objects comprising this puzzle
        constraints (list): `Constraint` objects for the cells in this puzzle

    """

    def __init__(self, width, cells, constraints):
        self.width = width
        self.cells = cells
        self.constraints = constraints

    @property
    def domain(self):
        """
        Returns: bool this puzzle's possible cells values

        """
        return set(range(1, self.width + 1))

    @property
    def unassigned(self):
        """
        Returns: iter the unassigned cells

        """
        return filter(lambda cell: cell.value is None, self.cells)

    @property
    def solved(self):
        """
        Returns: bool whether or not this puzzle is solved

        """
        return all(c.solved for c in self.constraints)

    @property
    def consistent(self):
        """
        Returns: bool whether or not this puzzle is consistent

        """
        return all(c.consistent for c in self.constraints)


class Cell:
    """
    Models a cell (two dimensional coordinate) in a kenken puzzle

    Args:
        row (int): cell
        col (int): column

    """

    domain = set()

    def __init__(self, row, col):
        self.tuple = row, col
        self.value = None
        self.constraints = []

    @property
    def row(self):
        """
        Returns: int

        """
        return self.tuple[0]

    @property
    def col(self):
        """
        Returns: int

        """
        return self.tuple[1]

    @property
    def candidates(self):
        """
        Computes and returns the possible values for this cell,
        reduced from the cell domain by each of the constraints on
        this cell
        
        Returns: set

        """
        candidates = self.domain
        for constraint in self.constraints:
            candidates = candidates & set(constraint.reduce(candidates))
        return candidates

    def __str__(self) -> str:
        return str(self.tuple)

    def __repr__(self) -> str:
        return repr(self.tuple)

    def __eq__(self, other) -> bool:
        return self.tuple == other.tuple

    def __lt__(self, other) -> bool:
        return self.tuple < other.tuple

    def __hash__(self) -> int:
        return hash(self.tuple)


class Constraint(ABC):
    """
    Base class to model a puzzle constraint in a kenken puzzle

    A constraint is a grouping of cells whose values must collectively
    satisfy some condition. For puzzles, there are six child classes for
    this class:

        - UniquenessConstraint for rows/column uniqueness
        - ConConstraint ($) constraint on a single cell
        - AddConstraint (+)
        - MulConstraint (*)
        - SubConstraint (-)
        - DivConstraint (/)
    
    Each subclass implements the method `evaluate`, which applies the
    constraint logic to a set of values, returning whether or not
    the constraint is satisfied.
    
    Further logic to reduce a set of candidate values for a constraint
    may be implemented in the `reduce` method. The implementation for
    that override should be deferred to the `reducer` dependency, rather
    than included as part of the class.

    Args:
        cells (list): the `Cell` objects in this cage

    """

    _reducer = None

    def __init__(self, cells):
        self.cells = cells
        for cell in cells:
            cell.constraints.append(self)

    @abstractmethod
    def evaluate(self, values) -> bool:
        """
        Evaluate this constraint for the given values

        Args:
            values (list): values

        Returns: bool whether or not this constraint is satisfied

        """
        pass

    @property
    def reducer(self):
        """
        Gets the reducer algorithms for this constraint

        Returns: ReductionStrategy

        """
        return self._reducer

    @reducer.setter
    def reducer(self, value):
        """
        Sets the reducer algorithms for this constraint

        Args:
            value (ReductionStrategy): an object that implements the interface
                                       for ReductionStrategy

        Returns: None

        """
        from solver import ReductionStrategy

        if not isinstance(value, ReductionStrategy):
            raise ValueError

        self._reducer = value

    def reduce(self, candidates) -> set:
        """
        Reduces a set of candidate values

        Args:
            candidates (set): set of candidate values 

        Returns: set prefer to return a new object, rather than mutating
                 the input set

        """
        return candidates

    @property
    def values(self):
        """
        Returns: list the current cell values (assigned and unassigned) for
                 this constraint

        """
        return [cell.value for cell in self.cells]

    @property
    def cardinality(self):
        """
        Returns: int the size of this constraint

        """
        return len(self.cells)

    @property
    def unassigned(self):
        """
        Returns: list the cells whose values are unassigned

        """
        return [cell for cell in self.cells if cell.value is None]

    @property
    def assigned(self):
        """
        Returns: list the cells whose values are assigned

        """
        return [cell for cell in self.cells if cell.value is not None]

    @property
    def solved(self):
        """
        Returns: bool whether or not this constraint is solved

        """
        values = self.values
        return None not in values and self.evaluate(values)

    @property
    def consistent(self):
        """
        Returns: bool whether or not this constraint is consistent
        
        """
        # TODO improve this implementation in child classes
        return None in self.values or self.solved


class UniquenessConstraint(Constraint):
    def evaluate(self, values) -> bool:
        """
        Returns whether `values` is unique

        Args:
            values (list): values 

        Returns: bool

        """
        return len(values) == len(set(values))

    def reduce(self, candidates) -> set:
        return self.reducer.reduce_unique(self, candidates)


class ValueConstraint(Constraint):
    """
    Base class to model a puzzle constraint whose cell values must
    reduce to the constraint's target value

    Each subclass implements the property `type`, which identifies the
    constraint and can be used for parsing .kk files

    Args:
        cells (list): the `Cell` objects in this cage
        value (int): target constraint value

    """

    TYPE_ADD = '+'
    TYPE_SUB = '-'
    TYPE_MUL = '*'
    TYPE_DIV = '/'
    TYPE_CON = '$'

    def __init__(self, cells, value):
        super().__init__(cells)
        self.value = value

    def __str__(self) -> str:
        return str(self.value) + self.type

    @property
    @abstractmethod
    def type(self) -> str:
        """
        Returns: str a type identifier for this constraint

        """
        pass


class AddConstraint(ValueConstraint):
    def evaluate(self, values) -> bool:
        """
        Returns whether `values` sums to the target value

        Args:
            values (list): values 

        Returns: bool

        """
        return sum(values) == self.value

    def reduce(self, candidates) -> set:
        return self.reducer.reduce_add(self, candidates)

    @property
    def total(self) -> int:
        return sum(cell.value for cell in self.assigned)

    @property
    def remainder(self) -> int:
        return self.value - self.total

    @property
    def type(self) -> str:
        return self.TYPE_ADD


class MulConstraint(ValueConstraint):
    def evaluate(self, values) -> bool:
        """
        Returns whether `values` multiplies to the target value

        Args:
            values (list): values 

        Returns: bool

        """
        return product(values) == self.value

    def reduce(self, candidates) -> set:
        return self.reducer.reduce_mul(self, candidates)

    @property
    def total(self) -> int:
        return product(cell.value for cell in self.assigned)

    @property
    def remainder(self) -> int:
        return self.value // self.total

    @property
    def type(self) -> str:
        return self.TYPE_MUL


class SubConstraint(ValueConstraint):
    def evaluate(self, values) -> bool:
        """
        Returns whether `values` multiplies to the target value

        Args:
            values (list): values 

        Returns: bool

        """
        return abs(values[0] - values[1]) == self.value

    def reduce(self, candidates) -> set:
        return self.reducer.reduce_sub(self, candidates)

    @property
    def type(self) -> str:
        return self.TYPE_SUB


class DivConstraint(ValueConstraint):
    def evaluate(self, values) -> bool:
        """
        Returns whether `values` divides to the target value

        Args:
            values (list): values 

        Returns: bool

        """
        return (values[0] == values[1] * self.value or
                values[1] == values[0] * self.value)

    def reduce(self, candidates) -> set:
        return self.reducer.reduce_div(self, candidates)

    @property
    def type(self) -> str:
        return self.TYPE_DIV


class ConConstraint(ValueConstraint):
    def evaluate(self, values) -> bool:
        """
        Returns whether `values` is the current value

        Args:
            values (list): values 

        Returns: bool

        """
        return values[0] == self.value

    def reduce(self, candidates) -> set:
        return self.reducer.reduce_con(self, candidates)

    @property
    def type(self) -> str:
        return self.TYPE_CON


VALUE_CONSTRAINTS = {
    ValueConstraint.TYPE_ADD: AddConstraint.__name__,
    ValueConstraint.TYPE_MUL: MulConstraint.__name__,
    ValueConstraint.TYPE_SUB: SubConstraint.__name__,
    ValueConstraint.TYPE_DIV: DivConstraint.__name__,
    ValueConstraint.TYPE_CON: ConConstraint.__name__,
}


def main():
    """
    A simple command line interface for kenken

    Supports the following arguments:

      -s=[file]: parse and solve the given puzzle (.kk) file
      -t|--test: run and benchmark all puzzles in the ./tests directory

    Returns: None

    """

    parser = argparse.ArgumentParser(description='Simple kenken solver')

    parser.add_argument(
        '-s', '--solve',
        help='parse and solve a specific puzzle file'
    )

    parser.add_argument(
        '-t', '--test',
        help='run and benchmark all test puzzles',
        action='store_true'
    )

    args = vars(parser.parse_args())

    def solve(filename):
        puzzle = parse_file(filename)

        solved, stats = backtrack_solve(puzzle)
        formatter = AsciiPuzzleFormatter(puzzle)

        if solved:
            print('SOLVED ' + filename)
            print(stats)
            print(formatter.format())
        else:
            print('FAILED TO SOLVE ' + filename)

    if args['solve']:
        solve(args['solve'])

    if args['test']:
        tests = glob.glob('./puzzles/*.kk')
        for file in tests:
            solve(file)


if __name__ == '__main__':
    main()
