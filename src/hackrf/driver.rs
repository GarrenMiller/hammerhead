use anyhow::Result;
use std::fs::File;
use std::io::Write;
use waverave_hackrf::open_hackrf;

pub async fn run() -> Result<()> {
    let mut hackrf = open_hackrf()?;
    hackrf.set_sample_rate(15_360_000.0).await?;
    hackrf.set_lna_gain(24).await?;
    hackrf.set_vga_gain(16).await?;
    hackrf.set_freq(754_000_000).await?;

    let mut file = File::create("lte_capture.c8")?;
    let mut rx = hackrf.start_rx(131072).await.map_err(|e| e.err)?;

    for _ in 0..128 { rx.submit(); }

    // 23.04M samples/sec * 0.1 sec * 2 bytes/sample = 4,608,000 bytes total
    // With 131,072 byte chunks, 35 iterations is ~0.1 seconds.
    for _ in 0..24 {
        let buf = rx.next_complete().await?;
        file.write_all(buf.bytes())?;
        rx.submit();
    }
    rx.stop().await?;
    Ok(())
}
