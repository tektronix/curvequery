from .api_types import Identity
from .api_types import CompatibilityError
from .helper_methods import _ident
from .helper_methods import _get_handler


class Instrument:
    def __init__(self, resource_name, resource_manager, identity, timeout):
        self.rsrc_name = resource_name
        self.rsrc_mgr = resource_manager
        self.timeout = timeout
        if isinstance(identity, Identity):
            self._identity = identity
        else:
            self._identity = _ident(
                resource_name=resource_name,
                resource_manager=resource_manager,
                timeout=timeout,
            )
        self._features = []

    @property
    def idn(self):
        """A description of the instrument"""
        return self._identity

    @property
    def features(self):
        """A list of supported instrument features"""
        return self._features

    @features.setter
    def features(self, value):
        name, func = value
        setattr(self, name, func)
        self._features.append(name)

    def write(self, *args, **kwargs):
        """Writes a command to the instrument"""
        with self.rsrc_mgr.open_resource(self.rsrc_name) as instr:
            instr.timeout = self.timeout
            instr.write(*args, **kwargs)

    def query(self, *args, **kwargs):
        """Retrieves data from the instrument"""
        with self.rsrc_mgr.open_resource(self.rsrc_name) as instr:
            instr.timeout = self.timeout
            return instr.query(*args, **kwargs)


def instrument_factory(
    *, resource_name, resource_manager, instrument_cls, identity_override, timeout
):
    """
    Dynamically constructs and returns an instrument object associated with the given
    VISA resource name.

        resource_name (str): A string describing the name of a VISA resource.
        resource_manager (obj or None): An optional pyvisa resource manager object.
        instrument_cls (class): The desired subclass of the Instrument class.
        identity_override (obj or None): An optional Identity named tuple used to
            override the automatic instrument identity detection.
    """

    # automatically create a pyvisa resource manager object, unless one was provided.
    if not resource_manager:
        import pyvisa

        resource_manager = pyvisa.ResourceManager()

    # create a new empty instrument object for the target instrument
    inst_obj = instrument_cls(
        resource_name, resource_manager, identity=identity_override, timeout=timeout
    )
    idn = inst_obj.idn

    # open a pyvisa resource connection to the target instrument attaching features
    # to the instrument object. This only used for better error reporting if an
    # CompatibilityError exception is raised in the _get_handler() function.
    with resource_manager.open_resource(resource_name) as connection:
        connection.timeout = timeout

        # Find the features associated with the target instrument using the feature
        # tables assigned to the specified Instrument object subclass
        for feature_table in inst_obj.tables:

            # for each feature table, attach relevant features to the instrument object
            try:
                handler = _get_handler(connection, idn, feature_table, inst_obj)
                inst_obj.features = (feature_table.name, handler)
            except CompatibilityError:
                pass

    # The pyvisa resource connection is now closed
    return inst_obj
