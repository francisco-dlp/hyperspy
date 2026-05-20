Events Package Boundary
=======================

HyperSpy is in the process of extracting its event handling system into a standalone ``hyperspy-events`` distribution. The work is staged inside the repository so that the boundary can be stabilized before the final split.

What changed
------------

The event handling classes and utilities have been copied into an in-repo package at ``packages/hyperspy_events/``. This includes:

- Core event classes: ``Event``, ``EventParallel``, and event type definitions
- Event manager: ``EventManager`` for registration, triggering, and lifecycle
- Event utilities: helper functions for event creation and management
- Package-local helpers for callback management and event propagation

The ``hyperspy/events.py`` module has become a re-export shim that imports from ``hyperspy_events`` to maintain backward compatibility.

What did not change
-------------------

HyperSpy still owns the integration layers that connect events to its domain objects. The following remain in HyperSpy during stabilization:

- Signal event integration (``hyperspy/signal.py``)
- Axes manager events (``hyperspy/axes.py``)
- Model and component events (``hyperspy/model.py``, ``hyperspy/_components/``)
- ROI events and synchronization (``hyperspy/roi.py``)
- Explorer and plotting event handlers (``hyperspy/drawing/``)
- Any domain-specific event triggers tied to HyperSpy objects

For developers
--------------

If you are contributing to core event handling (event creation, registration, triggering, callback management), consider whether the change belongs in the staged package. If you are changing how events interact with HyperSpy signals, models, axes, or domain objects, the change belongs in HyperSpy.

The staged package has its own documentation and tests. You can build them locally:

.. code-block:: bash

   python -m pytest packages/hyperspy_events/tests -q
   python -m sphinx -b html packages/hyperspy_events/docs packages/hyperspy_events/docs/_build/html

Package documentation
---------------------

Full API reference and migration notes for the staged package are maintained in the package docs tree:

- `Package API reference <../_events_package/api_reference.html>`_
- `Migration notes <../_events_package/migration_notes.html>`_

These pages are built from ``packages/hyperspy_events/docs/`` and are not duplicated in the main HyperSpy documentation.

Widget mini-events removal
--------------------------

The widget-specific ``mini-events.py`` implementation has been deleted and replaced with a dependency on the ``hyperspy-events`` package. All widget event handling now uses the centralized event system.

Future extraction
-----------------

When the standalone package is ready, it will be extracted from a fresh clone using ``git filter-repo`` with a path set that preserves contributor history for both the staged package subtree and the legacy HyperSpy paths that authored the event code. Until then, HyperSpy continues to expose compatibility imports under ``hyperspy.events``.
