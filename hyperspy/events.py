"""Compatibility shim for events now provided by hyperspy_events."""

from hyperspy_events.events import Event, Events, EventSuppressor  # noqa: F401

__all__ = ["Event", "Events", "EventSuppressor"]
