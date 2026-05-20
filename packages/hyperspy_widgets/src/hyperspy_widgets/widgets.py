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

"""Interactive widgets that can be added to :class:`~.api.signals.BaseSignal` plots."""

from ._widgets.circle import CircleWidget
from ._widgets.horizontal_line import HorizontalLineWidget
from ._widgets.label import LabelWidget
from ._widgets.line2d import Line2DWidget
from ._widgets.polygon import PolygonWidget
from ._widgets.range import RangeWidget
from ._widgets.rectangles import RectangleWidget, SquareWidget
from ._widgets.scalebar import ScaleBar
from ._widgets.vertical_line import VerticalLineWidget
from .widget import (
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
