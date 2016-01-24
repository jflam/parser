use std::ffi::CStr;
use std::os::raw::c_char;
use std::fs::File;
use std::io::prelude::*;
use std::path::Path;
use std::error::Error;
use std::slice;

extern crate libc;

use libc::{uint32_t, size_t, c_double};

#[no_mangle]
pub extern fn hello() {
    println!("Hello, from Rust!");
}

#[no_mangle]
pub extern fn square(x: i32) -> i32 {
    x * x
}

fn cstr_to_string(name: *const c_char) -> String {
    return unsafe { CStr::from_ptr(name).to_string_lossy().into_owned() };
}

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
    file.read_to_string(&mut s);
    println!("The file is {}", s);
}

#[no_mangle]
pub extern fn call_me_back(f_ptr: extern fn(x: i32)) {
//    assert!(!f_ptr.is_null()); how test for null-ness here?
    f_ptr(42);
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

    // Note that the numbers reference must be mut as well, and note the &mut reference!
    let mut numbers: &mut [c_double] = unsafe {
        assert!(!array_ptr.is_null());

        // Note the difference is calling ::from_raw_parts_mut()
        slice::from_raw_parts_mut(array_ptr, len as usize)
    };

    for i in 0..len {
        numbers[i] = 2.0;
        println!("number {}", numbers[i]);
    };
}

#[no_mangle] 
pub extern fn get_double_from_python(f_ptr: extern fn(number: *mut c_double)) -> f64 {
//    assert!(!f_ptr.is_null()); how test for nullness here?

    let mut number: f64 = 0.0;
    f_ptr(&mut number);
    println!("this is what I got from python: {}", number);
    number
}

/*
#[no_mangle]
pub extern fn fill_array(f_ptr: extern fn(x: i32, array_ptr: *mut c_double)) {

    // Ask Python to allocate an array with 4 elements
    let len: usize = 4;
    let mut array_ptr: *mut c_double = ptr::null_mut();
    let mut parray_ptr = &mut array_ptr as &mut *mut c_double;
    f_ptr(4, parray_ptr);
    //let mut array_ptr = f_ptr(4);
    //println!("got a ptr: ");
    let mut numbers: &mut [c_double] = unsafe {
        assert!(!array_ptr.is_null());

        slice::from_raw_parts_mut(array_ptr, len)
    };

    println!("before iteration");
    for i in 0..len {
        numbers[i] = 42.0;
        println!("number = {}", numbers[i]);
    }
}

*/
