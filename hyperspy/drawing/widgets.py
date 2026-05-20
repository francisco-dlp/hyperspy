"""Compatibility shim for widget exports now provided by hyperspy_widgets."""

from hyperspy_widgets._widgets.circle import CircleWidget
from hyperspy_widgets._widgets.horizontal_line import HorizontalLineWidget
from hyperspy_widgets._widgets.label import LabelWidget
from hyperspy_widgets._widgets.line2d import Line2DWidget
from hyperspy_widgets._widgets.polygon import PolygonWidget
from hyperspy_widgets._widgets.range import RangeWidget
from hyperspy_widgets._widgets.rectangles import RectangleWidget, SquareWidget
from hyperspy_widgets._widgets.scalebar import ScaleBar
from hyperspy_widgets._widgets.vertical_line import VerticalLineWidget
from hyperspy_widgets.widget import (
    DraggableWidgetBase,
    ResizableDraggableWidgetBase,
    ResizersMixin,
    Widget1DBase,
    Widget2DBase,
    WidgetBase,
)

__all__ = [
    "WidgetBase",
    "DraggableWidgetBase",
    "ResizableDraggableWidgetBase",
    "Widget2DBase",
    "Widget1DBase",
    "ResizersMixin",
    "HorizontalLineWidget",
    "VerticalLineWidget",
    "LabelWidget",
    "CircleWidget",
    "ScaleBar",
    "RectangleWidget",
    "SquareWidget",
    "RangeWidget",
    "Line2DWidget",
    "PolygonWidget",
]
