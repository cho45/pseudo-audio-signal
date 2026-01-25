import json
import os

import numpy as np
from scipy import signal

def design_filters(sr):
    # ITU-T G.227 Analog Filter Specification
    # Transfer function based on the network described in G.227
    network = [
        [1, 130, 4001, 36040, 400],
        [11638, 54050, 91238, 67280, 18400]
    ]
    
    num_a, den_a = network
    # Scale coefficients for 1000Hz normalization
    num_a = [x * ((2 * np.pi * 1000)**(-(4-i))) for i, x in enumerate(num_a)]
    den_a = [x * ((2 * np.pi * 1000)**(-(4-i))) for i, x in enumerate(den_a)]
    
    # Bilinear transform to digital IIR
    num_d, den_d = signal.bilinear(num_a, den_a, sr)
    
    # Design FIR correction filter (similar to fir_optimization_analysis.py)
    f_m = np.linspace(0, sr/2, 2**15)
    p = 1j * f_m / 1000
    numerator = 18400 + 91238*p**2 + 11638*p**4 + p*(67280 + 54050*p**2)
    denominator = 400 + 4001*p**2 + p**4 + p*(36040 + 130*p**2)
    loss_m = np.abs(numerator / denominator)
    
    w_iir, h_iir = signal.freqz(num_d, den_d, worN=2**15)
    diff = (1/loss_m) / np.abs(h_iir)
    
    H_desired = np.concatenate([diff, diff[::-1]])
    h_temp = np.real(np.fft.ifft(H_desired))
    h_shifted = np.fft.fftshift(h_temp)
    
    fir_length = 97 # Same as current coeffs.json[1] length
    center = len(h_shifted) // 2
    start = center - fir_length // 2
    h_truncated = h_shifted[start:start + fir_length]
    
    window = np.kaiser(fir_length, 8.0)
    fir = h_truncated * window
    fir = fir / np.sum(fir) # Normalization for DC
    
    return {
        "iir": {"num": num_d.tolist(), "den": den_d.tolist()},
        "fir": fir.tolist()
    }

coeffs = {
    "44100": design_filters(44100),
    "48000": design_filters(48000)
}

script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, '..', 'coeffs.json')

with open(output_path, 'w') as f:
    json.dump(coeffs, f, indent=2)

print(f"Generated {output_path}")
