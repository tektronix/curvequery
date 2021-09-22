from collections import namedtuple
from enum import Enum
from enum import unique
from time import sleep


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
