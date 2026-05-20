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

import numpy as np
import pytest

import hyperspy.api as hs
from hyperspy.misc.test_utils import mock_event
from hyperspy.signals import Signal1D, Signal2D


class TestSquareWidget:
    @pytest.mark.parametrize("button", ("right-click", "left-click"))
    def test_jump_click(self, button):
        im = Signal2D(np.arange(10 * 10 * 10 * 10).reshape((10, 10, 10, 10)))
        im.axes_manager[0].scale = 0.1
        im.axes_manager[1].scale = 5
        im.plot()

        jump = mock_event(
            im._plot.navigator_plot.figure,
            im._plot.navigator_plot.figure.canvas,
            key="shift",
            button=button,
            xdata=0.5,
            ydata=10,
        )
        im._plot.pointer._onjumpclick(event=jump)
        current_index = [el.index for el in im.axes_manager.navigation_axes]
        assert current_index == [5, 2]

    def test_jump_click_single_trigger(self):
        im = Signal2D(np.arange(10 * 10 * 10 * 10).reshape((10, 10, 10, 10)))
        im.axes_manager[0].scale = 0.1
        im.axes_manager[1].scale = 5
        im.plot()

        def count_calls(obj):
            count_calls.counter += 1

        count_calls.counter = 0

        im.axes_manager.events.indices_changed.connect(count_calls)

        jump = mock_event(
            im._plot.navigator_plot.figure,
            im._plot.navigator_plot.figure.canvas,
            key="shift",
            button="left-click",
            xdata=0.5,
            ydata=10,
        )
        im._plot.pointer._onjumpclick(event=jump)
        assert count_calls.counter == 1
        current_index = [el.index for el in im.axes_manager.navigation_axes]
        assert current_index == [5, 2]

    def test_jump_click_1d(self):
        im = Signal1D(np.arange(10 * 10).reshape((10, 10)))
        im.axes_manager[0].scale = 0.1
        im.plot()
        jump = mock_event(
            im._plot.navigator_plot.figure,
            im._plot.navigator_plot.figure.canvas,
            key="shift",
            button="left-click",
            xdata=1,
            ydata=0.2,
        )
        im._plot.pointer._onjumpclick(event=jump)
        current_index = [el.index for el in im.axes_manager.navigation_axes]
        assert current_index == [2]

    def test_jump_click_1d_vertical(self):
        im = Signal2D(np.arange(10 * 10 * 10).reshape((10, 10, 10)))
        im.axes_manager[0].scale = 0.1
        im.plot()
        jump = mock_event(
            im._plot.navigator_plot.figure,
            im._plot.navigator_plot.figure.canvas,
            key="shift",
            button="left-click",
            xdata=0.2,
        )
        im._plot.pointer._onjumpclick(event=jump)
        current_index = [el.index for el in im.axes_manager.navigation_axes]
        assert current_index == [2]

    def test_jump_click_out_of_bounds(self):
        im = Signal2D(np.arange(10 * 10 * 10 * 10).reshape((10, 10, 10, 10)))
        im.axes_manager[0].scale = 0.1
        im.axes_manager[1].scale = 5
        im.plot()

        jump = mock_event(
            im._plot.navigator_plot.figure,
            im._plot.navigator_plot.figure.canvas,
            key="shift",
            button="left-click",
            xdata=-5,
            ydata=100,
        )
        im._plot.pointer._onjumpclick(event=jump)
        current_index = [el.index for el in im.axes_manager.navigation_axes]
        assert current_index == [0, 9]

    def test_drag_continuous_update(self):
        im = Signal2D(np.arange(10 * 10 * 10 * 10).reshape((10, 10, 10, 10)))
        im.axes_manager[0].scale = 1
        im.axes_manager[1].scale = 1
        im.plot()

        def count_calls(obj):
            count_calls.counter += 1

        count_calls.counter = 0
        im.axes_manager.events.indices_changed.connect(count_calls)

        widget = im._plot.pointer
        pick = mock_event(
            im._plot.navigator_plot.figure,
            im._plot.navigator_plot.figure.canvas,
            key=None,
            button="left-click",
            xdata=0.5,
            ydata=0.5,
            artist=widget.patch[0],
        )
        widget.onpick(pick)
        assert widget.picked
        drag_events = []
        for i in np.linspace(0.5, 5, 40):
            drag = mock_event(
                im._plot.navigator_plot.figure,
                im._plot.navigator_plot.figure.canvas,
                key=None,
                button="left-click",
                xdata=i,
                ydata=0.5,
                artist=widget.patch[0],
            )
            drag_events.append(drag)
        for d in drag_events:
            widget._onmousemove(d)
        assert count_calls.counter == 5
        assert im.axes_manager.navigation_axes[0].index == 5
        assert im.axes_manager.navigation_axes[1].index == 0

    def test_drag_continuous_update1d(self):
        im = Signal2D(np.arange(10 * 10 * 10).reshape((10, 10, 10)))
        im.axes_manager[0].scale = 1
        im.plot()

        def count_calls(obj):
            count_calls.counter += 1

        count_calls.counter = 0
        im.axes_manager.events.indices_changed.connect(count_calls)

        widget = im._plot.pointer
        pick = mock_event(
            im._plot.navigator_plot.figure,
            im._plot.navigator_plot.figure.canvas,
            key=None,
            button="left-click",
            xdata=0.5,
            ydata=0.5,
            artist=widget.patch[0],
        )
        widget.onpick(pick)
        assert widget.picked
        drag_events = []
        for i in np.linspace(0.5, 5, 40):
            drag = mock_event(
                im._plot.navigator_plot.figure,
                im._plot.navigator_plot.figure.canvas,
                key=None,
                button="left-click",
                xdata=i,
                ydata=0.5,
                artist=widget.patch[0],
            )
            drag_events.append(drag)
        for d in drag_events:
            widget._onmousemove(d)
        assert count_calls.counter == 5
        assert im.axes_manager.navigation_axes[0].index == 5

    def test_drag_continuous_update1d_no_change(self):
        im = Signal2D(np.arange(10 * 10 * 10).reshape((10, 10, 10)))
        im.axes_manager[0].scale = 1
        im.plot()

        def count_calls(obj):
            count_calls.counter += 1

        count_calls.counter = 0
        im.axes_manager.events.indices_changed.connect(count_calls)

        widget = im._plot.pointer
        pick = mock_event(
            im._plot.navigator_plot.figure,
            im._plot.navigator_plot.figure.canvas,
            key=None,
            button="left-click",
            xdata=0.5,
            ydata=0.5,
            artist=widget.patch[0],
        )
        widget.onpick(pick)
        assert widget.picked
        drag_events = []
        for i, j in zip(np.linspace(0.5, 5, 40), np.linspace(0.0, 0.49, 40)):
            drag = mock_event(
                im._plot.navigator_plot.figure,
                im._plot.navigator_plot.figure.canvas,
                key=None,
                button="left-click",
                xdata=j,
                ydata=i,
                artist=widget.patch[0],
            )
            drag_events.append(drag)
        for d in drag_events:
            widget._onmousemove(d)
        assert count_calls.counter == 0
        assert im.axes_manager.navigation_axes[0].index == 0


def test_widgets_non_uniform_axis():
    s = hs.data.luminescence_signal(uniform=False).isig[10:20]
    roi = hs.roi.SpanROI()
    s.plot()
    roi.add_widget(s)
    np.testing.assert_allclose(roi.left, 1.61375935)
    np.testing.assert_allclose(roi.right, 1.61887959)

    roi2 = hs.roi.SpanROI()
    with pytest.raises(ValueError):
        roi2.add_widget(s, snap=True)

    w = list(roi.widgets)[0]
    with pytest.raises(ValueError):
        w.snap_size = True
