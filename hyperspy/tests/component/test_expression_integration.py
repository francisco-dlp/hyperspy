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
import pytest

from hyperspy._components.expression import Expression


class TestExpressionIntegration:
    """Test integration methods for Expression components."""

    def test_polynomial_symbolic_integration(self):
        """Test symbolic integration of polynomial expressions."""
        # Create a simple polynomial: 2*x + 3
        poly = Expression(
            expression="2*x + 3",
            name="Linear",
            compute_integrals=True,
        )

        # Integrate from 0 to 1: integral should be [x^2 + 3*x] from 0 to 1 = 1 + 3 = 4
        result = poly.integrate((0, 1), method="symbolic")
        expected = 4.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_quadratic_symbolic_integration(self):
        """Test symbolic integration of quadratic expressions."""
        # Create a quadratic: a*x^2 + b*x + c
        quad = Expression(
            expression="a * x**2 + b * x + c",
            name="Quadratic",
            a=1.0,
            b=2.0,
            c=3.0,
            compute_integrals=True,
        )

        # Integrate from 0 to 2: integral should be [x^3/3 + x^2 + 3*x] from 0 to 2
        # = 8/3 + 4 + 6 = 8/3 + 10 = 38/3 ≈ 12.667
        result = quad.integrate((0, 2), method="symbolic")
        expected = 38.0 / 3.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_polynomial_numerical_integration(self):
        """Test numerical integration of polynomial expressions."""
        # Create a simple polynomial: 2*x + 3
        poly = Expression(
            expression="2*x + 3",
            name="Linear",
            compute_integrals=True,
        )

        # Integrate from 0 to 1 using numerical method
        result = poly.integrate((0, 1), method="numerical")
        expected = 4.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_exponential_symbolic_integration(self):
        """Test symbolic integration of exponential expressions."""
        # Create exponential: exp(x)
        exp_comp = Expression(
            expression="exp(x)",
            name="Exponential",
            compute_integrals=True,
        )

        # Integrate from 0 to 1: integral should be [exp(x)] from 0 to 1 = e - 1
        result = exp_comp.integrate((0, 1), method="symbolic")
        expected = np.exp(1) - 1
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_exponential_numerical_integration(self):
        """Test numerical integration of exponential expressions."""
        # Create exponential: exp(x)
        exp_comp = Expression(
            expression="exp(x)",
            name="Exponential",
            compute_integrals=True,
        )

        # Integrate from 0 to 1 using numerical method
        result = exp_comp.integrate((0, 1), method="numerical")
        expected = np.exp(1) - 1
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_gaussian_symbolic_integration(self):
        """Test symbolic integration of Gaussian expressions."""
        # Create a simple Gaussian: exp(-x^2)
        gaussian = Expression(
            expression="exp(-x**2)",
            name="Gaussian",
            compute_integrals=True,
        )

        # Integrate from -1 to 1 using symbolic method
        # This should work symbolically using error functions
        result = gaussian.integrate((-1, 1), method="symbolic")
        # For this test, we just check that symbolic integration doesn't fail
        assert isinstance(result, (int, float))
        assert result > 0

    def test_gaussian_numerical_integration(self):
        """Test numerical integration of Gaussian expressions."""
        # Create a simple Gaussian: exp(-x^2)
        gaussian = Expression(
            expression="exp(-x**2)",
            name="Gaussian",
            compute_integrals=True,
        )

        # Integrate from -1 to 1 using numerical method
        result = gaussian.integrate((-1, 1), method="numerical")

        # Expected value: integral of exp(-x^2) from -1 to 1
        # This is related to the error function: sqrt(pi) * erf(1)
        import scipy.special

        expected = np.sqrt(np.pi) * scipy.special.erf(1)
        np.testing.assert_allclose(result, expected, rtol=1e-3)

    def test_2d_expression_x_integration(self):
        """Test integration over x for 2D expressions."""
        # Create a 2D expression: x + y
        expr_2d = Expression(
            expression="x + y",
            name="2D_Linear",
            compute_integrals=True,
        )

        # Integrate over x from 0 to 2 with y=1
        # Integral should be [x^2/2 + y*x] from 0 to 2 with y=1 = 2 + 2 = 4
        result = expr_2d.integrate((0, 2), variable="x", method="symbolic", y=1.0)
        expected = 4.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_2d_expression_y_integration(self):
        """Test integration over y for 2D expressions."""
        # Create a 2D expression: x + y
        expr_2d = Expression(
            expression="x + y",
            name="2D_Linear",
            compute_integrals=True,
        )

        # Integrate over y from 0 to 2 with x=1
        # Integral should be [x*y + y^2/2] from 0 to 2 with x=1 = 2 + 2 = 4
        result = expr_2d.integrate((0, 2), variable="y", method="symbolic", x=1.0)
        expected = 4.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_2d_expression_double_integration(self):
        """Test double integration for 2D expressions."""
        # Create a 2D expression: x + y
        expr_2d = Expression(
            expression="x + y",
            name="2D_Linear",
            compute_integrals=True,
        )

        # Double integrate over [0,1] x [0,1]
        # Integral should be integral of (x + y) over unit square = 1
        result = expr_2d.integrate(
            [(0, 1), (0, 1)], variable=("x", "y"), method="symbolic"
        )
        expected = 1.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_2d_expression_numerical_x_integration(self):
        """Test numerical integration over x for 2D expressions."""
        # Create a 2D expression: x + y
        expr_2d = Expression(
            expression="x + y",
            name="2D_Linear",
            compute_integrals=True,
        )

        # Integrate over x from 0 to 2 with y=1 using numerical method
        result = expr_2d.integrate((0, 2), variable="x", method="numerical", y=1.0)
        expected = 4.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_2d_expression_numerical_double_integration(self):
        """Test numerical double integration for 2D expressions."""
        # Create a 2D expression: x + y
        expr_2d = Expression(
            expression="x + y",
            name="2D_Linear",
            compute_integrals=True,
        )

        # Double integrate over [0,1] x [0,1] using numerical method
        result = expr_2d.integrate(
            [(0, 1), (0, 1)], variable=("x", "y"), method="numerical"
        )
        expected = 1.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_auto_method_fallback(self):
        """Test that 'auto' method tries symbolic first, then numerical."""
        # Create a polynomial that should work with symbolic integration
        poly = Expression(
            expression="x**2",
            name="Quadratic",
            compute_integrals=True,
        )

        # Using 'auto' method should succeed
        result = poly.integrate((0, 2), method="auto")
        expected = 8.0 / 3.0  # [x^3/3] from 0 to 2 = 8/3
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_parameter_values_in_integration(self):
        """Test that parameter values are correctly used in integration."""
        # Create a parameterized expression: a * x + b
        param_expr = Expression(
            expression="a * x + b",
            name="Parameterized",
            a=2.0,
            b=3.0,
            compute_integrals=True,
        )

        # Integrate from 0 to 1
        result = param_expr.integrate((0, 1), method="symbolic")
        expected = 4.0  # [a*x^2/2 + b*x] from 0 to 1 with a=2, b=3 = 1 + 3 = 4
        np.testing.assert_allclose(result, expected, rtol=1e-6)

        # Change parameter values and test again
        param_expr.a.value = 1.0
        param_expr.b.value = 0.0
        result2 = param_expr.integrate((0, 2), method="symbolic")
        expected2 = 2.0  # [x^2/2] from 0 to 2 = 2
        np.testing.assert_allclose(result2, expected2, rtol=1e-6)

    def test_invalid_method_raises_error(self):
        """Test that invalid method parameter raises ValueError."""
        expr = Expression(
            expression="x",
            name="Linear",
            compute_integrals=True,
        )

        with pytest.raises(ValueError, match="Invalid method 'invalid'"):
            expr.integrate((0, 1), method="invalid")

    def test_invalid_variable_raises_error(self):
        """Test that invalid variable parameter raises ValueError."""
        expr = Expression(
            expression="x",
            name="Linear",
            compute_integrals=True,
        )

        with pytest.raises(ValueError, match="Unsupported variable: z"):
            expr.integrate((0, 1), variable="z")

    def test_1d_component_y_variable_raises_error(self):
        """Test that using y variable with 1D component raises ValueError."""
        expr_1d = Expression(
            expression="x",
            name="Linear1D",
            compute_integrals=True,
        )

        with pytest.raises(
            ValueError, match="Variable 'y' is only valid for 2D components"
        ):
            expr_1d.integrate((0, 1), variable="y")

    def test_2d_component_missing_fixed_variable_x(self):
        """Test that 2D component integration over x without y raises ValueError."""
        expr_2d = Expression(
            expression="x + y",
            name="2D_Expression",
            compute_integrals=True,
        )

        with pytest.raises(NotImplementedError, match="must provide 'y' value"):
            expr_2d.integrate((0, 1), variable="x", method="symbolic")

    def test_2d_component_missing_fixed_variable_y(self):
        """Test that 2D component integration over y without x raises ValueError."""
        expr_2d = Expression(
            expression="x + y",
            name="2D_Expression",
            compute_integrals=True,
        )

        with pytest.raises(NotImplementedError, match="must provide 'x' value"):
            expr_2d.integrate((0, 1), variable="y", method="symbolic")

    def test_invalid_limits_format(self):
        """Test that invalid limits format raises ValueError."""
        expr = Expression(
            expression="x",
            name="Linear",
            compute_integrals=True,
        )

        # Single variable integration needs tuple
        with pytest.raises(ValueError, match="limits must be a tuple"):
            expr.integrate([0, 1], variable="x")

        # Wrong number of elements
        with pytest.raises(ValueError, match="limits must be a tuple"):
            expr.integrate((0, 1, 2), variable="x")

    def test_double_integration_invalid_limits(self):
        """Test double integration with invalid limits."""
        expr_2d = Expression(
            expression="x + y",
            name="2D_Expression",
            compute_integrals=True,
        )

        # Wrong number of variable elements
        with pytest.raises(
            ValueError, match="variable must be a tuple of exactly 2 elements"
        ):
            expr_2d.integrate([(0, 1), (0, 2)], variable=("x", "y", "z"))

        # Wrong limits format for double integration
        with pytest.raises(ValueError, match="limits must be a list/tuple of 2 tuples"):
            expr_2d.integrate((0, 1), variable=("x", "y"))

        # Wrong variables for 2D integration
        with pytest.raises(ValueError, match="variables must be 'x' and 'y'"):
            expr_2d.integrate([(0, 1), (0, 2)], variable=("x", "z"))

    def test_integrate_nd_basic_functionality(self):
        """Test that integrate_nd works for basic expressions."""
        expr = Expression(
            expression="a*x",
            name="Linear",
            compute_integrals=True,
        )
        expr.a.value = 1.0  # Set parameter value

        # Test single integration
        result = expr.integrate_nd((0, 1))
        expected = 0.5  # integral of a*x from 0 to 1 with a=1 is 0.5
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

        # Test with different parameter value
        expr.a.value = 2.0
        result = expr.integrate_nd((0, 1))
        expected = 1.0  # integral of 2*x from 0 to 1 is 1.0
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"


class TestExpressionIntegrationAdvanced:
    """Advanced integration tests for Expression components."""

    def test_trigonometric_integration(self):
        """Test integration of trigonometric expressions."""
        # Create a sine expression
        sin_expr = Expression(
            expression="sin(x)",
            name="Sine",
            compute_integrals=True,
        )

        # Integrate from 0 to pi: should give 2
        result = sin_expr.integrate((0, np.pi), method="symbolic")
        expected = 2.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_complex_expression_integration(self):
        """Test integration of more complex expressions."""
        # Create a complex expression: a * exp(-b * x^2) * cos(c * x)
        complex_expr = Expression(
            expression="a * exp(-b * x**2) * cos(c * x)",
            name="Complex",
            a=1.0,
            b=1.0,
            c=1.0,
            compute_integrals=True,
        )

        # This should work but might be complex symbolically
        # Test that it doesn't crash and returns a reasonable result
        try:
            result = complex_expr.integrate((-1, 1), method="symbolic")
            assert isinstance(result, (int, float))
        except NotImplementedError:
            # If symbolic fails, that's okay for complex expressions
            pass

    def test_array_fixed_variable_integration(self):
        """Test integration with array of fixed variable values."""
        # Create a 2D expression
        expr_2d = Expression(
            expression="x * y",
            name="Product2D",
            compute_integrals=True,
        )

        # Integrate over x with array of y values
        y_values = np.array([1.0, 2.0, 3.0])
        result = expr_2d.integrate((0, 2), variable="x", method="numerical", y=y_values)

        # For each y value, integral of x*y from 0 to 2 is y * [x^2/2] = y * 2 = 2*y
        expected = 2.0 * y_values
        np.testing.assert_allclose(result, expected, rtol=1e-6)
