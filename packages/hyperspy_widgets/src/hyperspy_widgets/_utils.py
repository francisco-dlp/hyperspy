"""Minimal matplotlib helpers used by the widget core."""

import matplotlib as mpl
from packaging.version import Version


def on_figure_window_close(figure, function):
    """Connect a close-event callback to a matplotlib figure."""

    def function_wrapper(_event):
        function()

    figure.canvas.mpl_connect("close_event", function_wrapper)


def picker_kwargs(value, kwargs=None):
    if kwargs is None:
        kwargs = {}
    if Version(mpl.__version__) >= Version("3.3.0"):
        kwargs.update({"pickradius": value, "picker": True})
    else:
        kwargs["picker"] = value
    return kwargs
