from typing import Optional

from pyvisa import constants, logger, errors


def read_bytes_with_tqdm(tqdm_obj):
    """Returns a pyvisa read bytes method that uses the provided tqdm object"""

    # Modified version of the original pyvisa method (commit 113ab10c3932a1e3bf512806b261912e23b3d8d8)
    def modified_read_bytes_method(
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
                    tqdm_obj.update(size)
                    ret.extend(chunk)
                    left_to_read -= len(chunk)
                    if break_on_termchar and (
                            status == success or status == termchar_read
                    ):
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

    return modified_read_bytes_method
