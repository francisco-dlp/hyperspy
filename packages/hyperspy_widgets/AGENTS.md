<!-- Parent: ../../AGENTS.md -->
<!-- Generated: 2026-05-22 | Updated: 2026-05-22 -->

# hyperspy_widgets

## Purpose
Standalone interactive matplotlib widget core extracted from `hyperspy/drawing/widget.py` and `hyperspy/drawing/_widgets/`. This package owns pure widget primitives (drag, resize, selection, position sync) and concrete widget implementations (lines, rectangles, circles, polygons, scalebar, labels, ranges). It must NOT depend on HyperSpy domain objects (signals, models, ROIs, explorers).

## Key Files

| File | Description |
|------|-------------|
| `widget.py` | `WidgetBase` — base class for all interactive matplotlib widgets (patch management, events, axes binding) |
| `widget.py` | `DraggableWidgetBase` — adds drag-to-move interaction |
| `widget.py` | `ResizableDraggableWidgetBase` — adds resize handles and step-snapping on top of drag |
| `widget.py` | `Widget1DBase` — base for 1D widgets (position on one axis) |
| `widget.py` | `Widget2DBase` — base for 2D widgets (position on two axes) |
| `widgets.py` | Public re-export surface — all concrete widget classes and base classes |
| `_axis_source.py` | `AxisSourceBinding` — adapter for optional external axis providers (connect/disconnect, push/pull position) |
| `_axis_source.py` | Free helpers: `axis_step()`, `index_position_from_axes()`, `position_from_index_values()` |
| `_defaults.py` | Package-local `Preferences` (`Plot.pick_tolerance`) — no dependency on HyperSpy defaults |
| `_math.py` | `closest_nice_number()` — numeric helper used by `ScaleBar` |
| `_utils.py` | `on_figure_window_close()`, `picker_kwargs()` — minimal matplotlib helpers |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `_widgets/` | Concrete widget implementations (see below) |
| `tests/` | Package-local test suite |
| `docs/` | Sphinx documentation for the standalone package |

## _widgets/ — Concrete Widgets

| File | Widget | Bases |
|------|--------|-------|
| `vertical_line.py` | `VerticalLineWidget` | `DraggableWidgetBase` |
| `horizontal_line.py` | `HorizontalLineWidget` | `DraggableWidgetBase` |
| `line2d.py` | `Line2DWidget` | `ResizableDraggableWidgetBase` |
| `range.py` | `RangeWidget` | `ResizableDraggableWidgetBase` |
| `rectangles.py` | `RectangleWidget` | `ResizableDraggableWidgetBase`, `Widget2DBase` |
| `rectangles.py` | `SquareWidget` | `RectangleWidget` |
| `circle.py` | `CircleWidget` | `ResizableDraggableWidgetBase`, `Widget2DBase` |
| `polygon.py` | `PolygonWidget` | `ResizableDraggableWidgetBase`, `Widget2DBase` |
| `label.py` | `LabelWidget` | `WidgetBase` |
| `scalebar.py` | `ScaleBar` | Standalone (not a `WidgetBase` subclass) — matplotlib scale annotation |

## For AI Agents

### Critical Concept: Package Boundary

This package is a **staged extraction** — it currently lives in the HyperSpy monorepo (`packages/hyperspy_widgets/`) but must operate as an independent package. Key rules:

1. **No HyperSpy imports** — the package must not import from `hyperspy.*` at runtime. All integration stays in the main HyperSpy package.
2. **`_axis_source.py` is the bridge point** — it accepts optional axis providers without importing `AxesManager`. HyperSpy's `WidgetAxisBridge` (in `hyperspy/drawing/widget_bridge.py`) is the HyperSpy-side glue that connects `AxesManager` to widgets.
3. **`ScaleBar` is special** — it is not a `WidgetBase` subclass but lives in `_widgets/` because it is pure matplotlib infrastructure with no HyperSpy coupling.
4. **Events come from `hyperspy_events`** — the package imports `Event` and `Events` from `hyperspy_events`, not from HyperSpy internals.

### Working In This Directory

- Widgets create and manage matplotlib patches via `self._patch` (list of Artist objects).
- `WidgetBase._set_axes()` is the hook where subclasses assign their axes; call it in `__init__` after the `super().__init__()`.
- `WidgetBase.connect(ax)` registers all matplotlib event listeners on the given axes.
- `WidgetBase.disconnect(ax)` removes them — always call in cleanup.
- `WidgetBase.set_on()` / `set_off()` toggle visibility; `close()` removes the widget entirely and triggers `events.closed`.
- Position updates flow through `_axis_binding` (an `AxisSourceBinding` instance), not through direct axis manipulation.
- Widgets trigger `events.changed` after internal state updates. Integrators connect to this event.

### Class Hierarchy

```
WidgetBase
├── DraggableWidgetBase (drag to move)
│   ├── ResizableDraggableWidgetBase (adds resize handles, step snap)
│   │   ├── Widget1DBase
│   │   │   ├── Line2DWidget
│   │   │   └── RangeWidget
│   │   └── Widget2DBase
│   │       ├── RectangleWidget
│   │       │   └── SquareWidget
│   │       ├── CircleWidget
│   │       └── PolygonWidget
│   ├── VerticalLineWidget
│   └── HorizontalLineWidget
└── LabelWidget

Standalone: ScaleBar
```

### Adding a New Widget

1. Create the file in `_widgets/`.
2. Import and re-export in `_widgets/__init__.py`.
3. Add to `widgets.py` public surface and `__all__`.
4. Add tests in `tests/` using the `FakeAxis` / `FakeAxisSource` helpers from `_test_support.py`.

### Testing Requirements

```bash
pytest packages/hyperspy_widgets/tests/
```

- Use `_test_support.FakeAxis` and `_test_support.FakeAxisSource` instead of real HyperSpy axes.
- Use `matplotlib.use('Agg')` or the `mpl_cleanup` fixture for non-interactive rendering.
- Widget host/bridge tests are at `packages/hyperspy_widgets/tests/test_widget_host.py` and `test_widget_bridge.py`.

### Common Patterns

- Every widget subclass must implement `_set_patch()` — this creates and configures the matplotlib artists.
- Widgets store state in `self._pos` (numpy array) and `self._size` (scalar).
- Use `self._axis_binding.connect(callback)` / `disconnect(callback)` for external axis source events, not raw matplotlib event handling.
- The `events.changed` event signals to integrators that the widget state has changed; `events.closed` signals cleanup.

## Dependencies

### Internal
- `hyperspy_events` — `Event`, `Events` for widget lifecycle events
- `hyperspy/drawing/widget_bridge.py` — HyperSpy-side bridge connecting `AxesManager` to widget positions (not imported by this package; consumed by HyperSpy integrators)

### External
- `matplotlib` — patch creation, event handling, rendering
- `numpy` — position arrays, math utilities

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
