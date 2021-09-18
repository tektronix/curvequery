import pytest
from time import sleep


@pytest.fixture(scope="session")
def curve_data_dch_counter(all_series_osc):
    if all_series_osc:
        all_series_osc.default_setup()
        all_series_osc.write("DISPLAY:GLOBAL:CH2:STATE 1")
        all_series_osc.write("HORIZONTAL:SCALE 20e-6")
        all_series_osc.write("TRIGGER:A:EDGE:SOURCE LINE")
        for _ in all_series_osc.acquire(count=1):
            pass
    return all_series_osc.curve(decompose_dch=False)


@pytest.fixture(scope="session")
def curve_data_dch_counter_decompose(all_series_osc):
    if all_series_osc:
        all_series_osc.default_setup()
        all_series_osc.write("DISPLAY:GLOBAL:CH2:STATE 1")
        all_series_osc.write("HORIZONTAL:SCALE 20e-6")
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
        if word & 0x80 < next_word & 0x80:
            result.append(next_word & 0x7F)

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


@pytest.mark.parametrize("target", ["CH1", "CH2"])
def test_counter_check_sources(curve_data_dch_counter, target):
    """Verify the resulting waveforms contain the correct sources"""
    assert len(curve_data_dch_counter.sources) == 2
    assert target in curve_data_dch_counter.sources


def test_counter_incrementing_value(curve_data_dch_counter):
    """Verify the resulting waveforms capture a incrementing count"""
    wave_in = curve_data_dch_counter.data["CH2"].data
    counts = decode_digital_data_counter(wave_in)
    for i, code in enumerate(counts):
        try:
            next_code = counts[i + 1]
        except IndexError:
            break
        assert (code + 1) % 0x80 == next_code


def test_counter_decomposed_frequency(curve_data_dch_counter_decompose):
    """Test relative frequencies of the decomposed bits"""
    for i in range(7):
        wave_in = curve_data_dch_counter_decompose.data[f"CH2_D{i}"].data
        bitstream = decode_digital_bitstream(wave_in)
        expected = 250 / 2 ** i
        assert len(bitstream) + 2 > expected
        assert len(bitstream) - 2 < expected


@pytest.mark.parametrize("target", ["CH1"] + [f"CH2_D{i}" for i in range(8)])
def test_counter_check_sources(curve_data_dch_counter_decompose, target):
    """Verify the resulting waveforms contain the correct sources"""
    assert len(curve_data_dch_counter_decompose.sources) == 9
    assert target in curve_data_dch_counter_decompose.sources
