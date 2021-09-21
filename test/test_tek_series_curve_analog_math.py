from math import sin
from math import pi
from math import fabs

import pytest
from pytest import approx

# Verticle Scale and Position setting combinations for the y_scale test
TEST_Y_SCALE_SETTINGS = [
    (i, j)
    for i in [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    for j in [-5, -2.5, -1, -0.5, 0, 1, 2.5, 5]
]

# Horizontal Scale and Position settings for the x_scale_test
TEST_X_SETTINGS = [(i, j) for i in [1e-6, 2e-6, 1e-3] for j in [0, 1, 50, 51, 99, 100]]


@pytest.fixture(scope="session")
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
        for _ in all_series_osc_with_afg.acquire(count=1):
            pass
    return all_series_osc_with_afg.curve(verbose=True)


@pytest.mark.parametrize("target", ["CH1", "MATH1"])
def test_source(curve_data_afg_50mhz_ch1_math1, target):
    """Verify the result waveform collection includes the expected sources"""
    assert len(curve_data_afg_50mhz_ch1_math1.sources) == 2
    assert target in curve_data_afg_50mhz_ch1_math1.sources


def test_compare_ch1_math1(curve_data_afg_50mhz_ch1_math1):
    """Verify the sum of the two waveforms is approximately zero"""
    ch1 = curve_data_afg_50mhz_ch1_math1["CH1"].data
    math1 = curve_data_afg_50mhz_ch1_math1["MATH1"].data
    for i in (a + b for a, b in zip(ch1, math1)):
        assert i == approx(0, abs=1e-3)


@pytest.mark.parametrize("target", ["CH1", "MATH1"])
def test_amplitude(curve_data_afg_50mhz_ch1_math1, target):
    """Verify the resulting waveforms have an amplitude greater than 400 mV"""
    actual = curve_data_afg_50mhz_ch1_math1[target].data
    assert max(actual) - min(actual) > 0.4


@pytest.mark.parametrize("target, scale", [("CH1", 0.25), ("MATH1", -0.25)])
def test_sine_wave(curve_data_afg_50mhz_ch1_math1, target, scale):
    """Verify the resulting waveforms contain 50 MHz waveforms"""
    actual = curve_data_afg_50mhz_ch1_math1[target].data
    step_size = 4 * pi / len(actual)
    expected = [scale * sin(step_size * i) for i in range(len(actual))]
    for i in (a - b for a, b in zip(actual, expected)):
        assert i == approx(0, abs=fabs(scale / 10))


@pytest.mark.parametrize("verticle_scale, position", TEST_Y_SCALE_SETTINGS)
def test_y_scale(all_series_osc, verticle_scale, position):
    if all_series_osc:
        all_series_osc.default_setup()
        all_series_osc.write(f"CH1:SCALE {verticle_scale}")
        all_series_osc.write(f"CH1:POSITION {position}")
        all_series_osc.write("HORIZONTAL:MODE MANUAL")
        all_series_osc.write("HORIZONTAL:MODE:RECORDLENGTH 1000")
        all_series_osc.write("TRIGGER:A:EDGE:SOURCE LINE")
        for _ in all_series_osc.acquire(count=1):
            actual = all_series_osc.curve()["CH1"].y_scale
            expected_top = verticle_scale * (5 - position)
            expected_bottom = verticle_scale * (-5 - position)
            assert actual.top == expected_top
            assert actual.bottom == expected_bottom


@pytest.mark.parametrize("horizontal_scale, horizontal_position", TEST_X_SETTINGS)
def test_x_scale(all_series_osc, horizontal_scale, horizontal_position):
    if all_series_osc:
        all_series_osc.default_setup()
        all_series_osc.write(f"HORIZONTAL:SCALE {horizontal_scale}")
        all_series_osc.write(f"HORIZONTAL:POSITION {horizontal_position}")
        all_series_osc.write("TRIGGER:A:EDGE:SOURCE LINE")
        for _ in all_series_osc.acquire(count=1):
            wave = all_series_osc.curve()["CH1"]
            num_samples = len(wave.data)
            actual = wave.x_scale
            expected_slope = 10 * horizontal_scale / num_samples
            expected_offset = -10 * horizontal_scale * horizontal_position / 100
            print(horizontal_scale, horizontal_position)
            assert actual.slope == approx(expected_slope, rel=1e-3)
            assert actual.offset == approx(expected_offset, rel=1e-3, abs=1e-3)
