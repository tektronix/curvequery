from .api_types import Identity
from .api_types import CompatibilityError


def _identity_parser(idn_str):
    idn = tuple(idn_str.split(","))
    return Identity(*idn)


def _ident(resource_name, resource_manager):

    # If not provided, create a pyvisa ResourceManager object
    if not resource_manager:
        import pyvisa

        resource_manager = pyvisa.ResourceManager()

    # open a connection and fetch the instrument IDN string
    with resource_manager.open_resource(resource_name) as inst:
        inst.clear()
        idn = inst.query("*IDN?").strip()
    return _identity_parser(idn)


def _get_handler(connection, idn, table, instr_obj):
    """
    Returns an instantiated feature object from the given feature table and instrument
    ID.

    Parameters:
        connection (obj): An open pyvisa resource handle for the instrument
        idn (obj): An Identity named tuple for the instrument
        table (obj): A FeatureTable named tuple for the feature
        instr_obj (obj): A reference to the parent instrument object associated with
            the instrument
    """

    try:
        return table.entries[(idn.company, idn.model)](instr_obj)
    except KeyError:
        raise CompatibilityError(
            "Instrument {} {} does not a support {}".format(
                idn.company, idn.model, table.name
            ),
            inst=connection,
        )


def _disabled_pbar(iterable, *args, **kwargs):
    for i in iterable:
        yield i
