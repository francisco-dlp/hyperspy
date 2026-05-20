def test_widgets_import_surface():
    from hyperspy_widgets.widgets import SquareWidget, VerticalLineWidget

    assert VerticalLineWidget.__name__ == "VerticalLineWidget"
    assert SquareWidget.__name__ == "SquareWidget"
