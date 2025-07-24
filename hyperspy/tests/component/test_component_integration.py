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

from hyperspy.component import Component


class TestableComponent(Component):
    """A simple 1D component for testing integration."""

    def __init__(self):
        super().__init__(["A"])
        self.A.value = 1.0

    def function(self, x):
        return self.A.value * x


class Testable2DComponent(Component):
    """A simple 2D component for testing integration."""

    def __init__(self):
        super().__init__(["A"])
        self.A.value = 1.0
        self._is2D = True

    def function(self, x, y):
        return self.A.value * x * y


class ComponentWithoutFunction(Component):
    """A component without function method for testing error cases."""

    def __init__(self):
        super().__init__(["A"])
        self.A.value = 1.0


class TestComponentIntegration:
    """Test component integration methods."""

    def test_1d_component_integration(self):
        """Test integration of 1D component."""
        comp = TestableComponent()
        comp.A.value = 2.0

        # Integrate 2*x from 0 to 3: should be 2*x^2/2 = x^2, so 3^2 = 9
        result = comp.integrate((0, 3), variable="x")
        expected = 9.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_1d_component_different_methods(self):
        """Test that different method names work for 1D component."""
        comp = TestableComponent()

        # Test numerical and auto methods
        result_numerical = comp.integrate((0, 2), variable="x", method="numerical")
        result_auto = comp.integrate((0, 2), variable="x", method="auto")
        np.testing.assert_allclose(result_numerical, result_auto, rtol=1e-6)

        # Test that symbolic raises NotImplementedError
        with pytest.raises(
            NotImplementedError, match="Symbolic integration is not implemented"
        ):
            comp.integrate((0, 2), variable="x", method="symbolic")

    def test_2d_component_double_integration(self):
        """Test double integration of 2D component."""
        comp = Testable2DComponent()
        comp.A.value = 1.0

        # Integrate x*y over [0,2] x [0,3]: should be (2^2/2) * (3^2/2) = 2 * 4.5 = 9
        result = comp.integrate([(0, 2), (0, 3)], variable=("x", "y"))
        expected = 9.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_2d_component_single_variable_integration_x(self):
        """Test single variable integration over x for 2D component."""
        comp = Testable2DComponent()
        comp.A.value = 1.0

        # Integrate x*y over x=[0,2] with y=3: should be (2^2/2) * 3 = 2 * 3 = 6
        result = comp.integrate((0, 2), variable="x", y=3.0)
        expected = 6.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_2d_component_single_variable_integration_y(self):
        """Test single variable integration over y for 2D component."""
        comp = Testable2DComponent()
        comp.A.value = 1.0

        # Integrate x*y over y=[0,3] with x=2: should be 2 * (3^2/2) = 2 * 4.5 = 9
        result = comp.integrate((0, 3), variable="y", x=2.0)
        expected = 9.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_2d_component_array_integration_x(self):
        """Test single variable integration with array of fixed values."""
        comp = Testable2DComponent()
        comp.A.value = 1.0

        # Integrate x*y over x=[0,2] with y=[1,2,3]
        y_values = np.array([1.0, 2.0, 3.0])
        results = comp.integrate((0, 2), variable="x", y=y_values)
        expected = np.array([2.0, 4.0, 6.0])  # 2*y for each y value
        np.testing.assert_allclose(results, expected, rtol=1e-6)

    def test_2d_component_array_integration_y(self):
        """Test single variable integration with array of fixed values over y."""
        comp = Testable2DComponent()
        comp.A.value = 1.0

        # Integrate x*y over y=[0,3] with x=[1,2]
        x_values = np.array([1.0, 2.0])
        results = comp.integrate((0, 3), variable="y", x=x_values)
        expected = np.array([4.5, 9.0])  # x*(3^2/2) for each x value
        np.testing.assert_allclose(results, expected, rtol=1e-6)

    def test_2d_component_array_integration_y_multiple(self):
        """Test y-variable array integration with multiple x values."""
        comp = Testable2DComponent()
        comp.A.value = 1.0

        # Integrate x*y over y=[0,2] with x=[1,2,3]
        x_values = np.array([1.0, 2.0, 3.0])
        results = comp.integrate((0, 2), variable="y", x=x_values)
        expected = np.array([2.0, 4.0, 6.0])  # x*(2^2/2) = x*2 for each x value
        np.testing.assert_allclose(results, expected, rtol=1e-6)

    def test_invalid_method_raises_error(self):
        """Test that invalid method parameter raises ValueError."""
        comp = TestableComponent()

        with pytest.raises(ValueError, match="Invalid method 'invalid'"):
            comp.integrate((0, 1), method="invalid")

    def test_component_without_function_raises_error(self):
        """Test that component without function method raises NotImplementedError."""
        comp = ComponentWithoutFunction()

        with pytest.raises(
            NotImplementedError, match="does not implement the 'function' method"
        ):
            comp.integrate((0, 1))

    def test_invalid_variable_raises_error(self):
        """Test that invalid variable parameter raises ValueError."""
        comp = TestableComponent()

        with pytest.raises(ValueError, match="Unsupported variable"):
            comp.integrate((0, 1), variable="z")

    def test_1d_component_y_variable_raises_error(self):
        """Test that using y variable with 1D component raises ValueError."""
        comp = TestableComponent()

        with pytest.raises(
            ValueError, match="Variable 'y' is only valid for 2D components"
        ):
            comp.integrate((0, 1), variable="y", x=1.0)

    def test_2d_component_missing_fixed_variable_x(self):
        """Test that 2D component integration over x without y raises ValueError."""
        comp = Testable2DComponent()

        with pytest.raises(ValueError, match="must provide 'y' value"):
            comp.integrate((0, 1), variable="x")

    def test_2d_component_missing_fixed_variable_y(self):
        """Test that 2D component integration over y without x raises ValueError."""
        comp = Testable2DComponent()

        with pytest.raises(ValueError, match="must provide 'x' value"):
            comp.integrate((0, 1), variable="y")

    def test_invalid_limits_format(self):
        """Test that invalid limits format raises ValueError."""
        comp = TestableComponent()

        # Single variable integration needs tuple
        with pytest.raises(ValueError, match="limits must be a tuple"):
            comp.integrate([0, 1], variable="x")

        # Wrong number of elements
        with pytest.raises(ValueError, match="limits must be a tuple"):
            comp.integrate((0, 1, 2), variable="x")

    def test_double_integration_invalid_limits(self):
        """Test double integration with invalid limits."""
        comp = Testable2DComponent()

        # Wrong number of variable elements
        with pytest.raises(
            ValueError, match="variable must be a tuple of exactly 2 elements"
        ):
            comp.integrate([(0, 1), (0, 2)], variable=("x", "y", "z"))

        # Wrong limits format for double integration (single tuple instead of two
        # tuples)
        with pytest.raises(ValueError, match="limits must be a list/tuple of 2 tuples"):
            comp.integrate((0, 1), variable=("x", "y"))

        # Wrong variables for 2D integration
        with pytest.raises(ValueError, match="variables must be 'x' and 'y'"):
            comp.integrate([(0, 1), (0, 2)], variable=("x", "z"))


class TestComponentIntegrationND:
    """Test component integrate_nd method."""

    def test_integrate_nd_raises_not_implemented(self):
        """Test that integrate_nd raises NotImplementedError."""
        comp = TestableComponent()

        with pytest.raises(NotImplementedError, match="Navigation-aware integration"):
            comp.integrate_nd((0, 1))

    def test_integrate_nd_with_any_method(self):
        """Test that integrate_nd raises NotImplementedError regardless of method."""
        comp = TestableComponent()

        # All methods should raise NotImplementedError without validation
        for method in ["auto", "numerical", "symbolic", "invalid"]:
            with pytest.raises(
                NotImplementedError, match="Navigation-aware integration"
            ):
                comp.integrate_nd((0, 1), method=method)


class TestComponentIntegrationDocstrings:
    """Test that dynamic docstrings are properly applied."""

    def test_integrate_docstring_contains_parameters(self):
        """Test that integrate method has proper docstring."""
        docstring = Component.integrate.__doc__
        assert docstring is not None
        assert "limits : tuple or list of tuples" in docstring
        assert "variable : str or tuple, default 'x'" in docstring
        assert "method : str, default 'numerical'" in docstring
        assert "**kwargs" in docstring

    def test_integrate_nd_docstring_contains_parameters(self):
        """Test that integrate_nd method has proper docstring."""
        docstring = Component.integrate_nd.__doc__
        assert docstring is not None
        assert "limits : tuple or list of tuples" in docstring
        assert "variable : str or tuple, default 'x'" in docstring
        assert "method : str, default 'numerical'" in docstring
        assert "**kwargs" in docstring

    def test_constant_term_property(self):
        """Test that _constant_term property returns 0 for base Component."""
        comp = TestableComponent()
        assert comp._constant_term == 0
