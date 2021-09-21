import pytest
from visadore import get

SUPPORTED_ALL_SERIES_OSC = [
    ("TEKTRONIX", "MSO54"),
    ("TEKTRONIX", "MSO56"),
    ("TEKTRONIX", "MSO58"),
]


def has_afg_license(instr):
    """Returns True if the first license includes an AFG license"""
    return "AFG" in instr.query("LIC:ITEM? 0").strip().split('"')[3].split(",")


def pytest_addoption(parser):
    parser.addoption(
        "--resource",
        action="append",
        default=[],
        help="List of resource names to pass to test functions",
    )
    parser.addoption(
        "--skip-license-checks",
        action="store_true",
        help="Skip all license checks",
    )


def pytest_generate_tests(metafunc):
    if "resource_name" in metafunc.fixturenames:
        metafunc.parametrize(
            "resource_name", metafunc.config.option.resource, scope="session"
        )
    if "skip_license_checks" in metafunc.fixturenames:
        metafunc.parametrize(
            "skip_license_checks",
            [metafunc.config.option.skip_license_checks],
            scope="session",
        )


def osc_fixture(supported_instrument_list, license_check_funcs):
    def osc_with_supported_list_and_license(_):
        @pytest.fixture(scope="session")
        def fixture(resource_name, skip_license_checks):
            """A fixture that returns an instrument object if the instrument is in the list
            of supported instruments and the required licenses.  Otherwise, the fixture will
            skip the test."""
            skip = False
            osc = get(resource_name)
            idn = osc.idn
            if (idn.company, idn.model) in supported_instrument_list:
                if not skip_license_checks:
                    for lic in license_check_funcs:
                        if not lic(osc):
                            skip = True
            else:
                skip = True
            if skip:
                pytest.skip("{} not a supported instrument".format(idn))
            else:
                return osc

        return fixture

    return osc_with_supported_list_and_license


@osc_fixture(SUPPORTED_ALL_SERIES_OSC, [])
def all_series_osc(resource_name, skip_license_checks):
    pass


@osc_fixture(SUPPORTED_ALL_SERIES_OSC, [has_afg_license])
def all_series_osc_with_afg(resource_name, skip_license_checks):
    pass
