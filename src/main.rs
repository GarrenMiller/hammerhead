use clap::Parser;

mod lte;
mod hackrf;

#[derive(Parser)]
struct Cli {
    /// The file to process; expects a .c8 file with interleaved I/Q bits
    file: Option<std::path::PathBuf>,
    /// Whether or not to gather data to a file
    #[arg(long)]
    gather: bool
}

#[tokio::main]
async fn main() {
    let args = Cli::parse();
    if let Some(file) = args.file {
        lte::c8::process_file(file);
    }
    if args.gather {
        hackrf::driver::run().await;
    }
}
