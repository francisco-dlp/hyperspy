from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backend_bases import MouseEvent


class DummyEvent:
    def __init__(self):
        self._callbacks = []
        self._suppressed = set()

    def connect(self, callback, _metadata=None):
        self._callbacks.append(callback)

    def disconnect(self, callback):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def trigger(self, obj=None):
        for callback in list(self._callbacks):
            if callback not in self._suppressed:
                callback(obj)

    @contextmanager
    def suppress_callback(self, callback):
        self._suppressed.add(callback)
        try:
            yield
        finally:
            self._suppressed.discard(callback)


class FakeAxis:
    def __init__(self, size, scale=1.0, offset=0.0, values=None):
        if values is None:
            self.axis = offset + np.arange(size, dtype=float) * scale
            self.scale = float(scale)
            self.is_uniform = True
        else:
            self.axis = np.asarray(values, dtype=float)
            size = len(self.axis)
            if size < 2:
                raise ValueError("FakeAxis needs at least two points.")
            self.scale = float(scale)
            self.is_uniform = False
        self.size = int(size)
        self.index = 0

    @property
    def low_index(self):
        return 0

    @property
    def high_index(self):
        return self.size - 1

    @property
    def low_value(self):
        return float(self.axis[self.low_index])

    @property
    def high_value(self):
        return float(self.axis[self.high_index])

    @property
    def value(self):
        return self.index2value(self.index)

    @value.setter
    def value(self, new_value):
        self.index = self.value2index(new_value)

    def value2index(self, value):
        value = float(value)
        if value < self.low_value or value > self.high_value:
            raise ValueError("Value out of bounds")
        if self.is_uniform:
            return int(round((value - self.low_value) / self.scale))
        return int(np.argmin(np.abs(self.axis - value)))

    def index2value(self, index):
        index = int(index)
        if index < self.low_index or index > self.high_index:
            raise ValueError("Index out of bounds")
        return float(self.axis[index])


class FakeAxisSource:
    def __init__(self, navigation_axes=(), signal_axes=(), shape=None):
        self.navigation_axes = list(navigation_axes)
        self.signal_axes = list(signal_axes)
        self.navigation_dimension = len(self.navigation_axes)
        self.signal_dimension = len(self.signal_axes)
        self.shape = (
            tuple(shape)
            if shape is not None
            else tuple(axis.size for axis in [*self.navigation_axes, *self.signal_axes])
        )
        self.events = SimpleNamespace(indices_changed=DummyEvent())


def make_plot_axes(length=50):
    fig, ax = plt.subplots()
    ax.plot(np.arange(length))
    return fig, ax


def make_image_axes(shape=(10, 10)):
    fig, ax = plt.subplots()
    ax.imshow(np.arange(np.prod(shape)).reshape(shape))
    return fig, ax


def make_event(ax, xdata=None, ydata=None, button=1, key=None, artist=None):
    xmid = np.mean(ax.get_xlim())
    ymid = np.mean(ax.get_ylim())
    xdata = xmid if xdata is None else xdata
    ydata = ymid if ydata is None else ydata
    x, y = ax.transData.transform((xdata, ydata))
    return SimpleNamespace(
        inaxes=ax,
        xdata=xdata,
        ydata=ydata,
        x=x,
        y=y,
        button=button,
        key=key,
        artist=artist,
    )


def make_motion_event(ax, xdata, ydata, button=1, key=None):
    x, y = ax.transData.transform((xdata, ydata))
    return MouseEvent(
        "motion_notify_event",
        ax.figure.canvas,
        x,
        y,
        button=button,
        key=key,
    )
