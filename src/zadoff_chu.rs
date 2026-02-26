use std::f64::consts::PI;

pub fn get_zc_sequence() {
    // A Zadoff-Chu sequence is defined by the following:
    // s_q[n] = exp[-j * pi * q * (n * (n + 1) / N)] 
    // 1. N is the length of the sequence
    // 2. q is the "root index", which is the ID of the sequence
    // 3. n is the index of the particular sample (from 0 to N - 1)
    
    let mut root_sequence: Vec<f64> = Vec::new();
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
        let real = theta.cos();
        let imaginary = theta.sin();

        // Create interleaved sequence like it comes from radio
        root_sequence.push(real);
        root_sequence.push(imaginary);
    }
}

