HyperSpy Widgets
================

The **HyperSpy Widgets** package provides the matplotlib-based interactive widget core that powers region-of-interest overlays, cursors, and annotation tools in HyperSpy plots.

These widgets are currently staged inside the HyperSpy repository as an in-repo package. In the future they will become a standalone ``hyperspy-widgets`` distribution, but during stabilization HyperSpy still owns the integration glue (ROI synchronization, signal explorer wiring, model tooling, and so on).

.. toctree::
   :maxdepth: 2

   api_reference
   migration_notes

What this package contains
--------------------------

- Base widget abstractions: :class:`~hyperspy_widgets.widget.WidgetBase`, draggable and resizable bases, and the resizer mixin.
- Concrete matplotlib widgets: lines, rectangles, circles, polygons, ranges, scale bars, and labels.
- Package-local helper logic for axis binding, events, and defaults.

What stays in HyperSpy
----------------------

HyperSpy retains the integration layers that connect widgets to its signal, model, and ROI systems. For the full boundary contract, see the :doc:`migration_notes` page and the ``EXTRACTION_MANIFEST.md`` file in the package root.

Getting help
------------

- Report issues at the `HyperSpy issue tracker <https://github.com/hyperspy/hyperspy/issues>`_.
- Ask questions on `Gitter <https://gitter.im/hyperspy/hyperspy>`_.
