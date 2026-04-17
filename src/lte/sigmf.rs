use super::zadoff_chu;
use std::fs::File;
use std::io::{BufReader, Read};

pub fn process_file(path: std::path::PathBuf) {
    if let Err(e) = read_sigmf_data(path) {
        eprintln!("Error processing SigMF file: {}", e);
    }
}

fn read_sigmf_data(path: std::path::PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    let window_size = 62 * 8; // Match ZC sequence length (62 complex samples, each is 2 * f32 = 8 bytes)
    let file = File::open(path)?;
    let mut reader = BufReader::new(file);

    // Use the Zadoff-Chu sequence for correlation
    let zc_sequence_i8 = zadoff_chu::get_zc_sequence(25);
    let zc_sequence: Vec<f32> = zc_sequence_i8.iter().map(|&x| x as f32 / 127.0).collect();

    let mut largest = 0.0;
    let mut counter = 0;
    let mut buffer = vec![0u8; window_size];

    loop {
        if reader.read_exact(&mut buffer).is_err() {
            break;
        }

        let mut input = Vec::with_capacity(62 * 2);
        for chunk in buffer.chunks_exact(4) {
            let f = f32::from_le_bytes(chunk.try_into()?);
            input.push(f);
        }

        let correlation = get_chunk_correlation(&zc_sequence, input);
        if correlation > largest {
            largest = correlation;
        }
        counter += 1;
    }

    println!("The largest SigMF correlation value is: {largest} at index {counter}");
    Ok(())
}

fn get_chunk_correlation(zc_sequence: &[f32], input_sequence: Vec<f32>) -> f32 {
    let mut real_sum = 0.0;
    let mut imag_sum = 0.0;

    for i in 0..62 {
        let z_real = zc_sequence[i * 2];
        let z_imag = zc_sequence[i * 2 + 1];
        let i_real = input_sequence[i * 2];
        let i_imag = input_sequence[i * 2 + 1];

        // Complex multiplication: (z_real - j*z_imag) * (i_real + j*i_imag)
        // = (z_real*i_real + z_imag*i_imag) + j*(z_real*i_imag - z_imag*i_real)
        real_sum += z_real * i_real + z_imag * i_imag;
        imag_sum += z_real * i_imag - z_imag * i_real;
    }

    (real_sum * real_sum + imag_sum * imag_sum).sqrt()
}
