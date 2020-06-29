from .api_types import WaveformCollection
from .api_types import Waveform

FORMATTER_LOOKUP = {  # number of bytes, then signedness
    "1": {"RI": "b", "RP": "B"},
    "2": {"RI": "h", "RP": "H"},
    "4": {"RI": "i", "RP": "I", "FP": "f"},
    "8": {"RI": "q", "RP": "Q", "FP": "d"},
}


class Tek3k4kCurveFeat(FeatureBase):
    """Returns a WaveformCollection object containing waveform data available on the instrument"""

    def action_fcn(self, instr, *, verbose=False, **kwargs):
        """should store connection"""
        # self.data = []
        # self.active_source = ""
        result = WaveformCollection()
        instr.write("verbose OFF;header OFF")

        # iterate through all available sources
        for ch, ch_data, x_scale, y_scale in self._get_data(
            instr, self._list_sources(instr), **kwargs
        ):
            if verbose:
                print(ch)
            result.data[ch] = Waveform(ch_data, x_scale, y_scale)
        return result

    @staticmethod
    def _list_sources(connection):
        """Returns a list of channel name strings that we could query"""
        connection.write("verbose ON;header ON")
        result_string = connection.query("select?")
        connection.write("verbose OFF;header OFF")
        result_string = result_string.replace(":SELECT:", "", 1)
        result_string = result_string[0 : result_string.find(";CONTROL ")]
        # split on semicolons and ignore the second (on/off) part of each.
        # Remove busses because that's wrong
        ret_val = filter(
            lambda source: "BUS" not in source,
            [entry.split(" ")[0] for entry in result_string.split(";")],
        )
        return ret_val

    @staticmethod
    def _get_header(connection, source):
        """Returns the header as a dictionary so you can see configuration details"""
        connection.write("data:source " + source)
        connection.write("verbose ON;header ON")
        result_string = connection.query("wfmoutpre?")
        connection.write("verbose OFF;header OFF")
        result_string = result_string.replace(":WFMOUTPRE:", "", 1)
        # split on semicolons and break those into key/value pairs by splitting on space
        return {x.split(" ")[0]: x.split(" ")[1] for x in result_string.split(";")}

    def _get_data(self, connection, sources, lower_bound=None, upper_bound=None):
        """queries data and returns it along with the corresponding header"""
        for source in sources:
            connection.write("data:source " + source)
            if lower_bound is None:
                connection.write("data:start 1")
            else:
                connection.write("data:start " + str(lower_bound))
            length = connection.query("horizontal:recordlength?")
            if upper_bound is None:
                connection.write("data:stop " + length)
            else:
                connection.write("data:stop " + str(upper_bound))

            header = self._get_header(connection, source)
            if connection.query("select:" + source + "?")[0] == "0":
                # The channel we want to read is off. Just return empty data and the header
                return [], header
            y_mult = float(header["YMULT"])
            y_offset = float(header["YOFF"])
            y_zero = float(header["YZERO"])
            ret_val = []
            if header["ENCDG"] == "ASCII":
                read_string = connection.query("curve?")
                ret_val = [
                    ((float(entry) - y_offset) * y_mult) + y_zero
                    for entry in read_string.split(",")
                ]
            elif header["ENCDG"] == "BINARY":
                format_string = FORMATTER_LOOKUP[header["BYT_NR"]][header["BN_FMT"]]
                is_big_endian = header["BYT_OR"] == "MSB"
                ret_val = connection.query_binary_values(
                    "curv?", datatype=format_string, is_big_endian=is_big_endian
                )
                ret_val = [((entry - y_offset) * y_mult) + y_zero for entry in ret_val]
            yield (source, ret_val, None, None)
