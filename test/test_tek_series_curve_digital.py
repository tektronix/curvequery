import pytest

FREQ_D0 = 625e3
MASK_D7_CLOCK = 0x80
MASK_D6_to_D0_DATA = 0x7F


@pytest.fixture(scope="session")
def curve_data_dch_counter(all_series_osc):
    if all_series_osc:
        all_series_osc.default_setup()
        all_series_osc.write("DISPLAY:GLOBAL:CH2:STATE 1")
        all_series_osc.write("DISPLAY:GLOBAL:CH1:STATE 0")
        all_series_osc.write("HORIZONTAL:SCALE 100e-6")
        all_series_osc.write("TRIGGER:A:EDGE:SOURCE LINE")
        for _ in all_series_osc.acquire(count=1):
            pass
    return all_series_osc.curve(decompose_dch=False)


@pytest.fixture(scope="session")
def curve_data_dch_counter_decompose(all_series_osc):
    if all_series_osc:
        all_series_osc.default_setup()
        all_series_osc.write("DISPLAY:GLOBAL:CH2:STATE 1")
        all_series_osc.write("DISPLAY:GLOBAL:CH1:STATE 0")
        all_series_osc.write("HORIZONTAL:SCALE 100e-6")
        all_series_osc.write("TRIGGER:A:EDGE:SOURCE LINE")
        for _ in all_series_osc.acquire(count=1):
            pass
    return all_series_osc.curve(decompose_dch=True)


def decode_digital_data_counter(waveform):
    """Decodes the waveform into a sequence of 7-bit values"""
    result = []
    for i, word in enumerate(waveform):
        try:
            next_word = waveform[i + 1]

        # No more words, so we are finished
        except IndexError:
            break

        # Bit 7 is the clock, bits 6:0 make up the data value
        # Capture the new 7-bit value on the falling edge of the clock
        if word & MASK_D7_CLOCK < next_word & MASK_D7_CLOCK:
            result.append(next_word & MASK_D6_to_D0_DATA)

    return result


def decode_digital_bitstream(waveform):
    """Extracts a bitstream from the waveform at the specified position"""
    result = []
    for i, bit in enumerate(waveform):
        try:
            next_bit = waveform[i + 1]

        # No more words, so we are finished
        except IndexError:
            break

        # Capture bit value changes
        if bit != next_bit:
            result.append(next_bit)

    return result


@pytest.mark.parametrize("target", ["CH2"])
def test_counter_check_sources(curve_data_dch_counter, target):
    """Verify the resulting waveforms contain the correct sources"""
    assert len(curve_data_dch_counter.sources) == 2
    assert target in curve_data_dch_counter.sources


def test_counter_incrementing_value(curve_data_dch_counter):
    """Verify the resulting waveforms capture a incrementing count"""
    wave_data = curve_data_dch_counter.data["CH2"].data
    counts = decode_digital_data_counter(wave_data)
    for i, code in enumerate(counts):
        try:
            next_code = counts[i + 1]
        except IndexError:
            break
        assert (code + 1) % (MASK_D6_to_D0_DATA + 1) == next_code


def test_counter_decomposed_frequency(curve_data_dch_counter_decompose):
    """Test relative frequencies of the decomposed bits"""
    for i in range(7):
        wave_data = curve_data_dch_counter_decompose.data[f"CH2_D{i}"].data
        wave_duration = curve_data_dch_counter_decompose.data[
            f"CH2_D{i}"
        ].x_scale.slope * len(wave_data)
        half_cycles_d0 = 2 * FREQ_D0 * wave_duration
        bitstream = decode_digital_bitstream(wave_data)
        expected = half_cycles_d0 / 2 ** i
        assert len(bitstream) * 1.1 > expected
        assert len(bitstream) * 0.9 < expected


@pytest.mark.parametrize("target", [f"CH2_D{i}" for i in range(8)])
def test_counter_check_sources(curve_data_dch_counter_decompose, target):
    """Verify the resulting waveforms contain the correct sources"""
    assert len(curve_data_dch_counter_decompose.sources) == 8
    assert target in curve_data_dch_counter_decompose.sources
