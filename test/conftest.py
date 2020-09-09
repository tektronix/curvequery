import pytest
from visadore import get

SUPPORTED_ALL_SERIES_OSC = [
    ("TEKTRONIX", "MSO54"),
    ("TEKTRONIX", "MSO56"),
    ("TEKTRONIX", "MSO58"),
    ("TEKTRONIX", "MSO44"),
    ("TEKTRONIX", "MSO46"),
]


def pytest_addoption(parser):
    parser.addoption(
        "--resource",
        action="append",
        default=[],
        help="list of resource names to pass to test functions",
    )


def pytest_generate_tests(metafunc):
    if "resource_name" in metafunc.fixturenames:
        metafunc.parametrize("resource_name", metafunc.config.option.resource)


def osc_fixture(supported_instrument_list):
    def osc_with_supported_list(fn):
        @pytest.fixture
        def fixture(resource_name):
            """A fixture that returns an instrument object if the instrument is in the list
            of supported instruments.  Otherwise, the fixture will skip the test."""
            osc = get(resource_name)
            idn = osc.idn
            if (idn.company, idn.model) in supported_instrument_list:
                return osc
            else:
                pytest.skip("{} not a supported instrument".format(idn))

        return fixture

    return osc_with_supported_list


@osc_fixture(SUPPORTED_ALL_SERIES_OSC)
def all_series_osc(resource_name):
    pass
