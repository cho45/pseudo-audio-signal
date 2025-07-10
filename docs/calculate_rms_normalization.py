#!/usr/bin/env python3
"""
ITU-T G.227 疑似音声信号の正規化係数計算
"""

import json
import numpy as np
from scipy import signal
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    coeffs_path = os.path.join(script_dir, '..', 'coeffs.json')
    
    with open(coeffs_path, 'r') as f:
        coeffs = json.load(f)
    
    iir_coeffs = coeffs[0]
    iir_num = np.array(iir_coeffs['num'])
    iir_den = np.array(iir_coeffs['den'])
    fir_coeffs = np.array(coeffs[1])
    
    # 周波数応答を計算
    _, h_iir = signal.freqz(iir_num, iir_den, worN=32768)
    _, h_fir = signal.freqz(fir_coeffs, worN=32768)
    
    # 合成応答
    h_combined = h_iir * h_fir
    
    # RMS値と正規化係数を計算
    power_sum = np.sum(np.abs(h_combined)**2)
    rms_output = np.sqrt(power_sum / len(h_combined))
    normalization_factor = 1.0 / rms_output
    
    print(f"正規化係数: {normalization_factor:.6f}")

if __name__ == "__main__":
    main()