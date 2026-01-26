#!/usr/bin/env python3
"""
帯域別総パワー誤差の計算

G.227理論特性と実装（IIR+FIR）の帯域別総パワーを比較し、
測定器スペックとして重要なパワー誤差を定量評価する。
"""

import json
import numpy as np
from scipy import signal, integrate


def load_coeffs(sr):
    """係数ファイルを読み込む"""
    with open('coeffs.json', 'r') as f:
        coeffs = json.load(f)
    return coeffs[str(sr)]


def calc_g227_response(f):
    """G.227理論特性を計算（ゲイン = loss の逆数）"""
    p = 1j * f / 1000
    numerator = 18400 + 91238*p**2 + 11638*p**4 + p*(67280 + 54050*p**2)
    denominator = 400 + 4001*p**2 + p**4 + p*(36040 + 130*p**2)
    loss = numerator / denominator
    H_theory = 1 / loss  # ゲイン = loss の逆数
    return H_theory


def calc_actual_response(coeffs, sr, f, include_fir=True):
    """実装の周波数応答を計算"""
    # IIRの周波数応答
    w = 2 * np.pi * f / sr
    _, h_iir = signal.freqz(coeffs['iir']['num'], coeffs['iir']['den'], worN=w)

    if include_fir:
        # FIRの周波数応答
        _, h_fir = signal.freqz(coeffs['fir'], [1.0], worN=w)
        # 合成
        H_actual = h_iir * h_fir
    else:
        H_actual = h_iir

    return H_actual


def calc_band_power(H, f, f_start, f_end):
    """指定帯域の総パワーを計算（数値積分）"""
    # 帯域内の周波数点を抽出
    mask = (f >= f_start) & (f <= f_end)
    f_band = f[mask]
    H_band = H[mask]

    # パワースペクトル密度 |H(f)|^2
    P_band = np.abs(H_band)**2

    # 台形則で数値積分
    power = integrate.trapezoid(P_band, f_band)

    return power


def main():
    # 評価するサンプルレート
    sample_rates = [44100, 48000]

    # 評価帯域の定義
    bands = [
        ('電話音声帯域', 300, 3400),
        ('G.227 Figure 2範囲', 50, 10000),
        ('全帯域', 10, None),  # None = Nyquist周波数
    ]

    print("="*80)
    print("帯域別総パワー誤差の評価")
    print("="*80)
    print()

    for sr in sample_rates:
        print(f"サンプルレート: {sr} Hz")
        print("-"*80)

        # 係数読み込み
        coeffs = load_coeffs(sr)

        # 十分細かい周波数点を生成（Nyquist周波数まで）
        N_points = 2**16  # 65536点
        f = np.linspace(0, sr/2, N_points)

        # 理論特性を計算
        H_theory = calc_g227_response(f)

        # IIR単体とIIR+FIRの両方を評価
        for filter_name, include_fir in [("IIRのみ", False), ("IIR+FIR", True)]:
            H_actual = calc_actual_response(coeffs, sr, f, include_fir=include_fir)

            print(f"\n【{filter_name}】")

            # 各帯域でパワー誤差を計算
            for band_name, f_start, f_end in bands:
                if f_end is None:
                    f_end = sr / 2

                # 帯域別総パワー
                P_theory = calc_band_power(H_theory, f, f_start, f_end)
                P_actual = calc_band_power(H_actual, f, f_start, f_end)

                # 誤差計算
                error_percent = (P_actual - P_theory) / P_theory * 100
                error_db = 10 * np.log10(P_actual / P_theory)

                print(f"\n{band_name} ({f_start}Hz - {f_end:.0f}Hz):")
                print(f"  理論値パワー: {P_theory:.6e}")
                print(f"  実装値パワー: {P_actual:.6e}")
                print(f"  誤差: {error_percent:+.4f}% ({error_db:+.4f} dB)")

        print()
        print("="*80)
        print()


if __name__ == '__main__':
    main()
