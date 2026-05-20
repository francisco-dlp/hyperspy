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

import weakref

import numpy as np


class WidgetAxisBridge:
    """Bidirectional sync: widget position ↔ AxesManager axes.

    All DataAxis knowledge lives HERE — never in widgets.
    Stores a weak reference to the widget to avoid circular references.
    """

    def __init__(self, widget, axes_manager, axes):
        self._widget = weakref.ref(widget) if widget is not None else lambda: None
        self.axes_manager = axes_manager
        self.axes = list(axes)  # list of DataAxis
        self._connected = False
        self._suppress_callback = None

    @property
    def widget(self):
        """Return the widget or None if it has been garbage collected."""
        return self._widget()

    @property
    def snap_grid(self):
        """Compute position snap grid for each axis.

        For uniform axes: arange(low_value, high_value + scale, scale).
        For non-uniform axes: axis.axis values directly.
        Returns a tuple of arrays, one per axis.
        """
        grids = []
        for ax in self.axes:
            if ax.is_uniform:
                step = ax.scale if ax.scale else 1.0
                grids.append(np.arange(ax.low_value, ax.high_value + step, step))
            else:
                grids.append(np.asarray(ax.axis).copy())
        return tuple(grids)

    def pull_position(self):
        """Read current position from axes values."""
        return tuple(ax.value for ax in self.axes)

    def push_position(self, position, suppress=False):
        """Write position to axes.

        For signal axes: sets axis.value individually.
        If suppress=True, suppresses the connected callback to prevent loops.
        """
        converted = []
        for v in position:
            if hasattr(v, "__iter__") and not isinstance(v, str):
                converted.append(float(v[0]))
            else:
                converted.append(float(v))
        position = tuple(converted)
        event = getattr(
            getattr(self.axes_manager, "events", None), "indices_changed", None
        )
        if event is not None and suppress and self._suppress_callback is not None:
            with event.suppress_callback(self._suppress_callback):
                for ax, val in zip(self.axes, position):
                    if ax.low_value <= val <= ax.high_value:
                        ax.value = val
            event.trigger(obj=self.axes_manager)
        else:
            for ax, val in zip(self.axes, position):
                if ax.low_value <= val <= ax.high_value:
                    ax.value = val
            if event is not None:
                event.trigger(obj=self.axes_manager)

    def connect(self, callback):
        """Listen to axes_manager.events.indices_changed → callback."""
        event = getattr(
            getattr(self.axes_manager, "events", None), "indices_changed", None
        )
        if event is not None:
            event.connect(callback, {"obj": "axis_source"})
            self._suppress_callback = callback
            self._connected = True

    def disconnect(self, callback):
        """Stop listening to axes_manager indices_changed events."""
        if not self._connected:
            return
        event = getattr(
            getattr(self.axes_manager, "events", None), "indices_changed", None
        )
        if event is not None:
            event.disconnect(callback)
            self._connected = False
            self._suppress_callback = None
