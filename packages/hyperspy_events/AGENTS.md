<!-- Parent: ../../AGENTS.md -->
<!-- Generated: 2026-05-22 | Updated: 2026-05-22 -->

# hyperspy_events

## Purpose
Standalone, zero-dependency event-driven programming primitives extracted from `hyperspy/events.py`. Provides `Event`, `Events`, and `EventSuppressor` — the same event system used throughout HyperSpy for signal lifecycle, model fitting, component updates, ROI interactions, and drawing callbacks.

## Key Files

| File | Description |
|------|-------------|
| `events.py` | `Event` — single event with `.connect()`, `.disconnect()`, `.trigger()`, `.suppress()`, `.suppress_callback()` |
| `events.py` | `Events` — container for named events; `.suppress()` context manager, event docstring introspection |
| `events.py` | `EventSuppressor` — context manager for suppressing a single callback on an event |

## For AI Agents

### Critical Concept: Zero Internal Dependencies

This module uses only the Python standard library (`inspect`, `re`, `sys`, `collections.abc`, `contextlib`, `functools`). The `pyproject.toml` declares **no runtime dependencies** (`dependencies = []`). This means:

1. Any Python package can depend on `hyperspy_events` without pulling in HyperSpy.
2. The widget package (`hyperspy_widgets`) imports `Event` and `Events` from here, not from HyperSpy internals.
3. `hyperspy/events.py` will become a thin re-export shim importing from `hyperspy_events.events`.

### Working In This Directory

- `Event` is a callable that stores callbacks internally. Creating an event: `e = Event(doc="...", arguments=["obj"])`.
- Callbacks are connected with `event.connect(callback, metadata_dict)`. The metadata dict passes keyword arguments to the callback — use `{"obj": "obj"}` to receive the trigger object as the `obj` kwarg.
- `Events` is a container: assign `Event` instances as attributes (`self.events.changed = Event(...)`), then use `events.suppress()` as a context manager to batch mutations.
- `EventSuppressor` suppresses a single callback on a single event — useful for preventing feedback loops when a callback itself triggers the event it listens to.
- `Event._update_connections()` uses `sys._getframe()` to extract variable names from the caller's stack frame — this is fragile to refactoring but exposed only through `connect(metadata={})`.

### Testing Requirements

```bash
pytest packages/hyperspy_events/tests/
```

Tests import from `hyperspy_events` directly (not from `hyperspy.events`). The test suite covers:
- Event creation, connection, disconnection
- Trigger with and without keyword arguments
- Suppression (single event, `Events` container, `EventSuppressor`)
- Connected function with multiple outputs
- Copy behavior
- Memory management (callback cleanup)

### Common Patterns

```python
# Connect a callback that receives the trigger object:
event.connect(my_handler, {"obj": "obj"})

# Suppress all events in a container during batch operations:
with obj.events.suppress():
    obj.val_a = a
    obj.val_b = b

# Suppress a single callback to prevent feedback loops:
with event.suppress_callback(my_callback):
    event.trigger(obj=obj)
```

## Dependencies

### Internal
- None — this package has zero internal HyperSpy dependencies.

### External
- None — uses only the Python standard library.

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
