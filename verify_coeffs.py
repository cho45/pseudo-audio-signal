import numpy as np
from scipy import signal
import json
import matplotlib.pyplot as plt

def evaluate_performance(sr, iir_num, iir_den, fir_coeffs):
    # ITU-T G.227 Theory
    f_m = np.linspace(10, sr/2, 2**15)
    p = 1j * f_m / 1000
    numerator = 18400 + 91238*p**2 + 11638*p**4 + p*(67280 + 54050*p**2)
    denominator = 400 + 4001*p**2 + p**4 + p*(36040 + 130*p**2)
    h_theory = np.abs(denominator / numerator) # G.227 loss inverse
    
    # Actual Filter Response
    w, h_iir = signal.freqz(iir_num, iir_den, worN=f_m, fs=sr)
    _, h_fir = signal.freqz(fir_coeffs, [1], worN=f_m, fs=sr)
    h_actual = np.abs(h_iir * h_fir)
    
    # Error calculation
    error_db = 20 * np.log10(h_actual / h_theory)
    max_error = np.max(np.abs(error_db))
    rmse_db = np.sqrt(np.mean(error_db**2))
    
    return f_m, error_db, max_error, rmse_db

with open('coeffs.json', 'r') as f:
    coeffs = json.load(f)

plt.figure(figsize=(12, 8))

for sr_str in ["44100", "48000"]:
    sr = int(sr_str)
    c = coeffs[sr_str]
    f, err, max_e, rmse = evaluate_performance(sr, c['iir']['num'], c['iir']['den'], c['fir'])
    
    print(f"Sampling Rate: {sr} Hz")
    print(f"  Max Error: {max_e:.4f} dB")
    print(f"  RMSE: {rmse:.4f} dB")
    
    plt.semilogx(f, err, label=f"{sr}Hz (Max: {max_e:.3f}dB, RMSE: {rmse:.3f}dB)")

plt.grid(True, which="both", ls="-", alpha=0.5)
plt.axhline(0.1, color='r', linestyle='--', alpha=0.3)
plt.axhline(-0.1, color='r', linestyle='--', alpha=0.3)
plt.title("ITU-T G.227 Filter Error (Relative to Theory)")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Error (dB)")
plt.legend()
plt.savefig('verification_result.png')
print("Saved verification_result.png")
