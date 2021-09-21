import pytest

# noinspection PyProtectedMember
from curvequery._tek_series_mso import get_event_queue

INVALID_COMMAND = "INVALID:COMMAND"


def test_get_event_queue_return_type(all_series_osc):
    """Verify the event queue returns a list of strings"""
    if all_series_osc:
        all_series_osc.default_setup()
        with all_series_osc.rsrc_mgr.open_resource(all_series_osc.rsrc_name) as inst:
            get_event_queue(inst, verbose=True)
            all_series_osc.write(INVALID_COMMAND)
            events = get_event_queue(inst)
            assert isinstance(events, list)
            for e in events:
                assert isinstance(e, str)


@pytest.mark.parametrize(
    "command, expected",
    [("", "No events to report - queue empty"), (INVALID_COMMAND, INVALID_COMMAND)],
)
def test_get_event_queue_return_value(all_series_osc, command, expected):
    """Check for expected return values"""
    if all_series_osc:
        all_series_osc.default_setup()
        with all_series_osc.rsrc_mgr.open_resource(all_series_osc.rsrc_name) as inst:
            get_event_queue(inst, verbose=True)
            all_series_osc.write(command)
            for i, e in enumerate(get_event_queue(inst)):
                if i == 0:
                    assert expected in e


def test_setup_getter_type(all_series_osc):
    """Verify that the setup getter returns a string"""
    if all_series_osc:
        assert isinstance(all_series_osc.setup(), str)


def test_setup_getter_starts_with_star_rst(all_series_osc):
    """Verify that the setup getter value starts with the expected value"""
    if all_series_osc:
        settings = all_series_osc.setup()
        assert settings.startswith("*RST;:")


def test_default_setup_turns_off_ch2(all_series_osc):
    """Verify that default setup turns off CH2"""
    if all_series_osc:
        all_series_osc.write(":DISPLAY:GLOBAL:CH2:STATE 1")
        all_series_osc.default_setup()
        actual = all_series_osc.setup().find(":DISPLAY:GLOBAL:CH2:STATE 0")
        assert actual != -1


def test_setup_setter_restores_ch2(all_series_osc):
    """Verify that the setup setter can restore CH2"""
    if all_series_osc:
        all_series_osc.write(":DISPLAY:GLOBAL:CH2:STATE 1")
        settings = all_series_osc.setup()
        all_series_osc.default_setup()
        all_series_osc.setup(settings)
        actual = all_series_osc.query(":DISPLAY:GLOBAL:CH2:STATE?").strip()
        assert actual == "1"
