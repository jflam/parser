from cffi import FFI
ffi = FFI()

lib = ffi.dlopen("target/debug/parser.dll")
ffi.cdef("void crc(const char*);")

lib.crc("test/2015-12-23-14-32-19.fit".encode("ascii"))
