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

Features are organized into files where each file contains features compatible with a given 
instrument family or group of instrument families. 
Adding a new feature to an existing Instrument model (i.e. specific make / model) is fairly simple.
The visadore plugin manager handles all of the complexity associated with the dynamic construction 
of the instrument object.
Visadore uses setuptools entry points defined in the setup.cfg file to map the appropriate features
to a specific instrument base don that instrument's make and model information.
Visadore uses the *IDN? query to determine the make and model of the instrument.

Adding a new feature requires the following steps:
<ol>
    <li>Create a new feature class inheriting from the FeatureBase abstract base class.</li>
    <li>Register the new feature / instrument mapping in setup.cfg.</li>
</ol>

__Creating a FeatureBase Subclass__

The following example, shows how to add a new feature to read the setup configuration 
from a Tektronix 4 Series oscilloscope.

Create a new FeatureBase subclass in the _tek_series_mso.py file.
This where all of the specific functionality associated with the feature is defined.

    class TekSeriesSetupFeat(base.FeatureBase):
        def feature(self, settings=None):
            """
            Sets or gets the setup configuration from the instrument as a string.
            """
            with self.resource_manager.open_resource(self.resource_name) as inst:
                inst.timeout = 20000    # this can take a while, so use a 20 second timeout
                if settings:
                    inst.write("{:s}".format(settings))
                    inst.query("*OPC?")
                else:
                    return inst.query("SET?")

In this simple example, the new subclass is named TekSeriesSetupFeat.
The feature functionality is implemented in the feature() method.  
The feature() method must always be defined by the subclass.
Subsequent positional and keyword arguments are optional and specific to the given 
action function. 
The feature() method in this example queries and returns the setup configuration string 
from the instrument.

__Talking to the Instrument__

A VISA connection to the instrument must be created by the Feature() method to communicate 
with the instrument.
the connection must also be closed by the feature code.
Typically, the __with__ statement is used to do this, and it looks like the following:

    with self.resource_manager.open_resource(self.resource_name) as inst:
        # talk to the instrument (inst)

__Registering the Feature__

The new FeatureBase subclass needs to be registered in the setuptools entry points so 
that visadore can find it.
The entry point is defined in the setup.cfg file.
Here is the entry point definition for the new feature.

    visadore.tektronix.mso46 =
        ...
        setup = curvequery._tek_series_mso:TekSeriesSetupFeat

This definition maps the new TekSeriesSetupFeat subclass to instruments that report their 
make as "Tektronix" and their model as "MSO46."
The setup.cfg contains many such definitions.

__Test the Feature__

Finally, test your new feature.

    >>> from visadore import get
    >>> oscope = get("TCPIP::192.168.1.10::INSTR")
    TEKTRONIX,MSO46,DP100005,CF:91.1CT FV:1.18.0.6630
    >>> oscope.setup()
    '*RST;:PARAMBATCHING 0;:TRIGGER:AUXLEVEL 0.0E+0;:CH1:BANDWIDTH 1.0000E+9;:CH... '

## Contributor License Agreement
Contributions to this project must be accompanied by a Contributor License Agreement. You (or 
your employer) retain the copyright to your contribution; this simply gives us permission to use 
and redistribute your contributions as part of the project.

You generally only need to submit a CLA once, so if you've already submitted one (even if it was 
for a different project), you probably don't need to do it again.
