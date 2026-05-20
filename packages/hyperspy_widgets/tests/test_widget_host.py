import pytest
from hyperspy_widgets.widget import WidgetBase

from hyperspy.drawing.widget_host import WidgetHost


def test_add_widget():
    host = WidgetHost()
    widget = WidgetBase()

    added_events = []
    host.events.widget_added.connect(lambda widget: added_events.append(widget))

    host.add(widget)

    assert host.widget_count == 1
    assert widget in host.widgets
    assert len(added_events) == 1
    assert added_events[0] is widget


def test_add_widget_idempotent():
    host = WidgetHost()
    widget = WidgetBase()

    added_events = []
    host.events.widget_added.connect(lambda widget: added_events.append(widget))

    host.add(widget)
    host.add(widget)

    assert host.widget_count == 1
    assert len(added_events) == 1


def test_remove_widget():
    host = WidgetHost()
    widget = WidgetBase()

    host.add(widget)

    removed_events = []
    host.events.widget_removed.connect(lambda widget: removed_events.append(widget))

    host.remove(widget)

    assert host.widget_count == 0
    assert widget not in host.widgets
    assert len(removed_events) == 1
    assert removed_events[0] is widget


def test_remove_nonexistent_widget():
    host = WidgetHost()
    widget = WidgetBase()

    removed_events = []
    host.events.widget_removed.connect(lambda widget: removed_events.append(widget))

    host.remove(widget)

    assert host.widget_count == 0
    assert len(removed_events) == 0


def test_auto_remove_on_widget_close():
    host = WidgetHost()
    widget = WidgetBase()

    host.add(widget)
    assert host.widget_count == 1

    widget.close()

    assert host.widget_count == 0
    assert widget not in host.widgets


def test_select_widget():
    host = WidgetHost()
    widget = WidgetBase()

    host.add(widget)

    selection_events = []
    host.events.selection_changed.connect(
        lambda old_widget, new_widget: selection_events.append((old_widget, new_widget))
    )

    host.select(widget)

    assert host.selected is widget
    assert len(selection_events) == 1
    assert selection_events[0] == (None, widget)


def test_select_unregistered_widget():
    host = WidgetHost()
    widget = WidgetBase()

    with pytest.raises(ValueError, match="Cannot select unregistered widget"):
        host.select(widget)


def test_select_same_widget_idempotent():
    host = WidgetHost()
    widget = WidgetBase()

    host.add(widget)
    host.select(widget)

    selection_events = []
    host.events.selection_changed.connect(
        lambda old_widget, new_widget: selection_events.append((old_widget, new_widget))
    )

    host.select(widget)

    assert host.selected is widget
    assert len(selection_events) == 0


def test_clear():
    host = WidgetHost()
    widget1 = WidgetBase()
    widget2 = WidgetBase()

    host.add(widget1)
    host.add(widget2)
    host.select(widget1)

    removed_events = []
    host.events.widget_removed.connect(lambda widget: removed_events.append(widget))

    host.clear()

    assert host.widget_count == 0
    assert host.selected is None
    assert len(removed_events) == 2
    assert widget1 in removed_events
    assert widget2 in removed_events


def test_widgets_returns_frozenset():
    host = WidgetHost()
    widget = WidgetBase()

    host.add(widget)

    assert isinstance(host.widgets, frozenset)
    with pytest.raises(AttributeError):
        host.widgets.add(WidgetBase())


def test_selection_changed_event():
    host = WidgetHost()
    widget1 = WidgetBase()
    widget2 = WidgetBase()

    host.add(widget1)
    host.add(widget2)
    host.select(widget1)

    selection_events = []
    host.events.selection_changed.connect(
        lambda old_widget, new_widget: selection_events.append((old_widget, new_widget))
    )

    host.select(widget2)

    assert len(selection_events) == 1
    assert selection_events[0] == (widget1, widget2)


def test_widget_added_event():
    host = WidgetHost()
    widget = WidgetBase()

    added_events = []
    host.events.widget_added.connect(lambda widget: added_events.append(widget))

    host.add(widget)

    assert len(added_events) == 1
    assert added_events[0] is widget


def test_widget_removed_event():
    host = WidgetHost()
    widget = WidgetBase()

    host.add(widget)

    removed_events = []
    host.events.widget_removed.connect(lambda widget: removed_events.append(widget))

    host.remove(widget)

    assert len(removed_events) == 1
    assert removed_events[0] is widget
