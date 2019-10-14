# CONTRIBUTING
Thank you for contributing to the curvequery package.  In order to improve 
readability, please review and adhere to the following guidelines when contributing 
to this project.

## Style Guide

This project follows the PEP 8 style guide which is used widely throughout the Python 
community. 
The Black code formatter is used to force conformance to the style guide.  
Specific exceptions to the PEP 8 guidelines are:
<ul>
    <li>The maximum line length is 88 characters.</li>
</ul>

## Naming Conventions

This project adheres to the naming conventions described in the Google Style Python 
Guide [Section 3.16](http://google.github.io/styleguide/pyguide.html#316-naming).  

## Adding New Features

### Adding a feature to an existing instrument type

Features are added to an Instrument object dynamically based the identity string (i.e. 
*IDN?) reported by the instrument. 
Adding a new feature to an existing Instrument subclass (i.e. specific make / model) 
is fairly simple.
The framework built into the curvequery package handles most of the complexity 
associated with dynamic feature assignment.

Adding a new feature requires the following steps:
<ol>
    <li>Create a new feature class inherting from the FeatureBase class.</li>
    <li>Register the new feature class by creating a new feature table.</li>
</ol>

__Creating a FeatureBase Subclass__

The following example, shows how to add a new feature to read the setup configuration 
from a Tektronix 4 Series oscilloscope.

First, create a new FeatureBase subclass to the _tek_series_mso.py file.
This where all of the specific functionality associated with the feature is defined.

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


__The Action Function__

In this simple example, the functionality is implemented in the static method 
_action_fcn().  
This is the action function.
The action function must always be defined by the subclass.
Subsequent positional and keyword arguments are optional and specific to the given 
action function. 
The action function in this example queries and returns the setup configuration string 
from the instrument.


__The Feature Tables__

The new FeatureBase subclass needs to be added to the mso_tables.py file.
Since we are adding a completely new feature that has not been implemented before, we 
need a add a new table.

    # A table that maps model numbers to the appropriate get setup class
    SETUP_TABLE = FeatureTable(name="setup", entries={
        ("TEKTRONIX", "MSO44"): _tek_series_mso.TekSeriesSetupFeat,
        ("TEKTRONIX", "MSO46"): _tek_series_mso.TekSeriesSetupFeat,
    })

The table is created using FeatureTable where the new feature is assigned to the name 
get_setup.

The new table also needs to be added to the list of tables in the same file.

    MSO_FEATURE_TABLES = [CURVE_TABLE, DEFAULT_TABLE, SETUP_TABLE]
    
Finally, test your new feature.

    >>> from curvequery import mso
    >>> oscope = mso("TCPIP::192.168.1.10::INSTR")
    TEKTRONIX,MSO46,DP100005,CF:91.1CT FV:1.18.0.6630
    >>> oscope.setup()
    '*RST;:PARAMBATCHING 0;:TRIGGER:AUXLEVEL 0.0E+0;:CH1:BANDWIDTH 1.0000E+9;:CH... '

__Action Functions that Implement Generators__

For action functions that implement generators, the pyvisa resource object cannot be 
used to access the instrument.
When the generator object is returned by the call to the action function, the pyvisa
resource object is automatically closed and can no longer be used to access the 
instrument.
Instead, generators should communicate with the instrument through the reference to the
Instrument sub-class object attached to the feature.
Calls to the write() and query() methods of the Instrument sub-class object will 
automatically create a new, temporary connection to the instrument.
See the example code fragment below.

    def action_fcn(self, _, *, sample_parameter=False):
        """
        Action Function
        """

        while True:

            # Is the instrument finished acquiring data?
            if self.parent_instr_obj.query("").strip() == "0":
                yield
