# HyperSpy Events Extraction Manifest

This document is the authoritative staged-package boundary for the future `hyperspy-events` distribution and `hyperspy_events` import package.

It freezes what moves first, what stays in HyperSpy during stabilization, and which historical paths must be preserved for the later fresh-clone `git filter-repo` extraction.

## Boundary contract

1. Move the entire events module into the staged package first. The module has no internal HyperSpy dependencies and is a clean extraction boundary.
2. Keep all HyperSpy-specific integration in HyperSpy during stabilization, including signal lifecycle events, model events, component events, ROI events, drawing events, and explorer wiring.
3. The future package must not depend at runtime on `hyperspy/signal.py`, `hyperspy/model.py`, `hyperspy/axes.py`, `hyperspy/component.py`, `hyperspy/roi.py`, `hyperspy/drawing/mpl_he.py`, or `hyperspy/samfire.py`.
4. `hyperspy/events.py` becomes a pure re-export shim importing from `hyperspy_events.events`. All 28+ consumer files continue to import through the legacy path without modification.
5. `packages/hyperspy_widgets/src/hyperspy_widgets/events.py` is a ~30% subset copy that will be deleted and replaced with a dependency on `hyperspy_events`.

## Move now into the future package

These are the legacy HyperSpy paths whose event behavior becomes package-owned in the staged extraction.

| Legacy path | Future staged-package destination | Why it moves now |
| --- | --- | --- |
| `hyperspy/events.py` | `packages/hyperspy_events/src/hyperspy_events/events.py` | The entire events module (`Events`, `Event`, `EventSuppressor`) is a self-contained stdlib-only subsystem with zero internal HyperSpy dependencies. |
| `hyperspy/tests/test_events.py` | `packages/hyperspy_events/tests/test_events.py` | Package-local tests for the events subsystem, adapted to import from `hyperspy_events`. |
| `doc/user_guide/events.rst` | `packages/hyperspy_events/docs/events.rst` | Events-specific documentation moves with the package. |

## Keep in HyperSpy during stabilization

These files remain HyperSpy-owned because they consume events for signal lifecycle, model fitting, component updates, ROI interactions, drawing callbacks, and workflow orchestration.

| Path retained in HyperSpy | Ownership reason |
| --- | --- |
| `hyperspy/signal.py` | Owns signal lifecycle events (`data_changed`, `axes_changed`, etc.) and event emission tied to `BaseSignal` mutations. |
| `hyperspy/model.py` | Owns model events (`fitted`, `update_plot`, etc.) tied to `BaseModel` fitting workflow. |
| `hyperspy/axes.py` | Owns axis change events and `AxesManager` event wiring for navigation and signal axis updates. |
| `hyperspy/component.py` | Owns component parameter events and reactive updates tied to `Component` base class. |
| `hyperspy/roi.py` | Owns ROI events and interactive ROI-widget synchronization behavior. |
| `hyperspy/drawing/mpl_he.py` | Owns explorer pointer events and navigator/signal figure coupling through event callbacks. |
| `hyperspy/drawing/figure.py` | Owns figure-level event wiring for matplotlib canvas interactions. |
| `hyperspy/drawing/signal1d.py` | Owns signal-plotting event callbacks and line-plot lifecycle events. |
| `hyperspy/drawing/markers.py` | Owns marker event updates tied to plotted annotations. |
| `hyperspy/models/model1d.py` | Owns model-specific event usage for 1D model fitting and plotting updates. |
| `hyperspy/samfire.py` | Owns SAMFire-specific event orchestration for adaptive multi-dimensional fitting. |
| `hyperspy/signal_tools/_line.py` | Owns signal-tool event wiring for interactive line-profile and measurement tools. |
| Any other HyperSpy file that imports from `hyperspy.events` | Remains in HyperSpy. The shim preserves their import paths during stabilization. |

### Unambiguous ownership rule

The staged package owns event primitives and event-local helpers only.

HyperSpy retains all event consumption and adaptation, including:

- Signal lifecycle events (`data_changed`, `axes_changed`, etc.)
- Model fitting events (`fitted`, `update_plot`, etc.)
- Component parameter events and reactive updates
- ROI event synchronization and slicing behavior
- Drawing callback events and figure lifecycle wiring
- Explorer pointer events and navigator linkage
- SAMFire and any other workflow-specific event orchestration
- Any HyperSpy-side glue between package events and HyperSpy domain objects

## Widget mini-events removal plan

The widget package currently contains a private ~30% subset copy of the events module at `packages/hyperspy_widgets/src/hyperspy_widgets/events.py`. This copy exists only because `hyperspy_events` was not yet a standalone package during the widget extraction.

| Current source | Package action | Notes |
| --- | --- | --- |
| `packages/hyperspy_widgets/src/hyperspy_widgets/events.py` | Delete and replace with dependency on `hyperspy-events` | The widget package will import `Event` and `Events` from `hyperspy_events` instead of its private copy. |
| `packages/hyperspy_widgets/pyproject.toml` | Add `hyperspy-events` as a runtime dependency | Enables the widget package to consume the standalone events package. |

### Important helper-dependency note

`hyperspy/events.py` is a move-now file owner, not a dependency source. The full module moves into the staged package. The HyperSpy shim is a thin re-export, not a copy of logic.

## Authoritative legacy path set for later `git filter-repo`

When the standalone extraction happens from a fresh clone, preserve contributor history for the events package by including the staged package subtree plus these legacy HyperSpy paths.

### Include set

```text
packages/hyperspy_events/**
hyperspy/events.py
hyperspy/tests/test_events.py
doc/user_guide/events.rst
```

### Explicit non-include set for the standalone events package

Do **not** include these HyperSpy-retained integration files in the standalone events extraction path set unless a later architectural decision explicitly broadens scope:

- `hyperspy/signal.py`
- `hyperspy/model.py`
- `hyperspy/axes.py`
- `hyperspy/component.py`
- `hyperspy/roi.py`
- `hyperspy/drawing/mpl_he.py`
- `hyperspy/drawing/figure.py`
- `hyperspy/drawing/signal1d.py`
- `hyperspy/drawing/markers.py`
- `hyperspy/models/model1d.py`
- `hyperspy/samfire.py`
- `hyperspy/signal_tools/_line.py`
- `packages/hyperspy_widgets/src/hyperspy_widgets/events.py`

## Stabilization expectations

- HyperSpy will continue to expose compatibility import paths under `hyperspy.events` after the core move.
- The package public surface should be the event classes and helpers only; HyperSpy integration must import from that stable public boundary rather than from private package internals.
- The shim at `hyperspy/events.py` remains the conceptual marker for the retained HyperSpy compatibility layer throughout stabilization.
- After stabilization, the widget package will consume `hyperspy_events` as a dependency and its private `events.py` copy will be removed.

(End of file)
