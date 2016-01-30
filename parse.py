from cffi import FFI
ffi = FFI()

lib = ffi.dlopen("target/debug/parser.dll")
ffi.cdef("void compute_file_crc(const char*);")

lib.compute_file_crc("test/2015-12-23-14-32-19.fit".encode("ascii"))
