import os
import math
import numpy


def to_numpy(file_name):

    file_size = os.path.getsize(file_name)

    # file contains two bytes per elevation
    # with dim x dim elevations for a total of
    # dim x dim x 2 bytes = num elevations and file size
    # get the number of dimensions with the following
    dim = int(math.sqrt(file_size/2))

    # read the file into a numpy array
    # >i2 means signed 2 bytes big endian number
    # dim * dim is the number of numbers to read
    # reshape makes the dim * dim length array
    # into a dim x dim 2d array
    return (numpy.fromfile(file_name, numpy.dtype('>i2'), dim * dim).reshape(dim, dim), dim)
