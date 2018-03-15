import numpy as np

from hyperspy.decorators import jit_ifnumba


try:
    import sparse
    sparse_installed = False

    class DenseSliceCOO(sparse.COO):
        """Just like sparse.COO, but returning a dense array on indexing/slicing"""

        def __getitem__(self, *args, **kwargs):
            obj = super().__getitem__(*args, **kwargs)
            try:
                return obj.todense()
            except AttributeError:
                # Indexing, unlike slicing, returns directly the content
                return obj
except ImportError:
    sparse_installed = False


@jit_ifnumba
def _stream_to_sparse_COO_array_sum_frames(
        stream_data, last_frame, shape, channels, rebin_energy=1, first_frame=0):
    navigation_index = 0
    frame_number = 0
    ysize, xsize = shape
    frame_size = xsize * ysize
    data_list = []
    coords = []
    data = 0
    count_channel = None
    for value in stream_data:
        if frame_number < first_frame:
            if value != 65535:  # Same spectrum
                continue
            else:
                navigation_index += 1
                if navigation_index == frame_size:
                    frame_number += 1
                    navigation_index = 0
                continue
        # when we reach the end of the frame, reset the navigation index to 0
        if navigation_index == frame_size:
            navigation_index = 0
            frame_number += 1
            if frame_number == last_frame:
                break
        # if different of ‘65535’, add a count to the corresponding channel
        if value != 65535:  # Same spectrum
            if data:
                if value == count_channel:  # Same channel, add a count
                    data += 1
                else:  # a new channel, same spectrum—requires new coord
                    # Store previous channel
                    coords.append((
                        int(navigation_index // xsize),
                        int(navigation_index % xsize),
                        int(count_channel // rebin_energy))
                    )
                    data_list.append(data)
                    # Add a count to new channel
                    data = 1
                    # Update count channel as this is a new channel
                    count_channel = value

            else:  # First non-zero channel of spectrum
                data = 1
                # Update count channel as this is a new channel
                count_channel = value

        else:  # Advances one pixel
            if data:  # Only store coordinates if the spectrum was not empty
                coords.append((
                    int(navigation_index // xsize),
                    int(navigation_index % xsize),
                    int(count_channel // rebin_energy))
                )
                data_list.append(data)
            navigation_index += 1
            data = 0

    final_shape = (ysize, xsize, channels // rebin_energy)
    coords = np.array(coords).T
    data = np.array(data_list)
    return coords, data, final_shape


@jit_ifnumba
def _stream_to_sparse_COO_array(
        stream_data, last_frame, shape, channels, rebin_energy=1, first_frame=0):
    navigation_index = 0
    frame_number = 0
    ysize, xsize = shape
    frame_size = xsize * ysize
    data_list = []
    coords = []
    data = 0
    count_channel = None
    for value in stream_data:
        if frame_number < first_frame:
            if value != 65535:  # Same spectrum
                continue
            else:
                navigation_index += 1
                if navigation_index == frame_size:
                    frame_number += 1
                    navigation_index = 0
                continue
        # when we reach the end of the frame, reset the navigation index to 0
        if navigation_index == frame_size:
            navigation_index = 0
            frame_number += 1
            if frame_number == last_frame:
                break
        # if different of ‘65535’, add a count to the corresponding channel
        if value != 65535:  # Same spectrum
            if data:
                if value == count_channel:  # Same channel, add a count
                    data += 1
                else:  # a new channel, same spectrum—requires new coord
                    # Store previous channel
                    coords.append((
                        frame_number - first_frame,
                        int(navigation_index // xsize),
                        int(navigation_index % xsize),
                        int(count_channel // rebin_energy))
                    )
                    data_list.append(data)
                    # Add a count to new channel
                    data = 1
                    # Update count channel as this is a new channel
                    count_channel = value

            else:  # First non-zero channel of spectrum
                data = 1
                # Update count channel as this is a new channel
                count_channel = value

        else:  # Advances one pixel
            if data:  # Only store coordinates if the spectrum was not empty
                coords.append((
                    frame_number - first_frame,
                    int(navigation_index // xsize),
                    int(navigation_index % xsize),
                    int(count_channel // rebin_energy))
                )
                data_list.append(data)
            navigation_index += 1
            data = 0

    final_shape = (last_frame - first_frame, ysize, xsize,
                   channels // rebin_energy)
    coords = np.array(coords).T
    data = np.array(data_list)
    return coords, data, final_shape


def stream_to_sparse_COO_array(
        stream_data, spatial_shape, channels, last_frame, rebin_energy=1,
        sum_frames=True, first_frame=0, ):
    """Returns data stored in a FEI stream as a nd COO array

    Parameters
    ----------
    stream_data: numpy array
    spatial_shape: tuple of ints
        (ysize, xsize)
    channels: ints
        Number of channels in the spectrum
    rebin_energy: int
        Rebin the spectra. The default is 1 (no rebinning applied)
    sum_frames: bool
        If True, sum all the frames

    """
    if not sparse_installed:
        raise ImportError(
            "The python-sparse package is not installed and it is required "
            "for lazy loading of SIs stored in FEI EMD stream format."
        )
    # The stream format does not add a final mark. We add to simplify the
    # reading code in this case
    stream_data = np.hstack((stream_data, 65535))
    if sum_frames:
        coords, data, shape = _stream_to_sparse_COO_array_sum_frames(
            stream_data=stream_data,
            shape=spatial_shape,
            channels=channels,
            rebin_energy=rebin_energy,
            first_frame=first_frame,
            last_frame=last_frame,
        )
    else:
        coords, data, shape = _stream_to_sparse_COO_array(
            stream_data=stream_data,
            shape=spatial_shape,
            channels=channels,
            rebin_energy=rebin_energy,
            first_frame=first_frame,
            last_frame=last_frame,
        )
    return DenseSliceCOO(coords=coords, data=data, shape=shape)


@jit_ifnumba
def _fill_array_with_stream_sum_frames(spectrum_image, stream,
                                       first_frame, last_frame, rebin_energy=1):
    # jit speeds up this function by a factor of ~ 30
    navigation_index = 0
    frame_number = 0
    shape = spectrum_image.shape
    for count_channel in np.nditer(stream):
        # when we reach the end of the frame, reset the navigation index to 0
        if navigation_index == (shape[0] * shape[1]):
            navigation_index = 0
            frame_number += 1
            # break the for loop when we reach the last frame we want to read
            if frame_number == last_frame:
                break
        # if different of ‘65535’, add a count to the corresponding channel
        if count_channel != 65535:
            if first_frame <= frame_number:
                spectrum_image[navigation_index // shape[1],
                               navigation_index % shape[1],
                               count_channel // rebin_energy] += 1
        else:
            navigation_index += 1


@jit_ifnumba
def _fill_array_with_stream(spectrum_image, stream, first_frame,
                            last_frame, rebin_energy=1):
    navigation_index = 0
    frame_number = 0
    shape = spectrum_image.shape
    for count_channel in np.nditer(stream):
        # when we reach the end of the frame, reset the navigation index to 0
        if navigation_index == (shape[1] * shape[2]):
            navigation_index = 0
            frame_number += 1
            # break the for loop when we reach the last frame we want to read
            if frame_number == last_frame:
                break
        # if different of ‘65535’, add a count to the corresponding channel
        if count_channel != 65535:
            if first_frame <= frame_number:
                spectrum_image[frame_number - first_frame,
                               navigation_index // shape[2],
                               navigation_index % shape[2],
                               count_channel // rebin_energy] += 1
        else:
            navigation_index += 1


def stream_to_array(
        stream, spatial_shape, channels, last_frame, first_frame=0,
        rebin_energy=1, sum_frames=True, dtype="uint16", spectrum_image=None):
    """Returns data stored in a FEI stream as a nd COO array

    Parameters
    ----------
    stream: numpy array
    spatial_shape: tuple of ints
        (ysize, xsize)
    channels: ints
        Number of channels in the spectrum
    rebin_energy: int
        Rebin the spectra. The default is 1 (no rebinning applied)
    sum_frames: bool
        If True, sum all the frames
    dtype: numpy dtype
        dtype of the array where to store the data
    number_of_frame: int or None
    spectrum_image: numpy array or None
        If not None, the array provided will be filled with the data in the
        stream.

    """

    frames = last_frame - first_frame
    if not sum_frames:
        if spectrum_image is None:
            spectrum_image = np.zeros(
                (frames, spatial_shape[0], spatial_shape[1],
                 int(channels / rebin_energy)),
                dtype=dtype)

            _fill_array_with_stream(
                spectrum_image=spectrum_image,
                stream=stream,
                first_frame=first_frame,
                last_frame=last_frame,
                rebin_energy=rebin_energy)
    else:
        if spectrum_image is None:
            spectrum_image = np.zeros(
                (spatial_shape[0], spatial_shape[1],
                 int(channels / rebin_energy)),
                dtype=dtype)
        _fill_array_with_stream_sum_frames(
            spectrum_image=spectrum_image,
            stream=stream,
            first_frame=first_frame,
            last_frame=last_frame,
            rebin_energy=rebin_energy)
    return spectrum_image


@jit_ifnumba(nopython=True)
def array_to_stream(array):
    """Convert an array to a FEI stream

    Parameters
    ----------
    array: array

    """

    channels = array.shape[-1]
    flat_array = array.ravel()
    stream_data = []
    channel = 0
    for value in flat_array:
        for j in range(value):
            stream_data.append(channel)
        channel += 1
        if channel % channels == 0:
            channel = 0
            stream_data.append(65535)
    stream_data = stream_data[:-1]  # Remove final mark
    stream_data = np.array(stream_data)
    return stream_data