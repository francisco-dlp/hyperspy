
from hyperspy import signals, components1d, components2d

def register_component1d(component):
    """Decorator to register a  1D component.

    Raises
    ------
    NameError: If a component of the same name is already in the registry.

    """
    name =  component.__name__
    if hasattr(components1d, name):
        raise NameError(
            "A component of the same name has already been registered")
    setattr(components1d, name, component)
    return component

def register_component2d(component):
    """Decorator to register a  1D component.

    Raises
    ------
    NameError: If a component of the same name is already in the registry.

    """
    name =  component.__name__
    if hasattr(components2d, name):
        raise NameError(
            "A component of the same name has already been registered")
    setattr(components1d, name, component)
    return component

def register_signal(component):
    """Decorator to register a Signal class.

    Raises
    ------
    NameError: If a signal of the same name is already in the registry.

    """
    name =  signal.__name__
    if hasattr(signals, name):
        raise NameError(
            "A Signal of the same name has already been registered")
    setattr(signals, name, signal)
    return signal
