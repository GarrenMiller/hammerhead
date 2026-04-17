use anyhow::Result;
use serde_json::json;
use std::fs::File;
use std::io::Write;
use waverave_hackrf::open_hackrf;

pub async fn run(freq: u64) -> Result<()> {
    let mut hackrf = open_hackrf()?;
    
    // Sensible defaults based on frequency
    let sample_rate = if freq < 110_000_000 {
        2_000_000.0 // FM Radio / Low bands
    } else if (freq >= 400_000_000 && freq <= 1_000_000_000) || (freq >= 1_700_000_000 && freq <= 2_700_000_000) {
        15_360_000.0 // Common LTE bands
    } else if freq >= 2_400_000_000 && freq <= 2_500_000_000 {
        20_000_000.0 // WiFi 2.4GHz
    } else {
        10_000_000.0 // General default
    };

    let lna_gain = 24;
    let vga_gain = 16;

    println!("Gathering at {} Hz with sample rate {} Msps...", freq, sample_rate / 1e6);

    hackrf.set_sample_rate(sample_rate).await?;
    hackrf.set_lna_gain(lna_gain).await?;
    hackrf.set_vga_gain(vga_gain).await?;
    hackrf.set_freq(freq).await?;

    let base_name = format!("capture_{}Hz", freq);
    let data_file_path = format!("{}.bin", base_name);
    let meta_file_path = format!("{}.json", base_name);

    let mut file = File::create(&data_file_path)?;
    let metadata = json!({
        "global": {
            "core:datatype": "cf32",
            "core:sample_rate": sample_rate.to_string(),
            "core:version": "0.0.1",
            "core:description": "hammerhead capture",
            "core:recorder": "hammerhead"
        },
        "captures": {
            "core:sample_start": 0,
            "core:center_frequency": freq.to_string(),
            "hammerhead:lna_gain": lna_gain,
            "hammerhead:vga_gain": vga_gain
        },
        "annotations": {
            "core:sample_start": 0,
            "core:sample_count": (24 * 131072 / 2).to_string()
        }
    });
    let mut meta_file = File::create(&meta_file_path)?;
    meta_file.write_all(serde_json::to_string_pretty(&metadata)?.as_bytes())?;

    let mut rx = hackrf.start_rx(131072).await.map_err(|e| e.err)?;

    for _ in 0..128 { rx.submit(); }

    for _ in 0..24 {
        let buf = rx.next_complete().await?;
        let samples = buf.bytes();
        let mut cf32_buf = Vec::with_capacity(samples.len() * 4);
        
        for &sample in samples {
            // Convert i8 to f32 normalized to [-1.0, 1.0]
            let f = (sample as i8 as f32) / 128.0;
            cf32_buf.extend_from_slice(&f.to_le_bytes());
        }
        
        file.write_all(&cf32_buf)?;
        rx.submit();
    }
    rx.stop().await?;
    Ok(())
}
