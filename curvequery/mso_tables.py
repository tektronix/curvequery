from . import _tek_3k_4k_mso
from . import _tek_series_mso
from .api_types import FeatureTable

# A table that maps model numbers to the appropriate curve query class
CURVE_TABLE = FeatureTable(name="curve", entries={
    ("TEKTRONIX", "MDO3104"): _tek_3k_4k_mso.Tek3k4kCurveFeat,
    ("TEKTRONIX", "MDO3102"): _tek_3k_4k_mso.Tek3k4kCurveFeat,
    ("TEKTRONIX", "MDO3054"): _tek_3k_4k_mso.Tek3k4kCurveFeat,
    ("TEKTRONIX", "MDO3052"): _tek_3k_4k_mso.Tek3k4kCurveFeat,
    ("TEKTRONIX", "MSO54"): _tek_series_mso.TekSeriesCurveFeat,
    ("TEKTRONIX", "MSO56"): _tek_series_mso.TekSeriesCurveFeat,
    ("TEKTRONIX", "MSO58"): _tek_series_mso.TekSeriesCurveFeat,
    ("TEKTRONIX", "MSO44"): _tek_series_mso.TekSeriesCurveFeat,
    ("TEKTRONIX", "MSO46"): _tek_series_mso.TekSeriesCurveFeat,
})

# A table that maps model numbers to the appropriate default setup class
DEFAULT_TABLE = FeatureTable(name="default_setup", entries={
    ("TEKTRONIX", "MSO54"): _tek_series_mso.TekSeriesDefaultFeat,
    ("TEKTRONIX", "MSO56"): _tek_series_mso.TekSeriesDefaultFeat,
    ("TEKTRONIX", "MSO58"): _tek_series_mso.TekSeriesDefaultFeat,
    ("TEKTRONIX", "MSO44"): _tek_series_mso.TekSeriesDefaultFeat,
    ("TEKTRONIX", "MSO46"): _tek_series_mso.TekSeriesDefaultFeat,
})

# A table that maps model numbers to the appropriate setup read and write feature
SETUP_TABLE = FeatureTable(name="setup", entries={
    ("TEKTRONIX", "MSO54"): _tek_series_mso.TekSeriesSetupFeat,
    ("TEKTRONIX", "MSO56"): _tek_series_mso.TekSeriesSetupFeat,
    ("TEKTRONIX", "MSO58"): _tek_series_mso.TekSeriesSetupFeat,
    ("TEKTRONIX", "MSO44"): _tek_series_mso.TekSeriesSetupFeat,
    ("TEKTRONIX", "MSO46"): _tek_series_mso.TekSeriesSetupFeat,
})

ACQ_TABLE = FeatureTable(name="acquire", entries={
    ("TEKTRONIX", "MSO54"): _tek_series_mso.TekSeriesAcquireFeat,
    ("TEKTRONIX", "MSO56"): _tek_series_mso.TekSeriesAcquireFeat,
    ("TEKTRONIX", "MSO58"): _tek_series_mso.TekSeriesAcquireFeat,
    ("TEKTRONIX", "MSO44"): _tek_series_mso.TekSeriesAcquireFeat,
    ("TEKTRONIX", "MSO46"): _tek_series_mso.TekSeriesAcquireFeat,
})

MSO_FEATURE_TABLES = [CURVE_TABLE, DEFAULT_TABLE, SETUP_TABLE, ACQ_TABLE]
