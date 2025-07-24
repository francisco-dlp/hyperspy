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
from scipy.interpolate import make_interp_spline

from hyperspy.component import Component
from hyperspy.docstrings.parameters import FUNCTION_ND_DOCSTRING
from hyperspy.ui_registry import add_gui_method


@add_gui_method(toolkey="hyperspy.ScalableFixedPattern_Component")
class ScalableFixedPattern(Component):
    r"""Fixed pattern component with interpolation support.

    .. math::

        f(x) = a \cdot s \left(b \cdot x - x_0\right) + c

    ============ =============
     Variable     Parameter
    ============ =============
     :math:`a`    yscale
     :math:`b`    xscale
     :math:`x_0`  shift
    ============ =============

    Parameters
    ----------
    yscale : float
        The scaling factor in y (intensity axis).
    xscale : float
        The scaling factor in x.
    shift : float
        The shift of the component
    interpolate : bool
        If False no interpolation is performed and only a y-scaled spectrum is
        returned.

    Attributes
    ----------
    yscale : :class:`~.component.Parameter`
        The scaling factor in y (intensity axis).
    xscale : :class:`~.component.Parameter`
        The scaling factor in x.
    shift : :class:`~.component.Parameter`
        The shift of the component
    interpolate : bool
        If False no interpolation is performed and only a y-scaled spectrum is
        returned.

    Methods
    -------
    prepare_interpolator

    Examples
    --------

    The fixed pattern is defined by a Signal1D of navigation 0 which must be
    provided to the ScalableFixedPattern constructor, e.g.:

    >>> s = hs.load('data.hspy') # doctest: +SKIP
    >>> my_fixed_pattern = hs.model.components1D.ScalableFixedPattern(s) # doctest: +SKIP

    """

    def __init__(self, signal1D, yscale=1.0, xscale=1.0, shift=0.0, interpolate=True):
        Component.__init__(self, ["xscale", "yscale", "shift"], ["yscale"])

        self._position = self.shift
        self._whitelist["signal1D"] = ("init,sig", signal1D)
        self._whitelist["interpolate"] = None
        self.signal = signal1D
        self.yscale.free = True
        self.yscale.value = yscale
        self.xscale.value = xscale
        self.shift.value = shift

        self.prepare_interpolator()
        # Options
        self.isbackground = True
        self.convolved = False
        self.interpolate = interpolate

    @property
    def interpolate(self):
        return self._interpolate

    @interpolate.setter
    def interpolate(self, value):
        self._interpolate = value
        self.xscale.free = value
        self.shift.free = value

    def prepare_interpolator(self, **kwargs):
        """Fine-tune the interpolation.

        Parameters
        ----------
        x : array
            The spectral axis of the fixed pattern
        **kwargs : dict
            Keywords argument are passed to
            :func:`scipy.interpolate.make_interp_spline`
        """

        self.f = make_interp_spline(
            self.signal.axes_manager.signal_axes[0].axis,
            self.signal.data.squeeze(),
            **kwargs,
        )

    def _function(self, x, xscale, yscale, shift):
        if self.interpolate is True:
            result = yscale * self.f(x * xscale - shift)
        else:
            result = yscale * self.signal.data
        axis = self.signal.axes_manager.signal_axes[0]
        if axis.is_binned:
            if axis.is_uniform:
                return result / axis.scale
            else:
                return result / np.gradient(axis.axis)
        else:
            return result

    def function(self, x):
        return self._function(x, self.xscale.value, self.yscale.value, self.shift.value)

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
        if self._is_navigation_multidimensional:
            x = axis[np.newaxis, :]
            if parameters_values is None:
                parameters_values = [p.map["values"] for p in self.parameters]
            parameters_values = [p[..., np.newaxis] for p in parameters_values]
            return self._function(x, *parameters_values)
        else:
            return self.function(axis)

    function_nd.__doc__ %= FUNCTION_ND_DOCSTRING

    def grad_yscale(self, x):
        return self.function(x) / self.yscale.value

    def integrate(self, limits, variable="x", method="auto", **kwargs):
        """
        Integrate the scalable fixed pattern using analytical spline integration.

        This method uses SciPy's B-spline analytical integration capabilities to provide
        faster and exact integration when interpolation is enabled. B-splines are
        piecewise polynomials, so their integration is mathematically exact, not
        numerical approximation. When interpolation is disabled, it falls back to
        numerical integration.

        The component function is: f(x) = yscale * spline(xscale * x - shift)
        Integration accounts for the scaling and shifting transformations.

        Parameters
        ----------
        limits : tuple
            Integration limits (a, b) where a and b are the lower and upper bounds.
        variable : str, default 'x'
            Integration variable (included for API compatibility).
            method : str, default 'auto'
            Integration method to use:

            * 'auto' : use analytical spline integration when available, fallback to numerical
            * 'analytical' : use only analytical spline integration (raises error if unavailable)
            * 'numerical' : use only numerical integration
        **kwargs
            Additional arguments passed to the integration methods.

        Returns
        -------
        float
            The integration result using analytical spline integration when interpolation
            is enabled and method allows it, otherwise numerical integration.

        Raises
        ------
        ValueError
            If limits is not a tuple of length 2, or if method is invalid.
        NotImplementedError
            If method='analytical' but spline integration is not available.

        Notes
        -----
        When interpolation is enabled, the integration uses the mathematical
        transformation: ∫[a,b] yscale * spline(xscale * x - shift) dx
        = yscale * (1/xscale) * ∫[a',b'] spline(u) du
        where a' = xscale*a - shift and b' = xscale*b - shift

        The spline integration is analytical (exact) because B-splines are piecewise
        polynomials and polynomial integration is mathematically exact.

        Examples
        --------
        >>> # Create a ScalableFixedPattern component
        >>> signal = hs.signals.Signal1D(data)
        >>> sfp = hs.model.components1D.ScalableFixedPattern(signal)
        >>> result = sfp.integrate((0, 5))  # Uses analytical spline integration by default
        >>> result = sfp.integrate((0, 5), method='analytical')  # Force analytical
        >>> result = sfp.integrate((0, 5), method='numerical')   # Force numerical
        """
        # Validate method
        valid_methods = {"auto", "analytical", "numerical"}
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Supported: {valid_methods}")

        if not isinstance(limits, tuple) or len(limits) != 2:
            raise ValueError("limits must be a tuple of length 2: (a, b)")

        a, b = limits

        # Use analytical spline integration if available and requested
        spline_available = (
            self.interpolate and hasattr(self, "f") and hasattr(self.f, "integrate")
        )

        if method == "analytical" and not spline_available:
            raise NotImplementedError(
                "Analytical spline integration is not available. "
                "Ensure interpolation is enabled and spline is properly initialized."
            )

        if method in ("auto", "analytical") and spline_available:
            # Transform integration limits for scaled and shifted spline
            # f(x) = yscale * spline(xscale * x - shift)
            # ∫ f(x) dx = yscale * (1/xscale) * ∫ spline(u) du
            # where u = xscale * x - shift
            transformed_a = self.xscale.value * a - self.shift.value
            transformed_b = self.xscale.value * b - self.shift.value

            # Integrate the underlying spline (this is analytical, not numerical)
            spline_integral = self.f.integrate(transformed_a, transformed_b)

            # Apply scaling factors
            # d/dx [yscale * spline(xscale * x - shift)] = yscale * xscale * spline'(xscale * x - shift)
            # So ∫ yscale * spline(xscale * x - shift) dx = yscale * (1/xscale) * ∫ spline(u) du
            result = self.yscale.value * spline_integral / self.xscale.value

            return float(result)

        # Fall back to numerical integration from parent Component class
        return super().integrate(limits, variable, method, **kwargs)
