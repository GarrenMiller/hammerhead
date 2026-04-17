use std::f64::consts::PI;

pub(super) fn get_zc_sequence(root: i8) -> Vec<i8> {
    // TODO: Generate each of the three sequences
    // A Zadoff-Chu sequence is defined by the following:
    // s_q[n] = exp[-j * pi * q * (n * (n + 1) / N)]
    // 1. N is the length of the sequence
    // 2. q is the "root index", which is the ID of the sequence
    // 3. n is the index of the particular sample (from 0 to N - 1)

    let mut root_sequence: Vec<i8> = Vec::new();
    let sequence_length = 63; // LTE says the length must be 63

    for n in 0..=sequence_length {
        // Skip the DC (center) band
        if n == 31 {
            continue;
        }

        // Build rest of the sequence (62 samples)
        // LTE TS 36.211 Section 6.11.1.1
        let theta = if n < 31 {
            (PI * root as f64 * n as f64 * (n as f64 + 1.0)) / 63.0
        } else {
            (PI * root as f64 * (n as f64 + 1.0) * (n as f64 + 2.0)) / 63.0
        };

        let real = theta.cos() * 127.0;
        let imaginary = -theta.sin() * 127.0; // exp(-j * theta)

        // Create interleaved sequence like it comes from radio
        root_sequence.push(real as i8);
        root_sequence.push(imaginary as i8);
    }
    return root_sequence;
}
