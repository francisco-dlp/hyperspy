"""Small numerical helpers used by widgets."""

import math

import numpy as np


def closest_nice_number(number):
    oom = 10 ** math.floor(math.log10(number))
    mantissa = number / oom
    refs = np.array([1, 2, 5, 10])
    logrefs = np.array([0.0, 0.6931, 1.6094, 2.3026])
    idx = np.argmin(np.abs(logrefs - np.log(mantissa)))
    return refs[idx] * oom
