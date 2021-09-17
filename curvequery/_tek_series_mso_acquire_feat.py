from time import time
from time import sleep

from visadore import base

from .api_types import SequenceTimeout


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
