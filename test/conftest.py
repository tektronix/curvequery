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


@pytest.fixture
def all_series_osc(resource_name):
    osc = get(resource_name)
    idn = osc.idn
    if (idn.company, idn.model) in SUPPORTED_ALL_SERIES_OSC:
        return osc
    else:
        pytest.skip("{} not a supported instrument".format(idn))
