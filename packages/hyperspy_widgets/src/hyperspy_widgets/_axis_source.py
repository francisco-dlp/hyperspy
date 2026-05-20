"""Package-owned axis-source helpers for widget positioning and defaults."""


class AxisSourceBinding:
    """Adapter for optional external axis providers used by widgets."""

    def __init__(self, axis_source=None):
        self.source = axis_source

    def _indices_event(self):
        if self.source is None:
            return None
        events = getattr(self.source, "events", None)
        return None if events is None else getattr(events, "indices_changed", None)

    def default_axes(self, dimensions):
        if self.source is None:
            return []

        navigation_dimension = getattr(self.source, "navigation_dimension", 0)
        signal_dimension = getattr(self.source, "signal_dimension", 0)
        navigation_axes = list(getattr(self.source, "navigation_axes", ()))
        signal_axes = list(getattr(self.source, "signal_axes", ()))
        shape = tuple(getattr(self.source, "shape", ()))

        if dimensions == 1:
            if navigation_dimension > 0:
                return navigation_axes[:1]
            return signal_axes[:1]

        if navigation_dimension >= dimensions:
            return navigation_axes[:dimensions]
        if signal_dimension >= dimensions:
            return signal_axes[:dimensions]
        if len(shape) >= dimensions:
            return (signal_axes + navigation_axes)[:dimensions]

        raise ValueError(f"Widget needs at least {dimensions} axes.")

    def connect(self, callback):
        event = self._indices_event()
        if event is not None:
            event.connect(callback, {"obj": "axis_source"})

    def disconnect(self, callback):
        event = self._indices_event()
        if event is not None:
            event.disconnect(callback)

    def pull_position(self, axes):
        return [axis.value for axis in axes]

    def push_position(self, axes, position, callback=None):
        event = self._indices_event()
        if event is None:
            return

        navigation_axes = list(getattr(self.source, "navigation_axes", ()))
        if (
            navigation_axes
            and list(axes) == navigation_axes
            and hasattr(self.source, "coordinates")
        ):
            coordinates = tuple(position)
            if getattr(self.source, "coordinates", None) != coordinates:
                self.source.coordinates = coordinates
            return

        suppress_callback = getattr(event, "suppress_callback", None)
        if callback is not None and suppress_callback is not None:
            with suppress_callback(callback):
                for axis, value in zip(axes, position):
                    axis.value = value
        else:
            for axis, value in zip(axes, position):
                axis.value = value
        event.trigger(obj=self.source)


def axis_step(axis):
    """Return the local axis step for uniform or non-uniform axes."""

    if axis.size <= 1:
        return getattr(axis, "scale", 1.0)
    if axis.index >= axis.size - 1:
        return axis.index2value(axis.index) - axis.index2value(axis.index - 1)
    return axis.index2value(axis.index + 1) - axis.index2value(axis.index)


def index_position_from_axes(axes, position):
    return tuple(axis.value2index(value) for axis, value in zip(axes, position))


def position_from_index_values(axes, values):
    return [axis.index2value(value) for axis, value in zip(axes, values)]
