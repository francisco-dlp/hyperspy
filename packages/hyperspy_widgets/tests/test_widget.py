from hyperspy_widgets._widgets.scalebar import ScaleBar
from hyperspy_widgets.widget import ResizableDraggableWidgetBase
from hyperspy_widgets.widgets import VerticalLineWidget

from ._test_support import FakeAxis, FakeAxisSource, make_event, make_image_axes


def test_get_step():
    axis = FakeAxis(size=4, scale=1.0)
    assert ResizableDraggableWidgetBase._get_step(object(), axis) == 1.0

    axis.index = 3
    assert ResizableDraggableWidgetBase._get_step(object(), axis) == 1.0


def test_scalebar_remove():
    _, ax = make_image_axes()
    scalebar = ScaleBar(ax, units="nm", pixel_size=1.2)

    assert scalebar.line is not None
    assert scalebar.text is not None

    scalebar.remove()

    assert scalebar.line not in ax.lines
    assert scalebar.text not in ax.texts


def test_calculate_size_uses_absolute_xlim():
    _, ax = make_image_axes()
    ax.set_xlim(10, 0)

    scalebar = ScaleBar(ax, units="nm", pixel_size=1.0)

    assert scalebar.length > 0


def test_scalebar_set_length_updates_without_error():
    _, ax = make_image_axes()
    scalebar = ScaleBar(ax, units="nm", pixel_size=1.0, color="red")

    scalebar.set_length(3.5)

    assert scalebar.length == 3.5
    assert scalebar.line.get_color() == "red"
    assert scalebar.text.get_color() == "red"


def test_vertical_line_widget_axis_source_sync():
    axis = FakeAxis(size=10, scale=1.0)
    axis_source = FakeAxisSource(navigation_axes=[axis])
    _, ax = make_image_axes()

    line = VerticalLineWidget(axis_source)
    line.set_mpl_ax(ax)
    line.connect_axis_source()

    axis.value = 3.0
    axis_source.events.indices_changed.trigger(obj=axis_source)
    assert line.position == (3.0,)

    line.is_pointer = True
    line._onjumpclick(make_event(ax, xdata=5.0, key="shift"))

    assert line.position == (5.0,)
    assert axis.value == 5.0
