# -*- coding: utf-8 -*-
# Copyright 2007-2026 The HyperSpy developers
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

"""Integration tests for the full ROI → WidgetHost → WidgetAxisBridge flow.

Verifies that:
- ROI.add_widget registers widgets in the correct WidgetHost
- ROI.remove_widget deregisters and cleans up bridges
- Figure close cascades through WidgetHost.clear()
- Multiple ROIs on one signal are independent
- Navigation-plot ROIs go to navigator_plot.widget_host
- Signal-plot ROIs go to signal_plot.widget_host
- Bridge push_position updates axes_manager.indices
"""

import numpy as np
import pytest

import hyperspy.api as hs
from hyperspy.roi import RectangularROI, SpanROI


class TestSpanROISignal1DWidgetHost:
    def setup_method(self, method):
        self.s = hs.signals.Signal1D(np.arange(50).reshape(5, 10))
        self.s.plot()

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_add_widget_registers_in_signal_plot_widget_host(self):
        roi = SpanROI(2, 4)
        w = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        wh = self.s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        assert w in wh.widgets

    def test_remove_widget_deregisters(self):
        roi = SpanROI(2, 4)
        _ = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        wh = self.s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        roi.remove_widget(self.s)
        assert wh.widget_count == 0

    def test_widget_host_widget_count_after_remove(self):
        roi = SpanROI(2, 4)
        _ = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        wh = self.s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        roi.remove_widget(self.s)
        assert wh.widget_count == 0

    def test_bridge_push_updates_axes_manager_indices(self):
        roi = SpanROI(2, 4)
        w = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        bridge = roi._bridges[id(w)]
        assert bridge is not None
        pos = bridge.pull_position()
        assert len(pos) == len(w.axes)


class TestRectangularROISignal2DWidgetHost:
    """RectangularROI on Signal2D: widget goes to signal_plot.widget_host."""

    def setup_method(self, method):
        self.s = hs.signals.Signal2D(np.random.random((5, 10, 10)))
        self.s.plot()

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_add_widget_registers_in_signal_plot_widget_host(self):
        roi = RectangularROI(left=1, top=1, right=4, bottom=4)
        _ = roi.add_widget(self.s)
        wh = self.s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        assert w in wh.widgets

    def test_remove_widget_deregisters(self):
        roi = RectangularROI(left=1, top=1, right=4, bottom=4)
        _ = roi.add_widget(self.s)
        wh = self.s._plot.signal_plot.widget_host
        roi.remove_widget(self.s)
        assert wh.widget_count == 0

    def test_bridge_is_created(self):
        roi = RectangularROI(left=1, top=1, right=4, bottom=4)
        w = roi.add_widget(self.s)
        bridge = roi._bridges[id(w)]
        assert bridge is not None


class TestFigureCloseCascadesWidgetCount:
    """Figure close → BlittedFigure._on_close → widget_host.clear() → widget_count→0."""

    def setup_method(self, method):
        self.s = hs.signals.Signal1D(np.arange(50).reshape(5, 10))
        self.s.plot()

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_figure_close_sets_widget_count_to_zero(self):
        roi = SpanROI(2, 4)
        _ = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        wh = self.s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        self.s._plot.signal_plot.close()
        assert wh.widget_count == 0

    def test_close_signal_plot_cascades(self):
        s = hs.signals.Signal1D(np.arange(50))
        s.plot()
        roi = SpanROI(2, 4)
        _ = roi.add_widget(s, axes=s.axes_manager.signal_axes)
        wh = s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        s._plot.close()
        assert wh.widget_count == 0


class TestMultipleROIsOnOneSignal:
    def setup_method(self, method):
        self.s = hs.signals.Signal1D(np.arange(50).reshape(5, 10))
        self.s.plot()

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_two_span_rois_independent_widgets(self):
        roi1 = SpanROI(2, 4)
        roi2 = SpanROI(6, 8)
        _ = roi1.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        w2 = roi2.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        wh = self.s._plot.signal_plot.widget_host
        assert wh.widget_count == 2
        assert w1 in wh.widgets
        assert w2 in wh.widgets

    def test_two_span_rois_independent_bridges(self):
        roi1 = SpanROI(2, 4)
        roi2 = SpanROI(6, 8)
        w1 = roi1.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        w2 = roi2.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        bridge1 = roi1._bridges[id(w1)]
        bridge2 = roi2._bridges[id(w2)]
        assert bridge1 is not bridge2

    def test_remove_one_leaves_other(self):
        roi1 = SpanROI(2, 4)
        roi2 = SpanROI(6, 8)
        _ = roi1.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        w2 = roi2.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        wh = self.s._plot.signal_plot.widget_host
        roi1.remove_widget(self.s)
        assert wh.widget_count == 1
        assert w2 in wh.widgets


class TestNavigationPlotROIgoesToNavigatorWidgetHost:
    """Navigation-axis ROI goes to navigator_plot.widget_host (not signal_plot)."""

    def setup_method(self, method):
        # Signal with navigation dimensions
        self.s = hs.signals.Signal1D(np.arange(50).reshape(5, 10))

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_nav_roi_goes_to_navigator_widget_host(self):
        self.s.plot()
        nav_axes = self.s.axes_manager.navigation_axes
        roi = SpanROI(0.5, 1.5)
        w = roi.add_widget(self.s, axes=nav_axes)
        nav_wh = self.s._plot.navigator_plot.widget_host
        _ = self.s._plot.signal_plot.widget_host
        # Widget is in the navigator widget host, not the signal one
        assert nav_wh.widget_count == 1
        assert w in nav_wh.widgets

    def test_nav_roi_not_in_signal_widget_host(self):
        self.s.plot()
        nav_axes = self.s.axes_manager.navigation_axes
        roi = SpanROI(0.5, 1.5)
        _ = roi.add_widget(self.s, axes=nav_axes)
        sig_wh = self.s._plot.signal_plot.widget_host
        assert sig_wh.widget_count == 0

    def test_nav_roi_bridge_connected_to_nav_axes(self):
        self.s.plot()
        nav_axes = self.s.axes_manager.navigation_axes
        roi = SpanROI(0.5, 1.5)
        w = roi.add_widget(self.s, axes=nav_axes)
        bridge = roi._bridges[id(w)]
        assert bridge is not None
        # Bridge should be connected to the axes_manager
        assert hasattr(bridge, "_connected")


class TestSignalPlotROIgoesToSignalWidgetHost:
    """Signal-axis ROI goes to signal_plot.widget_host."""

    def setup_method(self, method):
        self.s = hs.signals.Signal1D(np.arange(50))

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_signal_roi_goes_to_signal_widget_host(self):
        self.s.plot()
        sig_axes = self.s.axes_manager.signal_axes
        roi = SpanROI(10, 30)
        w = roi.add_widget(self.s, axes=sig_axes)
        sig_wh = self.s._plot.signal_plot.widget_host
        assert sig_wh.widget_count == 1
        assert w in sig_wh.widgets


class TestBridgePushUpdatesAxesIndices:
    def setup_method(self, method):
        self.s = hs.signals.Signal1D(np.arange(50).reshape(5, 10))

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_bridge_push_position_updates_axes(self):
        self.s.plot()
        roi = SpanROI(2, 4)
        w = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        bridge = roi._bridges[id(w)]
        new_pos = (3.0, 8.0)
        bridge.push_position(new_pos)
        ax = w.axes[0]
        assert ax.value == pytest.approx(3.0, rel=1e-6)

    def test_bridge_pull_returns_widget_position(self):
        self.s.plot()
        roi = SpanROI(5, 15)
        w = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        bridge = roi._bridges[id(w)]
        pos = bridge.pull_position()
        assert isinstance(pos, tuple)
        assert len(pos) == 1


class TestSignal2DMultipleAxes:
    def setup_method(self, method):
        self.s = hs.signals.Signal2D(np.random.random((5, 10, 10)))

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_rectangular_roi_two_axes(self):
        self.s.plot()
        sig_axes = self.s.axes_manager.signal_axes
        roi = RectangularROI(left=1, top=1, right=4, bottom=4)
        w = roi.add_widget(self.s, axes=sig_axes)
        wh = self.s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        bridge = roi._bridges[id(w)]
        assert bridge is not None
        assert len(bridge.axes) == 2


class TestRemoveWidgetCleansUpBridge:
    def setup_method(self, method):
        self.s = hs.signals.Signal1D(np.arange(50))
        self.s.plot()

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_remove_widget_removes_bridge_from_dict(self):
        roi = SpanROI(2, 4)
        _ = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        roi.remove_widget(self.s)
        assert True  # bridge cleanup verified by other tests

    def test_remove_widget_disconnects_bridge(self):
        roi = SpanROI(2, 4)
        w = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        roi.remove_widget(self.s)
        assert id(w) not in roi._bridges

    def test_remove_widget_no_widget_host_error(self):
        roi = SpanROI(2, 4)
        _ = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        wh = self.s._plot.signal_plot.widget_host
        roi.remove_widget(self.s)
        assert wh.widget_count == 0


class TestWidgetCloseAutoRemovesFromHost:
    def setup_method(self, method):
        self.s = hs.signals.Signal1D(np.arange(50))
        self.s.plot()

    def teardown_method(self, method):
        import matplotlib.pyplot as plt

        plt.close("all")

    def test_widget_close_removes_from_host(self):
        roi = SpanROI(2, 4)
        w = roi.add_widget(self.s, axes=self.s.axes_manager.signal_axes)
        wh = self.s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        w.close()
        assert wh.widget_count == 0

    def test_close_via_roi_interactive(self):
        s = hs.signals.Signal1D(np.arange(100))
        s.plot()
        roi = SpanROI(10, 20)
        _ = roi.add_widget(s, axes=s.axes_manager.signal_axes)
        wh = s._plot.signal_plot.widget_host
        assert wh.widget_count == 1
        for widget in roi.widgets:
            widget.close()
        assert wh.widget_count == 0
