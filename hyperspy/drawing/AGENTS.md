<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-05-19 | Updated: 2026-05-19 -->

# drawing

## Purpose
Matplotlib-based interactive plotting engine. Handles the `signal.plot()` infrastructure, including multi-panel figures, navigator/signal separation, interactive widgets, and the markers system.

## Key Files

| File | Description |
|------|-------------|
| `signal.py` | `SignalFigure` — top-level figure manager for any signal |
| `signal1d.py` | 1D signal panel rendering |
| `image.py` | 2D image panel rendering |
| `figure.py` | `BlittedFigure` — base figure with blit-based animation |
| `mpl_hse.py` | Hyperspy Signal Explorer figure layout |
| `mpl_hie.py` | Hyperspy Image Explorer figure layout |
| `mpl_he.py` | Hyperspy Explorer base |
| `markers.py` | Public markers entry point |
| `widget.py` | Navigator widget base |
| `widgets.py` | Concrete interactive widgets (crosshair, range, etc.) |
| `widget_host.py` | `WidgetHost` — manages widgets on one matplotlib Axes (selection, add/remove/clear, event lifecycle) |
| `widget_bridge.py` | `WidgetAxisBridge` — bidirectional sync between widget position and `AxesManager` axes (snap grid, push/pull) |
| `tiles.py` | Tiled signal display |
| `utils.py` | Plot utility helpers |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `_markers/` | Individual marker type implementations (Arrow, Circle, Line, etc.) |
| `_widgets/` | Low-level interactive widget implementations |

## For AI Agents

### Working In This Directory

- All rendering goes through `signal.plot()` which dispatches to the appropriate figure class based on signal dimension.
- Interactive updates rely on `events.py` — do not poll; connect/disconnect event handlers.
- Use blit (`figure.render_figure()`) for performance-critical animations.
- Markers are composable: each marker type in `_markers/` is independent; they are collected by `markers.py`.
- **Widget decoupling**: `WidgetHost` owns widget lifecycle per Axes; `WidgetAxisBridge` encapsulates all `AxesManager` knowledge. Widgets should never access `AxesManager` directly — use the bridge for position sync and snap grid computation.
- The drawing module depends on the staged `hyperspy_widgets` and `hyperspy_events` packages in `packages/` for widget primitives and event infrastructure.

### Testing Requirements

```bash
pytest hyperspy/tests/drawing/
```

Use `matplotlib.use('Agg')` or the `mpl_cleanup` fixture for non-interactive test rendering.

## Dependencies

### Internal
- `hyperspy/events.py` — reactive event system
- `hyperspy/axes.py` — `AxesManager` drives snap grid and position sync via `WidgetAxisBridge`
- `hyperspy/roi.py` — ROI widgets connect to drawing widgets
- `hyperspy_events` / `hyperspy_widgets` — staged extraction packages (see `packages/`) for event primitives and pure widget core

### External
- `matplotlib` — entire rendering stack

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
