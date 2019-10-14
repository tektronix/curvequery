from collections import namedtuple
from enum import Enum
from enum import unique
from time import sleep
from time import time

from .api_types import XScale
from .api_types import YScale
from .api_types import WaveformCollection
from .api_types import FeatureBase
from .api_types import Waveform
from .api_types import SequenceTimeout
from .helper_methods import _disabled_pbar

# noinspection SpellCheckingInspection
WaveformOutPre = namedtuple(
    "WaveformOutPre",
    [
        "IGN1",
        "IGN2",
        "IGN3",
        "IGN4",
        "IGN5",
        "IGN6",
        "IGN7",
        "IGN8",
        "IGN9",
        "IGN10",
        "XUNIT",
        "XINCR",
        "XZERO",
        "PT_OFF",
        "IGN15",
        "IGN16",
        "IGN17",
        "IGN18",
        "IGN19",
        "IGN20",
    ],
)

try:
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from tqdm import tqdm
except ImportError:
    pass


@unique
class WaveType(Enum):
    ANALOG = 1
    DIGITAL = 2
    MATH = 3


class TekSeriesDefaultFeat(FeatureBase):
    """
    Performs a default setup and waits for the operation to finish
    """

    @staticmethod
    def action_fcn(instr):
        instr.write("*RST")
        instr.query("*OPC?")


class TekSeriesCurveFeat(FeatureBase):
    """
    Returns a WaveformCollection object containing waveform data available on the instrument.

    Parameters:
        use_pbar (bool): Optionally display a progress bar. (default: False)
        decompose_dch (bool): Optionally convert a DCH channel into eight separate
            1-bit channels. (default: True)
    """

    def action_fcn(self, instr, *, verbose=False, **kwargs):
        """
        Action Function
        """

        result = WaveformCollection()

        # iterate through all available sources
        for ch, ch_data, x_scale, y_scale in self._get_data(
            instr, self._list_sources(instr), **kwargs
        ):
            if verbose:
                print(ch)
            result.data[ch] = Waveform(ch_data, x_scale, y_scale)
        return result

    @staticmethod
    def _classify_waveform(source):
        if source[0:4] == "MATH":
            return WaveType.MATH
        elif "_" in source:
            return WaveType.DIGITAL
        else:
            return WaveType.ANALOG

    @staticmethod
    def _has_data_available(instr, source):
        """Checks that the source seems to have actual data available for download.
        This function should be called before performing a curve query."""
        # Use "display:global:CH{x}:state?" to determine if the channel is displayed and available for download
        if source == "NONE":
            display_on = False
        else:
            display_on = bool(
                int(instr.query("display:global:{}:state?".format(source)))
            )
        return display_on

    @staticmethod
    def _get_xscale(instr):
        pre = WaveformOutPre(*tuple(instr.query("WFMOutpre?").strip().split(";")))
        slope = float(pre.XINCR)
        offset = float(pre.PT_OFF) * -slope + float(pre.XZERO)
        unit = pre.XUNIT.strip('"')
        return XScale(slope, offset, unit)

    @staticmethod
    def _get_yscale(instr, source):
        scale = float(instr.query("{}:SCALE?".format(source)))
        position = float(instr.query("{}:POSITION?".format(source)))
        top = scale * (5 - position)
        bottom = scale * (-5 - position)
        return YScale(top=top, bottom=bottom)

    def _list_sources(self, instr):
        """Returns a list of channel name strings that we could query"""
        available_waveforms = instr.query("data:source:available?").strip().split(",")

        # Condense digital channel bits into a single channel
        available_channels = set([i.split("_")[0] for i in available_waveforms])

        # Only include channels that available for download
        useful_channels = [
            i for i in available_channels if self._has_data_available(instr, i)
        ]

        # Return only waveforms that are available and have a corresponding useful channel
        useful_waveforms = [
            i for i in available_waveforms if i.split("_")[0] in useful_channels
        ]
        return useful_waveforms

    def _get_data(self, instr, sources, use_pbar=False, decompose_dch=True):
        """Returns an iterator that yields the source data from the oscilloscope"""

        encoding_table = {
            WaveType.MATH: ("FPBinary", 16, "d"),
            WaveType.DIGITAL: ("RIBinary", 16, "h"),
            WaveType.ANALOG: ("RIBinary", 16, "h"),
        }
        channel_table = {
            WaveType.MATH: lambda x: x,
            WaveType.DIGITAL: lambda x: "_".join([x.split("_")[0], "DALL"]),
            WaveType.ANALOG: lambda x: x,
        }

        # remember the state of the acquisition system and then stop acquiring waveforms
        acq_state = instr.query("ACQuire:STATE?").strip()
        instr.write("ACQuire:STATE STOP")

        # keep track of the sources so that we only download each digital channel only once
        downloaded_sources = []

        # if tqdm is installed, display a progress bar
        if use_pbar and ("tqdm" in globals()):
            pbar = tqdm
        else:
            pbar = _disabled_pbar

        # Process one signal source at a time
        for source in pbar(sources, desc="Downloading", unit="Wfm"):

            # Only download super channels and math waveforms once
            # Digital supper channels will produce 8 sources each
            if source.split("_")[0] not in downloaded_sources:

                # Determine the type of waveform and set key interface parameters
                wave_type = self._classify_waveform(source)
                channel = channel_table[wave_type](source)
                encoding, bit_nr, datatype = encoding_table[wave_type]

                # Switch to the source and setup the data encoding
                instr.write("data:source {}".format(channel))
                instr.write("data:encdg {}".format(encoding))
                instr.write("WFMOUTPRE:BIT_NR {}".format(bit_nr))

                # Horizontal scale information
                x_scale = self._get_xscale(instr)

                # Issue the curve query command
                instr.write("curv?")

                # Read the waveform data sent by the instrument
                source_data = instr.read_binary_values(
                    datatype=datatype, is_big_endian=True, expect_termination=True
                )

                # Normal analog channels must have the vertical scale and offset applied
                if wave_type is WaveType.ANALOG:
                    offset = float(instr.query("WFMOutpre:YZEro?"))
                    scale = float(instr.query("WFMOutpre:YMUlt?"))
                    source_data = [scale * i + offset for i in source_data]

                # Format and return the result
                if wave_type is WaveType.DIGITAL:

                    # Digital channel to be decomposed into separate bits
                    if decompose_dch:
                        for bit in range(8):
                            bit_channel = "{}_D{}".format(source.split("_")[0], bit)

                            # if the bit channel is available, decompose the data
                            if bit_channel in sources:
                                bit_data = [(i >> (2 * bit)) & 1 for i in source_data]
                                yield (bit_channel, bit_data, x_scale, None)

                    # Digital channel to be converted into an 8-bit word
                    else:
                        digital = []
                        for i in source_data:
                            a = (
                                (i & 0x4000) >> 7
                                | (i & 0x1000) >> 6
                                | (i & 0x400) >> 5
                                | (i & 0x100) >> 4
                                | (i & 0x40) >> 3
                                | (i & 0x10) >> 2
                                | (i & 0x4) >> 1
                                | i & 0x1
                            )
                            digital.append(a)
                            yield (source.split("_")[0], digital, x_scale, None)

                elif wave_type is WaveType.ANALOG:
                    # Include y-scale information with analog channel waveforms
                    y_scale = self._get_yscale(instr, source)
                    yield (source, source_data, x_scale, y_scale)

                elif wave_type is WaveType.MATH:
                    # Y-scale information for MATH channels is not supported at this time
                    yield (source, source_data, x_scale, None)

                else:
                    raise Exception(
                        "It should have been impossible to execute this code"
                    )

                # Keep track of each super channel and math source that has been handled
                downloaded_sources.append(source.split("_")[0])

        # Restore the acquisition state
        instr.write("ACQuire:STATE {}".format(acq_state))


class TekSeriesSetupFeat(FeatureBase):
    """
    Returns the setup configuration from the instrument as a string.
    """

    @staticmethod
    def action_fcn(instr, settings=None):
        """
        Action Function
        """

        instr.timeout = 20000
        if settings:
            instr.write("{:s}".format(settings))
            instr.query("*OPC?")
        else:
            return instr.query("SET?")


class TekSeriesAcquireFeat(FeatureBase):
    """
    Returns a generator object that runs a single sequence of the acquisition
        system for each iteration. If the count argument evaluates as True, the
        generator yields the count on each iteration.

    Parameters:
        count (int or None): The number of acquisitions to sequence. If None, sequence
            acquisitions indefinitely. (default: None)
        timeout (int or None): The number of seconds to wait for an acquisition to
            complete. If None, wait indefinitely. (default: None)
        restore_state (bool): Optionally save and restore the acquisition state of the
            instrument. (default: True)
    """

    def action_fcn(self, _, *, count=None, timeout=None, restore_state=True):
        """
        Action Function
        """

        def restore():
            """This helper function restores the acquisition state, if enabled"""
            if restore_state:
                self.parent_instr_obj.write(
                    "ACQUIRE:STOPAFTER {}".format(acq_stopafter)
                )
                self.parent_instr_obj.write("ACQUIRE:STATE {}".format(acq_state))

        # Save the state of the acquisition system
        acq_stopafter = self.parent_instr_obj.query("ACQUIRE:STOPAFTER?")
        acq_state = self.parent_instr_obj.query("ACQUIRE:STATE?")

        # initialize the instrument
        self.parent_instr_obj.write("ACQUIRE:STATE STOP")
        i = 0

        # Main loop
        while True:
            if isinstance(count, int):
                i += 1
                self.parent_instr_obj.write("ACQUIRE:STOPAFTER SEQUENCE")
                self.parent_instr_obj.write("ACQUIRE:STATE RUN")

            # Wait for the sequence to complete
            start_time = time()
            while True:

                # if the sequence is complete then stop waiting
                if self.parent_instr_obj.query("ACQUIRE:STATE?").strip() == "0":
                    break

                # if the acquisition is taking to long, raise an exception
                if (timeout is not None) and time() - start_time > timeout:
                    restore()
                    if count:
                        msg = "Acquisition sequence number {} did not complete".format(
                            i
                        )
                    else:
                        msg = "Acquisition sequence did not complete"
                    raise SequenceTimeout(msg)

                # wait a bit and then check again
                sleep(0.1)

            # Signal that a new acquisition is ready by sending the current count
            yield i

            # If count has gone to zero we are done.
            if (count is not None) and i >= count:
                break

        # Restore the acquisition state
        restore()
