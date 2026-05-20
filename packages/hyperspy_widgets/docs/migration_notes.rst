Migration Notes
===============

The ``hyperspy_widgets`` package is a **staged in-repo extraction**. It is not yet an independent distribution on PyPI or conda-forge. These notes explain the current boundary, what has moved, and what remains in HyperSpy.

Staged boundary
---------------

The widget core (base classes and concrete matplotlib widgets) now lives under ``packages/hyperspy_widgets/src/hyperspy_widgets/``. HyperSpy keeps the integration glue that wires those widgets into signals, models, ROIs, and explorers.

What moved now
^^^^^^^^^^^^^^

- ``WidgetBase``, ``DraggableWidgetBase``, ``ResizableDraggableWidgetBase``, ``Widget1DBase``, ``Widget2DBase``, and ``ResizersMixin``
- Concrete widgets: ``VerticalLineWidget``, ``HorizontalLineWidget``, ``LabelWidget``, ``Line2DWidget``, ``RangeWidget``, ``RectangleWidget``, ``SquareWidget``, ``CircleWidget``, ``PolygonWidget``, and ``ScaleBar``
- Package-local helpers: axis source binding, events, math utilities, and defaults

What stays in HyperSpy during stabilization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``hyperspy/roi.py`` ... ROI classes and ROI-to-widget synchronization
- ``hyperspy/drawing/mpl_he.py`` ... explorer pointer and plot lifecycle
- ``hyperspy/drawing/mpl_hse.py`` ... right-pointer explorer behavior
- ``hyperspy/models/model1d.py`` ... model-position widgets and labels
- ``hyperspy/signal_tools/_line.py`` ... signal-tool wrappers
- ``hyperspy/samfire.py`` ... SAMFire-specific square-widget guidance
- Any ``WidgetAdapter``-style glue or shim that connects package widgets to HyperSpy domain objects

Contributor history preservation
--------------------------------

When the package is later extracted into its own repository with a clean clone, the ``git filter-repo`` path set includes both the staged package subtree and the legacy HyperSpy paths that originally authored the widget code. This preserves contributor history for the widget core and the narrow helper logic that will be copied into package-local utility modules.

Future standalone expectations
------------------------------

- HyperSpy will continue to expose compatibility import paths under ``hyperspy.drawing.*`` after the core move.
- The package public surface should remain the widget classes and helpers only. HyperSpy integration must import from that stable public boundary.
- ``WidgetAdapter`` remains the conceptual marker for the HyperSpy-owned integration layer even if the glue is spread across several files.

How to install the staged package locally
-----------------------------------------

.. code-block:: bash

   pip install -e packages/hyperspy_widgets

This editable install is useful for local development and for the dual-install smoke tests that verify HyperSpy and the staged package work together.
