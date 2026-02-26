use anyhow::Result;
use std::fs::File;
use std::io::Write;
use waverave_hackrf::open_hackrf;

mod zadoff_chu;


// #[tokio::main]
// async fn main() -> Result<()> {
//     let hackrf = open_hackrf()?;
//
//     // Configure for your tower
//     hackrf.set_sample_rate(30_000_000.0).await?;
//     hackrf.set_amp_enable(false).await?; 
//     hackrf.set_lna_gain(24).await?;
//     hackrf.set_vga_gain(30).await?;
//     hackrf.set_freq(2_130_000_000).await?; // Tower is at 2127.5 MHz, but we want to have a bit of
//                                            // offset for better data
//
//     println!("[*] Capturing to 'lte_capture.raw'...");
//     let mut file = File::create("lte_capture.c8")?;
//
//     // Start Receiving
//     let mut hackrf_rx = hackrf.start_rx(131072).await.map_err(|e| e.err)?;
//     for _ in 0..128 { hackrf_rx.submit(); }
//
//     // Capture for about 2 seconds (~80MB of data)
//     for i in 0..300 {
//         let buf = hackrf_rx.next_complete().await?;
//
//         // The HackRF returns interleaved I and Q as i8.
//         // We write the raw byte buffer directly to the file.
//         file.write_all(buf.bytes())?;
//
//         hackrf_rx.submit();
//         if i % 50 == 0 { println!("  > Wrote chunk {}...", i); }
//     }
//
//     hackrf_rx.stop().await?;
//     println!("[+] Capture complete! Use 'Inspectrum' to view.");
//     Ok(())
// }


fn main() {
    zadoff_chu::get_zc_sequence();
}
