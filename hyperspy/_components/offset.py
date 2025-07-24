# -*- coding: utf-8 -*-
# Copyright 2007-2025 The HyperSpy developers
#
# This file is part of HyperSpy.
#
# HyperSpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HyperSpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HyperSpy. If not, see <https://www.gnu.org/licenses/#GPL>.


import numpy as np

from hyperspy.component import Component
from hyperspy.docstrings.parameters import FUNCTION_ND_DOCSTRING


class Offset(Component):
    r"""Component to add a constant value in the y-axis.

    .. math::

        f(x) = k

    ============ =============
    Variable      Parameter
    ============ =============
    :math:`k`     offset
    ============ =============

    Parameters
    ----------
    offset : float
        The offset to be fitted

    """

    def __init__(self, offset=0.0):
        Component.__init__(self, ("offset",), ["offset"])
        self.offset.free = True
        self.offset.value = offset

        self.isbackground = True
        self.convolved = False

        # Gradients
        self.offset.grad = self.grad_offset

    def function(self, x):
        return self._function(x, self.offset.value)

    def _function(self, x, o):
        return np.ones_like(x) * o

    @staticmethod
    def grad_offset(x):
        return np.ones_like(x)

    def estimate_parameters(self, signal, x1, x2, only_current=False):
        """Estimate the parameters by the two area method

        Parameters
        ----------
        signal : :class:`~.api.signals.Signal1D`
        x1 : float
            Defines the left limit of the spectral range to use for the
            estimation.
        x2 : float
            Defines the right limit of the spectral range to use for the
            estimation.

        only_current : bool
            If False estimates the parameters for the full dataset.

        Returns
        -------
        bool

        """
        super()._estimate_parameters(signal)
        axis = signal.axes_manager.signal_axes[0]
        i1, i2 = axis.value_range_to_indices(x1, x2)
        if axis.is_binned:
            # using the mean of the gradient for non-uniform axes is a best
            # guess to the scaling of binned signals for the estimation
            scaling_factor = (
                axis.scale
                if axis.is_uniform
                else np.mean(np.gradient(axis.axis), axis=-1)
            )

        if only_current is True:
            self.offset.value = signal._get_current_data()[i1:i2].mean()
            if axis.is_binned:
                self.offset.value /= scaling_factor
            return True
        else:
            if self.offset.map is None:
                self._create_arrays()
            dc = signal.data
            gi = [
                slice(None),
            ] * len(dc.shape)
            gi[axis.index_in_array] = slice(i1, i2)
            self.offset.map["values"][:] = dc[tuple(gi)].mean(axis.index_in_array)
            if axis.is_binned:
                self.offset.map["values"] /= scaling_factor
            self.offset.map["is_set"][:] = True
            self.fetch_stored_values()
            return True

    def function_nd(self, axis, parameters_values=None):
        """
        Calculate the component over given axes and with given parameter values.

        Parameters
        ----------
        axis : numpy.ndarray
            The axis onto which the component is calculated.
        %s

        Returns
        -------
        numpy.ndarray
            The component values.
        """
        if parameters_values is None:
            parameters_values = [self.offset.map["values"]]
        if self._is_navigation_multidimensional:
            x = axis[np.newaxis, :]
            o = parameters_values[0][..., np.newaxis]
        else:
            x = axis
            o = self.offset.value
        return self._function(x, o)

    function_nd.__doc__ %= FUNCTION_ND_DOCSTRING

    def integrate(
        self,
        limits,
        variable="x",
        method="analytical",
        parameters_values=None,
        **kwargs,
    ):
        """
        Analytical integration of the constant offset function.

        For a constant function f(x) = k, the integral from a to b is k × (b - a).
        This is much faster and more accurate than numerical integration.

        Parameters
        ----------
        limits : tuple
            Integration limits (a, b) where a and b are the lower and upper bounds.
        variable : str, default 'x'
            Integration variable (ignored for constant function, included for API compatibility).
        method : str, default 'analytical'
            Integration method (ignored for constant function, included for API compatibility).
        %s
        **kwargs
            Additional arguments (ignored, included for API compatibility).

        Returns
        -------
        float
            The analytical integration result: offset × (b - a).

        Raises
        ------
        ValueError
            If limits is not a tuple of length 2.

        Examples
        --------
        >>> offset = hs.model.components1D.Offset(offset=5.0)
        >>> result = offset.integrate((0, 3))  # Returns 15.0
        >>> result = offset.integrate((-1, 2))  # Returns 15.0
        >>>
        >>> # Runtime parameter substitution
        >>> result = offset.integrate((0, 3), parameters_values=[10.0])  # Returns 30.0
        """
        if not isinstance(limits, tuple) or len(limits) != 2:
            raise ValueError("limits must be a tuple of length 2: (a, b)")

        a, b = limits

        # Use provided parameter values or current values
        if parameters_values is None:
            offset_value = self.offset.value
        else:
            if len(parameters_values) != 1:
                raise ValueError(
                    f"Expected 1 parameter value, got {len(parameters_values)}"
                )
            offset_value = parameters_values[0]

        # For constant function f(x) = k, integral from a to b is k * (b - a)
        return offset_value * (b - a)

    @property
    def _constant_term(self):
        "Get value of constant term of component"
        # First get currently constant parameters
        if self.offset.free:
            return 0
        else:
            return self.offset.value


# Apply dynamic docstring interpolation following HyperSpy patterns
Offset.integrate.__doc__ %= FUNCTION_ND_DOCSTRING
