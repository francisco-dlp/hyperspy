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

"""Common docstring snippets for parameters."""

FUNCTION_ND_DOCSTRING = """parameters_values : list, None, optional
            List of parameters values used to calculate the component.
            The order of the parameter in the list is defined in the
            ``parameters`` attributes of the components
            If ``None``, the parameters values for all navigation positions
            are considered. The default is None.
        """

# Individual parameter docstrings for reuse across components
LIMITS_SIMPLE_DOCSTRING = """limits : tuple
            Integration limits (a, b) where a and b are the lower and upper bounds."""

LIMITS_COMPLEX_DOCSTRING = """limits : tuple or list of tuples
            Integration limits for the variable(s). For single variable: (a, b).
            For double integration: [(a1, b1), (a2, b2)] corresponding to variable
            order."""

VARIABLE_SIMPLE_DOCSTRING = """variable : str, default 'x'
            Integration variable (included for API compatibility)."""

VARIABLE_COMPLEX_DOCSTRING = """variable : str or tuple, default 'x'
            Variable(s) to integrate with respect to. For 1D components: 'x'.
            For 2D components: 'x', 'y', or ('x', 'y') for double integration.
            When integrating 2D components over single variables, fixed variable
            values must be provided as keyword arguments (e.g., y=1.0 when
            integrating over x)."""

METHOD_AUTO_NUMERICAL_DOCSTRING = """method : str, default 'auto'
            Integration method to use:

            * 'auto' : try symbolic first, fallback to numerical
            * 'symbolic' : use only symbolic integration
            * 'numerical' : use only numerical integration"""

METHOD_AUTO_ANALYTICAL_DOCSTRING = """method : str, default 'auto'
            Integration method to use:

            * 'auto' : use analytical spline integration when available, fallback to numerical
            * 'analytical' : use only analytical spline integration (raises error if unavailable)
            * 'numerical' : use only numerical integration"""

METHOD_ANALYTICAL_DOCSTRING = """method : str, default 'analytical'
            Integration method (ignored for constant function, included for API compatibility)."""

KWARGS_INTEGRATION_DOCSTRING = """**kwargs
            Additional keyword arguments passed to the integration methods."""

KWARGS_COMPATIBILITY_DOCSTRING = """**kwargs
            Additional arguments (ignored, included for API compatibility)."""

KWARGS_SPLINE_DOCSTRING = """**kwargs
            Additional arguments passed to the integration methods."""

# Integration-specific parameter combinations

INTEGRATION_PARAMETERS_DOCSTRING = """        limits : tuple or list of tuples
            Integration limits for the variable(s). For single variable: (a, b).
            For double integration: [(a1, b1), (a2, b2)] corresponding to variable
            order.
        variable : str or tuple, default 'x'
            Variable(s) to integrate with respect to. For 1D components: 'x'.
            For 2D components: 'x', 'y', or ('x', 'y') for double integration.
            When integrating 2D components over single variables, fixed variable
            values must be provided as keyword arguments (e.g., y=1.0 when
            integrating over x).
        method : str, default 'numerical'
            Integration method to use:

            * 'auto' : automatically select best available method (falls back to
              'numerical')
            * 'numerical' : use scipy.integrate.quad/dblquad for numerical
              integration
            * 'symbolic' : analytical integration (raises NotImplementedError for
              base Component)
        **kwargs
            Additional keyword arguments:

            * For marginal integration of 2D components: fixed variable values (e.g., y=1.0)
            * For scipy.integrate: additional integration options (epsabs, epsrel, etc.)"""

INTEGRATION_ND_PARAMETERS_DOCSTRING = """        limits : tuple or list of tuples
            Integration limits for the variable(s). For single variable: (a, b).
            For double integration: [(a1, b1), (a2, b2)] corresponding to variable order.
        variable : str or tuple, default 'x'
            Variable(s) to integrate with respect to. For 1D components: 'x'.
            For 2D components: 'x', 'y', or ('x', 'y') for double integration.
        method : str, default 'numerical'
            Integration method to use:

            * 'auto' : automatically select best available method (falls back to 'numerical')
            * 'numerical' : use scipy.integrate.quad/dblquad for numerical integration
            * 'symbolic' : analytical integration (raises NotImplementedError for base Component)
        **kwargs
            Additional keyword arguments passed to the integration backend."""


INTEGRATION_RETURNS_DOCSTRING = """Returns
        -------
        float or numpy.ndarray
            Integration result."""

INTEGRATION_EXAMPLES_RUNTIME_PARAMS_DOCSTRING = """        >>>
        >>> # Runtime parameter substitution
        >>> result = component.integrate((0, 5), parameters_values=[param1, param2, ...])"""

# Combined integration docstring templates for different components
OFFSET_INTEGRATION_TEMPLATE = """%s
        **kwargs
            Additional arguments (ignored, included for API compatibility).

        Returns
        -------
        float
            The analytical integration result: offset × (b - a).%s"""

SCALABLE_FIXED_PATTERN_INTEGRATION_TEMPLATE = """%s
        **kwargs
            Additional arguments passed to the integration methods.

        Returns
        -------
        float
            The integration result using analytical spline integration when interpolation
            is enabled and method allows it, otherwise numerical integration.%s"""

# Variable limits docstring templates
LIMITS_VARIABLE_DOCSTRING = """limits : tuple, array-like, or tuple of array-like
            Integration limits. Can be:

            * (a, b) : Fixed limits for all navigation positions
            * array-like : Variable limits with shape matching navigation dimensions.
              Each element should be a tuple (a, b) for that navigation position
            * For double integration: [(a1, b1), (a2, b2)] where each can be
              fixed or variable limits"""

LIMITS_VARIABLE_SIMPLE_DOCSTRING = """limits : tuple or array-like
            Integration limits (a, b) for single variable, or array of (a, b) tuples
            for variable limits across navigation dimensions."""

EXPRESSION_INTEGRATION_TEMPLATE = """%s
        **kwargs
            Additional keyword arguments passed to the integration methods.

        Returns
        -------
        float or numpy.ndarray
            Integration result.%s"""
