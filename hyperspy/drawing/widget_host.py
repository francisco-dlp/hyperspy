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

from hyperspy.events import Event, Events


class WidgetHost:
    """Manages widgets on one matplotlib Axes. Owned by figure classes."""

    def __init__(self):
        self._widgets = set()
        self._selected = None
        self.events = Events()
        self.events.widget_added = Event(
            """
            Event that triggers when a widget is added to the host.

            Parameters
            ----------
            widget : WidgetBase
                The widget that was added.
            """,
            arguments=["widget"],
        )
        self.events.widget_removed = Event(
            """
            Event that triggers when a widget is removed from the host.

            Parameters
            ----------
            widget : WidgetBase
                The widget that was removed.
            """,
            arguments=["widget"],
        )
        self.events.selection_changed = Event(
            """
            Event that triggers when the selected widget changes.

            Parameters
            ----------
            old_widget : WidgetBase or None
                The previously selected widget, or None.
            new_widget : WidgetBase or None
                The newly selected widget, or None.
            """,
            arguments=["old_widget", "new_widget"],
        )

    @property
    def widgets(self):
        """Return an immutable frozenset of registered widgets."""
        return frozenset(self._widgets)

    @property
    def selected(self):
        """Return the currently selected widget, or None."""
        return self._selected

    @property
    def widget_count(self):
        """Return the number of registered widgets."""
        return len(self._widgets)

    def add(self, widget):
        """Register a widget. Connect to its events.closed for auto-removal. Idempotent."""
        if widget in self._widgets:
            return
        self._widgets.add(widget)
        widget.events.closed.connect(self._on_widget_closed, {"obj": "obj"})
        self.events.widget_added.trigger(widget=widget)

    def remove(self, widget):
        """Deregister a widget. Disconnect from its events. No-op if not registered."""
        if widget not in self._widgets:
            return
        widget.events.closed.disconnect(self._on_widget_closed)
        self._widgets.discard(widget)
        if self._selected is widget:
            self._selected = None
        self.events.widget_removed.trigger(widget=widget)

    def select(self, widget):
        """Set a widget as selected. Trigger selection_changed if different."""
        if widget not in self._widgets:
            raise ValueError("Cannot select unregistered widget")
        if self._selected is widget:
            return
        old = self._selected
        self._selected = widget
        # Visual feedback: call widget's own select method
        widget.select()
        self.events.selection_changed.trigger(old_widget=old, new_widget=widget)

    def clear(self):
        """Remove all widgets."""
        for w in list(self._widgets):
            self.remove(w)

    def _on_widget_closed(self, obj):
        """Auto-remove widget when it closes. Same pattern as BlittedFigure.ax_markers."""
        self.remove(obj)
