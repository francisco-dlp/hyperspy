Widget Package Boundary
=======================

HyperSpy is in the process of extracting its matplotlib widget core into a standalone ``hyperspy-widgets`` distribution. The work is staged inside the repository so that the boundary can be stabilized before the final split.

What changed
------------

The pure matplotlib widget classes and their base abstractions have been copied into an in-repo package at ``packages/hyperspy_widgets/``. This includes:

- Base widget classes: ``WidgetBase``, draggable/resizable bases, and the resizer mixin
- Concrete widgets: vertical/horizontal lines, rectangles, squares, circles, polygons, ranges, scale bars, and labels
- Package-local helpers for axis binding, events, math utilities, and defaults

What did not change
-------------------

HyperSpy still owns the integration layers that connect widgets to its domain objects. The following remain in HyperSpy during stabilization:

- ROI classes and ROI-to-widget synchronization (``hyperspy/roi.py``)
- Explorer pointer assignment and plot lifecycle (``hyperspy/drawing/mpl_he.py``)
- Right-pointer explorer behavior (``hyperspy/drawing/mpl_hse.py``)
- Model-position widgets and labels tied to ``Model1D`` (``hyperspy/models/model1d.py``)
- Signal-tool wrappers that attach widgets to plotted signals (``hyperspy/signal_tools/_line.py``)
- SAMFire-specific widget guidance (``hyperspy/samfire.py``)
- Any ``WidgetAdapter``-style glue or shim between package widgets and HyperSpy objects

For developers
--------------

If you are contributing to widget behavior that is pure matplotlib (patch geometry, dragging, resizing, events), consider whether the change belongs in the staged package. If you are changing how widgets interact with HyperSpy signals, models, or ROIs, the change belongs in HyperSpy.

The staged package has its own documentation and tests. You can build them locally:

.. code-block:: bash

   python -m sphinx -b html packages/hyperspy_widgets/docs packages/hyperspy_widgets/docs/_build/html
   python -m pytest packages/hyperspy_widgets/tests -q

Package documentation
---------------------

Full API reference and migration notes for the staged package are maintained in the package docs tree:

- `Package API reference <../_widget_package/api_reference.html>`_
- `Migration notes <../_widget_package/migration_notes.html>`_

These pages are built from ``packages/hyperspy_widgets/docs/`` and are not duplicated in the main HyperSpy documentation.

Future extraction
-----------------

When the standalone package is ready, it will be extracted from a fresh clone using ``git filter-repo`` with a path set that preserves contributor history for both the staged package subtree and the legacy HyperSpy paths that authored the widget code. Until then, HyperSpy continues to expose compatibility imports under ``hyperspy.drawing.*``.
