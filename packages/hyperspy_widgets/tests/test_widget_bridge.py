import gc

import numpy as np

from hyperspy.drawing.widget_bridge import WidgetAxisBridge

from ._test_support import FakeAxis, FakeAxisSource


class TrackingFakeAxisSource(FakeAxisSource):
    """FakeAxisSource that tracks coordinates setter calls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._coordinates = tuple(0.0 for _ in range(self.navigation_dimension))
        self.coordinates_set_calls = []

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, value):
        self.coordinates_set_calls.append(value)
        self._coordinates = value


def test_snap_grid_uniform():
    axis = FakeAxis(size=5, scale=2, offset=10)
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(5,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    grids = bridge.snap_grid
    assert len(grids) == 1
    expected = np.arange(10, 20, 2)
    np.testing.assert_array_equal(grids[0], expected)


def test_snap_grid_nonuniform():
    axis = FakeAxis(size=4, values=[1, 3, 7, 15])
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(4,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    grids = bridge.snap_grid
    assert len(grids) == 1
    expected = np.array([1, 3, 7, 15], dtype=float)
    np.testing.assert_array_equal(grids[0], expected)


def test_snap_grid_single_point():
    axis = FakeAxis(size=1, scale=1.0, offset=0.0)
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(1,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    grids = bridge.snap_grid
    assert len(grids) == 1
    assert len(grids[0]) == 1
    assert grids[0][0] == 0.0


def test_pull_position():
    axis = FakeAxis(size=10, scale=1.0)
    axis.value = 3.0
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    position = bridge.pull_position()
    assert position == (3.0,)


def test_push_position_writes_values():
    axis = FakeAxis(size=10, scale=1.0)
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    bridge.push_position((3.0,))
    assert axis.value == 3.0


def test_push_position_triggers_indices_changed():
    axis = FakeAxis(size=10, scale=1.0)
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    calls = []
    axis_source.events.indices_changed.connect(lambda obj: calls.append(obj))

    bridge.push_position((3.0,))
    assert len(calls) == 1
    assert calls[0] is axis_source


def test_push_position_suppress_callback():
    axis = FakeAxis(size=10, scale=1.0)
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    calls = []

    def callback(obj):
        calls.append(obj)

    bridge.connect(callback)
    bridge.push_position((3.0,), suppress=True)

    assert len(calls) == 1
    assert calls[0] is axis_source
    assert axis.value == 3.0


def test_push_position_multi_nav_axis_values():
    ax1 = FakeAxis(size=5, scale=1.0)
    ax2 = FakeAxis(size=3, scale=2.0)
    axis_source = TrackingFakeAxisSource(navigation_axes=[ax1, ax2], shape=(5, 3))
    bridge = WidgetAxisBridge(None, axis_source, [ax1, ax2])

    event_calls = []
    axis_source.events.indices_changed.connect(lambda obj: event_calls.append(obj))

    bridge.push_position((2.0, 4.0))

    assert ax1.value == 2.0
    assert ax2.value == 4.0
    assert len(event_calls) == 1
    assert event_calls[0] is axis_source


def test_connect_and_disconnect():
    axis = FakeAxis(size=10, scale=1.0)
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    calls = []

    def callback(obj):
        calls.append(obj)

    bridge.connect(callback)
    axis_source.events.indices_changed.trigger(obj=axis_source)

    assert len(calls) == 1
    assert calls[0] is axis_source


def test_connect_disconnect_lifecycle():
    axis = FakeAxis(size=10, scale=1.0)
    axis_source = FakeAxisSource(navigation_axes=[axis], shape=(10,))
    bridge = WidgetAxisBridge(None, axis_source, [axis])

    calls = []

    def callback(obj):
        calls.append(obj)

    bridge.connect(callback)
    bridge.disconnect(callback)
    axis_source.events.indices_changed.trigger(obj=axis_source)

    assert len(calls) == 0


def test_weak_ref_widget():
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


def test_two_axes_bridge():
    ax1 = FakeAxis(size=5, scale=2.0, offset=10)
    ax2 = FakeAxis(size=3, scale=1.0, offset=0)
    axis_source = FakeAxisSource(navigation_axes=[ax1, ax2], shape=(5, 3))
    bridge = WidgetAxisBridge(None, axis_source, [ax1, ax2])

    grids = bridge.snap_grid
    assert len(grids) == 2

    expected1 = np.arange(10, 20, 2)
    expected2 = np.arange(0, 3, 1)
    np.testing.assert_array_equal(grids[0], expected1)
    np.testing.assert_array_equal(grids[1], expected2)
