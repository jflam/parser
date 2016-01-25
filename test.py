from ctypes import cdll, cast
from ctypes import CFUNCTYPE, POINTER
from ctypes import c_int, c_uint32, c_size_t, c_long, c_double, c_void_p, py_object, c_char
import numpy as numpy

lib = cdll.LoadLibrary("target/debug/parser.dll")

# Pass nothing
print("Calling Rust function without any parameters or results")
lib.hello()

# Pass 32 bit int
print("\nCalling Rust function with a 32 bit integer parameter")
print("4 squared = {}".format(lib.square(4)))

# Pass python string - is there a way in rust to deal with strings as Unicode
# vs. ANSI? This would be better than forcing encode on Python side
print("\nCalling Rust function with an ANSI string")
lib.say_hello("John".encode("ascii"))

# Do File I/O in rust and print the size of the read bytes to the console
print("\nCalling Rust function with a path to do some file i/o")
PATH = "test.py"
lib.parse(PATH.encode("ascii"))

# Call rust function passing in a Python list converted into a raw byte array
lib.sum_array.restype = c_uint32
lib.sum_array.argtypes = (POINTER(c_uint32), c_size_t)

# Helper function that copies the data from the List into a ray byte array
def sum_array(numbers):
    # Note that this does a copy of the original data
    buf_type = c_uint32 * len(numbers)  # compute size
    buf = buf_type(*numbers) # copy list into the buffer
    return lib.sum_array(buf, len(numbers))

print("\nCalling Rust function with a Python List converted into a raw array")
print("sum of [1,2,3,4] = {}".format(sum_array([1,2,3,4])))

# Call Rust function passing in a NumPy array as an in-parameter
lib.sum_float_array.restype = c_double
lib.sum_float_array.argtypes = (POINTER(c_double), c_size_t)

# Now let's call it with a Numpy array, which are typically floats
print("\nCalling Rust function with NumPy array as an in-parameter")
sum = lib.sum_float_array(numpy.random.rand(1000).ctypes.data_as(POINTER(c_double)), 1000)
print("Sum of random 1000 numbers in numpy array: {}".format(sum))

# Call Rust function passing in a NumPy array as an in/out parameter
lib.mutate_numpy_array.restype = None
lib.mutate_numpy_array.argtypes = (POINTER(c_double), c_size_t)

# Zero'd array will be changed to all 2s 
numpy_array = numpy.zeros(4)

print("\nCalling Rust function with a mutable NumPy array, and changing the data")
lib.mutate_numpy_array(numpy_array.ctypes.data_as(POINTER(c_double)), len(numpy_array))
print("mutated array: {}".format(numpy_array))

# Trivial callback from Rust, where Rust passes an int to Python 
CALLBACK = CFUNCTYPE(c_int, c_int)

lib.call_me_back.restype = None
lib.call_me_back.argtypes = [CALLBACK]

def callback(x):
    print("  Python: Received this 32 bit int from rust: {}".format(x))
    return x

print("\nCalling Rust function with a Python callback function that gets invoked with an integer")
lib.call_me_back(CALLBACK(callback))

# Call a Rust function which calls a callback in Python that returns a
# double as an out parameter. Note the pointer dereference semantics in this
# type.
def callback_double(p_double):
    p_double[0] = 42
    print("  Python: called from Rust and trying to return 42")

CALLBACK_DOUBLE = CFUNCTYPE(None, POINTER(c_double))

lib.get_double_from_python.restype = c_double
lib.get_double_from_python.argtypes = [CALLBACK_DOUBLE]

print("\nCalling Rust function with a Python callback function that returns a double as an out parameter")
result = lib.get_double_from_python(CALLBACK_DOUBLE(callback_double))
print("Python: got {} back from the Rust function".format(result))

#print("\nCalling Rust function with a null callback function pointer")
#result = lib.get_double_from_python(cast(None, CALLBACK_DOUBLE))

# More sophisticated callback where I dynamically allocate a numpy array in the
# callback function that Rust will fill in for me

# This is a global scoped reference that will hold onto the allocated array
g_array = None

# This is the allocator function that will allocate a NumPy array and
# return it to rust, where the array will be filled with data and returned 
# to Python. Note that this function has an important side-effect, it 
# stores the allocated array in g_results. In the future we can turn this into a
# dictioary where multiple allocations could happen and we use a cookie to
# lookup the correct array. For now, there is a single global.

def allocate(length, ppResult):
    global g_array
    g_array = numpy.zeros(length)
    ppResult[0] = g_array.ctypes.data_as(POINTER(c_double))
    print("  Python: allocating a NumPy array of length {}".format(length))

# fill_array will call back into Python to the allocate() function defined 
# above to allocate a NumPy array of sufficient size and fill that array with 
# elements. The fill_array() function will return that array back to Python, 
# where it will be treated as a NumPy array and we can use the hardware 
# accelerated functions to compute against that array. This will be the basis 
# for the high-speed parser that I will implement later in Rust.

ALLOCATOR = CFUNCTYPE(None, c_int, POINTER(POINTER(c_double)))

lib.fill_array.restype = None
lib.fill_array.argtypes = [ALLOCATOR]

print("\nCalling Rust function that will fill a Python-allocated NumPy array with values")
lib.fill_array(ALLOCATOR(allocate)) 
print("array is: {}".format(g_array))
print("and the total computed using numpy is {}".format(g_array.sum()))

# print("\nCalling Rust function with a null callback function pointer")
# lib.fill_array(cast(None, ALLOCATOR))
