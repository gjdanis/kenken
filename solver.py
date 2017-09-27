from utils import flatten, pairs, with_timing


class ReductionStrategy:
    """
    Simple "strategy" class with static methods that may be used to reduce a set of
    candidates by the rules of a constraint

    More info on this pattern here: https://en.wikipedia.org/wiki/Strategy_pattern

    """

    @staticmethod
    def reduce_unique(constraint, candidates):
        """
        Reduces the set of rules by the rules for a unique constraint

        Args:
            constraint (UniqueConstraint): constraint object
            candidates (set): to reduce 

        Returns: set

        """
        values = (cell.value for cell in constraint.assigned)
        return candidates.symmetric_difference(values)

    @staticmethod
    def reduce_add(constraint, candidates):
        """
        Reduces the set of candidates by the rules for an add constraint

        Args:
            constraint (AddConstraint): constraint object
            candidates (set): to reduce 

        Returns: set

        """
        remainder = constraint.remainder

        if len(constraint.unassigned) == 1:
            return {remainder} if remainder in candidates else set()

        candidates = (
            candidate for candidate in candidates
            if remainder - candidate > 0
        )

        return set(candidates)

    @staticmethod
    def reduce_mul(constraint, candidates):
        """
        Reduces the set of candidates by the rules for an add constraint

        Args:
            constraint (MulConstraint): constraint object
            candidates (set): to reduce 

        Returns: set

        """
        remainder = constraint.remainder

        if len(constraint.unassigned) == 1:
            return {remainder} if remainder in candidates else set()

        candidates = (
            candidate for candidate in candidates
            if remainder % candidate == 0
        )

        return set(candidates)

    @staticmethod
    def reduce_sub(constraint, candidates):
        """
        Reduces candidate pairs that don't satisfy a sub constraint

        Args:
            constraint (SubConstraint): constraint object
            candidates (set): to reduce

        Returns set:

        """
        candidate_pairs = pairs(candidates, lambda p: constraint.evaluate(p))
        return flatten(candidate_pairs)

    @staticmethod
    def reduce_div(constraint, candidates):
        """
        Reduces candidate pairs that don't satisfy a div constraint

        Args:
            constraint (DivConstraint): constraint object
            candidates (set): to reduce

        Returns set:

        """
        candidate_pairs = pairs(candidates, lambda p: constraint.evaluate(p))
        return flatten(candidate_pairs)

    @staticmethod
    def reduce_con(constraint, candidates):
        """
        Reduces candidates that don't satisfy the constant constraint

        Args:
            constraint (ConConstraint): constraint object
            candidates (set): to reduce 

        Returns: set

        """
        return {constraint.value} if constraint.value in candidates else set()


@with_timing
def backtrack_solve(puzzle):
    """
    Solves a kenken puzzle with backtracking

    During each iteration of the algorithm, a filtering strategy is applied
    to the puzzle's remaining unassigned cells

    See https://en.wikipedia.org/wiki/Backtracking for more information
    on this algorithm

    Args:
        puzzle `Puzzle`: object to solve

    Returns: tuple where first position value is whether or not the puzzle
             was solved; second is some stats on the algorithm performance

    """

    stats = {
        'backtracks': 0,
        'recursive_calls': 0
    }

    def initialize():
        """
        Initializes puzzle cell domains and sets the constraint reducer algorithm
        for all the constraints in the puzzle

        Returns: None

        """
        for cell in puzzle.cells:
            cell.domain = puzzle.domain

        for constraint in puzzle.constraints:
            constraint.reducer = ReductionStrategy()

    def solve():
        """
        Solve this puzzle recursively

        - The algorithm sorts the unsolved cells by candidate length
        - If the current assignment for a cell solves on recursing, the puzzle
          must be solved
        - Otherwise, none of the candidates solves the puzzle and we have to stop
          and unassign everything, backing up to the origin of the inconsistency

        Returns: bool

        """

        solve_order = sorted(puzzle.unassigned,
                             key=lambda c: len(c.candidates))

        for cell in solve_order:
            for candidate in cell.candidates:
                cell.value = candidate

                if puzzle.consistent:
                    stats['recursive_calls'] += 1
                    if solve():
                        return True

                cell.value = None

            stats['backtracks'] += 1
            return False
        return puzzle.solved

    initialize()
    return solve(), stats
