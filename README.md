
# Curve Query

The easy way to download curves from an oscilloscope.

<p align="center">
<a href="https://www.python.org"><img alt="Python: 3.4+" src="https://img.shields.io/badge/Python-3.4+-Green.svg"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://www.codefactor.io/repository/github/tektronix/curvequery"><img src="https://www.codefactor.io/repository/github/tektronix/curvequery/badge" alt="CodeFactor" /></a>
<a href="https://lgtm.com/projects/g/tektronix/curvequery/alerts/"><img alt="Total alerts" src="https://img.shields.io/lgtm/alerts/g/tektronix/curvequery.svg?logo=lgtm&logoWidth=18"/></a>
<a href="https://github.com/tektronix"><img alt="Tektronix" src="https://tektronix.github.io/media/TEK-opensource_badge.svg"></a> 
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
    Downloading: 100%|█████████████████████████████████| 11/11 [00:00<00:00, 34.05Wfm/s]

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

## Requirements

- Python: 
    - 3.5+
- 3rd Party Modules:
    - pyvisa 1.9.1      Python VISA interface library
    - visadore          Visadore plugin manager

## Installation

The curvequery package can be installed from source.

#### Installation from Source

See the [Source section](#source-section) below for instructions on how to make a source distribution tarball.
Using pip, install the package module directly from a source distribution tarball in the Windows and Linux environments.
Using this method, all 3rd-party package modules will automatically be downloaded from PyPI and installed.

    $ pip install curvequery-2.0.tar.gz

## <a name="source-section"></a>Source

The source code for curvequery is available on GitHub.
