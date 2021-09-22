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
