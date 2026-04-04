import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

def generate_pss(n_id_2):
    """
    Generate PSS sequence for a given N_ID_2 (0, 1, 2).
    LTE TS 36.211 Section 6.11.1.1
    """
    root_indices = [25, 29, 34]
    u = root_indices[n_id_2]
    
    # Zadoff-Chu sequence of length 62
    n = np.arange(31)
    d1 = np.exp(-1j * np.pi * u * n * (n + 1) / 63)
    n = np.arange(31, 62)
    d2 = np.exp(-1j * np.pi * u * (n + 1) * (n + 2) / 63)
    
    d = np.concatenate([d1, d2])
    return d

def correlate_pss(iq_data, fs, fft_size):
    """
    Correlate IQ data with all 3 PSS sequences.
    """
    pss_results = []
    for n_id_2 in range(3):
        d = generate_pss(n_id_2)
        
        # Map to subcarriers
        pss_fd = np.zeros(fft_size, dtype=np.complex64)
        pss_fd[1:32] = d[31:] # Positive frequencies
        pss_fd[-31:] = d[:31] # Negative frequencies
        
        # Time domain PSS (one symbol)
        pss_td = np.fft.ifft(pss_fd)
        
        # Correlate
        # We use a smaller window to find the peak faster
        window = iq_data[:fs//50] # 20ms
        corr = signal.correlate(window, pss_td, mode='valid')
        pss_results.append(np.abs(corr))
        
    return pss_results

def extract_resource_grid(iq_data, fs, fft_size, pss_peak_idx, n_symbols=140):
    """
    Extract OFDM resource grid starting from a PSS peak.
    In LTE, PSS is at symbol 6 (of subframe 0 or 5).
    """
    # Standard CP lengths for 5MHz (512 FFT)
    # Symbol 0: 40 samples (160/2048 * 512)
    # Symbols 1-6: 36 samples (144/2048 * 512)
    cp_0 = int(160 * fft_size / 2048)
    cp_n = int(144 * fft_size / 2048)
    
    # PSS is symbol 6. The start of the slot (symbol 0) is back:
    # 6 symbols + 6 CPs + 1 CP0
    samples_per_slot = 7 * fft_size + cp_0 + 6 * cp_n
    
    # Align to start of subframe (assuming PSS is in subframe 0 or 5)
    # Start of symbol 6 (PSS) relative to start of subframe:
    pss_start_rel = cp_0 + fft_size + 5 * (cp_n + fft_size)
    
    start_idx = pss_peak_idx - pss_start_rel
    if start_idx < 0:
        start_idx = pss_peak_idx + (samples_per_slot * 2) - pss_start_rel # Try next one?
        
    grid = []
    curr_idx = start_idx
    
    for i in range(n_symbols):
        cp_len = cp_0 if (i % 7 == 0) else cp_n
        symbol_data = iq_data[curr_idx + cp_len : curr_idx + cp_len + fft_size]
        if len(symbol_data) < fft_size:
            break
        
        symbol_fd = np.fft.fftshift(np.fft.fft(symbol_data))
        grid.append(symbol_fd)
        curr_idx += cp_len + fft_size
        
    return np.array(grid)

def find_pci(grid, n_id_2):
    """
    Placeholder for SSS detection to find N_ID_1.
    """
    # SSS is in symbol 5 (if PSS is in symbol 6)
    # sss_symbol = grid[5, :]
    return 0 # Dummy N_ID_1

def plot_results(iq_data, fs, pss_results, grid, best_n_id_2, n_id_1):
    pci = 3 * n_id_1 + best_n_id_2
    fig = plt.figure(figsize=(15, 18))
    
    # 1. PSS Correlation
    ax1 = plt.subplot(5, 1, 1)
    time_axis = np.arange(len(pss_results[0])) / (fs/1000)
    for i, res in enumerate(pss_results):
        alpha = 1.0 if i == best_n_id_2 else 0.3
        ax1.plot(time_axis, res, label=f'PSS N_ID_2={i}', alpha=alpha)
    ax1.set_title(f"1. PSS Synchronization (Timing Recovery) - Best N_ID_2: {best_n_id_2}, Physical Cell ID: {pci}")
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Correlation Magnitude")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Power Spectral Density (PSD)
    ax2 = plt.subplot(5, 1, 2)
    f, psd = signal.welch(iq_data, fs/1e6, nperseg=1024)
    ax2.semilogy(f - (fs/2e6), np.fft.fftshift(psd))
    ax2.set_title("2. Power Spectral Density (Frequency Occupancy)")
    ax2.set_xlabel("Frequency Offset from Center (MHz)")
    ax2.set_ylabel("Power/Freq (dB/Hz)")
    ax2.grid(True, alpha=0.3)

    # 3. Resource Grid (Waterfall)
    ax3 = plt.subplot(5, 1, 3)
    grid_mag = 20 * np.log10(np.abs(grid) + 1e-6)
    im = ax3.imshow(grid_mag, aspect='auto', interpolation='none', origin='lower', cmap='viridis')
    ax3.set_title("3. Resource Grid (Time-Frequency Map) - Note the central PSS/SSS bars")
    ax3.set_xlabel("Subcarrier Index (Frequency)")
    ax3.set_ylabel("OFDM Symbol Index (Time)")
    plt.colorbar(im, ax=ax3, label='Magnitude (dB)')
    
    # 4. Symbol Power Profile
    ax4 = plt.subplot(5, 1, 4)
    symbol_power = np.mean(np.abs(grid)**2, axis=1)
    ax4.plot(symbol_power, 'o-')
    ax4.set_title("4. Average Power per OFDM Symbol (Temporal Structure)")
    ax4.set_xlabel("Symbol Index")
    ax4.set_ylabel("Mean Square Power")
    ax4.grid(True, alpha=0.3)
    # Highlight PSS symbols (every 70 symbols in this capture)
    for i in range(6, len(symbol_power), 70):
        ax4.axvline(i, color='r', linestyle='--', alpha=0.5, label='PSS' if i==6 else "")

    # 5. Constellation
    ax5 = plt.subplot(5, 1, 5)
    center = grid.shape[1] // 2
    # Collect all PSS symbols in the grid
    pss_samples = []
    for i in range(6, grid.shape[0], 70):
        pss_sym = grid[i, :]
        pss_samples.extend(np.concatenate([pss_sym[center-31:center], pss_sym[center+1:center+32]]))
    
    ax5.scatter(np.real(pss_samples), np.imag(pss_samples), s=10, alpha=0.6, color='darkorange')
    ax5.set_title("5. PSS Constellation (Signal Quality Indicator)")
    ax5.set_xlabel("In-phase")
    ax5.set_ylabel("Quadrature")
    ax5.axis('equal')
    ax5.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('lte_demod_results.png')
    print("Saved enhanced results to lte_demod_results.png")

if __name__ == "__main__":
    import json
    import os
    
    data_path = 'datasets/globecom-powder/4G_Day_1_bes_s1.bin'
    meta_path = 'datasets/globecom-powder/4G_Day_1_bes_s1.json'
    
    with open(meta_path, 'r') as f:
        meta = json.load(f)
        fs = int(meta['global']['core:sample_rate'])
        
    # Standard LTE FFT size for ~7.68 Msps is 512
    fft_size = 512
    
    print(f"Loading {data_path}...")
    # Read first 100ms of data
    iq_data = np.fromfile(data_path, dtype=np.complex64, count=fs // 10)
    
    print("Correlating PSS...")
    pss_results = correlate_pss(iq_data, fs, fft_size)
    
    # Find best peak
    best_n_id_2 = np.argmax([np.max(res) for res in pss_results])
    peak_idx = np.argmax(pss_results[best_n_id_2])
    print(f"Best N_ID_2: {best_n_id_2}, Peak Index: {peak_idx}")
    
    print("Extracting Resource Grid...")
    grid = extract_resource_grid(iq_data, fs, fft_size, peak_idx)
    
    print("Plotting results...")
    n_id_1 = find_pci(grid, best_n_id_2)
    plot_results(iq_data, fs, pss_results, grid, best_n_id_2, n_id_1)
