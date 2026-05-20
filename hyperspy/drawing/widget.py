"""Compatibility shim for widget bases now provided by hyperspy_widgets."""

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
]
