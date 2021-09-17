from math import sin
from math import pi
from math import fabs

import pytest
from pytest import approx


@pytest.fixture(scope="module")
def curve_data_afg_50mhz_ch1_math1(all_series_osc_with_afg):
    if all_series_osc_with_afg:
        all_series_osc_with_afg.default_setup()
        all_series_osc_with_afg.write("HORIZONTAL:SCALE 4e-9")
        all_series_osc_with_afg.write("AFG:OUTPUT:STATE ON")
        all_series_osc_with_afg.write("AFG:FREQ 50e6")
        all_series_osc_with_afg.write("MATH:ADDNEW")
        all_series_osc_with_afg.write("MATH:MATH1:TYPE ADVANCED")
        all_series_osc_with_afg.write("MATH:MATH1:DEFINE '-CH1'")
        all_series_osc_with_afg.timeout = 5000
        all_series_osc_with_afg.query("*OPC?")
        all_series_osc_with_afg.write(
            "DISPLAY:WAVEVIEW1:MATH:MATH1:VERTICAL:SCALE 100e-3"
        )
    return all_series_osc_with_afg.curve()


@pytest.mark.parametrize("target", ["CH1", "MATH1"])
def test_source(curve_data_afg_50mhz_ch1_math1, target):
    assert target in curve_data_afg_50mhz_ch1_math1.sources


def test_compare_ch1_math1(curve_data_afg_50mhz_ch1_math1):
    ch1 = curve_data_afg_50mhz_ch1_math1["CH1"].data
    math1 = curve_data_afg_50mhz_ch1_math1["MATH1"].data
    for i in (a + b for a, b in zip(ch1, math1)):
        assert i == approx(0, abs=1e-3)


@pytest.mark.parametrize("target", ["CH1", "MATH1"])
def test_amplitude(curve_data_afg_50mhz_ch1_math1, target):
    actual = curve_data_afg_50mhz_ch1_math1[target].data
    assert max(actual) - min(actual) > 0.4


@pytest.mark.parametrize("target, scale", [("CH1", 0.25), ("MATH1", -0.25)])
def test_sine_wave(curve_data_afg_50mhz_ch1_math1, target, scale):
    actual = curve_data_afg_50mhz_ch1_math1[target].data
    step_size = 4 * pi / len(actual)
    expected = [scale * sin(step_size * i) for i in range(len(actual))]
    for i in (a - b for a, b in zip(actual, expected)):
        assert i == approx(0, abs=fabs(scale / 10))
