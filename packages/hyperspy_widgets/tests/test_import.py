def test_import_and_version():
    import hyperspy_widgets

    assert hyperspy_widgets.__name__ == "hyperspy_widgets"
    assert hasattr(hyperspy_widgets, "__version__")
