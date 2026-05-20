# HyperSpy Widgets Cutover Checklist

This checklist governs the transition from the in-repo staged package to the standalone `hyperspy-widgets` distribution consumed as an external dependency.

## When to cut over

Cut over only after **all** of the following are true:

- [ ] The standalone `hyperspy-widgets` package is published to PyPI (or the target index) with a stable version.
- [ ] The published package passes its own test suite on the supported Python versions.
- [ ] A HyperSpy branch that depends on the published package passes the full HyperSpy test suite.
- [ ] HyperSpy maintainers have agreed on a minimum version pin for `hyperspy-widgets`.
- [ ] The release notes for the upcoming HyperSpy release document the new external dependency.

## Cutover steps

### 1. Update HyperSpy packaging

- [ ] Add `hyperspy-widgets >= MIN_VERSION` to `hyperspy` runtime dependencies in `pyproject.toml`.
- [ ] Remove the staged package directory `packages/hyperspy_widgets/` from the HyperSpy repository.
- [ ] Remove any CI jobs that specifically test the staged package in isolation (e.g., `DualInstallSmoke` if it only tested the in-repo package).
- [ ] Update `doc/dev_guide/widget_package_boundary.rst` to state that the package is now an external dependency, not an in-repo subtree.

### 2. Update HyperSpy imports

- [ ] Verify that all HyperSpy imports of widget classes resolve through the published package.
- [ ] Remove any compatibility shims in `hyperspy/drawing/widget.py`, `hyperspy/drawing/widgets.py`, or `hyperspy/drawing/_widgets/` that re-export staged-package classes. The external dependency should provide these directly.
- [ ] Confirm that `hyperspy.drawing._widgets.range` still re-exports `matplotlib.widgets.SpanSelector` if HyperSpy code depends on that name.

### 3. Update HyperSpy integration code

The following HyperSpy-retained integration files must continue to work with the external package. Review each one:

- [ ] `hyperspy/roi.py` - ROI-to-widget synchronization still functions.
- [ ] `hyperspy/drawing/mpl_he.py` - Explorer pointer assignment and plot lifecycle still functions.
- [ ] `hyperspy/drawing/mpl_hse.py` - Right-pointer explorer behavior still functions.
- [ ] `hyperspy/models/model1d.py` - Model-position adjusters still function.
- [ ] `hyperspy/signal_tools/_line.py` - Signal-tool wrappers still function.
- [ ] `hyperspy/samfire.py` - SAMFire-specific widget guidance still functions.

### 4. Update documentation

- [ ] Remove or redirect `packages/hyperspy_widgets/docs/` references in HyperSpy documentation.
- [ ] Update `doc/dev_guide/widget_package_boundary.rst` with final state (external dependency, no in-repo staging).
- [ ] Update the HyperSpy installation instructions to mention `hyperspy-widgets` as a dependency.
- [ ] Ensure the standalone package docs are published and linked from the HyperSpy website.

### 5. Verify the extraction bootstrap still works

- [ ] Run `tools/extract_hyperspy_widgets.sh` from a fresh clone and confirm it still produces the expected standalone layout.
- [ ] Confirm `git shortlog -sne` in the extracted clone shows the same author count as before.

### 6. Post-cutover cleanup

- [ ] Archive or remove the `packages/hyperspy_widgets/` directory from the HyperSpy repository.
- [ ] Remove any Azure Pipelines template references that were specific to the staged-package CI path.
- [ ] Add a changelog entry in `upcoming_changes/` documenting the extraction.
- [ ] Close any open issues or PRs that were blocked waiting for the standalone package.

## Rollback criteria

If the cutover introduces regressions, revert the dependency addition and restore the staged package directory until the issues are resolved in the standalone package.

## Related files

- `packages/hyperspy_widgets/EXTRACTION_MANIFEST.md` - authoritative include set and boundary contract
- `tools/extract_hyperspy_widgets.sh` - one-shot extraction bootstrap
- `doc/dev_guide/widget_package_boundary.rst` - HyperSpy developer documentation for the boundary
