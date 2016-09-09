""" 
# guppi.py

A python file handler for guppi RAW files from the GBT.

The guppi raw format consists of a FITS-like header, followed by a block of data,
and repeated over and over until the end of the file.
"""

import numpy as np
import os
import time


class EndOfFileError(Exception):
    pass


class GuppiRaw(object):
    """ Python class for reading Guppi raw files

    Args:
        filename (str): name of the .raw file to open

    Optional args:
        n_blocks (int): if number of blocks to read is known, set it here.
                        This saves seeking through the file to check how many
                        integrations there are in the file.
    """

    def __init__(self, filename, n_blocks=None):
        self.filename = filename
        self.file_obj = open(filename, 'r')

        if not n_blocks:
            self.n_blocks = self.find_n_data_blocks()

        else:
            self.n_blocks = n_blocks

        self._d = np.zeros(1, dtype='float32')

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.file_obj.close()

    def __repr__(self):
        return "<GuppiRaw file handler for %s>" % self.filename

    def read_header(self):
        """ Read next header (multiple headers in file)

        Returns:
            (header, data_idx) - a dictionary of keyword:value header data and
            also the byte index of where the corresponding data block resides.
        """
        start_idx = self.file_obj.tell()

        try:
            header_dict = {}
            keep_reading = True
            while keep_reading:
                line = self.file_obj.read(80)
                # print line
                if 'END     ' in line:
                    keep_reading = False
                    break
                else:
                    key, val = line.split('=')
                    key, val = key.strip(), val.strip()

                    if "'" in val:
                        # Items in quotes are strings
                        val = val.strip("'").strip()
                    elif "." in val:
                        # Items with periods are floats (if not a string)
                        val = float(val)
                    else:
                        # Otherwise it's an integer
                        val = int(val)

                header_dict[key] = val
        except ValueError:
            raise EndOfFileError

        data_idx = self.file_obj.tell()
        self.file_obj.seek(start_idx)
        return header_dict, data_idx

    def read_first_header(self):
        """ Read first header in file

        Returns:
            header (dict): keyword:value pairs of header metadata
        """
        self.file_obj.seek(0)
        header_dict, pos = self.read_header()
        self.file_obj.seek(0)
        return header_dict

    def read_next_data_block(self):
        """ Read the next block of data and its header

        Returns: (header, data)
            header (dict): dictionary of header metadata
            data (np.array): Numpy array of data, converted into to complex64.
        """
        header, data_idx = self.read_header()
        self.file_obj.seek(data_idx)

        # Read data and reshape
        d = np.fromfile(self.file_obj, count=header['BLOCSIZE'], dtype='int8')
        n_chan = header['OBSNCHAN']
        n_pol = header['NPOL']
        n_samples = header['BLOCSIZE'] / n_chan / n_pol

        d = d.reshape((n_chan, n_samples, n_pol))  # Real, imag

        if self._d.shape != d.shape:
            self._d = np.zeros(d.shape, dtype='float32')

        self._d[:] = d

        return header, self._d.view('complex64')

    def find_n_data_blocks(self):
        """ Seek through the file to find how many data blocks there are in the file

        Returns:
            n_blocks (int): number of data blocks in the file
        """
        self.file_obj.seek(0)
        header0, data_idx0 = self.read_header()

        self.file_obj.seek(data_idx0)
        self.file_obj.seek(header0['BLOCSIZE'], 1)
        n_blocks = 1
        end_found = False
        while not end_found:
            try:
                header, data_idx = self.read_header()
                self.file_obj.seek(data_idx)
                self.file_obj.seek(header['BLOCSIZE'], 1)
                n_blocks += 1
            except EndOfFileError:
                end_found = True
                break

        self.file_obj.seek(0)
        return n_blocks

    def reset_index(self):
        """ Return file_obj seek to start of file """
        self.file_obj.seek(0)
