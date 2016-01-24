from ctypes import cdll
from ctypes import CFUNCTYPE, c_int, c_uint32, c_size_t, POINTER, c_long, c_double, c_void_p, py_object
import numpy as N

lib = cdll.LoadLibrary("c:/users/jflam/src/rust/parser/target/debug/parser.dll")

# Pass nothing
lib.hello()

# Pass 32 bit int
print("4 squared = {}".format(lib.square(4)))

# Pass python string - is there a way in rust to deal with strings as Unicode
# vs. ANSI? This would be better than forcing encode on Python side
lib.say_hello("John".encode("ascii"))

# Do File I/O in rust
PATH = "c:/users/jflam/src/rust/parser/test.py"
print("Dumping {} to console using rust lib:".format(PATH))
lib.parse(PATH.encode("ascii"))

# Trivial callback from rust - note that the first parameter to CFUNCTYPE is the return type
CALLBACK = CFUNCTYPE(c_int, c_int)

lib.call_me_back.restype = None
lib.call_me_back.argtypes = [CALLBACK]

def callback(x):
    print("Received this 32 bit int from rust: {}".format(x))
    return x

print("calling rust ...")
lib.call_me_back(CALLBACK(callback))
print("done!");

# Passing native Python lists across the FFI only works for in-parameters only
# More complex call into a rust function passing an array rust function compute the sum

lib.sum_array.restype = c_uint32
lib.sum_array.argtypes = (POINTER(c_uint32), c_size_t)

def sum_array(numbers):
    # Note that this does a copy of the original data
    buf_type = c_uint32 * len(numbers)  # compute size
    buf = buf_type(*numbers)
    return lib.sum_array(buf, len(numbers))

print("sum of [1,2,3,4] = {}".format(sum_array([1,2,3,4])))

lib.sum_float_array.restype = c_double
lib.sum_float_array.argtypes = (POINTER(c_double), c_size_t)

def sum_float_array(numbers):
    # Note that this does a copy of the original data
    buf_type = c_double * len(numbers)
    buf = buf_type(*numbers)
    return lib.sum_float_array(buf, len(numbers))

# Now let's call it with a Numpy array, which are typically floats
print("sum of random 1000 numbers in numpy array: {}",
        format(sum_float_array(N.random.rand(1000))))

# Now let's see if we can pass a mutable array to rust and have it change on the
# other side

lib.mutate_numpy_array.restype = None
lib.mutate_numpy_array.argtypes = (POINTER(c_double), c_size_t)

numpy_array = N.zeros(4)
numpy_array[0] = 1
numpy_array[1] = 2
numpy_array[2] = 3
numpy_array[3] = 4

print("original array: {}".format(numpy_array))
lib.mutate_numpy_array(numpy_array.ctypes.data_as(POINTER(c_double)), len(numpy_array))
print("mutated array: {}".format(numpy_array))

# Call a function which calls a callback in Python that explicitly returns a
# double as an out parameter. Note the pointer dereference semantics in this
# type.

def callback_double(p_double):
    p_double[0] = 42
    print("called from rust and trying to return 42")

CALLBACK_DOUBLE = CFUNCTYPE(None, POINTER(c_double))

lib.get_double_from_python.restype = c_double
lib.get_double_from_python.argtypes = [CALLBACK_DOUBLE]

result = lib.get_double_from_python(CALLBACK_DOUBLE(callback_double))
print("got {} back from python via rust!".format(result))

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
    g_array = N.zeros(length)
    ppResult[0] = g_array.ctypes.data_as(POINTER(c_double))
    print("here in allocate")

# fill_array will call back into Python to the allocate() function defined 
# above to allocate a NumPy array of sufficient size and fill that array with 
# elements. The fill_array() function will return that array back to Python, 
# where it will be treated as a NumPy array and we can use the hardware 
# accelerated functions to compute against that array. This will be the basis 
# for the high-speed parser that I will implement later in Rust.

ALLOCATOR = CFUNCTYPE(None, c_int, POINTER(POINTER(c_double)))

lib.fill_array.restype = None
lib.fill_array.argtypes = [ALLOCATOR]

lib.fill_array(ALLOCATOR(allocate)) 
print("array is: {}".format(g_array))
print("and the total computed using numpy is {}".format(g_array.sum()))
