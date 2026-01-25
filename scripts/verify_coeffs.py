#!/usr/bin/env python3
"""
coeffs.json の検証スクリプト
生成されたフィルタ係数が ITU-T G.227 理論特性に対してどの程度の誤差があるかを評価
"""

import json
import os

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

# スクリプトのディレクトリを基準にパスを解決
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COEFFS_PATH = os.path.join(SCRIPT_DIR, '..', 'coeffs.json')
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'verification_result.png')


def evaluate_performance(sr, iir_num, iir_den, fir_coeffs):
    # ITU-T G.227 Theory
    f_m = np.linspace(10, sr/2, 2**15)
    p = 1j * f_m / 1000
    numerator = 18400 + 91238*p**2 + 11638*p**4 + p*(67280 + 54050*p**2)
    denominator = 400 + 4001*p**2 + p**4 + p*(36040 + 130*p**2)
    h_theory = np.abs(denominator / numerator)  # G.227 loss inverse

    # Actual Filter Response
    w, h_iir = signal.freqz(iir_num, iir_den, worN=f_m, fs=sr)
    _, h_fir = signal.freqz(fir_coeffs, [1], worN=f_m, fs=sr)
    h_actual = np.abs(h_iir * h_fir)

    # Error calculation
    error_db = 20 * np.log10(h_actual / h_theory)

    def calc_stats(mask):
        err = error_db[mask]
        return {'max_error': np.max(np.abs(err)), 'rmse': np.sqrt(np.mean(err**2))}

    # Band definitions
    bands = {
        'full_band': (f_m >= 10),                        # 全帯域
        'g227_fig2': (f_m >= 50) & (f_m <= 10000),       # G.227 Figure 2 範囲
        'telephone': (f_m >= 300) & (f_m <= 3400),       # 電話音声帯域 (ITU-T G.711)
    }

    result = {'freq': f_m, 'error_db': error_db}
    for name, mask in bands.items():
        result[name] = calc_stats(mask)

    return result


def main():
    with open(COEFFS_PATH, 'r') as f:
        coeffs = json.load(f)

    plt.figure(figsize=(12, 8))

    for sr_str in ["44100", "48000"]:
        sr = int(sr_str)
        c = coeffs[sr_str]
        result = evaluate_performance(sr, c['iir']['num'], c['iir']['den'], c['fir'])

        full = result['full_band']
        g227 = result['g227_fig2']
        tel = result['telephone']

        print(f"Sampling Rate: {sr} Hz")
        print(f"  Full band (10Hz - {sr//2}Hz):")
        print(f"    Max Error: {full['max_error']:.4f} dB")
        print(f"    RMSE: {full['rmse']:.4f} dB")
        print(f"  G.227 Figure 2 (50Hz - 10kHz):")
        print(f"    Max Error: {g227['max_error']:.4f} dB")
        print(f"    RMSE: {g227['rmse']:.4f} dB")
        print(f"  Telephone band (300Hz - 3.4kHz):")
        print(f"    Max Error: {tel['max_error']:.4f} dB")
        print(f"    RMSE: {tel['rmse']:.4f} dB")

        plt.semilogx(result['freq'], result['error_db'],
                     label=f"{sr}Hz (Max: {full['max_error']:.3f}dB, RMSE: {full['rmse']:.3f}dB)")

    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.axhline(0.1, color='r', linestyle='--', alpha=0.3)
    plt.axhline(-0.1, color='r', linestyle='--', alpha=0.3)
    plt.axvspan(50, 10000, alpha=0.05, color='blue', label='G.227 Fig.2 (50Hz-10kHz)')
    plt.axvspan(300, 3400, alpha=0.1, color='green', label='Telephone (300Hz-3.4kHz)')
    plt.title("ITU-T G.227 Filter Error (Relative to Theory)")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Error (dB)")
    plt.legend()
    plt.savefig(OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
