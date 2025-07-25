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

import importlib
import logging
import warnings
from functools import wraps

import numpy as np
import sympy

from hyperspy.component import Component
from hyperspy.docstrings.parameters import (
    FUNCTION_ND_DOCSTRING,
)

_logger = logging.getLogger(__name__)


class DivergentIntegralError(ValueError):
    """Exception raised when an integral is mathematically divergent.

    This exception should be raised when symbolic analysis determines that
    an integral diverges to infinity, rather than attempting numerical
    integration which may produce misleading results.
    """

    pass


_CLASS_DOC = """%s component (created with Expression).

.. math::

    f(x) = %s

"""


def _fill_function_args(fn):
    @wraps(fn)
    def fn_wrapped(self, x):
        return fn(x, *[p.value for p in self.parameters])

    return fn_wrapped


def _fill_function_args_2d(fn):
    @wraps(fn)
    def fn_wrapped(self, x, y):
        return fn(x, y, *[p.value for p in self.parameters])

    return fn_wrapped


def _parse_substitutions(string):
    splits = map(str.strip, string.split(";"))
    expr = sympy.sympify(next(splits))
    # We substitute one by one manually, as passing all at the same time does
    # not work as we want (substitutions inside other substitutions do not work)
    for sub in splits:
        t = tuple(map(str.strip, sub.split("=")))
        expr = expr.subs(t[0], sympy.sympify(t[1]))
    return expr


class Expression(Component):
    """Create a component from a string expression.

    It automatically generates the partial derivatives and the
    class docstring.

    Parameters
    ----------
    expression : str
        Component function in SymPy text expression format with
        substitutions separated by `;`. See examples and the SymPy
        documentation for details. In order to vary the components along the
        signal dimensions, the variables `x` and `y` must be included for 1D
        or 2D components. Also, if `module` is "numexpr" the
        functions are limited to those that numexpr support. See its
        documentation for details.
    name : str
        Name of the component.
    position : str, optional
        The parameter name that defines the position of the component if
        applicable. It enables interative adjustment of the position of the
        component in the model. For 2D components, a tuple must be passed
        with the name of the two parameters e.g. `("x0", "y0")`.
    module : None or str {``"numpy"`` | ``"numexpr"`` | ``"scipy"``}, default "numpy"
        Module used to evaluate the function. numexpr is often faster but
        it supports fewer functions and requires installing numexpr.
        If None, the "numexpr" will be used if installed.
    add_rotation : bool, default False
        This is only relevant for 2D components. If `True` it automatically
        adds `rotation_angle` parameter.
    rotation_center : None or tuple
        If None, the rotation center is the center i.e. (0, 0) if `position`
        is not defined, otherwise the center is the coordinates specified
        by `position`. Alternatively a tuple with the (x, y) coordinates
        of the center can be provided.
    rename_pars : dict
        The desired name of a parameter may sometimes coincide with e.g.
        the name of a scientific function, what prevents using it in the
        `expression`. `rename_parameters` is a dictionary to map the name
        of the parameter in the `expression`` to the desired name of the
        parameter in the `Component`. For example: {"_gamma": "gamma"}.
    compute_gradients : bool, optional
        If `True`, compute the gradient automatically using sympy. If sympy
        does not support the calculation of the partial derivatives, for
        example in case of expression containing a "where" condition,
        it can be disabled by using `compute_gradients=False`.
    linear_parameter_list : list
        A list of the components parameters that are known to be linear
        parameters.
    check_parameter_linearity : bool
        If `True`, automatically check if each parameter is linear and set
        its corresponding attribute accordingly. If `False`, the default is to
        set all parameters, except for those who are specified in
        ``linear_parameter_list``.

    **kwargs : dict
        Keyword arguments can be used to initialise the value of the
        parameters.

    Notes
    -----
    As of version 1.4, Sympy's lambdify function, that the
    :class:`~.api.model.components1D.Expression`
    components uses internally, does not support the differentiation of
    some expressions, for example those containing a "where" condition.
    In such cases, the gradients can be set manually if required.

    Examples
    --------
    The following creates a Gaussian component and set the initial value
    of the parameters:

    >>> hs.model.components1D.Expression(
    ... expression="height * exp(-(x - x0) ** 2 * 4 * log(2)/ fwhm ** 2)",
    ... name="Gaussian",
    ... height=1,
    ... fwhm=1,
    ... x0=0,
    ... position="x0",)
    <Gaussian (Expression component)>

    Substitutions for long or complicated expressions are separated by
    semicolumns:

    >>> expr = 'A*B/(A+B) ; A = sin(x)+one; B = cos(y) - two; y = tan(x)'
    >>> comp = hs.model.components1D.Expression(
    ...    expression=expr,
    ...    name='my function'
    ... )
    >>> comp.parameters
    (<Parameter one of my function component>,
     <Parameter two of my function component>)

    """

    def __init__(
        self,
        expression,
        name,
        position=None,
        module="numpy",
        autodoc=True,
        add_rotation=False,
        rotation_center=None,
        rename_pars={},
        compute_gradients=True,
        compute_integrals=False,
        linear_parameter_list=None,
        check_parameter_linearity=True,
        **kwargs,
    ):
        if module is None:
            module = "numexpr"

        if module == "numexpr":
            numexpr_spec = importlib.util.find_spec("numexpr")
            if numexpr_spec is None:
                module = "numpy"
                _logger.warning(
                    "Numexpr is not installed, falling back to numpy, "
                    "which is slower to calculate model."
                )

        if linear_parameter_list is None:
            linear_parameter_list = []
        self._add_rotation = add_rotation
        self._str_expression = expression
        self._module = module
        self._rename_pars = rename_pars if rename_pars is not None else {}
        # Since the expression string uses the parameter name before renaming
        # it is useful to have the inverse mapping
        self._rename_pars_inv = {v: k for k, v in self._rename_pars.items()}
        self._compute_gradients = compute_gradients
        self._compute_integrals = compute_integrals

        if rotation_center is None:
            self.compile_function(module=module, position=position)
        else:
            self.compile_function(module=module, position=rotation_center)

        # Initialise component
        Component.__init__(self, self._parameter_strings, linear_parameter_list)
        # When creating components using Expression (for example GaussianHF)
        # we shouldn't add anything else to the _whitelist as the
        # component should be initizialized with its own kwargs.
        # An exception is "module"
        self._whitelist["module"] = ("init", module)
        if self.__class__ is Expression:
            self._whitelist["expression"] = ("init", expression)
            self._whitelist["name"] = ("init", name)
            self._whitelist["position"] = ("init", position)
            self._whitelist["rename_pars"] = ("init", rename_pars)
            self._whitelist["linear_parameter_list"] = ("init", linear_parameter_list)
            self._whitelist["compute_gradients"] = ("init", compute_gradients)
            if self._is2D:
                self._whitelist["add_rotation"] = ("init", self._add_rotation)
                self._whitelist["rotation_center"] = ("init", rotation_center)
        self.name = name

        # Set the position parameter
        if position:
            if self._is2D:
                self._position_x = getattr(self, position[0])
                self._position_y = getattr(self, position[1])
            else:
                self._position = getattr(self, position)

        # Set the initial value of the parameters
        if kwargs:
            for kwarg, value in kwargs.items():
                setattr(getattr(self, kwarg), "value", value)

        if autodoc:
            self.__doc__ = _CLASS_DOC % (name, sympy.latex(self._parsed_expr))

        for parameter_name in linear_parameter_list:
            setattr(getattr(self, parameter_name), "_linear", True)

        if check_parameter_linearity:
            for p in self.parameters:
                if p.name not in linear_parameter_list:
                    # _parsed_expr used "non public" parameter name and we
                    # need to use the correct parameter name by using
                    # _rename_pars_inv
                    p._linear = _check_parameter_linearity(
                        self._parsed_expr, self._rename_pars_inv.get(p.name, p.name)
                    )

    def compile_function(self, module, position=False):
        """
        Compile the function and calculate the gradient automatically when
        possible.
        Useful to recompile the function and gradient with a different module.
        """
        try:  # Expression is just a constant
            float(self._str_expression)
        except ValueError:
            pass
        else:
            raise ValueError("Expression must contain a symbol, i.e. x, a, etc.")
        expr = _parse_substitutions(self._str_expression)
        self._parsed_expr = expr

        # Extract x
        x = [symbol for symbol in expr.free_symbols if symbol.name == "x"]
        if not x:  # Expression is just a parameter, no x -> Offset
            # lambdify doesn't support constant
            # https://github.com/sympy/sympy/issues/5642
            # x = [sympy.Symbol('x')]
            raise ValueError('Expression must contain the "x" symbol.')
        x = x[0]
        # Extract y
        y = [symbol for symbol in expr.free_symbols if symbol.name == "y"]

        self._is2D = True if y else False
        if self._is2D:
            y = y[0]
        if self._is2D and self._add_rotation:
            position = position or (0, 0)
            rotx = sympy.sympify(
                "{0} + (x - {0}) * cos(rotation_angle) - (y - {1}) *"
                " sin(rotation_angle)".format(*position)
            )
            roty = sympy.sympify(
                "{1} + (x - {0}) * sin(rotation_angle) + (y - {1}) *"
                "cos(rotation_angle)".format(*position)
            )
            expr = expr.subs({"x": rotx, "y": roty}, simultaneous=False)
        original_vars = [symbol for symbol in expr.free_symbols]
        real_vars = sympy.symbols([symbol.name for symbol in original_vars], real=True)
        # just replace with the assumption that all our variables are real
        # as this helps with differentiation
        expr = expr.subs(
            {orig: real_ for (orig, real_) in zip(original_vars, real_vars)}
        )
        eval_expr = expr.evalf()
        # Extract parameters
        variables = ("x", "y") if self._is2D else ("x",)
        parameters = [
            symbol for symbol in expr.free_symbols if symbol.name not in variables
        ]
        # to have a reliable order
        parameters.sort(key=lambda parameter: parameter.name)
        # Create compiled function
        variables = [x, y] if self._is2D else [x]
        self._f = sympy.utilities.lambdify(
            variables + parameters, eval_expr, modules=module, dummify=False
        )

        if self._is2D:

            def f(x, y):
                return self._f(x, y, *[p.value for p in self.parameters])
        else:

            def f(x):
                return self._f(x, *[p.value for p in self.parameters])

        setattr(self, "function", f)
        parnames = [
            self._rename_pars.get(symbol.name, symbol.name) for symbol in parameters
        ]
        self._parameter_strings = parnames

        if self._compute_gradients:
            try:
                ffargs = _fill_function_args_2d if self._is2D else _fill_function_args
                for p in parameters:
                    grad_expr = sympy.diff(eval_expr, p)
                    name = self._rename_pars.get(p.name, p.name)
                    f_grad = sympy.utilities.lambdify(
                        variables + parameters,
                        grad_expr.evalf(),
                        modules=module,
                        dummify=False,
                    )
                    grad_p = ffargs(f_grad).__get__(self, Expression)
                    if len(grad_expr.free_symbols) == 0:
                        # Vectorize in case of constant function
                        # https://github.com/sympy/sympy/issues/5642
                        grad_p = np.vectorize(grad_p)
                    setattr(self, f"grad_{name}", grad_p)

            except (SyntaxError, AttributeError):
                warnings.warn(
                    "The gradients can not be computed with sympy.", UserWarning
                )

        # Compute symbolic integrals
        if self._compute_integrals:
            try:
                # Use the actual symbols x and y instead of variables list
                var_symbols = [x] if not self._is2D else [x, y]

                # Create integral functions for each variable
                for var in var_symbols:
                    var_name = var.name
                    # Create integral function for this variable - use self._parsed_expr
                    integral_expr = sympy.integrate(self._parsed_expr, var)

                    # Create a lambda function that evaluates the indefinite integral
                    f_integral = sympy.lambdify(
                        var_symbols + parameters,
                        integral_expr,
                        modules=module,
                        dummify=False,
                    )

                    # Store the symbolic integral and lambda function
                    setattr(self, f"_integral_{var_name}_expr", integral_expr)
                    setattr(self, f"_integral_{var_name}_func", f_integral)

                # Set flag to indicate symbolic integration is available
                self._symbolic_integration_available = True

            except (SyntaxError, AttributeError, NotImplementedError) as e:
                warnings.warn(
                    f"Symbolic integrals cannot be computed with sympy: {e}. "
                    "Integration will fall back to numerical methods.",
                    UserWarning,
                )
                # Set flag to indicate symbolic integration failed
                self._symbolic_integration_available = False
        else:
            self._symbolic_integration_available = False

    def function_nd(self, *args, parameters_values=None):
        """Calculate the component over given axes and with given parameter values.

        Parameters
        ----------
        *args : numpy.ndarray
            The axes onto which the component is calculated.
            For 1D component, only a single array of dimension 1 is necessary.
            For 2D component, two arrays of dimension 1 are necessary.
        %s

        Returns
        -------
        numpy.ndarray
            The component values.
        """
        if parameters_values is None:
            parameters_values = []
            try:
                parameters_values = [p.map["values"] for p in self.parameters]
            except TypeError:
                # When p.map is None
                raise RuntimeError(
                    "The parameter map must be set before using `function_nd`."
                )

        if self._is2D:
            x, y = args[0], args[1]
            # navigation dimension is 0, f_nd same as f
            if not self._is_navigation_multidimensional:
                return self.function(x, y)
            else:
                return self._f(
                    x[np.newaxis, ...],
                    y[np.newaxis, ...],
                    *[p[..., np.newaxis, np.newaxis] for p in parameters_values],
                )
        else:
            x = args[0]
            if not self._is_navigation_multidimensional:
                return self.function(x)
            else:
                return self._f(
                    x[np.newaxis, ...],
                    *[p[..., np.newaxis] for p in parameters_values],
                )

    function_nd.__doc__ %= FUNCTION_ND_DOCSTRING

    def integrate_nd(
        self, limits, variable="x", method="auto", parameters_values=None, **kwargs
    ):
        """Integrate the expression over multiple parameter sets simultaneously.

        This method efficiently computes the integral for multidimensional navigation
        arrays of parameters, similar to function_nd. It attempts symbolic integration
        when available, falling back to numerical integration.

        Parameters
        ----------
        limits : tuple or list of tuple
            Integration limits for the variable(s). For single variable: (a, b).
            For double integration: [(a1, b1), (a2, b2)] corresponding to variable order.
        variable : str or tuple, default 'x'
            Variable(s) to integrate with respect to. For 1D components: 'x'.
            For 2D components: 'x', 'y', or ('x', 'y') for double integration.
        method : str, default 'auto'
            Integration method to use:

            * 'auto' : try symbolic first, fallback to numerical
            * 'symbolic' : use only symbolic integration
            * 'numerical' : use only numerical integration
        parameters_values : list, optional
            List of parameter arrays for multidimensional navigation. If None,
            uses the parameter maps. Each array should match the navigation shape.
        **kwargs
            Additional keyword arguments passed to the integration methods.

        Returns
        -------
        numpy.ndarray
            Integration results with shape matching the navigation dimensions.
            For single parameter set, returns a scalar.

        Examples
        --------
        >>> # Create expression with navigation-dependent parameters
        >>> expr = hs.model.components1D.Expression('a*x + b', name='linear')
        >>> # Integration with parameter arrays
        >>> a_values = np.array([1.0, 2.0, 3.0])
        >>> b_values = np.array([0.0, 1.0, 2.0])
        >>> results = expr.integrate_nd((0, 2), parameters_values=[a_values, b_values])
        """
        # Validate method
        valid_methods = {"auto", "symbolic", "numerical"}
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Supported: {valid_methods}")

        # Use provided parameter values or get from parameter maps
        if parameters_values is None:
            if self._is_navigation_multidimensional:
                try:
                    parameters_values = [p.map["values"] for p in self.parameters]
                except (TypeError, AttributeError):
                    raise RuntimeError(
                        "Parameter maps must be set for multidimensional integration. "
                        "Use function_nd first or provide parameters_values explicitly."
                    )
            else:
                # Single parameter case - use regular integrate method
                return self.integrate(limits, variable, method, **kwargs)

        # Check if symbolic integration is available and requested
        symbolic_available = (
            hasattr(self, "_symbolic_integration_available")
            and self._symbolic_integration_available
        )

        if method == "symbolic" and not symbolic_available:
            raise NotImplementedError(
                "Symbolic integration is not available. "
                "Enable it with compute_integrals=True when creating the Expression component."
            )

        # Try symbolic integration first if available and requested
        if method in ("auto", "symbolic") and symbolic_available:
            try:
                return self._integrate_symbolic_nd(
                    limits, variable, parameters_values, **kwargs
                )
            except Exception as e:
                if method == "symbolic":
                    raise NotImplementedError(f"Symbolic integration failed: {e}")
                # Fall through to numerical for 'auto'

        # Use numerical integration
        if method in ("auto", "numerical"):
            return self._integrate_numerical_nd(
                limits, variable, parameters_values, **kwargs
            )

        raise RuntimeError(f"Integration failed for method '{method}'")

    def _integrate_symbolic_nd(self, limits, variable, parameters_values, **kwargs):
        """Perform symbolic integration for multidimensional parameter arrays."""
        # Handle single variable integration
        if isinstance(variable, str):
            if variable not in ("x", "y"):
                raise ValueError(f"Unsupported variable '{variable}'. Use 'x' or 'y'.")

            if variable == "y" and not self._is2D:
                raise ValueError("Variable 'y' is only valid for 2D components")

            if not isinstance(limits, tuple) or len(limits) != 2:
                raise ValueError("For single variable, limits must be a tuple (a, b)")

            return self._integrate_symbolic_single_nd(
                limits, variable, parameters_values, **kwargs
            )

        # Handle double integration (more complex - would need careful implementation)
        elif isinstance(variable, tuple):
            # For now, fall back to element-wise computation for double integration
            # This could be optimized in the future
            nav_shape = parameters_values[0].shape
            results = np.zeros(nav_shape)

            for idx in np.ndindex(nav_shape):
                param_vals = [p[idx] for p in parameters_values]
                results[idx] = self._integrate_symbolic_double(
                    limits, variable, param_vals, **kwargs
                )

            return results
        else:
            raise ValueError("Variable must be a string or tuple of strings")

    def _integrate_symbolic_single_nd(
        self, limits, variable, parameters_values, **kwargs
    ):
        """Perform symbolic single variable integration for parameter arrays."""
        # Get the symbolic integral function
        integral_func = getattr(self, f"_integral_{variable}_func", None)
        if integral_func is None:
            raise RuntimeError(
                f"Symbolic integral for variable '{variable}' not available"
            )

        lower, upper = limits
        nav_shape = parameters_values[0].shape

        # For 2D components integrating over one variable, handle fixed values
        if self._is2D:
            other_var = "y" if variable == "x" else "x"
            if other_var in kwargs:
                other_val = kwargs[other_var]

                # Initialize results array
                results = np.zeros(nav_shape)

                # Compute for each navigation position
                for idx in np.ndindex(nav_shape):
                    param_vals = [p[idx] for p in parameters_values]

                    if variable == "x":
                        upper_val = integral_func(upper, other_val, *param_vals)
                        lower_val = integral_func(lower, other_val, *param_vals)
                    else:  # variable == "y"
                        upper_val = integral_func(other_val, upper, *param_vals)
                        lower_val = integral_func(other_val, lower, *param_vals)

                    results[idx] = float(upper_val - lower_val)

                return results
            else:
                raise ValueError(
                    f"For 2D component integration over '{variable}', "
                    f"must provide '{other_var}' value as keyword argument"
                )
        else:
            # 1D component - vectorized computation
            results = np.zeros(nav_shape)

            for idx in np.ndindex(nav_shape):
                param_vals = [p[idx] for p in parameters_values]
                upper_val = integral_func(upper, *param_vals)
                lower_val = integral_func(lower, *param_vals)
                results[idx] = float(upper_val - lower_val)

            return results

    def _integrate_numerical_nd(self, limits, variable, parameters_values, **kwargs):
        """Perform numerical integration for multidimensional parameter arrays."""
        from scipy.integrate import dblquad, quad

        nav_shape = parameters_values[0].shape
        results = np.zeros(nav_shape)

        # Store original parameter values
        original_values = [p.value for p in self.parameters]

        try:
            # Compute integration for each navigation position
            for idx in np.ndindex(nav_shape):
                # Set parameter values for this navigation position
                param_vals = [p[idx] for p in parameters_values]
                for param, value in zip(self.parameters, param_vals):
                    param.value = value

                # Perform integration using existing single-point method
                if isinstance(variable, str):
                    if not isinstance(limits, tuple) or len(limits) != 2:
                        raise ValueError(
                            "For single variable, limits must be a tuple (a, b)"
                        )

                    a, b = limits

                    if variable == "x":
                        if self._is2D and "y" in kwargs:
                            y_fixed = kwargs["y"]

                            def integrand(x_val):
                                return self.function(x_val, y_fixed)
                        elif not self._is2D:

                            def integrand(x_val):
                                return self.function(x_val)
                        else:
                            raise ValueError(
                                "For 2D component integration over 'x', must provide 'y' value"
                            )

                        results[idx], _ = quad(integrand, a, b)

                    elif variable == "y":
                        if not self._is2D:
                            raise ValueError(
                                "Variable 'y' is only valid for 2D components"
                            )
                        if "x" not in kwargs:
                            raise ValueError(
                                "For 2D component integration over 'y', must provide 'x' value"
                            )

                        x_fixed = kwargs["x"]

                        def integrand(y_val):
                            return self.function(x_fixed, y_val)

                        results[idx], _ = quad(integrand, a, b)
                    else:
                        raise ValueError(
                            f"Unsupported variable '{variable}'. Use 'x' or 'y'."
                        )

                elif isinstance(variable, tuple):
                    # Double integration
                    if len(variable) != 2 or set(variable) != {"x", "y"}:
                        raise ValueError(
                            "For double integration, variables must be ('x', 'y')"
                        )
                    if not self._is2D:
                        raise ValueError(
                            "Double integration is only available for 2D components"
                        )

                    x_limits, y_limits = limits

                    def integrand(y_val, x_val):
                        return self.function(x_val, y_val)

                    results[idx] = dblquad(
                        integrand,
                        x_limits[0],
                        x_limits[1],  # x integration limits
                        y_limits[0],
                        y_limits[1],  # y integration limits
                    )[0]
                else:
                    raise ValueError("Variable must be a string or tuple of strings")

        finally:
            # Restore original parameter values
            for param, original_value in zip(self.parameters, original_values):
                param.value = original_value

        return results

    @property
    def _constant_term(self):
        """
        Get value of constant term of component, assuming that the nonlinear
        term are fixed.

        The 'constant' part of a component is any part that doesn't change
        when the free parameters are changed.
        """
        free_linear_parameters = [
            # Use `_free` private attribute not to interfere with twin
            self._rename_pars_inv.get(p.name, p.name)
            for p in self.parameters
            if p._linear and p._free
        ]

        expr = sympy.sympify(self._str_expression)
        args = [sympy.sympify(arg, strict=False) for arg in free_linear_parameters]
        constant_expr, _ = expr.as_independent(*args, as_Add=True)

        # Then replace symbols with value of each parameter
        free_symbols = [str(free) for free in constant_expr.free_symbols]
        for p in self.parameters:
            if p.name in free_symbols:
                name = self._rename_pars_inv.get(p.name, p.name)
                constant_expr = constant_expr.subs(name, p.value)

        return float(constant_expr.evalf())

    def _separate_pseudocomponents(self):
        """
        Separate an expression into a group of lambdified functions
        that can compute the free parts of the expression, and a single
        lambdified function that computes the fixed parts of the expression

        Used by the _compute_expression_part method.
        """
        expr = self._str_expression
        ex = sympy.sympify(expr)
        remaining_elements = ex.copy()
        free_pseudo_components = {}
        variables = ("x", "y") if self._is2D else ("x",)

        for para in self.free_parameters:
            name = self._rename_pars_inv.get(para.name, para.name)
            symbol = sympy.sympify(name, strict=False)
            element = ex.as_independent(symbol)[-1]
            remaining_elements -= element
            element_names = set([str(p) for p in element.free_symbols]) - set(variables)
            free_pseudo_components[para.name] = {
                "function": sympy.utilities.lambdify(
                    variables + tuple(element_names), element, modules=self._module
                ),
                "parameters": [
                    getattr(self, self._rename_pars.get(e, e)) for e in element_names
                ],
            }

        element_names = set([str(p) for p in remaining_elements.free_symbols]) - set(
            variables
        )

        fixed_pseudo_components = {
            "function": sympy.utilities.lambdify(
                variables + tuple(element_names),
                remaining_elements,
                modules=self._module,
            ),
            "parameters": [
                getattr(self, self._rename_pars.get(e, e)) for e in element_names
            ],
        }

        return (
            free_pseudo_components,
            fixed_pseudo_components,
        )

    def _compute_expression_part(self, part):
        """Compute the expression for a given value or map["values"]."""
        model = self.model
        try:
            model_convolved = model.convolved
            convolution_supported = True
        except NotImplementedError:
            convolution_supported = False
        function = part["function"]
        parameters = [para.value for para in part["parameters"]]
        if convolution_supported and model_convolved and self.convolved:
            data = model._convolve_component_values(
                function(model._convolution_axis, *parameters)
            )
        else:
            axes = [ax.axis for ax in model.axes_manager.signal_axes]
            mesh = np.meshgrid(*axes)
            data = function(*mesh, *parameters)
            slice_ = np.where(model._channel_switches)
            if len(np.shape(data)) == 0:
                # For calculation of constant term of the component
                signal_shape = model.axes_manager._signal_shape_in_array
                data = data * np.ones(signal_shape)[slice_]
            else:
                data = np.moveaxis(data[slice_], 0, -1)

        return data

    def integrate(
        self, limits, variable="x", method="auto", parameters_values=None, **kwargs
    ):
        """Integrate the expression symbolically or numerically.

        This method first attempts symbolic integration when available and the
        method is 'auto' or 'symbolic'. If symbolic integration is not available
        or fails, it falls back to numerical integration using the parent
        Component class's integration method.

        Supports both definite and improper integration, as well as fixed and
        variable integration limits for navigation-aware integration across
        multiple parameter sets.

        Parameters
        ----------
        limits : tuple, array-like, or tuple of array-like
            Integration limits. Can be:

            * (a, b) : Fixed limits for all navigation positions
            * (a_array, b_array) : Variable limits with arrays matching navigation dimensions
            * array of (a, b) tuples : Variable limits for each navigation position
            * For double integration: [(a1, b1), (a2, b2)] where each can be fixed or variable

            For improper integration, limits can include infinite values:
            (-np.inf, np.inf), (-np.inf, x), (x, np.inf), etc.

        variable : str or tuple, default 'x'
            Variable(s) to integrate with respect to. For 1D components: 'x'.
            For 2D components: 'x', 'y', or ('x', 'y') for double integration.
            When integrating 2D components over single variables, fixed variable
            values must be provided as keyword arguments (e.g., y=1.0 when
            integrating over x).
        method : str, default 'auto'
            Integration method to use:

            * 'auto' : try symbolic first, fallback to numerical
            * 'symbolic' : use only symbolic integration
            * 'numerical' : use only numerical integration
        parameters_values : list or None, optional
            List of parameters values used to calculate the component.
            The order of the parameter in the list is defined in the
            ``parameters`` attributes of the components.
            If ``None``, the parameters values for all navigation positions
            are considered. Default is None.
        **kwargs
            Additional keyword arguments passed to the integration methods.

        Returns
        -------
        float or numpy.ndarray
            Integration result as scalar for fixed limits, or array matching
            navigation dimensions for variable limits.

        Raises
        ------
        ValueError
            If invalid variable, method, or limits are provided.
            If compute_integrals=False and symbolic integration is attempted.
        NotImplementedError
            If symbolic integration fails and method='symbolic', or if symbolic
            integration is not available when method='symbolic' is specified.
        RuntimeError
            If integration computation fails.

        Examples
        --------
        **Basic 1D Integration with Different Dimensional Data**

        Create a 1D signal with different navigation dimensions (following AI Guide):        >>> import hyperspy.api as hs
        >>> import numpy as np
        >>> # Navigation dimensions: 48 × 32 (different sizes for clarity)
        >>> # Signal dimension: 256 energy channels
        >>> data = np.random.random((48, 32, 256))
        >>> spectrum_image = hs.signals.Signal1D(data)
        >>> spectrum_image.axes_manager[0].name = 'scan_x'     # 48 pixels
        >>> spectrum_image.axes_manager[1].name = 'scan_y'     # 32 pixels
        >>> spectrum_image.axes_manager[2].name = 'energy'     # 256 channels
        >>> spectrum_image.axes_manager[2].scale = 0.1         # 0.1 eV/channel
        >>> spectrum_image.axes_manager[2].offset = 100.0      # Start at 100 eV

        Create a Gaussian component for peak fitting:

        >>> model = spectrum_image.create_model()
        >>> gaussian_peak = hs.model.components1D.Gaussian()
        >>> gaussian_peak.A.value = 1000.0        # Peak amplitude
        >>> gaussian_peak.centre.value = 150.0    # Peak at 150 eV
        >>> gaussian_peak.sigma.value = 5.0       # 5 eV width
        >>> model.append(gaussian_peak)

        Integrate the Gaussian peak over the main peak region:

        >>> # Integration in calibrated energy units (eV)
        >>> peak_area = gaussian_peak.integrate((140.0, 160.0))
        >>> print(f"Peak area: {peak_area:.2f} counts·eV")

        **Polynomial Expression Integration**

        Create a polynomial expression component:        >>> poly = hs.model.components1D.Expression(
        ...     expression="a * x**2 + b * x + c",
        ...     name="Polynomial",
        ...     compute_integrals=True)
        >>> poly.a.value = 1.0
        >>> poly.b.value = 2.0
        >>> poly.c.value = 3.0

        **Definite Integration:**

        Integrate from 0 to 2 using symbolic method:

        >>> result = poly.integrate((0, 2), method='symbolic')
        >>> print(f"Definite integral: {result}")
        12.666666666666666

        **Improper Integration with Divergence Detection**

        For functions extending to infinity, enable analytical integration:        >>> # Exponential decay component (requires compute_integrals=True)
        >>> exp_component = hs.model.components1D.Expression(
        ...     expression="A * exp(-energy/decay_constant)",
        ...     name="exponential_tail",
        ...     position="decay_constant",
        ...     compute_integrals=True  # Enable symbolic integration
        ... )
        >>> exp_component.A.value = 500.0
        >>> exp_component.decay_constant.value = 20.0  # 20 eV decay

        Integrate from peak center to infinity (proper convergent integral):

        >>> tail_area = exp_component.integrate((150.0, np.inf))
        >>> print(f"Tail integral: {tail_area:.2f} counts·eV")

        **Gaussian with improper bounds:**

        >>> gaussian = hs.model.components1D.Expression(
        ...     expression="a * exp(-(x - mu)**2 / (2 * sigma**2))",
        ...     name="Gaussian",
        ...     compute_integrals=True)
        >>> gaussian.a.value = 1.0
        >>> gaussian.mu.value = 0.0
        >>> gaussian.sigma.value = 1.0
        >>> result = gaussian.integrate((-np.inf, np.inf))
        >>> print(f"Improper integral: {result}")

        **Multi-Dimensional Integration Patterns**

        For 2D detector data, integrate over specific spatial dimensions:        >>> # 4D-STEM data: scan positions × detector pixels
        >>> # Different dimensions: 24×16 scan, 128×64 detector
        >>> stem_data = np.random.random((24, 16, 128, 64))
        >>> stem_signal = hs.signals.Signal2D(stem_data)
        >>> stem_signal.axes_manager[0].name = 'scan_x'        # 24 positions
        >>> stem_signal.axes_manager[1].name = 'scan_y'        # 16 positions
        >>> stem_signal.axes_manager[2].name = 'detector_x'    # 128 pixels
        >>> stem_signal.axes_manager[3].name = 'detector_y'    # 64 pixels

        Create 2D Expression model for diffraction spot:

        >>> model_2d = stem_signal.create_model()
        >>> spot_2d = hs.model.components1D.Expression(
        ...     expression="A * exp(-((detector_x-x0)**2 + (detector_y-y0)**2) / (2*sigma**2))",
        ...     name="diffraction_spot",
        ...     compute_integrals=True
        ... )
        >>> spot_2d.A.value = 1000.0
        >>> spot_2d.x0.value = 64.0      # Center x at detector middle
        >>> spot_2d.y0.value = 32.0      # Center y at detector middle
        >>> spot_2d.sigma.value = 8.0    # 8-pixel spot size

        Integrate over detector_x while keeping detector_y fixed:

        >>> # Integration along detector_x direction (preserves y-dependence)
        >>> x_integrated = spot_2d.integrate((50.0, 78.0), var='detector_x')

        **Variable limits integration:**

        Handle per-pixel integration limits (advanced use case):

        >>> # Different integration ranges for each navigation pixel
        >>> # Lower limits array (24×16 navigation shape)
        >>> lower_energy = np.linspace(120, 140, 24*16).reshape(24, 16)
        >>> upper_energy = np.linspace(160, 180, 24*16).reshape(24, 16)
        >>>
        >>> # Variable integration creates result with navigation shape
        >>> variable_areas = gaussian_peak.integrate((lower_energy, upper_energy))
        >>> print(f"Variable integration shape: {variable_areas.shape}")  # (24, 16)

        **2D component double integration:**

        >>> expr_2d = hs.model.components2D.Expression(
        ...     expression="a * x * y + b * x**2",
        ...     name="TwoDFunction",
        ...     compute_integrals=True)
        >>> expr_2d.a.value = 2.0
        >>> expr_2d.b.value = 1.0

        Double integration over x=[0,1], y=[0,2]:

        >>> result = expr_2d.integrate([(0, 1), (0, 2)], ('x', 'y'), method='symbolic')

        **Parameter Override for Sensitivity Analysis**

        Test component behavior with different parameter values:        >>> # Override parameters without changing component state
        >>> sensitivity_results = {}
        >>> for sigma_test in [3.0, 5.0, 7.0]:
        ...     area = gaussian_peak.integrate((140.0, 160.0), sigma=sigma_test)
        ...     sensitivity_results[sigma_test] = area
        >>>
        >>> print("Sensitivity to sigma:")
        >>> for sigma, area in sensitivity_results.items():
        ...     print(f"  σ = {sigma:.1f} eV → Area = {area:.1f} counts·eV")

        **Runtime parameter substitution:**

        >>> result = poly.integrate((0, 2), parameters_values=[2.0, 1.0, 0.5])

        **Improper integration with infinite bounds:**

        >>> # Create exponential decay component
        >>> exp_decay = hs.model.components1D.Expression(
        ...     expression="a * exp(-x / tau)",
        ...     name="ExponentialDecay",
        ...     compute_integrals=True)
        >>> exp_decay.a.value = 1.0
        >>> exp_decay.tau.value = 2.0

        Integrate from 0 to infinity:

        >>> result = exp_decay.integrate((0, np.inf))
        >>> print(f"∫₀^∞ e^(-x/τ) dx = {result:.3f}")

        See Also
        --------
        :meth:`hyperspy.component.Component.integrate` : Base component integration

        Notes
        -----
        - Improper integration requires ``compute_integrals=True`` when creating the component
        - Symbolic integration uses SymPy and requires expressions with analytical antiderivatives
        - Variable limits integration currently uses numerical methods only
        - For 2D components, single-variable integration requires fixed values for other variables
        - Infinite bounds are supported: use numpy.inf, float('inf'), or similar
        """

        # Check if we have improper integration (infinite bounds)
        has_infinite_bounds = self._has_infinite_bounds(limits)

        # Check if we have variable limits first
        nav_shape = getattr(self, "_navigation_shape", None)
        is_variable_limits, parsed_limits = self._parse_limits(limits, nav_shape)

        # Handle variable limits (not improper integration)
        if is_variable_limits:
            if method == "symbolic":
                raise NotImplementedError(
                    "Symbolic integration with variable limits is not currently supported. "
                    "Use method='numerical' or 'auto' for variable limits integration."
                )

            # Use numerical integration for variable limits
            if parameters_values is not None:
                return self._integrate_numerical_variable_with_params(
                    parsed_limits, variable, parameters_values, **kwargs
                )
            else:
                return super().integrate(limits, variable, method="numerical", **kwargs)

        # Handle improper integration with infinite bounds
        if has_infinite_bounds:
            # Try symbolic improper integration first if available and requested
            try:
                import importlib.util

                symbolic_available = importlib.util.find_spec("sympy") is not None
            except ImportError:
                symbolic_available = False

            if method in ("auto", "symbolic") and symbolic_available:
                try:
                    return self._integrate_symbolic_improper(
                        limits, variable, parameters_values=parameters_values, **kwargs
                    )
                except DivergentIntegralError:
                    # Always re-raise divergent integral errors - don't fall back to numerical
                    raise
                except Exception as e:
                    if method == "symbolic":
                        raise NotImplementedError(
                            f"Symbolic improper integration failed: {e}"
                        )
                    # Fall through to numerical for 'auto' only for non-divergent failures

            # Use numerical integration for improper bounds
            if method in ("auto", "numerical"):
                if parameters_values is not None:
                    return self._integrate_numerical_with_params(
                        limits, variable, parameters_values, **kwargs
                    )
                else:
                    return super().integrate(
                        limits, variable, method="numerical", **kwargs
                    )

            raise RuntimeError(f"Improper integration failed for method '{method}'")

        # For fixed limits, proceed with original logic
        # Validate method
        valid_methods = {"auto", "symbolic", "numerical"}
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Supported: {valid_methods}")

        # Check if symbolic integration is requested but not available
        symbolic_available = (
            hasattr(self, "_symbolic_integration_available")
            and self._symbolic_integration_available
        )

        if method == "symbolic" and not symbolic_available:
            raise NotImplementedError(
                "Symbolic integration is not available. "
                "Enable it with compute_integrals=True when creating the Expression component."
            )

        # Try symbolic integration first if available and requested
        if method in ("auto", "symbolic") and symbolic_available:
            try:
                return self._integrate_symbolic(
                    limits, variable, parameters_values=parameters_values, **kwargs
                )
            except Exception as e:
                if method == "symbolic":
                    raise NotImplementedError(f"Symbolic integration failed: {e}")
                # Fall through to numerical for 'auto'

        # Use numerical integration from parent Component class
        if method in ("auto", "numerical"):
            # If parameters_values is provided, we need to handle numerical integration ourselves
            # since the parent Component.integrate doesn't support parameter substitution
            if parameters_values is not None:
                return self._integrate_numerical_with_params(
                    limits, variable, parameters_values, **kwargs
                )
            else:
                return super().integrate(limits, variable, **kwargs)

        raise RuntimeError(f"Integration failed for method '{method}'")

    def _integrate_symbolic(self, limits, variable, parameters_values=None, **kwargs):
        """Perform symbolic integration using the precomputed integrals."""
        # Handle single variable integration
        if isinstance(variable, str):
            if variable not in ("x", "y"):
                raise ValueError(f"Unsupported variable '{variable}'. Use 'x' or 'y'.")

            if variable == "y" and not self._is2D:
                raise ValueError("Variable 'y' is only valid for 2D components")

            if not isinstance(limits, tuple) or len(limits) != 2:
                raise ValueError("For single variable, limits must be a tuple (a, b)")

            return self._integrate_symbolic_single(
                limits, variable, parameters_values=parameters_values, **kwargs
            )

        # Handle double integration
        elif isinstance(variable, tuple):
            if len(variable) != 2:
                raise ValueError(
                    "For double integration, variable must be a tuple of exactly 2 elements"
                )

            if not self._is2D:
                raise ValueError(
                    "Double integration is only available for 2D components"
                )

            if set(variable) != {"x", "y"}:
                raise ValueError(
                    "For double integration, variables must be 'x' and 'y'"
                )

            if not isinstance(limits, (list, tuple)) or len(limits) != 2:
                raise ValueError(
                    "For double integration, limits must be a list/tuple of 2 tuples"
                )

            return self._integrate_symbolic_double(
                limits, variable, parameters_values=parameters_values, **kwargs
            )

        else:
            raise ValueError("Variable must be a string or tuple of strings")

    def _integrate_symbolic_single(
        self, limits, variable, parameters_values=None, **kwargs
    ):
        """Perform symbolic single variable integration."""
        # Get the symbolic integral function
        integral_func = getattr(self, f"_integral_{variable}_func", None)
        if integral_func is None:
            raise RuntimeError(
                f"Symbolic integral for variable '{variable}' not available"
            )

        # Use provided parameter values or get current values
        if parameters_values is None:
            param_values = [p.value for p in self.parameters]
        else:
            param_values = parameters_values
        # For 2D components integrating over one variable, substitute fixed values
        if self._is2D:
            other_var = "y" if variable == "x" else "x"
            if other_var in kwargs:
                other_val = kwargs[other_var]

                # Evaluate definite integral using fundamental theorem of calculus
                lower, upper = limits

                if variable == "x" and other_var == "y":
                    if np.isscalar(other_val):
                        upper_val = integral_func(upper, other_val, *param_values)
                        lower_val = integral_func(lower, other_val, *param_values)
                        return float(upper_val - lower_val)
                    else:
                        # Handle array of y values
                        other_array = np.asarray(other_val)
                        results = np.zeros_like(other_array, dtype=float)
                        for i, y_val in enumerate(other_array.flat):
                            upper_val = integral_func(upper, y_val, *param_values)
                            lower_val = integral_func(lower, y_val, *param_values)
                            results.flat[i] = float(upper_val - lower_val)
                        return results.reshape(other_array.shape)
                else:  # variable == "y" and other_var == "x"
                    if np.isscalar(other_val):
                        upper_val = integral_func(other_val, upper, *param_values)
                        lower_val = integral_func(other_val, lower, *param_values)
                        return float(upper_val - lower_val)
                    else:
                        # Handle array of x values
                        other_array = np.asarray(other_val)
                        results = np.zeros_like(other_array, dtype=float)
                        for i, x_val in enumerate(other_array.flat):
                            upper_val = integral_func(x_val, upper, *param_values)
                            lower_val = integral_func(x_val, lower, *param_values)
                            results.flat[i] = float(upper_val - lower_val)
                        return results.reshape(other_array.shape)
            else:
                raise ValueError(
                    f"For 2D component integration over '{variable}', "
                    f"must provide '{other_var}' value as keyword argument"
                )
        else:
            # 1D component
            lower, upper = limits

            upper_val = integral_func(upper, *param_values)
            lower_val = integral_func(lower, *param_values)

            return float(upper_val - lower_val)

    def _integrate_symbolic_double(
        self, limits, variable, parameters_values=None, **kwargs
    ):
        """Perform symbolic double integration."""
        import sympy

        # For double integration, we need to compute ∫∫ f(x,y) dy dx (or dx dy)
        # We'll use symbolic integration twice - first over one variable, then the other

        # Extract variables and limits
        var1, var2 = variable
        limits1, limits2 = limits

        try:
            # Use provided parameter values or get current values
            if parameters_values is None:
                param_values = [p.value for p in self.parameters]
            else:
                param_values = parameters_values

            # Get the original parsed expression
            expr = self._parsed_expr

            # Extract the symbol objects for the variables
            x_symbol = [s for s in expr.free_symbols if s.name == "x"][0]
            y_symbol = [s for s in expr.free_symbols if s.name == "y"][0]
            parameter_symbols = [
                s for s in expr.free_symbols if s.name not in ("x", "y")
            ]
            parameter_symbols.sort(key=lambda s: s.name)  # Keep consistent ordering

            # Map variable names to symbol objects
            var_map = {"x": x_symbol, "y": y_symbol}
            symbol1, symbol2 = var_map[var1], var_map[var2]

            # First integration: integrate over var2 (inner integral)
            inner_integral = sympy.integrate(expr, symbol2)

            # Create limits for inner integral
            lower2, upper2 = limits2

            # Evaluate the inner integral at its limits
            inner_upper = inner_integral.subs(symbol2, upper2)
            inner_lower = inner_integral.subs(symbol2, lower2)
            inner_result = sympy.simplify(inner_upper - inner_lower)

            # Second integration: integrate the result over var1 (outer integral)
            outer_integral = sympy.integrate(inner_result, symbol1)

            # Create limits for outer integral
            lower1, upper1 = limits1

            # Evaluate the outer integral at its limits
            outer_upper = outer_integral.subs(symbol1, upper1)
            outer_lower = outer_integral.subs(symbol1, lower1)
            outer_result = sympy.simplify(outer_upper - outer_lower)

            # Substitute parameter values
            for param_symbol, param_value in zip(parameter_symbols, param_values):
                outer_result = outer_result.subs(param_symbol, param_value)

            # Evaluate to get numerical result
            result = float(outer_result.evalf())

            return result

        except Exception as e:
            raise RuntimeError(
                f"Symbolic double integration failed: {e}. "
                "Try using method='numerical' instead."
            )

    def _integrate_numerical_with_params(
        self, limits, variable, parameters_values, **kwargs
    ):
        """Perform numerical integration with custom parameter values."""
        import numpy as np
        from scipy.integrate import dblquad, quad

        # Temporarily store original parameter values
        original_values = [p.value for p in self.parameters]

        try:
            # Set the provided parameter values
            for param, value in zip(self.parameters, parameters_values):
                param.value = value

            # Handle single variable integration
            if isinstance(variable, str):
                if not isinstance(limits, tuple) or len(limits) != 2:
                    raise ValueError(
                        "For single variable, limits must be a tuple (a, b)"
                    )

                a, b = limits

                if variable == "x":
                    if self._is2D:
                        # 2D component, need y value
                        if "y" not in kwargs:
                            raise ValueError(
                                "For 2D component integration over 'x', must provide "
                                "'y' value as keyword argument"
                            )
                        y_fixed = kwargs["y"]

                        if np.isscalar(y_fixed):

                            def integrand(x_val):
                                return self.function(x_val, y_fixed)

                            result, _ = quad(integrand, a, b)
                            return result
                        else:
                            # Array of y values
                            y_array = np.asarray(y_fixed)
                            results = np.zeros_like(y_array, dtype=float)
                            for i, y_val in enumerate(y_array.flat):

                                def integrand(x_val):
                                    return self.function(x_val, y_val)

                                results.flat[i], _ = quad(integrand, a, b)
                            return results.reshape(y_array.shape)
                    else:
                        # 1D component
                        def integrand(x_val):
                            return self.function(x_val)

                        result, _ = quad(integrand, a, b)
                        return result

                elif variable == "y":
                    if not self._is2D:
                        raise ValueError("Variable 'y' is only valid for 2D components")

                    if "x" not in kwargs:
                        raise ValueError(
                            "For 2D component integration over 'y', must provide "
                            "'x' value as keyword argument"
                        )
                    x_fixed = kwargs["x"]

                    if np.isscalar(x_fixed):

                        def integrand(y_val):
                            return self.function(x_fixed, y_val)

                        result, _ = quad(integrand, a, b)
                        return result
                    else:
                        # Array of x values
                        x_array = np.asarray(x_fixed)
                        results = np.zeros_like(x_array, dtype=float)
                        for i, x_val in enumerate(x_array.flat):

                            def integrand(y_val):
                                return self.function(x_val, y_val)

                            results.flat[i], _ = quad(integrand, a, b)
                        return results.reshape(x_array.shape)
                else:
                    raise ValueError(
                        f"Unsupported variable '{variable}'. Use 'x' or 'y'."
                    )

            # Handle double integration
            elif isinstance(variable, tuple):
                if len(variable) != 2:
                    raise ValueError(
                        "For double integration, variable must be a tuple of exactly 2 elements"
                    )

                if not self._is2D:
                    raise ValueError(
                        "Double integration is only available for 2D components"
                    )

                if set(variable) != {"x", "y"}:
                    raise ValueError(
                        "For double integration, variables must be 'x' and 'y'"
                    )

                if not isinstance(limits, (list, tuple)) or len(limits) != 2:
                    raise ValueError(
                        "For double integration, limits must be a list/tuple of 2 tuples"
                    )

                x_limits, y_limits = limits

                def integrand(y_val, x_val):
                    return self.function(x_val, y_val)

                result = dblquad(
                    integrand,
                    x_limits[0],
                    x_limits[1],
                    lambda x: y_limits[0],
                    lambda x: y_limits[1],
                )[0]
                return result

            else:
                raise ValueError("Variable must be a string or tuple of strings")

        finally:
            # Restore original parameter values
            for param, original_value in zip(self.parameters, original_values):
                param.value = original_value

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
        original_values = [p.value for p in self.parameters]

        try:
            # Set the provided parameter values
            for param, value in zip(self.parameters, parameters_values):
                param.value = value

            # Integrate for each navigation position
            for idx in np.ndindex(a_array.shape):
                a = a_array[idx]
                b = b_array[idx]

                # Create integrand function for this position
                if self._is2D and variable in ["x", "y"]:
                    if variable == "x":
                        if "y" not in kwargs:
                            raise ValueError(
                                "For 2D components, 'y' value must be provided when integrating over 'x'"
                            )
                        y_fixed = kwargs["y"]

                        def integrand(x_val):
                            return self.function(x_val, y_fixed)

                    elif variable == "y":
                        if "x" not in kwargs:
                            raise ValueError(
                                "For 2D components, 'x' value must be provided when integrating over 'y'"
                            )
                        x_fixed = kwargs["x"]

                        def integrand(y_val):
                            return self.function(x_fixed, y_val)

                else:
                    # 1D component
                    def integrand(x_val):
                        return self.function(x_val)

                results[idx] = quad(integrand, a, b)[0]

        finally:
            # Restore original parameter values
            for param, original_value in zip(self.parameters, original_values):
                param.value = original_value

        return results if results.size > 1 else results.item()

    def _integrate_symbolic_improper(
        self, limits, variable, parameters_values=None, **kwargs
    ):
        """Perform symbolic improper integration with infinite bounds."""

        # Handle single variable integration
        if isinstance(variable, str):
            if variable not in ("x", "y"):
                raise ValueError(f"Unsupported variable '{variable}'. Use 'x' or 'y'.")

            if variable == "y" and not self._is2D:
                raise ValueError("Variable 'y' is only valid for 2D components")

            if not isinstance(limits, tuple) or len(limits) != 2:
                raise ValueError("For single variable, limits must be a tuple (a, b)")

            return self._integrate_symbolic_improper_single(
                limits, variable, parameters_values=parameters_values, **kwargs
            )

        # Handle double integration (not yet supported for improper)
        elif isinstance(variable, tuple):
            raise NotImplementedError(
                "Symbolic improper double integration is not yet implemented. "
                "Use method='numerical' for double improper integration."
            )

        else:
            raise ValueError("Variable must be a string or tuple of strings")

    def _integrate_symbolic_improper_single(
        self, limits, variable, parameters_values=None, **kwargs
    ):
        """Perform symbolic improper integration for single variable."""
        import numpy as np
        import sympy

        # Use provided parameter values or get current values
        if parameters_values is None:
            param_values = [p.value for p in self.parameters]
        else:
            param_values = parameters_values

        # Get the original parsed expression
        expr = self._parsed_expr

        # Extract the symbol objects for the variable
        var_symbol = None
        for s in expr.free_symbols:
            if s.name == variable:
                var_symbol = s
                break

        if var_symbol is None:
            raise ValueError(f"Variable '{variable}' not found in expression")

        # Get parameter symbols and substitute values
        parameter_symbols = [s for s in expr.free_symbols if s.name != variable]
        parameter_symbols.sort(key=lambda s: s.name)  # Keep consistent ordering

        # Substitute parameter values
        substituted_expr = expr
        for param_symbol, param_value in zip(parameter_symbols, param_values):
            substituted_expr = substituted_expr.subs(param_symbol, param_value)

        # Handle different types of infinite bounds
        lower, upper = limits

        # Convert numpy infinities to sympy infinities
        if np.isinf(lower):
            lower = -sympy.oo if lower < 0 else sympy.oo
        if np.isinf(upper):
            upper = sympy.oo if upper > 0 else -sympy.oo

        # For 2D components integrating over one variable, substitute fixed values
        if self._is2D:
            other_var = "y" if variable == "x" else "x"
            if other_var in kwargs:
                other_val = kwargs[other_var]
                other_symbol = None
                for s in substituted_expr.free_symbols:
                    if s.name == other_var:
                        other_symbol = s
                        break
                if other_symbol is not None:
                    substituted_expr = substituted_expr.subs(other_symbol, other_val)
            else:
                raise ValueError(
                    f"For 2D component integration over '{variable}', "
                    f"must provide '{other_var}' value as keyword argument"
                )

        try:
            # Compute the improper integral using SymPy
            result = sympy.integrate(substituted_expr, (var_symbol, lower, upper))

            # Check for divergent results
            if result == sympy.oo or result == -sympy.oo:
                raise DivergentIntegralError(
                    f"The integral from {limits[0]} to {limits[1]} diverges to infinity. "
                    f"This integral cannot be computed as it is mathematically divergent."
                )
            elif result.has(sympy.oo):
                raise DivergentIntegralError(
                    f"The integral from {limits[0]} to {limits[1]} contains infinite terms. "
                    f"This integral cannot be computed as it is mathematically divergent."
                )
            else:
                # Try to evaluate the result numerically
                try:
                    # Use str conversion for robust evaluation
                    result_str = str(result.evalf())
                    # Parse as float if possible
                    final_result = float(result_str)
                    if np.isfinite(final_result):
                        return final_result
                    else:
                        raise ValueError("Integral evaluates to non-finite value")
                except (TypeError, ValueError, AttributeError) as e:
                    raise ValueError(f"Cannot evaluate symbolic improper integral: {e}")

        except DivergentIntegralError:
            # Always re-raise divergent integral errors
            raise
        except Exception as e:
            # Re-raise as more specific error for better error handling
            raise NotImplementedError(f"Symbolic improper integration failed: {e}")

    def _has_infinite_bounds(self, limits):
        """Check if limits contain infinite bounds for improper integration."""
        import numpy as np

        if not isinstance(limits, (tuple, list)):
            return False

        # Handle single variable case (a, b)
        if len(limits) == 2 and not isinstance(limits[0], (tuple, list)):
            a, b = limits
            # Handle case where a or b might be arrays
            try:
                return np.any(np.isinf(a)) or np.any(np.isinf(b))
            except (TypeError, ValueError):
                # If np.isinf fails, they're probably not numeric
                return False

        # Handle double integration case [(a1, b1), (a2, b2)]
        if len(limits) == 2 and isinstance(limits[0], (tuple, list)):
            for limit_pair in limits:
                if len(limit_pair) == 2:
                    a, b = limit_pair
                    try:
                        if np.any(np.isinf(a)) or np.any(np.isinf(b)):
                            return True
                    except (TypeError, ValueError):
                        continue

        # Handle variable limits - check if any bounds are infinite
        try:
            limits_array = np.asarray(limits)
            return np.any(np.isinf(limits_array))
        except (ValueError, TypeError):
            return False

        return False


def _check_parameter_linearity(expr, name):
    """Check whether expression is linear for a given parameter."""
    symbol = sympy.Symbol(name)
    try:
        if not sympy.diff(expr, symbol, 2) == 0:
            return False
    except AttributeError:
        # AttributeError occurs if the expression cannot be parsed
        # for instance some expressions with where.
        warnings.warn(
            f"The linearity of the parameter `{name}` can't be "
            "determined automatically.",
            UserWarning,
        )
        return False
    return True


# Apply dynamic docstring interpolation following HyperSpy patterns
