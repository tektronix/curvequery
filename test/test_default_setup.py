def test_default_setup_available(all_series_osc):
    if all_series_osc:
        assert "default_setup" in all_series_osc.features


def test_default_setup_returns_none(all_series_osc):
    if all_series_osc:
        assert all_series_osc.default_setup() is None
