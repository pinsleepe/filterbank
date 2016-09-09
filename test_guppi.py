from guppi import *
from pprint import pprint


def test_guppi():
    filename = 'blc1_guppi_57388_HIP113357_0010.0002.raw'

    guppi = GuppiRaw(filename)

    print guppi

    header = guppi.read_first_header()

    pprint(header)

    guppi.read_header()
    guppi.find_n_data_blocks()
    header, idx = guppi.read_header()
    header, data = guppi.read_next_data_block()
    header, data = guppi.read_next_data_block()
    header, data = guppi.read_next_data_block()
    guppi.reset_index()


if __name__ == "__main__":
    test_guppi()
