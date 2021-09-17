from visadore import base
import pyvisa

from ._tek_series_mso import get_event_queue


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
