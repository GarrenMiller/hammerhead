use std::fs::File;
use std::io::{BufReader, BufRead};
use super::zadoff_chu;

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
    // The signal cross-correlation sequence rxy[m] of discrete-time signals x[n] and y[n] is the sum from n = 0 to n = N_1
    // of x[n] * y[n - m] where N_1 is the index of the last element in the sequence, and m is the
    // time shift (lag) between signals.
    
    let result: i32 = zc_sequence
        .chunks(2)
        .zip(input_sequence.chunks(2))
        .map(|(z, i)| ((i[0] as i32 + i[1] as i32) * (i[0] as i32 - i[1] as i32)))
        .sum();

    result
}
