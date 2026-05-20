# HyperSpy Widgets Extraction Manifest

This document is the authoritative staged-package boundary for the future `hyperspy-widgets` distribution and `hyperspy_widgets` import package.

It freezes what moves first, what stays in HyperSpy during stabilization, and which historical paths must be preserved for the later fresh-clone `git filter-repo` extraction.

## Boundary contract

1. Move only the pure matplotlib widget core and widget-local helper logic into the staged package first.
2. Keep HyperSpy-specific integration in HyperSpy during stabilization, including ROI synchronization, explorer pointer wiring, model tooling, signal tools, and SAMFire usage.
3. `WidgetAdapter`-style integration remains in HyperSpy during stabilization. If that adapter layer exists as a concrete class, helper, or shim rather than one dedicated file, it is still HyperSpy-owned glue and is not part of the first extraction wave.
4. The future package must not depend at runtime on `hyperspy/roi.py`, `hyperspy/drawing/mpl_he.py`, `hyperspy/drawing/mpl_hse.py`, `hyperspy/models/model1d.py`, `hyperspy/signal_tools/_line.py`, or `hyperspy/samfire.py`.
5. Widget-local utility behavior currently borrowed from broader HyperSpy modules must be copied or replaced with package-owned code rather than imported from HyperSpy internals.
6. ROI integration tests are explicitly out of package scope for this boundary freeze. They remain HyperSpy-owned during stabilization.

## Move now into the future package

These are the legacy HyperSpy paths whose widget-core behavior becomes package-owned in the staged extraction.

| Legacy path | Future staged-package destination | Why it moves now |
| --- | --- | --- |
| `hyperspy/drawing/widget.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/widget.py` | Base widget abstractions (`WidgetBase`, draggable/resizable bases, resizer mixin) are the package core. |
| `hyperspy/drawing/widgets.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/widgets.py` | Public widget export surface for the package. |
| `hyperspy/drawing/_widgets/__init__.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/__init__.py` | Namespace package marker for concrete widgets. |
| `hyperspy/drawing/_widgets/vertical_line.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/vertical_line.py` | Pure matplotlib widget implementation. |
| `hyperspy/drawing/_widgets/horizontal_line.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/horizontal_line.py` | Pure matplotlib widget implementation. |
| `hyperspy/drawing/_widgets/label.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/label.py` | Pure widget for labeling/model-position overlays. |
| `hyperspy/drawing/_widgets/line2d.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/line2d.py` | Pure widget geometry/manipulation logic. |
| `hyperspy/drawing/_widgets/range.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/range.py` | Span-selector widget logic belongs to widget core. |
| `hyperspy/drawing/_widgets/rectangles.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/rectangles.py` | Rectangle and square widget implementations are package-owned. |
| `hyperspy/drawing/_widgets/circle.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/circle.py` | Circle/annulus widget implementation is package-owned. |
| `hyperspy/drawing/_widgets/polygon.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/polygon.py` | Polygon drawing/manipulation logic is package-owned. |
| `hyperspy/drawing/_widgets/scalebar.py` | `packages/hyperspy_widgets/src/hyperspy_widgets/_widgets/scalebar.py` | `ScaleBar` is widget-local matplotlib infrastructure even though it is not a `WidgetBase` subclass. |

## Keep in HyperSpy during stabilization

These files remain HyperSpy-owned because they adapt widgets to HyperSpy signals, models, ROIs, explorers, or workflows.

| Path retained in HyperSpy | Ownership reason |
| --- | --- |
| `hyperspy/roi.py` | Owns ROI classes, ROI-to-widget synchronization, ROI slicing behavior, and widget selection logic bound to HyperSpy signals. |
| `hyperspy/drawing/mpl_he.py` | Owns explorer pointer assignment, plot lifecycle, and navigator/signal figure coupling. |
| `hyperspy/drawing/mpl_hse.py` | Owns right-pointer explorer behavior and signal-explorer-specific widget wiring. |
| `hyperspy/models/model1d.py` | Owns model-position adjusters and model-specific `VerticalLineWidget`/`LabelWidget` usage. |
| `hyperspy/signal_tools/_line.py` | Owns signal-tool wrappers that attach widget classes to HyperSpy `Signal1D` and `Signal2D` objects. |
| `hyperspy/samfire.py` | Owns SAMFire-specific square-widget guidance and navigation synchronization. |
| Any concrete `WidgetAdapter` implementation or equivalent HyperSpy-side glue | Remains in HyperSpy even if it later lives in a differently named file. The adapter boundary is deliberately not moved in the first extraction stage. |

### Unambiguous ownership rule

The staged package owns widget primitives and widget-local helpers only.

HyperSpy retains all object adaptation, including:

- ROI ↔ widget synchronization and ROI slicing
- signal explorer pointer creation and navigator linkage
- model-position widgets and labels tied to `Model1D`
- signal-tool wrappers that create widgets for plotted signals
- SAMFire and any other workflow-specific widget orchestration
- `WidgetAdapter`-style glue between package widgets and HyperSpy domain objects

## Copy or replace as package-local utility logic

The future package must own replacements for these narrow helper dependencies.

| Current source | Package action | Notes |
| --- | --- | --- |
| `hyperspy/drawing/utils.py::picker_kwargs` | Copy or replace in a package-local matplotlib helper module | Used by `VerticalLineWidget`, `HorizontalLineWidget`, and `Line2DWidget`. |
| `hyperspy/drawing/utils.py::on_figure_window_close` | Copy or replace in a package-local matplotlib helper module | Used by `WidgetBase.connect()` to manage widget cleanup on figure close. |
| `hyperspy/misc/math_tools.py::closest_nice_number` | Copy or replace in a package-local numeric helper module | Used by `ScaleBar` to derive nice display lengths. |
| `hyperspy/events.py` event primitives | Reimplement or extract a minimal package-owned equivalent | `WidgetBase` currently depends on `Event` and `Events`, but the package must not depend on the whole HyperSpy event module at runtime. |
| `hyperspy/defaults_parser.py` preferences access | Replace with package-owned defaults/config surface | Widget core currently depends on `preferences.Plot.pick_tolerance`; the package needs its own small configuration contract instead of importing HyperSpy preferences. |

### Important helper-dependency note

`hyperspy/events.py` and `hyperspy/defaults_parser.py` are dependency sources, not move-now file owners. They stay in HyperSpy. Only the narrow widget-facing behavior should be recreated inside the package.

## Authoritative legacy path set for later `git filter-repo`

When the standalone extraction happens from a fresh clone, preserve contributor history for the widget package by including the staged package subtree plus these legacy HyperSpy paths.

### Include set

```text
packages/hyperspy_widgets/**
hyperspy/drawing/widget.py
hyperspy/drawing/widgets.py
hyperspy/drawing/_widgets/__init__.py
hyperspy/drawing/_widgets/vertical_line.py
hyperspy/drawing/_widgets/horizontal_line.py
hyperspy/drawing/_widgets/label.py
hyperspy/drawing/_widgets/line2d.py
hyperspy/drawing/_widgets/range.py
hyperspy/drawing/_widgets/rectangles.py
hyperspy/drawing/_widgets/circle.py
hyperspy/drawing/_widgets/polygon.py
hyperspy/drawing/_widgets/scalebar.py
hyperspy/drawing/utils.py
hyperspy/misc/math_tools.py
```

### Why `hyperspy/drawing/utils.py` and `hyperspy/misc/math_tools.py` are included

They preserve authorship for the exact helper logic that will be copied into the package:

- `picker_kwargs`
- `on_figure_window_close`
- `closest_nice_number`

Those files are broader than the widget package, so the later extraction/bootstrap step must trim or rewrite the extracted result into package-local utility modules. The history still needs to be preserved now.

### Explicit non-include set for the standalone widget package

Do **not** include these HyperSpy-retained integration files in the standalone widget extraction path set unless a later architectural decision explicitly broadens scope:

- `hyperspy/roi.py`
- `hyperspy/drawing/mpl_he.py`
- `hyperspy/drawing/mpl_hse.py`
- `hyperspy/models/model1d.py`
- `hyperspy/signal_tools/_line.py`
- `hyperspy/samfire.py`
- `hyperspy/events.py`
- `hyperspy/defaults_parser.py`

## Stabilization expectations

- HyperSpy will continue to expose compatibility import paths under `hyperspy.drawing.*` after the core move.
- The package public surface should be the widget classes and helpers only; HyperSpy integration must import from that stable public boundary rather than from private package internals.
- `WidgetAdapter` remains the conceptual marker for the retained HyperSpy integration layer throughout stabilization, even if the glue is spread across shims, helpers, or wrapper classes.
