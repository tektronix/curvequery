def test_default_setup_available(all_series_osc):
    if all_series_osc:
        assert "default_setup" in all_series_osc.features


def test_default_setup_returns_none(all_series_osc):
    if all_series_osc:
        assert all_series_osc.default_setup() is None


def test_default_setup_enables_ch1_only(all_series_osc):
    if all_series_osc:
        all_series_osc.write("DISPLAY:GLOBAL:CH2:STATE ON")
        all_series_osc.default_setup()
        assert all_series_osc.curve().sources == ["CH1"]
