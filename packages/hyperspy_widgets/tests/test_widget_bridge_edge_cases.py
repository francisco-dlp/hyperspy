"""Edge case tests for WidgetAxisBridge.

Tests defensive scenarios, idempotency, and boundary conditions.
"""

import gc

import numpy as np

from hyperspy.drawing.widget_bridge import WidgetAxisBridge

from ._test_support import FakeAxis, FakeAxisSource


class TestSinglePointAxis:
    """Edge cases with single-point axes (size=1)."""

    def test_snap_grid_single_point_uniform(self):
        """Single-point uniform axis produces a grid with one element."""
        axis = FakeAxis(size=1, scale=1.0, offset=5.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(1,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        grids = bridge.snap_grid
        assert len(grids) == 1
        assert len(grids[0]) == 1
        assert grids[0][0] == 5.0

    def test_pull_position_single_point(self):
        """Pull position from single-point axis returns its only value."""
        axis = FakeAxis(size=1, scale=1.0, offset=42.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(1,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        position = bridge.pull_position()
        assert position == (42.0,)

    def test_push_position_single_point(self):
        """Push position to single-point axis succeeds if value matches."""
        axis = FakeAxis(size=1, scale=1.0, offset=10.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(1,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((10.0,))
        assert axis.value == 10.0

    def test_push_position_out_of_bounds_single_point(self):
        """Out-of-bounds push to single-point axis is silently ignored."""
        axis = FakeAxis(size=1, scale=1.0, offset=10.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(1,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((99.0,))
        assert axis.value == 10.0


class TestEmptyAxis:
    """Edge cases with empty axis lists."""

    def test_empty_axes_snap_grid(self):
        """Bridge with no axes returns empty tuple for snap_grid."""
        axis_source = FakeAxisSource(navigation_axes=[], shape=())
        bridge = WidgetAxisBridge(None, axis_source, [])

        grids = bridge.snap_grid
        assert grids == ()

    def test_empty_axes_pull_position(self):
        """Pull position with no axes returns empty tuple."""
        axis_source = FakeAxisSource(navigation_axes=[], shape=())
        bridge = WidgetAxisBridge(None, axis_source, [])

        position = bridge.pull_position()
        assert position == ()

    def test_empty_axes_push_position(self):
        """Push position with no axes is a no-op."""
        axis_source = FakeAxisSource(navigation_axes=[], shape=())
        bridge = WidgetAxisBridge(None, axis_source, [])

        bridge.push_position(())
        bridge.push_position((), suppress=True)

    def test_empty_axes_connect_disconnect(self):
        """Connect/disconnect with no axes does not crash."""
        axis_source = FakeAxisSource(navigation_axes=[], shape=())
        bridge = WidgetAxisBridge(None, axis_source, [])

        calls = []

        def callback(obj):
            calls.append(obj)

        bridge.connect(callback)
        bridge.disconnect(callback)


class TestDoubleDisconnectIdempotency:
    """Tests that disconnect is safe to call multiple times."""

    def test_double_disconnect_no_raise(self):
        """Calling disconnect twice should not raise."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        calls = []

        def callback(obj):
            calls.append(obj)

        bridge.connect(callback)
        bridge.disconnect(callback)
        bridge.disconnect(callback)

        assert len(calls) == 0

    def test_disconnect_without_connect_no_raise(self):
        """Disconnecting without connecting should not raise."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        def callback(obj):
            pass

        bridge.disconnect(callback)

    def test_multiple_bridges_disconnect_idempotent(self):
        """Multiple bridges can disconnect independently without issues."""
        ax1 = FakeAxis(size=5, scale=1.0)
        ax2 = FakeAxis(size=5, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[ax1, ax2], shape=(5, 5))
        bridge1 = WidgetAxisBridge(None, axis_source, [ax1])
        bridge2 = WidgetAxisBridge(None, axis_source, [ax2])

        calls = []

        def callback(obj):
            calls.append(obj)

        bridge1.connect(callback)
        bridge2.connect(callback)
        bridge1.disconnect(callback)
        bridge2.disconnect(callback)
        bridge2.disconnect(callback)


class TestOutOfBoundsPushPosition:
    """Tests push_position with out-of-bounds values."""

    def test_push_position_value_too_low(self):
        """Value below axis low_value is silently ignored."""
        axis = FakeAxis(size=10, scale=1.0, offset=0.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((-5.0,))
        assert axis.value == 0.0

    def test_push_position_value_too_high(self):
        """Value above axis high_value is silently ignored."""
        axis = FakeAxis(size=10, scale=1.0, offset=0.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((99.0,))
        assert axis.value == 0.0

    def test_push_position_partially_out_of_bounds(self):
        """When one axis is out of bounds, others still update."""
        ax1 = FakeAxis(size=10, scale=1.0, offset=0.0)
        ax2 = FakeAxis(size=10, scale=1.0, offset=0.0)
        axis_source = FakeAxisSource(navigation_axes=[ax1, ax2], shape=(10, 10))
        bridge = WidgetAxisBridge(None, axis_source, [ax1, ax2])

        bridge.push_position((5.0, 99.0))

        assert ax1.value == 5.0
        assert ax2.value == 0.0

    def test_push_position_with_suppress_out_of_bounds(self):
        """Suppress works correctly with out-of-bounds values."""
        axis = FakeAxis(size=10, scale=1.0, offset=0.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        calls = []

        def callback(obj):
            calls.append(obj)

        bridge.connect(callback)
        bridge.push_position((99.0,), suppress=True)

        assert len(calls) == 1
        assert axis.value == 0.0


class TestMixedNavSignalAxes:
    """Tests with mixed navigation and signal axes."""

    def test_bridge_with_nav_and_signal_axes(self):
        """Bridge works correctly when axes span nav and signal dimensions."""
        nav_ax = FakeAxis(size=5, scale=1.0, offset=0.0)
        sig_ax = FakeAxis(size=3, scale=0.5, offset=10.0)
        axis_source = FakeAxisSource(
            navigation_axes=[nav_ax], signal_axes=[sig_ax], shape=(5, 3)
        )
        bridge = WidgetAxisBridge(None, axis_source, [nav_ax, sig_ax])

        grids = bridge.snap_grid
        assert len(grids) == 2
        np.testing.assert_array_equal(grids[0], np.arange(0, 5, 1.0))
        np.testing.assert_array_equal(grids[1], np.array([10.0, 10.5, 11.0]))

    def test_pull_position_nav_and_signal(self):
        """Pull position returns values from both nav and signal axes."""
        nav_ax = FakeAxis(size=5, scale=1.0, offset=0.0)
        sig_ax = FakeAxis(size=3, scale=0.5, offset=10.0)
        nav_ax.value = 2.0
        sig_ax.value = 11.0
        axis_source = FakeAxisSource(
            navigation_axes=[nav_ax], signal_axes=[sig_ax], shape=(5, 3)
        )
        bridge = WidgetAxisBridge(None, axis_source, [nav_ax, sig_ax])

        position = bridge.pull_position()
        assert position == (2.0, 11.0)

    def test_push_position_nav_and_signal(self):
        """Push position writes to both nav and signal axes."""
        nav_ax = FakeAxis(size=5, scale=1.0, offset=0.0)
        sig_ax = FakeAxis(size=3, scale=0.5, offset=10.0)
        axis_source = FakeAxisSource(
            navigation_axes=[nav_ax], signal_axes=[sig_ax], shape=(5, 3)
        )
        bridge = WidgetAxisBridge(None, axis_source, [nav_ax, sig_ax])

        bridge.push_position((3.0, 11.0))

        assert nav_ax.value == 3.0
        assert sig_ax.value == 11.0


class TestMultipleBridges2DWidget:
    """Tests with multiple bridges for 2D widget scenarios."""

    def test_two_bridges_same_axes_manager(self):
        """Two bridges can share the same axes_manager with different axes."""
        ax1 = FakeAxis(size=5, scale=1.0, offset=0.0)
        ax2 = FakeAxis(size=3, scale=2.0, offset=10.0)
        axis_source = FakeAxisSource(navigation_axes=[ax1, ax2], shape=(5, 3))

        bridge1 = WidgetAxisBridge(None, axis_source, [ax1])
        bridge2 = WidgetAxisBridge(None, axis_source, [ax2])

        pos1 = bridge1.pull_position()
        pos2 = bridge2.pull_position()

        assert pos1 == (0.0,)
        assert pos2 == (10.0,)

        bridge1.push_position((2.0,))
        bridge2.push_position((12.0,))

        assert ax1.value == 2.0
        assert ax2.value == 12.0

    def test_bridges_trigger_independent_callbacks(self):
        ax1 = FakeAxis(size=5, scale=1.0, offset=0.0)
        ax2 = FakeAxis(size=3, scale=2.0, offset=10.0)
        axis_source = FakeAxisSource(navigation_axes=[ax1, ax2], shape=(5, 3))

        bridge1 = WidgetAxisBridge(None, axis_source, [ax1])
        bridge2 = WidgetAxisBridge(None, axis_source, [ax2])

        calls1 = []
        calls2 = []

        def callback1(obj):
            calls1.append(obj)

        def callback2(obj):
            calls2.append(obj)

        bridge1.connect(callback1)
        bridge2.connect(callback2)

        bridge1.push_position((4.0,))
        assert len(calls1) == 1
        assert len(calls2) == 1

        bridge2.push_position((12.0,))
        assert len(calls1) == 2
        assert len(calls2) == 2


class TestWeakRefCleanupGC:
    """Tests for weak reference cleanup after garbage collection."""

    def test_weak_ref_widget_none_after_gc(self):
        """Widget reference becomes None after widget is garbage collected."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))

        class MockWidget:
            pass

        widget = MockWidget()
        bridge = WidgetAxisBridge(widget, axis_source, [axis])

        assert bridge.widget is widget

        del widget
        gc.collect()

        assert bridge.widget is None

    def test_bridge_works_after_widget_gc(self):
        """Bridge continues to work after widget is garbage collected."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))

        class MockWidget:
            pass

        widget = MockWidget()
        bridge = WidgetAxisBridge(widget, axis_source, [axis])

        del widget
        gc.collect()

        assert bridge.widget is None

        grids = bridge.snap_grid
        assert len(grids) == 1

        bridge.push_position((5.0,))
        assert axis.value == 5.0

        position = bridge.pull_position()
        assert position == (5.0,)

    def test_multiple_widgets_gc_independently(self):
        """Multiple widgets are garbage collected independently."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))

        class MockWidget:
            pass

        widget1 = MockWidget()
        widget2 = MockWidget()
        bridge1 = WidgetAxisBridge(widget1, axis_source, [axis])
        bridge2 = WidgetAxisBridge(widget2, axis_source, [axis])

        assert bridge1.widget is widget1
        assert bridge2.widget is widget2

        del widget1
        gc.collect()

        assert bridge1.widget is None
        assert bridge2.widget is widget2

        del widget2
        gc.collect()

        assert bridge1.widget is None
        assert bridge2.widget is None


class TestNonUniformAxisEdgeCases:
    """Additional edge cases for non-uniform axes."""

    def test_snap_grid_non_uniform(self):
        """Non-uniform axis snap_grid returns axis values directly."""
        values = [1.0, 3.0, 7.0, 15.0]
        axis = FakeAxis(size=4, values=values)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(4,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        grids = bridge.snap_grid
        np.testing.assert_array_equal(grids[0], np.array(values))

    def test_push_position_non_uniform_out_of_bounds(self):
        """Out-of-bounds value is silently ignored in non-uniform axis."""
        values = [1.0, 3.0, 7.0, 15.0]
        axis = FakeAxis(size=4, values=values)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(4,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((0.5,))
        assert axis.value == 1.0

        bridge.push_position((100.0,))
        assert axis.value == 1.0

    def test_pull_position_non_uniform(self):
        """Pull position from non-uniform axis returns current values."""
        values = [1.0, 3.0, 7.0, 15.0]
        axis = FakeAxis(size=4, values=values)
        axis.index = 2
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(4,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        position = bridge.pull_position()
        assert position == (7.0,)


class TestBridgeBeforeAxesSet:
    """Bridge created before axes are fully set in the axes_manager."""

    def test_bridge_before_axis_added_to_source(self):
        """Bridge works even if axis is not yet in the axes_manager."""
        axis = FakeAxis(size=5, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[], shape=())
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((3.0,))
        assert axis.value == 3.0
        assert bridge.pull_position() == (3.0,)

    def test_bridge_then_set_axis_index(self):
        """Bridge created before axis value is set; reflects later changes."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        assert bridge.pull_position() == (0.0,)

        axis.index = 7
        assert bridge.pull_position() == (7.0,)


class TestBridgeBehaviorEdgeCases:
    """Miscellaneous bridge behavior edge cases."""

    def test_bridge_with_none_widget(self):
        """Bridge created with None widget does not crash."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        assert bridge.widget is None

        bridge.push_position((5.0,))
        position = bridge.pull_position()
        assert position == (5.0,)

    def test_push_position_float_conversion(self):
        """Push position converts numeric types to float correctly."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((3.0,))
        assert axis.value == 3.0

        bridge.push_position((3,))
        assert axis.value == 3.0

    def test_push_position_array_like(self):
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((np.array([3.0]),))
        assert axis.value == 3.0

    def test_suppress_callback_without_connect(self):
        """Push with suppress=True when not connected does not crash."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        bridge.push_position((5.0,), suppress=True)
        assert axis.value == 5.0


class TestConnectDisconnectLifecycle:
    """Extended connect/disconnect lifecycle tests."""

    def test_reconnect_after_disconnect(self):
        """Bridge can be reconnected after disconnecting."""
        axis = FakeAxis(size=10, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
        bridge = WidgetAxisBridge(None, axis_source, [axis])

        calls = []

        def callback(obj):
            calls.append(obj)

        bridge.connect(callback)
        assert len(calls) == 0

        bridge.disconnect(callback)
        bridge.connect(callback)

        bridge.push_position((3.0,))
        assert len(calls) == 1

    def test_disconnect_all_callbacks(self):
        """Multiple bridges can be disconnected in any order."""
        ax1 = FakeAxis(size=5, scale=1.0)
        ax2 = FakeAxis(size=5, scale=1.0)
        axis_source = FakeAxisSource(navigation_axes=[ax1, ax2], shape=(5, 5))

        calls = []

        def callback(obj):
            calls.append(obj)

        bridge1 = WidgetAxisBridge(None, axis_source, [ax1])
        bridge2 = WidgetAxisBridge(None, axis_source, [ax2])

        bridge1.connect(callback)
        bridge2.connect(callback)

        bridge2.disconnect(callback)
        bridge1.disconnect(callback)

        assert len(calls) == 0
