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
from hyperspy.docstrings.parameters import (
    FUNCTION_ND_DOCSTRING,
)
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

    def integrate_nd(
        self, limits, variable="x", method="auto", parameters_values=None, **kwargs
    ):
        """
        Integrate the scalable fixed pattern over multiple parameter sets simultaneously.

        This method efficiently computes the integral for multidimensional navigation
        arrays of parameters, similar to function_nd. It uses analytical spline integration
        when interpolation is enabled, falling back to numerical integration otherwise.

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
        parameters_values : list, optional
            List of parameter arrays for multidimensional navigation. If None,
            uses the parameter maps. Should contain three arrays: [xscale_values, yscale_values, shift_values].
        **kwargs
            Additional arguments passed to the integration methods.

        Returns
        -------
        numpy.ndarray
            Integration results with shape matching the navigation dimensions.
            For single parameter set, returns a scalar.

        Examples
        --------
        >>> # Create ScalableFixedPattern with navigation-dependent parameters
        >>> signal = hs.signals.Signal1D(data)
        >>> sfp = hs.model.components1D.ScalableFixedPattern(signal)
        >>> # Integration with parameter arrays
        >>> xscale_vals = np.array([1.0, 1.5, 2.0])
        >>> yscale_vals = np.array([2.0, 3.0, 4.0])
        >>> shift_vals = np.array([0.0, 0.5, 1.0])
        >>> results = sfp.integrate_nd((0, 5), parameters_values=[xscale_vals, yscale_vals, shift_vals])
        """
        # Validate method
        valid_methods = {"auto", "analytical", "numerical"}
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Supported: {valid_methods}")

        if not isinstance(limits, tuple) or len(limits) != 2:
            raise ValueError("limits must be a tuple of length 2: (a, b)")

        # Use provided parameter values or get from parameter maps
        if parameters_values is None:
            if self._is_navigation_multidimensional:
                try:
                    parameters_values = [
                        self.xscale.map["values"],
                        self.yscale.map["values"],
                        self.shift.map["values"],
                    ]
                except (TypeError, AttributeError):
                    raise RuntimeError(
                        "Parameter maps must be set for multidimensional integration. "
                        "Use function_nd first or provide parameters_values explicitly."
                    )
            else:
                # Single parameter case - use regular integrate method
                return self.integrate(limits, variable, method, **kwargs)

        # Validate parameter arrays
        if len(parameters_values) != 3:
            raise ValueError(
                f"Expected 3 parameter arrays [xscale, yscale, shift], got {len(parameters_values)}"
            )

        xscale_values, yscale_values, shift_values = parameters_values

        # Check if analytical integration is possible and requested
        analytical_available = (
            hasattr(self, "_interpolator") and self._interpolator is not None
        )

        if method == "analytical" and not analytical_available:
            raise NotImplementedError(
                "Analytical integration is not available. "
                "Enable interpolation or use method='numerical'."
            )

        # Use analytical integration if available and requested
        if method in ("auto", "analytical") and analytical_available:
            try:
                return self._integrate_analytical_nd(
                    limits, xscale_values, yscale_values, shift_values
                )
            except Exception as e:
                if method == "analytical":
                    raise NotImplementedError(f"Analytical integration failed: {e}")
                # Fall through to numerical for 'auto'

        # Use numerical integration
        if method in ("auto", "numerical"):
            return self._integrate_numerical_nd(
                limits, xscale_values, yscale_values, shift_values, **kwargs
            )

        raise RuntimeError(f"Integration failed for method '{method}'")

    def _integrate_analytical_nd(
        self, limits, xscale_values, yscale_values, shift_values
    ):
        """Perform analytical spline integration for parameter arrays."""
        a, b = limits
        nav_shape = xscale_values.shape
        results = np.zeros(nav_shape)

        # Compute integration for each navigation position
        for idx in np.ndindex(nav_shape):
            xscale_val = xscale_values[idx]
            yscale_val = yscale_values[idx]
            shift_val = shift_values[idx]

            # Apply the coordinate transformation for spline integration
            # f(x) = yscale * spline(xscale * x - shift)
            # ∫f(x)dx = yscale * (1/xscale) * ∫spline(u)du where u = xscale*x - shift
            a_transformed = xscale_val * a - shift_val
            b_transformed = xscale_val * b - shift_val

            # Use the spline's antiderivative
            spline_integral = self._interpolator.antiderivative()
            integral_value = spline_integral(b_transformed) - spline_integral(
                a_transformed
            )

            # Apply scaling factors
            results[idx] = yscale_val * (1.0 / xscale_val) * integral_value

        return results

    def _integrate_numerical_nd(
        self, limits, xscale_values, yscale_values, shift_values, **kwargs
    ):
        """Perform numerical integration for parameter arrays."""
        from scipy.integrate import quad

        a, b = limits
        nav_shape = xscale_values.shape
        results = np.zeros(nav_shape)

        # Store original parameter values
        original_xscale = self.xscale.value
        original_yscale = self.yscale.value
        original_shift = self.shift.value

        try:
            # Compute integration for each navigation position
            for idx in np.ndindex(nav_shape):
                # Set parameter values for this navigation position
                self.xscale.value = xscale_values[idx]
                self.yscale.value = yscale_values[idx]
                self.shift.value = shift_values[idx]

                # Use numerical integration
                def integrand(x_val):
                    return self.function(x_val)

                results[idx], _ = quad(integrand, a, b)

        finally:
            # Restore original parameter values
            self.xscale.value = original_xscale
            self.yscale.value = original_yscale
            self.shift.value = original_shift

        return results

    def grad_yscale(self, x):
        return self.function(x) / self.yscale.value

    def integrate(
        self, limits, variable="x", method="auto", parameters_values=None, **kwargs
    ):
        """
        Integrate the scalable fixed pattern using analytical spline integration.

        This method uses SciPy's B-spline analytical integration capabilities to provide
        faster and exact integration when interpolation is enabled. B-splines are
        piecewise polynomials, so their integration is mathematically exact, not
        numerical approximation. When interpolation is disabled, it falls back to
        numerical integration.

        The component function is: f(x) = yscale * spline(xscale * x - shift)
        Integration accounts for the scaling and shifting transformations.

        Supports both fixed and variable integration limits for navigation-aware
        integration across multiple parameter sets.

        Parameters
        ----------
        limits : tuple, array-like, or tuple of array-like
            Integration limits. Can be:

            * (a, b) : Fixed limits for all navigation positions
            * (a_array, b_array) : Variable limits with arrays matching navigation dimensions
            * array of (a, b) tuples : Variable limits for each navigation position
        variable : str, default 'x'
            Integration variable (included for API compatibility).
        method : str, default 'auto'
            Integration method to use:

            * 'auto' : use analytical spline integration when available, fallback to numerical
            * 'analytical' : use only analytical spline integration (raises error if unavailable)
            * 'numerical' : use only numerical integration
        parameters_values : list, None, optional
            List of parameters values used to calculate the component.
            The order of the parameter in the list is defined in the
            ``parameters`` attributes of the components
            If ``None``, the parameters values for all navigation positions
            are considered. The default is None.
        **kwargs
            Additional arguments passed to the integration methods.

        Returns
        -------
        float or numpy.ndarray
            The integration result using analytical spline integration when interpolation
            is enabled and method allows it, otherwise numerical integration.
            Returns scalar for fixed limits, or array matching navigation dimensions
            for variable limits.

        Raises
        ------
        ValueError
            If limits format is invalid, or if method is invalid.
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
        >>>
        >>> # Variable limits integration
        >>> import numpy as np
        >>> a_vals = np.array([0, 1])
        >>> b_vals = np.array([5, 6])
        >>> results = sfp.integrate((a_vals, b_vals))
        >>>
        >>> result = sfp.integrate((0, 5), method='analytical')  # Force analytical
        >>> result = sfp.integrate((0, 5), method='numerical')   # Force numerical
        >>>
        >>> # Runtime parameter substitution [xscale, yscale, shift]
        >>> result = sfp.integrate((0, 5), parameters_values=[2.0, 3.0, 1.0])
        """

        # Validate method
        valid_methods = {"auto", "analytical", "numerical"}
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Supported: {valid_methods}")

        # Check if we have variable limits
        nav_shape = getattr(self, "_navigation_shape", None)
        is_variable_limits, parsed_limits = self._parse_limits(limits, nav_shape)

        if is_variable_limits:
            # Variable limits - analytical integration with variable limits
            # is complex for splines, so fall back to numerical for now
            if method == "analytical":
                raise NotImplementedError(
                    "Analytical spline integration with variable limits is not currently supported. "
                    "Use method='numerical' or 'auto' for variable limits integration."
                )

            # Use numerical integration for variable limits
            if parameters_values is not None:
                return self._integrate_numerical_variable_with_params(
                    parsed_limits, variable, parameters_values, **kwargs
                )
            else:
                return super().integrate(limits, variable, method="numerical", **kwargs)

        # Fixed limits - proceed with original logic
        if not isinstance(limits, tuple) or len(limits) != 2:
            raise ValueError("For fixed limits, must be a tuple of length 2: (a, b)")

        a, b = limits

        # Get parameter values (using provided values or current values)
        if parameters_values is None:
            xscale_value = self.xscale.value
            yscale_value = self.yscale.value
            shift_value = self.shift.value
        else:
            if len(parameters_values) != 3:
                raise ValueError(
                    f"Expected 3 parameter values [xscale, yscale, shift], got {len(parameters_values)}"
                )
            xscale_value, yscale_value, shift_value = parameters_values

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
            transformed_a = xscale_value * a - shift_value
            transformed_b = xscale_value * b - shift_value

            # Integrate the underlying spline (this is analytical, not numerical)
            spline_integral = self.f.integrate(transformed_a, transformed_b)

            # Apply scaling factors
            # d/dx [yscale * spline(xscale * x - shift)] = yscale * xscale * spline'(xscale * x - shift)
            # So ∫ yscale * spline(xscale * x - shift) dx = yscale * (1/xscale) * ∫ spline(u) du
            result = yscale_value * spline_integral / xscale_value

            return float(result)

        # Fall back to numerical integration
        if method in ("auto", "numerical"):
            # If parameters_values is provided, we need to handle numerical integration ourselves
            if parameters_values is not None:
                return self._integrate_numerical_with_params(
                    limits, variable, parameters_values, **kwargs
                )
            else:
                return super().integrate(limits, variable, method, **kwargs)

        raise RuntimeError(f"Integration failed for method '{method}'")

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
            transformed_a = xscale_value * a - shift_value
            transformed_b = xscale_value * b - shift_value

            # Integrate the underlying spline (this is analytical, not numerical)
            spline_integral = self.f.integrate(transformed_a, transformed_b)

            # Apply scaling factors
            # d/dx [yscale * spline(xscale * x - shift)] = yscale * xscale * spline'(xscale * x - shift)
            # So ∫ yscale * spline(xscale * x - shift) dx = yscale * (1/xscale) * ∫ spline(u) du
            result = yscale_value * spline_integral / xscale_value

            return float(result)

        # Fall back to numerical integration
        if method in ("auto", "numerical"):
            # If parameters_values is provided, we need to handle numerical integration ourselves
            if parameters_values is not None:
                return self._integrate_numerical_with_params(
                    limits, variable, parameters_values, **kwargs
                )
            else:
                return super().integrate(limits, variable, method, **kwargs)

        raise RuntimeError(f"Integration failed for method '{method}'")

    def _integrate_numerical_with_params(
        self, limits, variable, parameters_values, **kwargs
    ):
        """Perform numerical integration with custom parameter values."""
        from scipy.integrate import quad

        # Temporarily store original parameter values
        original_xscale = self.xscale.value
        original_yscale = self.yscale.value
        original_shift = self.shift.value

        try:
            # Set the provided parameter values
            xscale_value, yscale_value, shift_value = parameters_values
            self.xscale.value = xscale_value
            self.yscale.value = yscale_value
            self.shift.value = shift_value

            # Use numerical integration
            a, b = limits

            def integrand(x_val):
                return self.function(x_val)

            result, _ = quad(integrand, a, b)
            return result

        finally:
            # Restore original parameter values
            self.xscale.value = original_xscale
            self.yscale.value = original_yscale
            self.shift.value = original_shift

    def _integrate_numerical_variable_with_params(
        self, parsed_limits, variable, parameters_values, **kwargs
    ):
        """Handle numerical variable limits integration with parameter substitution."""
        import numpy as np
        from scipy.integrate import quad

        # Extract limits - could be (a_array, b_array) or array of (a,b) tuples
        if isinstance(parsed_limits, tuple) and len(parsed_limits) == 2:
            # Format: (a_array, b_array)
            a_array, b_array = parsed_limits
        else:
            # Format: array of (a,b) tuples
            limits_array = np.asarray(parsed_limits)
            a_array = limits_array[..., 0]
            b_array = limits_array[..., 1]

        # Initialize results array with same shape as limits
        results = np.zeros_like(a_array, dtype=float)

        # Store original parameter values
        original_xscale = self.xscale.value
        original_yscale = self.yscale.value
        original_shift = self.shift.value

        try:
            # Set the provided parameter values
            xscale_value, yscale_value, shift_value = parameters_values
            self.xscale.value = xscale_value
            self.yscale.value = yscale_value
            self.shift.value = shift_value

            # Integrate for each navigation position
            for idx in np.ndindex(a_array.shape):
                a = a_array[idx]
                b = b_array[idx]

                def integrand(x_val):
                    return self.function(x_val)

                results[idx] = quad(integrand, a, b)[0]

        finally:
            # Restore original parameter values
            self.xscale.value = original_xscale
            self.yscale.value = original_yscale
            self.shift.value = original_shift

        return results if results.size > 1 else results.item()
