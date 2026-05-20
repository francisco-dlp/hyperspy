# HyperSpy Events Cutover Checklist

This checklist governs the transition from the in-repo staged package to the standalone `hyperspy-events` distribution consumed as an external dependency.

## When to cut over

Cut over only after **all** of the following are true:

- [ ] The standalone `hyperspy-events` package is published to PyPI (or the target index) with a stable version.
- [ ] The published package passes its own test suite on the supported Python versions.
- [ ] A HyperSpy branch that depends on the published package passes the full HyperSpy test suite.
- [ ] HyperSpy maintainers have agreed on a minimum version pin for `hyperspy-events`.
- [ ] The release notes for the upcoming HyperSpy release document the new external dependency.

## Cutover steps

### 1. Update HyperSpy packaging

- [ ] Add `hyperspy-events >= MIN_VERSION` to `hyperspy` runtime dependencies in `pyproject.toml`.
- [ ] Remove the staged package directory `packages/hyperspy_events/` from the HyperSpy repository.
- [ ] Remove any CI jobs that specifically test the staged package in isolation (e.g., `DualInstallSmoke` if it only tested the in-repo package).
- [ ] Update `doc/dev_guide/events_package_boundary.rst` to state that the package is now an external dependency, not an in-repo subtree.

### 2. Update HyperSpy imports

- [ ] Verify that all HyperSpy imports of events classes resolve through the published package.
- [ ] Remove any compatibility shims in `hyperspy/events.py` that re-export staged-package classes. The external dependency should provide these directly.
- [ ] Confirm that the shim at `hyperspy/events.py` correctly imports `Event`, `Events`, and `EventSuppressor` from `hyperspy_events.events` after the staged directory is removed.

### 3. Update HyperSpy integration code

The following HyperSpy-retained integration files must continue to work with the external package. Review each one:

- [ ] `hyperspy/signal.py` - Signal lifecycle events (`data_changed`, `axes_changed`, etc.) still function.
- [ ] `hyperspy/model.py` - Model fitting events (`fitted`, `update_plot`, etc.) still function.
- [ ] `hyperspy/axes.py` - Axis change events and `AxesManager` event wiring still function.
- [ ] `hyperspy/component.py` - Component parameter events and reactive updates still function.
- [ ] `hyperspy/roi.py` - ROI events and interactive ROI-widget synchronization still function.
- [ ] `hyperspy/drawing/mpl_he.py` - Explorer pointer events and navigator/signal figure coupling still function.
- [ ] `hyperspy/drawing/figure.py` - Figure-level event wiring for matplotlib canvas interactions still function.
- [ ] `hyperspy/drawing/signal1d.py` - Signal-plotting event callbacks and line-plot lifecycle events still function.
- [ ] `hyperspy/drawing/markers.py` - Marker event updates tied to plotted annotations still function.
- [ ] `hyperspy/models/model1d.py` - Model-specific event usage for 1D model fitting and plotting updates still function.
- [ ] `hyperspy/samfire.py` - SAMFire-specific event orchestration for adaptive multi-dimensional fitting still function.
- [ ] `hyperspy/signal_tools/_line.py` - Signal-tool event wiring for interactive line-profile and measurement tools still function.

### 4. Update widget package dependency

- [ ] Add `hyperspy-events >= MIN_VERSION` to `packages/hyperspy_widgets/pyproject.toml` runtime dependencies.
- [ ] Delete `packages/hyperspy_widgets/src/hyperspy_widgets/events.py` (the private subset copy).
- [ ] Update `packages/hyperspy_widgets/src/hyperspy_widgets/__init__.py` (or relevant files) to import `Event` and `Events` from `hyperspy_events` instead of the private copy.
- [ ] Verify the widget package tests still pass after switching to the external dependency.

### 5. Update documentation

- [ ] Remove or redirect `packages/hyperspy_events/docs/` references in HyperSpy documentation.
- [ ] Update `doc/dev_guide/events_package_boundary.rst` with final state (external dependency, no in-repo staging).
- [ ] Update the HyperSpy installation instructions to mention `hyperspy-events` as a dependency.
- [ ] Ensure the standalone package docs are published and linked from the HyperSpy website.

### 6. Verify the extraction bootstrap still works

- [ ] Run `tools/extract_hyperspy_events.sh` from a fresh clone and confirm it still produces the expected standalone layout.
- [ ] Confirm `git shortlog -sne` in the extracted clone shows the same author count as before.

### 7. Post-cutover cleanup

- [ ] Archive or remove the `packages/hyperspy_events/` directory from the HyperSpy repository.
- [ ] Remove any Azure Pipelines template references that were specific to the staged-package CI path.
- [ ] Add a changelog entry in `upcoming_changes/` documenting the extraction.
- [ ] Close any open issues or PRs that were blocked waiting for the standalone package.

## Rollback criteria

If the cutover introduces regressions, revert the dependency addition and restore the staged package directory until the issues are resolved in the standalone package.

## Related files

- `packages/hyperspy_events/EXTRACTION_MANIFEST.md` - authoritative include set and boundary contract
- `tools/extract_hyperspy_events.sh` - one-shot extraction bootstrap
- `doc/dev_guide/events_package_boundary.rst` - HyperSpy developer documentation for the boundary
