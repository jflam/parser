extern crate libc;
extern crate byteorder;

use std::ptr;
use std::slice;
use std::error::Error;
use std::ffi::CStr;
use std::fs::File;
use std::io::prelude::*;
use std::os::raw::c_char;
use std::path::Path;

use libc::{uint32_t, size_t, c_double};

pub mod crc;

// Simplest possible call - no parameters, no return value
#[no_mangle]
pub extern fn hello() {
    println!("Hello, from Rust!");
}

// Function call with primitive value (all primitive values should be equivalent here) with
// primitive value return type
#[no_mangle]
pub extern fn square(x: i32) -> i32 {
    x * x
}

// Helper function to convert a const char* to a Rust String
fn cstr_to_string(name: *const c_char) -> String {
    return unsafe { CStr::from_ptr(name).to_string_lossy().into_owned() };
}

// Function call that takes an ANSI const char* as an input parameter
#[no_mangle]
pub extern fn say_hello(name: *const c_char) {
    println!("Hello, {}", cstr_to_string(name));
}

#[no_mangle]
pub extern fn parse(cstr_path: *const c_char) {
    let str = cstr_to_string(cstr_path);
    let path = Path::new(&str);
    let mut file = match File::open(path) {
        Err(why) => panic!("could not open {} because {}", path.display(),
                                                           Error::description(&why)),
        Ok(file) => file,
    };
    let mut s = String::new();
    match file.read_to_string(&mut s) {
        Err(why) => panic!("could not read {} because {}", path.display(), 
                                                           Error::description(&why)),
        Ok(_) => println!("The length of the file is {}", s.len()), 
    };
}

#[no_mangle]
pub extern fn call_me_back(f_ptr: Option<extern fn(x: i32)>) {
    match f_ptr {
        Some(f) => f(42),
        None => panic!("null function pointer"),
    };
}

// This is the simple case where we are passing arrays as in-parameters to a Rust function

#[no_mangle]
pub extern fn sum_array(array_ptr: *const uint32_t, len: size_t) -> uint32_t {

    // This is the unsafe operation that is used to convert the array into
    // the correct type.

    let numbers = unsafe {
        assert!(!array_ptr.is_null());
        slice::from_raw_parts(array_ptr, len as usize)
    };

    let sum = numbers.iter().fold(0, |acc, v| acc + v);

    sum as uint32_t
}

#[no_mangle]
pub extern fn sum_float_array(array_ptr: *const c_double, len: size_t) -> c_double {

    let numbers = unsafe {
        assert!(!array_ptr.is_null());
        slice::from_raw_parts(array_ptr, len as usize)
    };

    let sum = numbers.iter().fold(0.0, |acc, v| acc + v);

    sum as c_double
}

#[no_mangle]
pub extern fn mutate_numpy_array(array_ptr: *mut c_double, len: size_t) {

    let mut numbers: &mut [c_double] = unsafe {
        assert!(!array_ptr.is_null());
        slice::from_raw_parts_mut(array_ptr, len as usize)
    };

    for i in 0..len {
        numbers[i] = 2.0;
    };
}

// Note that we are explicitly testing for nullness here in this case and panicing if we 
// encounter a null function pointer. This shows off using the Option type to encapsulate
// values that may or may not be present.

#[no_mangle] 
pub extern fn get_double_from_python(f_ptr: Option<extern fn(number: *mut c_double)>) -> f64 {
    match f_ptr {
        Some(f) => {
            let mut number: f64 = 0.0;
            f(&mut number);
            return number
        },
        None => panic!("null pointer passed in"),
    };
}

#[no_mangle]
pub extern fn fill_array(f_ptr: Option<extern fn(x: i32, array_ptr: *mut *mut c_double)>) {
    match f_ptr {
        Some(f) => {
            // Ask Python to allocate an array with 4 elements
            let len: usize = 4;
            let mut array_ptr: *mut c_double = ptr::null_mut();
            f(4, &mut array_ptr);

            let mut numbers: &mut [c_double] = unsafe {
                assert!(!(array_ptr).is_null());
                slice::from_raw_parts_mut(array_ptr, len)
            };

            for i in 0..len {
                numbers[i] = 42.0;
            }
        },
        None => panic!("null function pointer passed in"),
    };
}

#[no_mangle]
pub extern fn compute_file_crc(cstr_path: *const c_char) {
    use crc::compute_crc;
    let str_path = cstr_to_string(cstr_path);
    let path = Path::new(&str_path);
    let mut file = match File::open(path) {
        Err(why) => panic!("couldn't open {} because {}", path.display(), Error::description(&why)),
        Ok(file) => file,
    };
    let mut buffer = vec![];
    file.read_to_end(&mut buffer).unwrap();
    let value = compute_crc(&buffer);
    println!("CRC = {:x}", value);
}
