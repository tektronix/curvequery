from collections import namedtuple

Identity = namedtuple("Identity", "company, model, serial, config")
XScale = namedtuple("XScale", "slope, offset, unit")
YScale = namedtuple("YScale", "top, bottom")
FeatureTable = namedtuple("FeatureTable", "name, entries")
Waveform = namedtuple("Waveform", "data, x_scale, y_scale")


class VisaResourceError(Exception):
    def __init__(self, msg, *, inst=None):
        if inst:
            super_msg = "{} ({})".format(msg, inst)
        else:
            super_msg = msg
        super().__init__(super_msg)


class CompatibilityError(VisaResourceError):
    pass


class CurveQueryError(VisaResourceError):
    pass


class SequenceTimeout(Exception):
    """Raised when an acquisition does not finish in the specified time out period"""


class WaveformCollection:
    def __init__(self):
        self.idn = None
        self.data = {}

    @property
    def sources(self):
        return list(self.data.keys())

    def __getitem__(self, item):
        return self.data[item]

    def __len__(self):
        return len(self.data.keys())


class FeatureBase:
    """
    This parent class provides the common framework needed to implement an
    instrument feature subclass.

    Attributes:
        parent_instr_obj (obj): A reference to the parent instrument object
            associated with the feature.
    """

    def __init__(self, parent_instr_obj):
        """
        This __init__ method should not be subclassed.

        Parameters:
            parent_instr_obj (obj): A reference to the parent instrument object
                associated with the feature.
        """

        self.parent_instr_obj = parent_instr_obj

    def __call__(self, *args, **kwargs):
        """
        This __call__method should not be subclassed. This method calls the action_fcn method.
        """

        with self.parent_instr_obj.rsrc_mgr.open_resource(
            self.parent_instr_obj.rsrc_name
        ) as instr:
            instr.timeout = self.parent_instr_obj.timeout
            return self.action_fcn(instr, *args, **kwargs)
