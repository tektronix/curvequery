
# Curve Query

The easy way to download curves from an oscilloscope.

<p align="center">
<a href="https://www.python.org"><img alt="Python: 3.7+" src="https://img.shields.io/badge/Python-3.7+-Green.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://www.codefactor.io/repository/github/tektronix/curvequery"><img src="https://www.codefactor.io/repository/github/tektronix/curvequery/badge" alt="CodeFactor" /></a>
<a href="https://lgtm.com/projects/g/tektronix/curvequery/alerts/"><img alt="Total alerts" src="https://img.shields.io/lgtm/alerts/g/tektronix/curvequery.svg?logo=lgtm&logoWidth=18"/></a>
</p>

## Description

The curvequery package is a collection of tools to simplify downloading waveform data from an oscilloscope.
It is a layer of functionality built on top of the PyVISA package and the Visadore plugin manager.

Maintainer: [Chad Stryker](https://github.com/cwstryker)

## Usage

Creating a connection to the mixed signal oscilloscope is easy.
Invoke the Visadore plugin manager to create the oscilloscope interface object.

    >>> from visadore import get
    >>> oscope = get("TCPIP::192.168.1.10::INSTR")
    TEKTRONIX,MSO58,Q200011,CF:91.1CT FV:1.12.5.5575
    
### High Level API

The Oscilloscope object provides a high-level API that simplifies getting data from the oscilloscope.

    >>> print(oscope.idn)
    Identity(company='TEKTRONIX', model='MSO58', serial='Q200011', config='CF:91.1CT FV:1.12.5.5575')
    
    >>> wave_collection = oscope.curve()    # download waveform data from the instrument
    Downloading:  20%|██        | 65.0M/320M [00:05<00:19, 12.9MB/s]

    >>> oscope.default_setup()              # restore the instrument's default settings

The waveform collection object returned by the curve() method contains the data downloaded from the instrument.

    >>> wave_collection.sources
    ['CH1', 'CH2', 'CH8_D0', 'CH8_D1', 'CH8_D2', 'CH8_D3', 'CH8_D4', 'CH8_D5', 'CH8_D6', 'CH8_D7', 'MATH1']
    
    >>> wave_collection['CH1'].data
    [-0.030000000000000027, -0.030000000000000027, ... ]
    
In addition, the horizontal scale (x axis) and vertical scale (y axis) is also provided.
    
    >>> wave_collection['CH1'].y_scale
    YScale(top=3.51, bottom=-1.49)
    
    >>> wave_collection['CH1'].x_scale
    XScale(slope=1.6e-10, offset=-1.999845e-06, unit='s')

### Low Level API

The oscilloscope object also allows for low-level interaction with the oscilloscope.

    >>> oscope.write("*RST")
    >>> print(oscope.query("*IDN?"))
    "TEKTRONIX,MSO58,Q200011,CF:91.1CT FV:1.12.5.5575"
    
A pyvisa Resource Manager object can be explicitly referenced when creating an oscilloscope object.

    >>> import pyvisa
    >>> rm = pyvisa.ResoureManager()
    >>> oscope = mso("TCPIP::192.168.1.12::INSTR", resource_manager=rm)
    
### Future Feature Enhancements

Other potential high level features are possible...

    >>> id = oscope.add("meas", source="ch1", measurement="risetime")  # potential future feature
    >>> measurements = oscope.meas()                                   # potential future feature

## Progress Bar

When using the curve feature, the progress bar is enabled by default, and it displays the number of bytes 
associated with the curve query.

    Downloading:  20%|██        | 65.0M/320M [00:05<00:19, 12.9MB/s]

## Requirements

The following Python elements are required. 

- Python: 
    - 3.7+
- 3rd Party Modules:
    - pyvisa == 1.11.3   Python VISA interface library
    - visadore           Visadore plugin manager
    - tqdm >= 4.62.2     Progress bar

To improve the progress bar support, the curve query package monkey patches pyvisa at runtime; therefore, 
a specific version of pyvisa (shown above) must be used. 
The installer will ensure that the required version of pyvisa is used.

## Installation

The curve query package can be installed from source.

#### Installation from Source

To install curve query, first clone the source repository from GitHub.
Using pip, install the package module directly from a clone of the git repository in either the Windows 
and Linux environments.

    ../curvequery> python -m pip install .

Alternatively, create a wheel file using pip, and use the wheel file to install curve query on a different 
Windows or Linux computer.

    ../curvequery> python -m pip wheel .

Using either of these methods, all 3rd-party package modules will automatically be downloaded from PyPI 
and installed.

## Source

The source code for curve query is available on GitHub.
