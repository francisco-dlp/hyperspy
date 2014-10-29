import numpy as np
from operator import attrgetter


def attrsetter(target, attrs, value):
    """ Like operator.attrgetter, but for setattr - supports "nested" attributes.

        Parameters
        ----------
            target : object
            attrs : string
            value : object

    """
    where = attrs.rfind('.')
    if where != -1:
        target = attrgetter(attrs[:where])(target)
    setattr(target, attrs[where + 1:], value)

class SpecialSlicers:
    def __init__(self, obj, isNavigation):
        self.isNavigation = isNavigation
        self.obj = obj

    def __getitem__(self, slices):
        return self.obj._slicer(slices, self.isNavigation)


class FancySlicing(object):
    def _slicer(self, slices, isNavigation=None):
        try:
            len(slices)
        except TypeError:
            slices = (slices,)
        _orig_slices = slices

        has_nav = True if isNavigation is None else isNavigation
        has_signal = True if isNavigation is None else not isNavigation

        # Create a deepcopy of self that contains a view of self.data
        _obj = self._deepcopy_with_new_data(self.data)

        nav_idx = [el.index_in_array for el in
                   _obj.axes_manager.navigation_axes]
        signal_idx = [el.index_in_array for el in
                      _obj.axes_manager.signal_axes]

        if not has_signal:
            idx = nav_idx
        elif not has_nav:
            idx = signal_idx
        else:
            idx = nav_idx + signal_idx

        # Add support for Ellipsis
        if Ellipsis in _orig_slices:
            _orig_slices = list(_orig_slices)
            # Expand the first Ellipsis
            ellipsis_index = _orig_slices.index(Ellipsis)
            _orig_slices.remove(Ellipsis)
            _orig_slices = (_orig_slices[:ellipsis_index] + [slice(None), ] *
                            max(0, len(idx) - len(_orig_slices)) +
                            _orig_slices[ellipsis_index:])
            # Replace all the following Ellipses by :
            while Ellipsis in _orig_slices:
                _orig_slices[_orig_slices.index(Ellipsis)] = slice(None)
            _orig_slices = tuple(_orig_slices)

        if len(_orig_slices) > len(idx):
            raise IndexError("too many indices")

        slices = np.array([slice(None,)] *
                          len(_obj.axes_manager._axes))

        slices[idx] = _orig_slices + (slice(None),) * max(
            0, len(idx) - len(_orig_slices))

        array_slices = []
        for slice_, axis in zip(slices, _obj.axes_manager._axes):
            if (isinstance(slice_, slice) or
                    len(_obj.axes_manager._axes) < 2):
                array_slices.append(axis._slice_me(slice_))
            else:
                if isinstance(slice_, float):
                    slice_ = axis.value2index(slice_)
                array_slices.append(slice_)
                _obj._remove_axis(axis.index_in_axes_manager)

        _obj.data = _obj.data[array_slices]
        if hasattr(self, "_additional_slicing_targets"):
            for ta in self._additional_slicing_targets:
                try:
                    t = attrgetter(ta)(self)
                    if hasattr(t, '_slicer'):
                        attrsetter(_obj, ta, t._slicer(_orig_slices, isNavigation))
                except AttributeError:
                    pass
        _obj.get_dimensions_from_data()

        return _obj
