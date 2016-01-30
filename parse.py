import os
import time
from cffi import FFI
ffi = FFI()

lib = ffi.dlopen("target/release/parser.dll")
ffi.cdef("void compute_file_crc(const char*);")

class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print('elapsed time: %f ms' % self.msecs)

# Note that this file is a bit small to test the performance of Rust
# on larger files, we see a much greater performance on the order of 
# 600+MB/s 
FILENAME = "test/2015-12-23-14-32-19.fit"

file_length = os.stat(FILENAME).st_size

with Timer() as t:
    lib.compute_file_crc(FILENAME.encode("ascii"))

file_length_mb = file_length / 1000000
megabytes_per_second = file_length_mb / t.secs
print("Elapsed time: {}ms".format(t.msecs))
print("Velocity: {}MB/s".format(megabytes_per_second))
