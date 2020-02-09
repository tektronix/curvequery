from .instrument import Instrument
from .instrument import instrument_factory
from .mso_tables import MSO_FEATURE_TABLES


class Oscilloscope(Instrument):
    tables = MSO_FEATURE_TABLES


def mso(resource_name, *, resource_manager=None, identity_override=None, timeout=5000):
    return instrument_factory(
        resource_name=resource_name,
        resource_manager=resource_manager,
        instrument_cls=Oscilloscope,
        identity_override=identity_override,
        timeout=timeout,
    )
