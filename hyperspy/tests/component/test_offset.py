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

import itertools

import numpy as np
import pytest

import hyperspy.api as hs

TRUE_FALSE_2_TUPLE = [p for p in itertools.product((True, False), repeat=2)]


class TestOffset:
    def setup_method(self, method):
        s = hs.signals.Signal1D(np.zeros(10))
        s.axes_manager[0].scale = 0.01
        m = s.create_model()
        m.append(hs.model.components1D.Offset())
        m[0].offset.value = 10
        self.m = m

    @pytest.mark.parametrize(("uniform"), (True, False))
    @pytest.mark.parametrize(("only_current", "binned"), TRUE_FALSE_2_TUPLE)
    def test_estimate_parameters(self, only_current, binned, uniform):
        self.m.signal.axes_manager[-1].is_binned = binned
        self.m.assign_current_values_to_all()
        s = self.m.as_signal()
        if not uniform:
            s.axes_manager[-1].convert_to_non_uniform_axis()
        assert s.axes_manager[-1].is_binned == binned
        o = hs.model.components1D.Offset()
        o.estimate_parameters(s, None, None, only_current=only_current)
        assert o._axes_manager[-1].is_binned == binned
        assert o._axes_manager[-1].is_uniform == uniform
        np.testing.assert_allclose(o.offset.value, 10)

    @pytest.mark.parametrize(("uniform"), (True, False))
    @pytest.mark.parametrize(("binned"), (True, False))
    def test_function_nd(self, binned, uniform):
        self.m.signal.axes_manager[-1].is_binned = binned
        self.m.assign_current_values_to_all()
        s = self.m.as_signal()
        s = hs.stack([s] * 2)
        o = hs.model.components1D.Offset()
        o.estimate_parameters(s, None, None, only_current=False)
        assert o._axes_manager[-1].is_binned == binned
        axis = s.axes_manager.signal_axes[0]
        factor = axis.scale if binned else 1
        np.testing.assert_allclose(o.function_nd(axis.axis) * factor, s.data)

    def test_constant_term(self):
        m = self.m
        o = m[0]
        o.offset.free = True
        assert o._constant_term == 0

        o.offset.free = False
        assert o._constant_term == o.offset.value

    def test_integrate_analytical(self):
        """Test the analytical integration method for Offset component."""
        o = hs.model.components1D.Offset(offset=5.0)

        # Test basic integration
        result = o.integrate((0, 3))
        expected = 5.0 * (3 - 0)
        np.testing.assert_allclose(result, expected)

        # Test with negative limits
        result = o.integrate((-1, 2))
        expected = 5.0 * (2 - (-1))
        np.testing.assert_allclose(result, expected)

        # Test with reversed limits (should be negative)
        result = o.integrate((3, 1))
        expected = 5.0 * (1 - 3)
        np.testing.assert_allclose(result, expected)

        # Test with zero width integration
        result = o.integrate((2, 2))
        expected = 5.0 * (2 - 2)
        np.testing.assert_allclose(result, expected)

        # Test with different offset value
        o.offset.value = 2.5
        result = o.integrate((1, 5))
        expected = 2.5 * (5 - 1)
        np.testing.assert_allclose(result, expected)

        # Test with floating point limits
        result = o.integrate((0.5, 3.7))
        expected = 2.5 * (3.7 - 0.5)
        np.testing.assert_allclose(result, expected)

    def test_integrate_error_handling(self):
        """Test error handling for the integrate method."""
        o = hs.model.components1D.Offset(offset=5.0)

        # Test invalid limits format
        with pytest.raises(ValueError, match="limits must be a tuple of length 2"):
            o.integrate([0, 3])  # List instead of tuple

        with pytest.raises(ValueError, match="limits must be a tuple of length 2"):
            o.integrate((0, 3, 5))  # Too many elements

        with pytest.raises(ValueError, match="limits must be a tuple of length 2"):
            o.integrate(5)  # Not a tuple

    def test_integrate_api_compatibility(self):
        """Test that integrate method accepts standard parameters for API compatibility."""
        o = hs.model.components1D.Offset(offset=5.0)

        # Test that variable parameter is accepted (but ignored for constant function)
        result1 = o.integrate((0, 2), variable="x")
        result2 = o.integrate((0, 2), variable="y")  # Should work even though it's 1D
        result3 = o.integrate((0, 2))  # Default

        # All should give same result since it's a constant function
        expected = 5.0 * 2
        np.testing.assert_allclose(result1, expected)
        np.testing.assert_allclose(result2, expected)
        np.testing.assert_allclose(result3, expected)

        # Test that additional kwargs are accepted and ignored
        result = o.integrate((0, 2), method="analytical", some_param=123)
        np.testing.assert_allclose(result, expected)

    def test_integrate_vs_numerical(self):
        """Test that analytical integration gives same result as numerical."""
        from hyperspy.component import Component

        o = hs.model.components1D.Offset(offset=7.3)

        # Compare analytical vs numerical integration
        analytical_result = o.integrate((1, 4))
        numerical_result = Component.integrate(o, (1, 4))

        # Should be identical (within floating point precision)
        np.testing.assert_allclose(analytical_result, numerical_result, rtol=1e-12)

        # Test with different ranges
        for limits in [(0, 1), (-2, 3), (0.5, 1.5), (-1, -0.5)]:
            analytical = o.integrate(limits)
            numerical = Component.integrate(o, limits)
            np.testing.assert_allclose(analytical, numerical, rtol=1e-12)

    def test_integrate_nd_basic_functionality(self):
        """Test integrate_nd method for navigation-aware integration."""
        o = hs.model.components1D.Offset(offset=2.0)

        # Test single parameter value
        result = o.integrate_nd((0, 3))
        expected = 6.0  # 2.0 * (3 - 0)
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

        # Test different parameter value
        o.offset.value = 3.0
        result = o.integrate_nd((1, 4))
        expected = 9.0  # 3.0 * (4 - 1)
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

        # Test negative range
        result = o.integrate_nd((-1, 2))
        expected = 9.0  # 3.0 * (2 - (-1))
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"
