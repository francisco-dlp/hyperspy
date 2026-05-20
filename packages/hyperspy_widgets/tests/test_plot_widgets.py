import matplotlib
import numpy as np
import pytest
from hyperspy_widgets.widgets import (
    CircleWidget,
    Line2DWidget,
    PolygonWidget,
    RangeWidget,
)

from ._test_support import (
    FakeAxis,
    FakeAxisSource,
    make_image_axes,
    make_motion_event,
    make_plot_axes,
)


def _line_endpoint_indices(line):
    return tuple(
        np.array([axis.value2index(value) for axis, value in zip(line.axes, endpoint)])
        for endpoint in line.position
    )


class TestPlotLine2DWidget:
    def setup_method(self, method):
        del method
        self.axis_source = FakeAxisSource(
            signal_axes=[FakeAxis(size=100, scale=1.2), FakeAxis(size=100, scale=1.2)]
        )
        self.line2d = Line2DWidget(self.axis_source)

    def test_init(self):
        assert self.line2d.color == "red"
        assert self.line2d.linewidth == 1
        assert self.line2d.axis_source is self.axis_source
        np.testing.assert_allclose(self.line2d._size, np.array([0]))
        np.testing.assert_allclose(self.line2d._pos, np.array([[0, 0], [1.2, 0]]))

        assert self.line2d.position == ([0.0, 0.0], [1.2, 0.0])
        np.testing.assert_allclose(
            _line_endpoint_indices(self.line2d)[0], np.array([0, 0])
        )
        np.testing.assert_allclose(
            _line_endpoint_indices(self.line2d)[1], np.array([1, 0])
        )
        np.testing.assert_allclose(self.line2d.get_centre(), np.array([0.6, 0.0]))

    def test_position(self):
        self.line2d.position = ([12.0, 60.0], [36.0, 96.0])

        assert self.line2d.position == ([12.0, 60.0], [36.0, 96.0])
        np.testing.assert_allclose(
            _line_endpoint_indices(self.line2d)[0], np.array([10, 50])
        )
        np.testing.assert_allclose(
            _line_endpoint_indices(self.line2d)[1], np.array([30, 80])
        )
        np.testing.assert_allclose(self.line2d.get_centre(), np.array([24.0, 78.0]))

    def test_position_snap_position(self):
        self.line2d.snap_position = True
        self.line2d.position = ([12.5, 61.0], [36.0, 96.0])

        np.testing.assert_allclose(self.line2d.position, ([12.0, 61.2], [36.0, 96.0]))
        np.testing.assert_allclose(
            _line_endpoint_indices(self.line2d)[0], np.array([10, 51])
        )
        np.testing.assert_allclose(
            _line_endpoint_indices(self.line2d)[1], np.array([30, 80])
        )
        np.testing.assert_allclose(self.line2d.get_centre(), np.array([24.0, 78.6]))

    def test_length(self):
        x = 10
        self.line2d.position = ([10.0, 10.0], [10.0 + x, 10.0])
        assert self.line2d.get_line_length() == x

        y = 20
        self.line2d.position = ([20.0, 10.0], [20.0 + x, 10 + y])
        np.testing.assert_almost_equal(
            self.line2d.get_line_length(), np.sqrt(x**2 + y**2)
        )

    def test_change_size(self):
        _, ax = make_image_axes(shape=(100, 100))
        self.line2d.set_mpl_ax(ax)

        self.line2d.position = ([0.0, 0.0], [50.0, 50.0])
        assert self.line2d.size == (0,)
        self.line2d.increase_size()
        assert self.line2d.size == (1.2,)
        self.line2d.increase_size()
        assert self.line2d.size == (2.4,)
        self.line2d.decrease_size()
        assert self.line2d.size == (1.2,)

        self.line2d.size = (4.0,)
        assert self.line2d.size == (4.0,)

    def test_change_size_snap_size(self):
        _, ax = make_image_axes(shape=(100, 100))
        self.line2d.set_mpl_ax(ax)

        self.line2d.snap_size = True
        self.line2d.position = ([12.0, 60.0], [36.0, 96.0])
        assert self.line2d.position == ([12.0, 60.0], [36.0, 96.0])
        np.testing.assert_allclose(self.line2d.get_centre(), np.array([24.0, 78.0]))
        assert self.line2d.size == (0,)

        self.line2d.size = [3]
        np.testing.assert_allclose(self.line2d.size, np.array([2.4]))
        self.line2d.size = (5,)
        np.testing.assert_allclose(self.line2d.size, np.array([4.8]))
        self.line2d.size = np.array([7.4])
        np.testing.assert_allclose(self.line2d.size, np.array([7.2]))
        self.line2d.increase_size()
        np.testing.assert_allclose(self.line2d.size, np.array([8.4]))

    def test_change_size_snap_size_different_scale(self):
        line2d = Line2DWidget(
            FakeAxisSource(
                signal_axes=[
                    FakeAxis(size=100, scale=0.8),
                    FakeAxis(size=100, scale=1.2),
                ]
            )
        )

        assert line2d.axes[0].scale == 0.8
        assert line2d.axes[1].scale == 1.2
        line2d.snap_size = True
        assert line2d.snap_size is False

    def test_plot_line2d(self):
        _, ax = make_image_axes(shape=(100, 100))
        self.line2d.color = "green"
        self.line2d.position = ([12.0, 60.0], [36.0, 96.0])
        self.line2d.set_mpl_ax(ax)
        assert self.line2d.ax == ax

        line2d = Line2DWidget(self.axis_source)
        line2d.snap_position = True
        line2d.set_mpl_ax(ax)
        line2d.position = ([40.0, 20.0], [96.0, 36.0])
        line2d.linewidth = 4
        line2d.size = (15.0,)
        assert line2d.size == (15.0,)

        line2d_snap_all = Line2DWidget(self.axis_source)
        line2d_snap_all.snap_all = True
        line2d_snap_all.set_mpl_ax(ax)
        line2d_snap_all.position = ([50.0, 60.0], [96.0, 54.0])
        np.testing.assert_allclose(line2d_snap_all.position[0], [50.4, 60.0])
        np.testing.assert_allclose(line2d_snap_all.position[1], [96.0, 54.0])

        line2d_snap_all.size = (15.0,)
        np.testing.assert_allclose(line2d_snap_all.size[0], 14.4)


class TestPlotCircleWidget:
    def setup_method(self, method):
        del method
        self.axis_source = FakeAxisSource(
            signal_axes=[FakeAxis(size=100, scale=1.2), FakeAxis(size=100, scale=1.2)]
        )
        self.circle = CircleWidget(self.axis_source)

    def test_change_size_snap_size(self):
        _, ax = make_image_axes(shape=(100, 100))
        self.circle.set_mpl_ax(ax)
        self.circle.snap_all = True

        self.circle.position = (10, 10)
        self.circle.size = (5, 1.0)
        assert self.circle.position == (9.6, 9.6)
        np.testing.assert_allclose(self.circle.size, (5.4, 0.6))

        self.circle.decrease_size()
        np.testing.assert_allclose(self.circle.size, (4.2, 0.0))
        self.circle.decrease_size()
        np.testing.assert_allclose(self.circle.size, (3.0, 0.0))

        self.circle.increase_size()
        np.testing.assert_allclose(self.circle.size, (4.2, 0.0))

        self.circle.size = (5, 1.0)
        self.circle.increase_size()
        np.testing.assert_allclose(self.circle.size, (6.6, 1.8))

    def test_change_size(self):
        _, ax = make_image_axes(shape=(100, 100))
        self.circle.set_mpl_ax(ax)
        self.circle.snap_all = False

        position, size = (10, 10), (5, 2.5)
        self.circle.position = position
        self.circle.size = size
        assert self.circle.position == position
        assert self.circle.size == size


class TestPlotPolygonWidget:
    def test_polygon_setup(self):
        im_4d = FakeAxisSource(
            navigation_axes=[FakeAxis(size=4), FakeAxis(size=4)],
            signal_axes=[FakeAxis(size=4), FakeAxis(size=4)],
        )
        _, ax = make_image_axes(shape=(4, 4))
        polygon = PolygonWidget(im_4d)
        polygon.set_mpl_ax(ax)
        assert polygon.axes == im_4d.navigation_axes[0:2]
        assert polygon.ax is ax

        im_3d = FakeAxisSource(
            navigation_axes=[FakeAxis(size=4)],
            signal_axes=[FakeAxis(size=4), FakeAxis(size=4)],
        )
        polygon = PolygonWidget(im_3d)
        assert polygon.axes == im_3d.signal_axes[0:2]

        im_2d = FakeAxisSource(signal_axes=[FakeAxis(size=4), FakeAxis(size=4)])
        polygon = PolygonWidget(im_2d)
        assert polygon.axes == im_2d.signal_axes[0:2]

        with pytest.raises(ValueError):
            PolygonWidget(FakeAxisSource(signal_axes=[FakeAxis(size=4)]))

        im_2d_navsig = FakeAxisSource(
            navigation_axes=[FakeAxis(size=4)],
            signal_axes=[FakeAxis(size=4)],
            shape=(4, 4),
        )
        polygon = PolygonWidget(im_2d_navsig)
        assert polygon.axes == im_2d_navsig.signal_axes + im_2d_navsig.navigation_axes

    def test_set_vertices(self):
        polygon = PolygonWidget(
            FakeAxisSource(signal_axes=[FakeAxis(size=100), FakeAxis(size=100)])
        )
        _, ax = make_image_axes(shape=(100, 100))
        polygon.set_mpl_ax(ax)

        assert polygon.get_vertices() == []
        assert polygon.get_centre() == tuple()
        assert not polygon._finished_building
        assert not polygon.finished_building()

        verts = [(31, 41), (15, 92), (65, 35)]
        polygon.set_vertices(verts)
        np.testing.assert_allclose(polygon.get_vertices(), verts)
        assert polygon._finished_building
        assert polygon.finished_building()
        assert polygon.get_centre() == (40.0, 63.5)

        verts = np.arange(100).reshape((50, 2))
        verts[::2, 1] = 0
        polygon.set_vertices(verts)
        np.testing.assert_allclose(polygon.get_vertices(), list(verts))
        assert polygon._finished_building
        assert polygon.finished_building()
        assert polygon.get_centre() == (49.0, 49.5)

        verts = [(31, 41), (15, 92), (65, 35)]
        polygon._complete_building(verts)
        np.testing.assert_allclose(polygon._cached_vertices, verts)
        assert polygon._finished_building

    def test_unattached(self):
        polygon = PolygonWidget(None)
        assert polygon.get_vertices() == []
        assert polygon.get_centre() == tuple()

    def test_mock_event(self):
        polygon = PolygonWidget(
            FakeAxisSource(signal_axes=[FakeAxis(size=100), FakeAxis(size=100)])
        )
        _, ax = make_image_axes(shape=(100, 100))
        polygon.set_mpl_ax(ax)

        event = make_motion_event(ax, 1, 1)
        polygon._onmove(event)

        event.button = "x"
        polygon._onmove(event)

    def test_set_on(self):
        polygon = PolygonWidget(
            FakeAxisSource(signal_axes=[FakeAxis(size=100), FakeAxis(size=100)])
        )
        _, ax = make_image_axes(shape=(100, 100))

        assert polygon.ax is None
        assert polygon._is_on

        polygon.set_mpl_ax(ax)
        assert polygon.ax is ax
        polygon.set_mpl_ax(ax)
        assert polygon.ax is ax
        assert polygon._is_on

        polygon.set_on(False, render_figure=True)
        assert polygon.ax is None
        assert not polygon._is_on


class TestPlotRangeWidget:
    def setup_method(self, method):
        del method
        self.axis_source = FakeAxisSource(signal_axes=[FakeAxis(size=50, scale=1.2)])
        self.range_widget = RangeWidget(self.axis_source)

    def test_snap_position_span_None(self):
        assert self.range_widget.span is None
        self.range_widget.snap_position = True
        assert self.range_widget.snap_position

    def test_plot_range(self):
        _, ax = make_plot_axes(length=50)
        self.range_widget.set_mpl_ax(ax)
        assert self.range_widget.ax == ax
        assert self.range_widget.color == "r"
        assert self.range_widget.position == (0.0,)
        assert self.range_widget.size == (1.2,)
        assert self.range_widget.span.artists[0].get_alpha() == 0.25

        w = RangeWidget(self.axis_source, color="blue")
        w.set_mpl_ax(ax)
        w.set_ibounds(left=4, width=3)
        assert w.color == "blue"
        color_rgba = matplotlib.colors.to_rgba("blue", alpha=0.25)
        np.testing.assert_allclose(w.span.artists[0].get_fc(), color_rgba)
        np.testing.assert_allclose(w.span.artists[0].get_ec(), color_rgba)
        np.testing.assert_allclose(w.position[0], 4.8)
        np.testing.assert_allclose(w.size[0], 3.6)

        w2 = RangeWidget(self.axis_source)
        w2.set_mpl_ax(ax)
        assert w2.ax == ax

        w2.set_bounds(left=24.0, width=12.0)
        assert w2.position[0] == 24.0
        assert w2.size[0] == 12.0
        w2.color = "green"
        assert w2.color == "green"
        w2.alpha = 0.25
        assert w2.alpha == 0.25

    @pytest.mark.parametrize("render_figure", [True, False])
    def test_set_on(self, render_figure):
        _, ax = make_plot_axes(length=50)
        self.range_widget.ax = ax
        self.range_widget._is_on = False

        self.range_widget.set_on(True, render_figure=render_figure)
        assert self.range_widget.span.get_visible()

        self.range_widget.set_on(False, render_figure=render_figure)
        assert self.range_widget.span is None
        assert self.range_widget.ax is None

    def test_update(self):
        _, ax = make_plot_axes(length=50)
        self.range_widget.set_mpl_ax(ax)
        self.range_widget.span.update()

    def test_plot_range_with_vertical_axis(self):
        axis_source = FakeAxisSource(
            signal_axes=[FakeAxis(size=10, scale=0.1), FakeAxis(size=10, scale=5.0)]
        )
        _, ax = make_image_axes()

        range_h = RangeWidget(axis_source, direction="horizontal")
        range_h.set_mpl_ax(ax)

        range_v = RangeWidget(axis_source, direction="vertical", color="blue")
        range_v.axes = (axis_source.signal_axes[1],)
        range_v.set_mpl_ax(ax)
        assert range_v.position == (0.0,)
        assert range_v.size == (5.0,)

        range_v.set_bounds(left=20.0, width=15.0)
        assert range_v.position == (20.0,)
        assert range_v.size == (15.0,)
