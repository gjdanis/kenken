import collections
import itertools
import time

from functools import reduce, wraps


def pairs(nums, predicate=None) -> iter:
    """
    Returns a iterable of pairs for the given nums

    Args:
        nums (iter): items to compute pairs for
        predicate (callable): optional predicate function

    Returns: iter

    """
    return filter(predicate, itertools.combinations(nums, 2))


def flatten(iterable) -> iter:
    """
    Flattens a nested iterable

    Args:
        iterable (iter): to flatten

    Returns: iter

    """

    if isinstance(iterable, collections.Iterable):
        for item in iterable:
            yield from flatten(item)
    else:
        yield iterable


def product(nums):
    """
    Returns the product of a set of numbers

    Args:
        nums (iter): numbers

    Returns: float

    """
    return reduce(lambda x, y: x * y, nums, 1)


def with_timing(f, output=print):
    """
    Helper method to time and run a function and output the results

    Args:
        f (callable): function to decorate
        output (callable): function to output the time message

    Returns: callable decorated function

    """

    @wraps(f)
    def timed(*args, **kwargs):
        ts = time.time()
        result = f(*args, **kwargs)
        te = time.time()

        message = 'func:{!r} args:[{!r}, {!r}] took: {:2.4f} sec'.format(
            f.__name__, args, kwargs, te - ts
        )

        output(message)

        return result

    return timed