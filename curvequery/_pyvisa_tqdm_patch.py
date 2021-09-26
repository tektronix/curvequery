import struct

from typing import Callable
from typing import Iterable
from typing import Optional
from typing import Sequence
from typing import Type
from typing import Union

from pyvisa import constants
from pyvisa import errors
from pyvisa import logger
from pyvisa import util


# This file contains modified versions of methods from the pyvisa package
# module. The modifications enable support for the tqdm progress bar. These
# methods are dynamically patched (isn't Python wonderful) into a message-based
# instrument object by the _get_data() method of the Curve Query feature.
#
# This code was copied from pyvisa version 1.11.3.


def read_bytes_progress_bar(
    self,
    count: int,
    chunk_size: Optional[int] = None,
    break_on_termchar: bool = False,
) -> bytes:
    """Read a certain number of bytes from the instrument.

    Parameters
    ----------
    count : int
        The number of bytes to read from the instrument.
    chunk_size : Optional[int], optional
        The chunk size to use to perform the reading. If count > chunk_size
        multiple low level operations will be performed. Defaults to None,
        meaning the resource wide set value is set.
    break_on_termchar : bool, optional
        Should the reading stop when a termination character is encountered
        or when the message ends. Defaults to False.

    Returns
    -------
    bytes
        Bytes read from the instrument.

    """
    chunk_size = chunk_size or self.chunk_size
    ret = bytearray()
    left_to_read = count
    success = constants.StatusCode.success
    termchar_read = constants.StatusCode.success_termination_character_read

    with self.ignore_warning(
        constants.StatusCode.success_device_not_present,
        constants.StatusCode.success_max_count_read,
    ):
        try:
            status = None
            while len(ret) < count:
                size = min(chunk_size, left_to_read)
                logger.debug(
                    "%s - reading %d bytes (last status %r)",
                    self._resource_name,
                    size,
                    status,
                )
                chunk, status = self.visalib.read(self.session, size)
                self.progress_bar(len(chunk))
                ret.extend(chunk)
                left_to_read -= len(chunk)
                if break_on_termchar and (status == success or status == termchar_read):
                    break
        except errors.VisaIOError as e:
            logger.debug(
                "%s - exception while reading: %s\n" "Buffer content: %r",
                self._resource_name,
                e,
                ret,
            )
            raise
    return bytes(ret)


def _read_raw_progress_bar(self, size: Optional[int] = None):
    """Read the unmodified string sent from the instrument to the computer.

    In contrast to read(), no termination characters are stripped.

    Parameters
    ----------
    size : Optional[int], optional
        The chunk size to use to perform the reading. Defaults to None,
        meaning the resource wide set value is set.

    Returns
    -------
    bytearray
        Bytes read from the instrument.

    """
    size = self.chunk_size if size is None else size

    loop_status = constants.StatusCode.success_max_count_read

    ret = bytearray()
    with self.ignore_warning(
        constants.StatusCode.success_device_not_present,
        constants.StatusCode.success_max_count_read,
    ):
        try:
            status = loop_status
            while status == loop_status:
                logger.debug(
                    "%s - reading %d bytes (last status %r)",
                    self._resource_name,
                    size,
                    status,
                )
                chunk, status = self.visalib.read(self.session, size)
                self.progress_bar.update(len(chunk))
                ret.extend(chunk)
        except errors.VisaIOError as e:
            logger.debug(
                "%s - exception while reading: %s\nBuffer " "content: %r",
                self._resource_name,
                e,
                ret,
            )
            raise

    return ret


def read_binary_values_progress_bar(
    self,
    datatype: util.BINARY_DATATYPES = "f",
    is_big_endian: bool = False,
    container: Union[Type, Callable[[Iterable], Sequence]] = list,
    header_fmt: util.BINARY_HEADERS = "ieee",
    expect_termination: bool = True,
    data_points: int = 0,
    chunk_size: Optional[int] = None,
) -> Sequence[Union[int, float]]:
    """Read values from the device in binary format returning an iterable
    of values.

    Parameters
    ----------
    datatype : BINARY_DATATYPES, optional
        Format string for a single element. See struct module. 'f' by default.
    is_big_endian : bool, optional
        Are the data in big or little endian order. Defaults to False.
    container : Union[Type, Callable[[Iterable], Sequence]], optional
        Container type to use for the output data. Possible values are: list,
        tuple, np.ndarray, etc, Default to list.
    header_fmt : util.BINARY_HEADERS, optional
        Format of the header prefixing the data. Defaults to 'ieee'.
    expect_termination : bool, optional
        When set to False, the expected length of the binary values block
        does not account for the final termination character
        (the read termination). Defaults to True.
    data_points : int, optional
         Number of points expected in the block. This is used only if the
         instrument does not report it itself. This will be converted in a
         number of bytes based on the datatype. Defaults to 0.
    chunk_size : int, optional
        Size of the chunks to read from the device. Using larger chunks may
        be faster for large amount of data.

    Returns
    -------
    Sequence[Union[int, float]]
        Data read from the device.

    """
    block = self._read_raw_progress_bar(chunk_size)

    if header_fmt == "ieee":
        offset, data_length = util.parse_ieee_block_header(block)

    elif header_fmt == "hp":
        offset, data_length = util.parse_hp_block_header(block, is_big_endian)
    elif header_fmt == "empty":
        offset = 0
        data_length = 0
    else:
        raise ValueError(
            "Invalid header format. Valid options are 'ieee'," " 'empty', 'hp'"
        )

    # Allow to support instrument such as the Keithley 2000 that do not
    # report the length of the block
    data_length = data_length or data_points * struct.calcsize(datatype)

    expected_length = offset + data_length

    if expect_termination and self._read_termination is not None:
        expected_length += len(self._read_termination)

    # Read all the data if we know what to expect.
    if data_length != 0:
        block.extend(
            self.read_bytes_progress_bar(
                expected_length - len(block), chunk_size=chunk_size
            )
        )
    else:
        raise ValueError(
            "The length of the data to receive could not be "
            "determined. You should provide the number of "
            "points you expect using the data_points keyword "
            "argument."
        )

    try:
        # Do not reparse the headers since it was already done and since
        # this allows for custom data length
        return util.from_binary_block(
            block, offset, data_length, datatype, is_big_endian, container
        )
    except ValueError as e:
        raise errors.InvalidBinaryFormat(e.args[0])
