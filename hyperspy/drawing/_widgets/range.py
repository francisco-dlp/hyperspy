"""Compatibility shim for RangeWidget from hyperspy_widgets."""

from hyperspy_widgets._widgets.range import RangeWidget
from matplotlib.widgets import SpanSelector

__all__ = ["RangeWidget", "SpanSelector"]
