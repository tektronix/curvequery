# CONTRIBUTING
Thank you for contributing to the curve query package.  In order to improve 
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

## Pre-Commit Hooks

This project uses the pre-commit package to implement pre-commit hooks that run black and flake8.
Either install the pre-commit hooks...

    ../curvequery> pre-commit install

...or run black and flake8 manually before commit changes.

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

## Development Environment

When contributing to the project, additional packages are required.
Also, a number of tests are available to verify functionality of the package module.
All tests are stored in the ./test/ directory.

__Setting Up the Development Environment__

The development specific packages can be setup in your virtual environment using the following command.

    ..\curvequery> python -m pip install .[dev]

__Running Tests__

The command to run the entire test suite is shown below:

    ..\curvequery> pytest --resource VISA::RESOURCE::NAME

Given the nature of this package module, the tests require an external hardware target.
The following hardware was used to develop the test suite:
* MSO 5 Series Oscilloscope with an AFG license
* 3 foot BNC Cable
* TLP058 Logic Analyzer Probe
* MDO Demo 1 Board (020-3087-00 demo kit)

If an AFG license is not available, and external 50 MHz sine wave generator can be used.
The generator settings are 1 volt peak-to-peak (into a 1 megaohm input) and zero volts offset.
When invoking the test suite, add the "--skip-license-checks" option.

If a MDO Demo 1 Board is not available, you can use another data source that can implement an 8-bit counter.
The least significant bit of the 8-bit counter must oscillate at a frequency of 1.25 MHz.
The digital bits must be connected to the TLP058 probe as shown below.
* CH2_D0 - Bit 1
* CH2_D1 - Bit 2
* CH2_D2 - Bit 3
* CH2_D3 - Bit 4
* CH2_D4 - Bit 5
* CH2_D5 - Bit 6
* CH2_D6 - Bit 7 (msb)
* CH2_D7 - Bit 0 (lsb)

__Hardware Setup for Tests__

On the oscilloscope, connect the AFG output to CH1 using the BNC cable. 
Connect the TLP058 to CH2 of the oscilloscope. 
The other end of the logic analyzer probe connects to the MDO Demo 1 Board.

## Contributor License Agreement
Contributions to this project must be accompanied by a Contributor License Agreement. You (or 
your employer) retain the copyright to your contribution; this simply gives us permission to use 
and redistribute your contributions as part of the project.

You generally only need to submit a CLA once, so if you've already submitted one (even if it was 
for a different project), you probably don't need to do it again.
