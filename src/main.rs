use clap::Parser;

mod lte;
mod hackrf;

#[derive(Parser)]
struct Cli {
    /// The file to process; expects a .sigmf-data file (or .c8 legacy file)
    file: Option<std::path::PathBuf>,
    /// Gather data from HackRF at the specified frequency (e.g., 754M, 2.4G)
    #[arg(long, value_name = "FREQUENCY")]
    gather: Option<String>,
}

fn parse_frequency(freq_str: &str) -> Result<u64, String> {
    let freq_str = freq_str.to_uppercase();
    let (multiplier, numeric_part) = if freq_str.ends_with('K') {
        (1_000, &freq_str[..freq_str.len() - 1])
    } else if freq_str.ends_with('M') {
        (1_000_000, &freq_str[..freq_str.len() - 1])
    } else if freq_str.ends_with('G') {
        (1_000_000_000, &freq_str[..freq_str.len() - 1])
    } else {
        (1, freq_str.as_str())
    };

    numeric_part
        .parse::<f64>()
        .map(|f| (f * multiplier as f64) as u64)
        .map_err(|_| format!("Invalid frequency format: {}", freq_str))
}

#[tokio::main]
async fn main() {
    let args = Cli::parse();
    if let Some(file) = args.file {
        let extension = file.extension().and_then(|s| s.to_str()).unwrap_or("");
        if extension == "c8" {
            lte::c8::process_file(file);
        } else if extension == "bin" || extension == "sigmf-data" {
            lte::sigmf::process_file(file);
        } else {
            // Default to SigMF for anything else, or you can add more checks
            lte::sigmf::process_file(file);
        }
    }
    if let Some(freq_str) = args.gather {
        match parse_frequency(&freq_str) {
            Ok(freq) => {
                if let Err(e) = hackrf::driver::run(freq).await {
                    eprintln!("Error gathering data: {}", e);
                }
            }
            Err(e) => eprintln!("{}", e),
        }
    }
}
