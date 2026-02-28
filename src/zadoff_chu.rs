use std::f64::consts::PI;
use std::fs::File;
use std::io::{self, Read};

pub fn get_zc_sequence() -> Vec<i8> {
    // TODO: Generate each of the three sequences
    // A Zadoff-Chu sequence is defined by the following:
    // s_q[n] = exp[-j * pi * q * (n * (n + 1) / N)] 
    // 1. N is the length of the sequence
    // 2. q is the "root index", which is the ID of the sequence
    // 3. n is the index of the particular sample (from 0 to N - 1)
    
    let mut root_sequence: Vec<i8> = Vec::new();
    let N = 63; // LTE says the length must be 63
    let q = 25.0; // This is one of the three roots

    for mut n in 0..=N {
        // Skip the DC (center) band
        if n == 31 {
            continue;
        } 

        // Build rest of the sequence (62 samples)
        let n = n as f64;
        let N = N as f64;
        let theta = (PI * q * n * (n + 1.0)) / N;
        let real = theta.cos() * 127.0;
        let imaginary = theta.sin() * 127.0;

        // Create interleaved sequence like it comes from radio
        root_sequence.push(real as i8);
        root_sequence.push(imaginary as i8);
    }
    return root_sequence;
}

pub fn get_correlation_values() {
    // The correlation is the difference between the root sequence and it's conjugate. Max
    // correlation (e.g. when you conjugate the root) results in zero values.
    
    let chunk_size = 2;
    let mut file = File::open("lte_capture.c8").expect("Failed to open file");
    let mut buffer = vec![0u8; chunk_size];
    let mut total_data = Vec::new();


    let mut i = 0;
    loop {
        let bytes_read = file.read(&mut buffer).expect("Could not read from file");
        if i == 10 {
            break;
        }
        
        total_data.extend_from_slice(&buffer[..bytes_read]);
        println!("bytes read: {:?}", buffer);
        i += 1;
    }


}

