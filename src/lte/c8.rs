use super::zadoff_chu;
use std::fs::File;
use std::io::{BufRead, BufReader};

pub fn process_file(path: std::path::PathBuf) {
    read_file_in_byte_chunks(path);
}

fn read_file_in_byte_chunks(path: std::path::PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    let window_size = 62; // Match ZC sequence length
    let file = File::open(path)?;
    let mut reader = BufReader::with_capacity(window_size, file);
    let zc_sequence = zadoff_chu::get_zc_sequence(25);
    let mut largest = 0;
    let mut counter = 0;

    loop {
        let buffer = reader.fill_buf()?;
        let buffer_length = buffer.len();

        if buffer_length == 0 {
            break;
        }

        let input: Vec<i8> = buffer.iter().map(|&x| x as i8).collect();
        let correlation = get_chunk_correlation(&zc_sequence, input);
        if correlation.abs() > largest {
            largest = correlation.abs();
            counter += 1;
        }

        reader.consume(2);
    }

    println!("The largest value is: {largest} at index {counter}");

    Ok(())
}

fn get_chunk_correlation(zc_sequence: &Vec<i8>, input_sequence: Vec<i8>) -> i32 {
    let mut real_sum = 0i32;
    let mut imag_sum = 0i32;

    for i in 0..62 {
        let z_real = zc_sequence[i * 2] as i32;
        let z_imag = zc_sequence[i * 2 + 1] as i32;
        let i_real = input_sequence[i * 2] as i32;
        let i_imag = input_sequence[i * 2 + 1] as i32;

        // Complex multiplication: (z_real - j*z_imag) * (i_real + j*i_imag)
        // = (z_real*i_real + z_imag*i_imag) + j*(z_real*i_imag - z_imag*i_real)
        real_sum += z_real * i_real + z_imag * i_imag;
        imag_sum += z_real * i_imag - z_imag * i_real;
    }

    // Return the square of the magnitude to avoid sqrt (since we only care about relative size)
    real_sum * real_sum + imag_sum * imag_sum
}
