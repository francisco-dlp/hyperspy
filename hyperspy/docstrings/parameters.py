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
