from ctypes import cdll, cast
from ctypes import CFUNCTYPE, POINTER
from ctypes import c_int, c_uint32, c_size_t, c_long, c_double, c_void_p, py_object, c_char
import numpy as numpy

lib = cdll.LoadLibrary("target/debug/parser.dll")

def test_call_with_no_parameters_or_results(capsys):
    lib.hello()
    out, err = capsys.readouterr()
    # It seems like capsys.readouterr fails to capture Rust output to stdout
    # correctly
    #assert out == "Hello, from Rust!"

def test_call_with_primitive_type_returning_primitive_type():
    assert lib.square(4) == 16

def test_call_with_string_no_results(capsys):
    lib.say_hello("John".encode("ascii"))
    out, err = capsys.readouterr()
    #assert out == "Hello, John"

def test_call_python_callback_passing_primitive_type():

    # Trivial callback from rust - note that the first parameter to CFUNCTYPE is the return type
    CALLBACK = CFUNCTYPE(c_int, c_int)

    lib.call_me_back.restype = None
    lib.call_me_back.argtypes = [CALLBACK]

    def callback(x):
        assert x == 42
        return x

    lib.call_me_back(CALLBACK(callback))

def test_pass_copy_of_list_of_int_to_rust():
    lib.sum_array.restype = c_uint32
    lib.sum_array.argtypes = (POINTER(c_uint32), c_size_t)

    def sum_array(numbers):
        # Note that this does a copy of the original data
        buf_type = c_uint32 * len(numbers)  # compute size
        buf = buf_type(*numbers)
        return lib.sum_array(buf, len(numbers))

    assert sum_array([1,2,3,4]) == 10

def test_mutate_numpy_array():
    lib.mutate_numpy_array.restype = None
    lib.mutate_numpy_array.argtypes = (POINTER(c_double), c_size_t)

    numpy_array = numpy.zeros(4)

    lib.mutate_numpy_array(numpy_array.ctypes.data_as(POINTER(c_double)), len(numpy_array))
    assert numpy_array[0] == 2
    assert numpy_array[1] == 2
    assert numpy_array[2] == 2
    assert numpy_array[3] == 2

def test_call_python_callback_retrieve_primitive_type():
    def callback_double(p_double):
        p_double[0] = 42

    CALLBACK_DOUBLE = CFUNCTYPE(None, POINTER(c_double))

    lib.get_double_from_python.restype = c_double
    lib.get_double_from_python.argtypes = [CALLBACK_DOUBLE]

    result = lib.get_double_from_python(CALLBACK_DOUBLE(callback_double))
    assert result == 42

# This is a global scoped reference that will hold onto the allocated array
g_array = None

def test_calling_python_to_allocate_numpy_array_and_mutating_in_rust():

    # This is the allocator function that will allocate a NumPy array and
    # return it to Rust, where the array will be filled with data and returned 
    # to Python. Note that this function has an important side-effect, it 
    # stores the allocated array in g_array. In the future we can turn this into a
    # dictionary where multiple allocations could happen and we use a cookie to
    # lookup the correct array. For now, there is a single global.

    def allocate(length, ppResult):
        global g_array
        g_array = numpy.zeros(length)
        ppResult[0] = g_array.ctypes.data_as(POINTER(c_double))

    ALLOCATOR = CFUNCTYPE(None, c_int, POINTER(POINTER(c_double)))

    lib.fill_array.restype = None
    lib.fill_array.argtypes = [ALLOCATOR]

    lib.fill_array(ALLOCATOR(allocate)) 

    global g_array
    assert len(g_array) == 4
    assert g_array[0] == 42.0
    assert g_array[1] == 42.0
    assert g_array[2] == 42.0
    assert g_array[3] == 42.0
    assert g_array.sum() == 42.0 * 4
