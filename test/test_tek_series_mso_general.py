import pytest

# noinspection PyProtectedMember
from curvequery._tek_series_mso import get_event_queue

INVALID_COMMAND = "INVALID:COMMAND"


def test_get_event_queue_return_type(all_series_osc):
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
    if all_series_osc:
        all_series_osc.default_setup()
        with all_series_osc.rsrc_mgr.open_resource(all_series_osc.rsrc_name) as inst:
            get_event_queue(inst, verbose=True)
            all_series_osc.write(command)
            for i, e in enumerate(get_event_queue(inst)):
                if i == 0:
                    assert expected in e
