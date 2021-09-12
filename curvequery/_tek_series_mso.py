import types
from collections import namedtuple
from enum import Enum
from enum import unique
from functools import reduce
from time import sleep
from time import time

import pyvisa
from visadore import base
from tqdm import tqdm

from .api_types import SequenceTimeout
from .api_types import Waveform
from .api_types import WaveformCollection
from .api_types import XScale
from .api_types import YScale
from ._pyvisa_tqdm_patch import _raw_read_with_tqdm
from ._pyvisa_tqdm_patch import read_binary_values_with_custom_read_methods
from ._pyvisa_tqdm_patch import read_bytes_with_tqdm

UNLOCK_DELAY = 0.01
MAX_EVENTS = 33


@unique
class WaveType(Enum):
    ANALOG = 1
    DIGITAL = 2
    MATH = 3


JobParameters = namedtuple(
    "JobParameters",
    ["wave_type", "channel_name", "encoding", "bit_nr", "data_type", "record_length"],
)


class TekSeriesDefaultFeat(base.FeatureBase):
    def feature(self):
        """Performs a default setup and waits for the operation to finish"""
        with self.resource_manager.open_resource(self.resource_name) as inst:
            try:
                inst.write("*RST")
                inst.query("*OPC?")
            except pyvisa.errors.VisaIOError:
                get_event_queue(inst)
                raise


class TekSeriesCurveFeat(base.FeatureBase):
    def feature(self, *, use_pbar=True, decompose_dch=True, verbose=False):
        """
        Returns a WaveformCollection object containing waveform data available on the instrument.

        Parameters:
            use_pbar (bool): Optionally display a progress bar. (default: False)
            decompose_dch (bool): Optionally convert a DCH channel into eight separate
                1-bit channels. (default: True)
            verbose (bool): Display additional information
        """
        with self.resource_manager.open_resource(self.resource_name) as inst:
            result = WaveformCollection()

            # iterate through all available sources
            try:
                for ch, ch_data, x_scale, y_scale in self._get_data(
                    inst, self._list_sources(inst), use_pbar, decompose_dch
                ):
                    if verbose:
                        print(ch)
                    result.data[ch] = Waveform(ch_data, x_scale, y_scale)
            except pyvisa.errors.VisaIOError:
                get_event_queue(inst)
                raise
        return result

    @staticmethod
    def _classify_waveform(source):
        if source[0:4] == "MATH":
            wave_type = WaveType.MATH
        elif "_" in source:
            wave_type = WaveType.DIGITAL
        else:
            wave_type = WaveType.ANALOG
        return wave_type

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
        """Get the horizontal scale of the instrument"""

        # This function will generate a VISA timeout if there is no waveform data available
        # and the channel is enabled.
        try:
            xincr = instr.query("WFMOutpre:XINCR?").strip()
        except pyvisa.errors.VisaIOError:

            # Flush out the VISA interface event queue
            get_event_queue(instr, verbose=False)
            result = None
        else:

            # collect more horizontal data
            pt_off = instr.query("WFMOutpre:PT_OFF?").strip()
            xzero = instr.query("WFMOutpre:XZERO?").strip()
            xunit = instr.query("WFMOutpre:XUNIT?").strip()

            # calculate horizontal scale
            slope = float(xincr)
            offset = float(pt_off) * -slope + float(xzero)
            unit = xunit.strip('"')
            result = XScale(slope, offset, unit)
        return result

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

    def _make_jobs(self, instr, sources):
        """Scan the instrument for available sources of data construct a list of jobs"""

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

        results = {}
        for source in sources:
            if source.split("_")[0] not in results:
                # Determine the type of waveform and set key interface parameters
                wave_type = self._classify_waveform(source)
                channel = channel_table[wave_type](source)
                encoding, bit_nr, datatype = encoding_table[wave_type]

                # Set the start and stop point of the record
                rec_len = int(instr.query("horizontal:recordlength?").strip())

                # Keep track of each super channel and math source that has been handled
                results[source.split("_")[0]] = JobParameters(
                    wave_type, channel, encoding, bit_nr, datatype, rec_len
                )

        return results

    @staticmethod
    def _setup_curve_query(instr, source, parameters: dict[str, JobParameters]):
        """Setup the instrument for the curve query operation"""

        # extract the job parameters
        wave_type, channel, encoding, bit_nr, datatype, rec_len = parameters[source]

        # Switch to the source and setup the data encoding
        instr.write("data:source {}".format(channel))
        instr.write("data:encdg {}".format(encoding))
        instr.write("WFMOUTPRE:BIT_NR {}".format(bit_nr))

        # Set the start and stop point of the record
        rec_len = instr.query("horizontal:recordlength?").strip()
        instr.write("data:start 1")
        instr.write("data:stop {}".format(rec_len))

    def _post_process_analog(self, instr, source, source_data, x_scale):
        """Post processes analog channel data"""

        # Normal analog channels must have the vertical scale and offset applied
        offset = float(instr.query("WFMOutpre:YZEro?"))
        scale = float(instr.query("WFMOutpre:YMUlt?"))
        source_data = [scale * i + offset for i in source_data]

        # Include y-scale information with analog channel waveforms
        y_scale = self._get_yscale(instr, source)

        return source, source_data, x_scale, y_scale

    @staticmethod
    def _post_process_digital_bits(sources, source, source_data, x_scale, bit):
        """Post processes digital channel data as separate bits"""

        bit_channel = "{}_D{}".format(source.split("_")[0], bit)

        # if the bit channel is available, decompose the data
        if bit_channel in sources:
            bit_data = [(i >> (2 * bit)) & 1 for i in source_data]
            return bit_channel, bit_data, x_scale, None

        # Nothing to decompose
        else:
            return None

    @staticmethod
    def _post_process_digital_byte(source, source_data, x_scale):
        """Post processes digital channel data as a byte"""
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
        return source.split("_")[0], digital, x_scale, None

    def _get_data(self, instr, sources, use_pbar, decompose_dch):
        """Returns an iterator that yields the source data from the oscilloscope"""

        jobs = self._make_jobs(instr, sources)
        pbar_disabled = not use_pbar

        # remember the state of the acquisition system and then stop acquiring waveforms
        acq_state = instr.query("ACQuire:STATE?").strip()
        instr.write("ACQuire:STATE STOP")

        # Calculate the total number of bytes of data to be downloaded from the instrument
        # Two (2) bytes per sample
        total_bytes = 2 * reduce(
            lambda a, b: a + b, [jobs[i].record_length for i in jobs]
        )

        with tqdm(
            desc="Downloading",
            unit="B",
            total=total_bytes,
            disable=pbar_disabled,
            unit_scale=True,
        ) as t:

            # Patch the instr object with a custom methods that implement tqdm updates
            instr.read_bytes_tqdm = types.MethodType(
                read_bytes_with_tqdm(tqdm_obj=t), instr
            )
            instr._raw_read_tqdm = types.MethodType(
                _raw_read_with_tqdm(tqdm_obj=t), instr
            )
            instr.read_binary_values_tqdm = types.MethodType(
                read_binary_values_with_custom_read_methods(
                    read_bytes_method=instr.read_bytes_tqdm,
                    _raw_read_method=instr._raw_read_tqdm,
                ),
                instr,
            )

            for source in jobs:

                self._setup_curve_query(instr, source, jobs)

                # extract the job parameters
                wave_type, channel, encoding, bit_nr, datatype, rec_len = jobs[source]

                # Horizontal scale information
                x_scale = self._get_xscale(instr)
                if x_scale is not None:

                    # Issue the curve query command
                    instr.write("curv?")

                    # Read the waveform data sent by the instrument
                    source_data = instr.read_binary_values_tqdm(
                        datatype=datatype, is_big_endian=True, expect_termination=True
                    )

                    if wave_type is WaveType.DIGITAL:

                        # Digital channel to be decomposed into separate bits
                        if decompose_dch:
                            for bit in range(8):
                                result = self._post_process_digital_bits(
                                    sources, source, source_data, x_scale, bit
                                )
                                if result:
                                    yield result

                        # Digital channel to be converted into an 8-bit word
                        else:
                            yield self._post_process_digital_byte(
                                source, source_data, x_scale
                            )

                    elif wave_type is WaveType.ANALOG:
                        yield self._post_process_analog(
                            instr, source, source_data, x_scale
                        )

                    elif wave_type is WaveType.MATH:
                        # Y-scale information for MATH channels is not supported at this time
                        yield source, source_data, x_scale, None

                    else:
                        raise Exception(
                            "It should have been impossible to execute this code"
                        )

        # Restore the acquisition state
        instr.write("ACQuire:STATE {}".format(acq_state))


class TekSeriesSetupFeat(base.FeatureBase):
    def feature(self, settings=None):
        """
        Sets or gets the setup configuration from the instrument as a string.
        """
        with self.resource_manager.open_resource(self.resource_name) as inst:
            inst.timeout = 20000  # this can take a while, so use a 20 second timeout
            if settings:
                inst.write("{:s}".format(settings))
                inst.query("*OPC?")
            else:
                return inst.query("SET?")


class TekSeriesAcquireFeat(base.FeatureBase):
    def feature(self, *, count=None, timeout=None, restore_state=True):
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

        def restore(instr, enabled, stop_after, state):
            """This helper function restores the acquisition state, if enabled"""
            if enabled:
                instr.write("ACQUIRE:STOPAFTER {}".format(stop_after))
                instr.write("ACQUIRE:STATE {}".format(state))

        with self.resource_manager.open_resource(self.resource_name) as inst:

            # Save the state of the acquisition system
            acq_stopafter = inst.query("ACQUIRE:STOPAFTER?")
            acq_state = inst.query("ACQUIRE:STATE?")

            # initialize the instrument
            inst.write("ACQUIRE:STATE STOP")

        i = 0

        # Main loop
        while True:
            with self.resource_manager.open_resource(self.resource_name) as inst:
                if isinstance(count, int):
                    i += 1
                    inst.write("ACQUIRE:STOPAFTER SEQUENCE")
                    inst.write("ACQUIRE:STATE RUN")

                # Timeout loop to ensure the acquisition does not hang up
                start_time = time()
                while True:

                    # If the sequence is complete then stop waiting
                    if inst.query("ACQUIRE:STATE?").strip() == "0":
                        break

                    # If the acquisition is taking to long, raise an exception
                    if (timeout is not None) and time() - start_time > timeout:
                        restore(inst, restore_state, acq_stopafter, acq_state)
                        if count:
                            msg = "Acquisition sequence number {} did not complete".format(
                                i
                            )
                        else:
                            msg = "Acquisition sequence did not complete"
                        raise SequenceTimeout(msg)

                    # wait a bit and then check again
                    sleep(0.1)

            # exiting context manager, instrument object is closed
            # Signal that a new acquisition is ready by sending the current count
            yield i

            # If count has gone to zero we are done.
            if (count is not None) and i >= count:
                break

        # Restore the acquisition state
        with self.resource_manager.open_resource(self.resource_name) as inst:
            restore(inst, restore_state, acq_stopafter, acq_state)


def get_event_queue(instr, verbose=True):
    """This function queries events from the Event Queue and optionally prints the events on stdout"""
    events = []

    # An race condition will sometimes create a secondary timeout error
    # This short delay seems to fix the issue
    sleep(UNLOCK_DELAY)

    # Reset the VISA interface and capture the Status Byte contents
    instr.clear()
    sbr = instr.query("*STB?").strip()

    # Load events into the Event Queue
    sesr = instr.query("*ESR?").strip()

    # Optionally print data to stdout
    if verbose:
        print("VISA Timeout Exception Handler:")
        print("  Status Byte (SBR) Register: {}".format(sbr))
        print("  Standard Event Status (SESR) Register: {}".format(sesr))

    # Download the events from the Event Queue, one at a time, up to the size of the Event Queue
    for _ in range(MAX_EVENTS):

        # After a short delay, download a single event and split it into a number and a description
        sleep(UNLOCK_DELAY)
        events.append(instr.query("EVMSG?").strip())
        num, msg = tuple(events[-1].split(","))

        # A '1' denotes that the Event Queue is empty but more events are available
        if num == "1":

            # After a short delay, load more events into the Event Queue and optionally print the
            # SESR register contents to stdout
            sleep(UNLOCK_DELAY)
            sesr = instr.query("*ESR?").strip()
            if verbose:
                print("  Standard Event Status (SESR) Register: {}".format(sesr))

        # A '0' denotes that there are no more events waiting on the instrument
        if num == "0":
            break

        # Optionally, print the event to stdout
        if verbose:
            print("  Event: {}".format(events[-1]))

    # Return a list of all events captured from the Event Queue
    return events
