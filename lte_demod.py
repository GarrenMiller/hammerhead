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
        pss_fd[1:32] = d[31:]  # Positive frequencies
        pss_fd[-31:] = d[:31]  # Negative frequencies

        # Time domain PSS (one symbol)
        pss_td = np.fft.ifft(pss_fd)

        # Correlate
        # We use a smaller window to find the peak faster
        window = iq_data[: fs // 50]  # 20ms
        corr = signal.correlate(window, pss_td, mode="valid")
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
        start_idx = (
            pss_peak_idx + (samples_per_slot * 2) - pss_start_rel
        )  # Try next one?

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


def generate_sss_sequences(n_id_2):
    """
    Generate all 168 possible SSS sequences for a given n_id_2.
    LTE TS 36.211 Section 6.11.2.1
    """
    # Simplified m-sequence generation for SSS
    # In a real implementation, we'd use the full polynomials.
    # For this script, we'll use a pre-calculated or simplified approach.
    # Since full SSS is complex, let's focus on identifying the PCI via CRS if possible,
    # or implement a basic version.
    return []


def get_crs_positions(v_shift, fft_size, n_symbols=14):
    """
    Get indices of Cell-specific Reference Signals (CRS).
    v_shift = PCI % 6
    """
    indices = []
    # CRS is in symbols 0 and 4 of every slot (7 symbols)
    # Positions in frequency: k = 6m + (v + v_shift) mod 6
    for l in [0, 4, 7, 11]:  # Symbols in a subframe
        v = 0 if (l == 0 or l == 7) else 3
        k_start = (v + v_shift) % 6
        k = np.arange(k_start, fft_size, 6)
        for freq_idx in k:
            indices.append((l, freq_idx))
    return indices


def equalize_grid(grid, pci, n_id_2):
    """
    Perform Least-Squares (LS) channel estimation and equalization using PSS.
    """
    fft_size = grid.shape[1]
    center = fft_size // 2

    pss_symbol = grid[6, :]
    received_pss = np.concatenate(
        [pss_symbol[center - 31 : center], pss_symbol[center + 1 : center + 32]]
    )

    known_pss = generate_pss(n_id_2)

    H_pss = received_pss / known_pss

    equalized_grid = np.zeros_like(grid, dtype=np.complex64)
    for l in range(grid.shape[0]):
        symbol = grid[l, :]
        data_subcarriers = np.concatenate(
            [symbol[center - 31 : center], symbol[center + 1 : center + 32]]
        )

        if len(data_subcarriers) == len(H_pss):
            equalized_grid[l, center - 31 : center] = data_subcarriers[:31] / H_pss[:31]
            equalized_grid[l, center + 1 : center + 32] = (
                data_subcarriers[31:] / H_pss[31:]
            )

    return equalized_grid


def plot_results(iq_data, fs, pss_results, grid, best_n_id_2, n_id_1):
    pci = 3 * n_id_1 + best_n_id_2
    eq_grid = equalize_grid(grid, pci, best_n_id_2)

    fig = plt.figure(figsize=(15, 20))

    # ... (Plots 1-4 remain same) ...
    ax1 = plt.subplot(6, 1, 1)
    time_axis = np.arange(len(pss_results[0])) / (fs / 1000)
    for i, res in enumerate(pss_results):
        alpha = 1.0 if i == best_n_id_2 else 0.3
        ax1.plot(time_axis, res, label=f"PSS N_ID_2={i}", alpha=alpha)
    ax1.set_title(
        f"1. PSS Synchronization - Best N_ID_2: {best_n_id_2}, Physical Cell ID: {pci}"
    )
    ax1.set_xlabel("Time (ms)")
    ax1.legend()

    ax2 = plt.subplot(6, 1, 2)
    f, psd = signal.welch(iq_data, fs / 1e6, nperseg=1024)
    ax2.semilogy(f - (fs / 2e6), np.fft.fftshift(psd))
    ax2.set_title("2. Power Spectral Density")

    ax3 = plt.subplot(6, 1, 3)
    grid_mag = 20 * np.log10(np.abs(grid) + 1e-6)
    im = ax3.imshow(grid_mag, aspect="auto", interpolation="none", origin="lower")
    ax3.set_title("3. Raw Resource Grid")

    ax4 = plt.subplot(6, 1, 4)
    symbol_power = np.mean(np.abs(grid) ** 2, axis=1)
    ax4.plot(symbol_power, "o-")
    ax4.set_title("4. Symbol Power Profile")

    # 5. Raw vs Equalized Constellation
    ax5 = plt.subplot(6, 1, 5)
    center = grid.shape[1] // 2
    raw_pss = grid[6, :]
    raw_pss_samples = np.concatenate(
        [raw_pss[center - 31 : center], raw_pss[center + 1 : center + 32]]
    )
    ax5.scatter(
        raw_pss_samples.real, raw_pss_samples.imag, s=10, alpha=0.5, label="Raw PSS"
    )

    eq_pss = eq_grid[6, :]
    eq_pss_samples = np.concatenate(
        [eq_pss[center - 31 : center], eq_pss[center + 1 : center + 32]]
    )
    ax5.scatter(
        eq_pss_samples.real, eq_pss_samples.imag, s=10, alpha=0.8, label="Equalized PSS"
    )
    ax5.set_title("5. PSS Constellation (Before vs After Phase/Gain Equalization)")
    ax5.legend()
    ax5.axis("equal")

    # 6. Data Constellation (Non-central subcarriers)
    ax6 = plt.subplot(6, 1, 6)
    # Take a few symbols that aren't sync/broadcast
    data_samples = []
    for l in [2, 3, 8, 9]:  # Symbols usually containing PDSCH data
        sym = eq_grid[l, :]
        # Take subcarriers outside the central 72 (6 PRBs)
        data_samples.extend(sym[center + 36 : center + 100])
        data_samples.extend(sym[center - 100 : center - 36])

    ax6.scatter(
        np.real(data_samples), np.imag(data_samples), s=2, alpha=0.2, color="green"
    )
    ax6.set_title("6. Data Symbol Constellation (Potential PDSCH/Data)")
    ax6.set_xlabel("I")
    ax6.set_ylabel("Q")
    ax6.axis([-2, 2, -2, 2])
    ax6.grid(True)

    plt.tight_layout()
    plt.savefig("lte_demod_results.png")
    print("Saved results with equalization to lte_demod_results.png")


if __name__ == "__main__":
    import json
    import os

    data_path = "datasets/globecom-powder/4G_Day_1_bes_s1.bin"
    meta_path = "datasets/globecom-powder/4G_Day_1_bes_s1.json"

    with open(meta_path, "r") as f:
        meta = json.load(f)
        fs = int(meta["global"]["core:sample_rate"])

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
    # For now, we assume n_id_1 = 0 since full SSS is not yet implemented
    n_id_1 = 0
    plot_results(iq_data, fs, pss_results, grid, best_n_id_2, n_id_1)
