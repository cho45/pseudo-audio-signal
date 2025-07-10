#!/usr/bin/env python3
"""
FIR係数最適化分析ツール
異なる係数長さでFIRフィルタを設計し、性能を評価・比較
"""

import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib
import japanize_matplotlib
from scipy import signal
import json

def design_fir_filter(fir_length, iir_filters, sr=44100):
    """指定した長さで新しくFIRフィルタを設計"""
    
    # ITU-T G.227の理論特性
    f_m = np.linspace(0, sr/2, 2**15)
    p = 1j * f_m / 1000
    numerator = 18400 + 91238*p**2 + 11638*p**4 + p*(67280 + 54050*p**2)
    denominator = 400 + 4001*p**2 + p**4 + p*(36040 + 130*p**2)
    loss_m = np.abs(numerator / denominator)
    
    # IIRフィルタの合成応答
    h_iir = np.multiply.reduce([np.abs(f["hz"]) for f in iir_filters])
    
    # FIRで補正すべき特性
    diff = -20 * np.log10(loss_m) - 20 * np.log10(h_iir)
    diff = np.power(10, diff / 20)
    
    # 対称な周波数応答の作成
    H_desired = np.concatenate([diff, diff[::-1]])
    
    # IFFTでインパルス応答を計算
    h_temp = np.real(np.fft.ifft(H_desired))
    
    # 線形位相のために中心にシフト
    h_shifted = np.fft.fftshift(h_temp)
    
    # 指定した長さに切り詰め（奇数長）
    center = len(h_shifted) // 2
    start = center - fir_length // 2
    h_truncated = h_shifted[start:start + fir_length]
    
    # Kaiser窓を適用
    beta = 8.0
    window = np.kaiser(fir_length, beta)
    fir = h_truncated * window
    
    # 正規化（DCゲイン = 1）
    fir = fir / np.sum(fir)
    
    return fir

def load_iir_filters():
    """IIRフィルタの読み込み"""
    
    sr = 44100
    network = [
        [1, 130, 4001, 36040, 400],
        [11638, 54050, 91238, 67280, 18400]
    ]
    
    num, den = network
    num = [x * ((2 * np.pi * 1000)**(-(4-i))) for i, x in enumerate(num)]
    den = [x * ((2 * np.pi * 1000)**(-(4-i))) for i, x in enumerate(den)]
    
    # 双一次変換
    filtz = signal.lti(*signal.bilinear(num, den, sr))
    wz, hz = signal.freqz(filtz.num, filtz.den, worN=2**15)
    
    return [{
        "filter": filtz,
        "wz": wz,
        "hz": hz,
    }]

def evaluate_performance(fir_coeffs, iir_filters, sr=44100):
    """フィルタ性能の評価"""
    
    # ITU-T G.227の理論特性
    f_m = np.linspace(0, sr/2, 2**15)
    p = 1j * f_m / 1000
    numerator = 18400 + 91238*p**2 + 11638*p**4 + p*(67280 + 54050*p**2)
    denominator = 400 + 4001*p**2 + p**4 + p*(36040 + 130*p**2)
    loss_m = np.abs(numerator / denominator)
    h_expected = 1 / loss_m
    
    # 実装フィルタの周波数応答
    w, h_fir = signal.freqz(fir_coeffs, worN=2**15)
    h_iir = np.multiply.reduce([np.abs(f["hz"]) for f in iir_filters])
    h_actual = h_iir * np.abs(h_fir)
    
    # 周波数軸の調整
    freqs = w * sr / (2 * np.pi)
    
    # 性能評価
    relative_error = np.abs((h_actual - h_expected) / h_expected)
    rmse_relative = np.sqrt(np.mean(relative_error**2))
    max_relative_error = np.max(relative_error)
    max_error_freq = freqs[np.argmax(relative_error)]
    
    # dB RMSE
    h_actual_dB = 20 * np.log10(h_actual)
    h_expected_dB = 20 * np.log10(h_expected)
    error_dB = np.abs(h_actual_dB - h_expected_dB)
    rmse_dB = np.sqrt(np.mean(error_dB**2))
    
    # 周波数帯域別評価
    freq_bands = [(10, 100), (100, 1000), (1000, 10000), (10000, 22050)]
    band_names = ['10-100Hz', '100-1kHz', '1k-10kHz', '10k-22kHz']
    band_rmse = []
    
    for f_low, f_high in freq_bands:
        mask = (freqs >= f_low) & (freqs <= f_high)
        if np.any(mask):
            band_error = relative_error[mask]
            band_rmse.append(np.sqrt(np.mean(band_error**2)))
        else:
            band_rmse.append(0)
    
    return {
        'rmse_relative': rmse_relative,
        'rmse_dB': rmse_dB,
        'max_relative_error': max_relative_error,
        'max_error_freq': max_error_freq,
        'band_rmse': band_rmse,
        'band_names': band_names,
        'h_actual': h_actual,
        'h_expected': h_expected,
        'freqs': freqs,
        'relative_error': relative_error
    }

def load_current_coefficients():
    """現在の係数を読み込み"""
    
    try:
        with open('coeffs.json', 'r') as f:
            coeffs = json.load(f)
        
        current_fir = coeffs[1]
        current_length = len(current_fir)
        
        return current_fir, current_length
    except FileNotFoundError:
        print("警告: coeffs.jsonが見つかりません")
        return None, None

def analyze_coefficients(test_lengths=None, target_rmse=0.003, target_max_error=0.02):
    """係数分析のメイン関数"""
    
    print("=== FIR係数最適化分析 ===")
    
    # 現在の係数を読み込み
    current_fir, current_length = load_current_coefficients()
    if current_fir is None:
        print("現在の係数が読み込めません")
        return None
    
    print(f"現在の係数数: {current_length}")
    
    # IIRフィルタの読み込み
    iir_filters = load_iir_filters()
    
    # テストする係数長さの設定
    if test_lengths is None:
        # 現在の係数数を基準に範囲を設定
        base_length = current_length
        test_lengths = []
        for factor in [0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0, 1.1, 1.25]:
            length = int(base_length * factor)
            if length % 2 == 0:  # 奇数にする
                length += 1
            if length > 0 and length not in test_lengths:
                test_lengths.append(length)
        test_lengths.sort()
    
    results = []
    
    # 現在の係数の性能評価
    current_performance = evaluate_performance(current_fir, iir_filters)
    results.append({
        'length': current_length,
        'fir_coeffs': current_fir,
        'performance': current_performance,
        'is_current': True,
        'is_designed': False,
        'symmetry': np.allclose(current_fir, current_fir[::-1])
    })
    
    print(f"\n=== 現在の係数（{current_length}個）の性能 ===")
    print(f"相対誤差RMSE: {current_performance['rmse_relative']:.6f} = {current_performance['rmse_relative']*100:.3f}%")
    print(f"最大相対誤差: {current_performance['max_relative_error']:.6f} = {current_performance['max_relative_error']*100:.3f}% @ {current_performance['max_error_freq']:.1f} Hz")
    print(f"帯域別RMSE: {[f'{x*100:.3f}%' for x in current_performance['band_rmse']]}")
    
    # 異なる係数長さでの新設計テスト
    print(f"\n=== 新設計での性能比較 ===")
    
    for length in test_lengths:
        if length == current_length:
            continue  # 現在の係数はすでに評価済み
        
        print(f"\n係数数: {length}")
        
        # 新しくFIRフィルタを設計
        fir_coeffs = design_fir_filter(length, iir_filters)
        
        # 性能評価
        performance = evaluate_performance(fir_coeffs, iir_filters)
        
        # 結果表示
        print(f"  相対誤差RMSE: {performance['rmse_relative']:.6f} = {performance['rmse_relative']*100:.3f}%")
        print(f"  最大相対誤差: {performance['max_relative_error']:.6f} = {performance['max_relative_error']*100:.3f}% @ {performance['max_error_freq']:.1f} Hz")
        print(f"  帯域別RMSE: {[f'{x*100:.3f}%' for x in performance['band_rmse']]}")
        
        # 対称性確認
        symmetry = np.allclose(fir_coeffs, fir_coeffs[::-1])
        print(f"  対称性: {symmetry}")
        
        results.append({
            'length': length,
            'fir_coeffs': fir_coeffs,
            'performance': performance,
            'is_current': False,
            'is_designed': True,
            'symmetry': symmetry
        })
    
    # 最適化分析
    optimal_result = analyze_optimization(results, current_length, target_rmse, target_max_error)
    
    return results, optimal_result

def analyze_optimization(results, current_length, target_rmse=0.003, target_max_error=0.02):
    """最適化分析"""
    
    print("\n=== 最適化分析 ===")
    print(f"目標性能:")
    print(f"  相対誤差RMSE < {target_rmse*100:.1f}%")
    print(f"  最大相対誤差 < {target_max_error*100:.1f}%")
    
    print(f"\n性能比較:")
    print(f"{'係数数':>6} {'RMSE(%)':>8} {'最大誤差(%)':>10} {'判定':>6} {'タイプ':>8} {'削減率(%)':>8}")
    print("-" * 65)
    
    optimal_candidates = []
    
    for result in sorted(results, key=lambda x: x['length']):
        length = result['length']
        rmse = result['performance']['rmse_relative']
        max_error = result['performance']['max_relative_error']
        
        meets_target = rmse < target_rmse and max_error < target_max_error
        reduction = (current_length - length) / current_length * 100
        
        status = "✓" if meets_target else "✗"
        
        if result['is_current']:
            type_str = "現在"
        elif result['is_designed']:
            type_str = "新設計"
        else:
            type_str = "その他"
        
        print(f"{length:>6} {rmse*100:>8.3f} {max_error*100:>10.3f} {status:>6} {type_str:>8} {reduction:>8.1f}")
        
        if meets_target:
            optimal_candidates.append((length, rmse, max_error, reduction, result))
    
    # 最適解の推奨
    if optimal_candidates:
        # 最も小さい係数数を推奨
        optimal_length, optimal_rmse, optimal_max_error, optimal_reduction, optimal_result = min(optimal_candidates)
        print(f"\n推奨係数数: {optimal_length}")
        print(f"  相対誤差RMSE: {optimal_rmse*100:.3f}%")
        print(f"  最大相対誤差: {optimal_max_error*100:.3f}%")
        
        if optimal_reduction > 0:
            print(f"  削減効果: {optimal_reduction:.1f}% ({current_length-optimal_length}個削減)")
        elif optimal_reduction < 0:
            print(f"  増加: {-optimal_reduction:.1f}% ({optimal_length-current_length}個増加)")
        else:
            print(f"  現在と同じ係数数")
        
        return optimal_result
    else:
        print(f"\n警告: 目標性能を満たす係数数が見つかりません")
        return None

def visualize_results(results, current_length, save_filename='fir_optimization_analysis.png'):
    """結果の可視化"""
    
    fig, axes = plt.subplots(3, 3, figsize=(16, 12))
    
    # データ準備
    lengths = [r['length'] for r in results]
    rmse_values = [r['performance']['rmse_relative']*100 for r in results]
    max_errors = [r['performance']['max_relative_error']*100 for r in results]
    is_current = [r['is_current'] for r in results]
    
    # 現在の係数のインデックス
    current_idx = next(i for i, r in enumerate(results) if r['is_current'])
    
    # 1. 係数数 vs 性能
    ax = axes[0, 0]
    ax.plot(lengths, rmse_values, 'bo-', label='RMSE', linewidth=2, markersize=6)
    ax.plot(lengths, max_errors, 'r^-', label='最大誤差', linewidth=2, markersize=6)
    ax.plot(lengths[current_idx], rmse_values[current_idx], 'go', markersize=10, label='現在')
    ax.axhline(y=0.3, color='b', linestyle='--', alpha=0.5, label='RMSE目標')
    ax.axhline(y=2.0, color='r', linestyle='--', alpha=0.5, label='最大誤差目標')
    ax.set_xlabel('係数数')
    ax.set_ylabel('相対誤差 (%)')
    ax.set_title('係数数 vs 性能')
    ax.legend()
    ax.grid(True)
    
    # 2. 周波数応答比較
    ax = axes[0, 1]
    selected_lengths = [min(lengths), current_length, max(lengths)]
    for result in results:
        if result['length'] in selected_lengths:
            length = result['length']
            freqs = result['performance']['freqs']
            h_actual = result['performance']['h_actual']
            linestyle = '-' if result['is_current'] else '--'
            linewidth = 3 if result['is_current'] else 2
            ax.semilogx(freqs, 20*np.log10(h_actual), 
                       label=f'{length}係数{"(現在)" if result["is_current"] else ""}', 
                       linewidth=linewidth, linestyle=linestyle)
    
    ax.set_xlabel('周波数 (Hz)')
    ax.set_ylabel('振幅 (dB)')
    ax.set_title('周波数応答比較')
    ax.legend()
    ax.grid(True)
    ax.set_xlim(10, 22050)
    
    # 3. 相対誤差分布
    ax = axes[0, 2]
    for result in results:
        if result['length'] in selected_lengths:
            length = result['length']
            freqs = result['performance']['freqs']
            relative_error = result['performance']['relative_error']
            linestyle = '-' if result['is_current'] else '--'
            linewidth = 3 if result['is_current'] else 2
            ax.semilogx(freqs, relative_error*100, 
                       label=f'{length}係数{"(現在)" if result["is_current"] else ""}', 
                       linewidth=linewidth, linestyle=linestyle)
    
    ax.set_xlabel('周波数 (Hz)')
    ax.set_ylabel('相対誤差 (%)')
    ax.set_title('相対誤差分布')
    ax.legend()
    ax.grid(True)
    ax.set_xlim(10, 22050)
    
    # 4. 計算コスト比較
    ax = axes[1, 0]
    block_size = 128
    mult_per_block = [length * block_size for length in lengths]
    colors = ['green' if ic else 'orange' for ic in is_current]
    
    bars = ax.bar(range(len(lengths)), mult_per_block, color=colors, alpha=0.7)
    ax.set_xlabel('係数数')
    ax.set_ylabel('乗算回数/ブロック')
    ax.set_title('計算コスト比較')
    ax.set_xticks(range(len(lengths)))
    ax.set_xticklabels(lengths, rotation=45)
    ax.grid(True)
    
    # 5. 削減効果 vs 性能
    ax = axes[1, 1]
    reduction_percent = [(current_length - length) / current_length * 100 for length in lengths]
    
    scatter = ax.scatter(reduction_percent, rmse_values, s=100, c=['green' if ic else 'blue' for ic in is_current], 
                        alpha=0.7, label='RMSE')
    ax.scatter(reduction_percent, max_errors, s=100, c=['green' if ic else 'red' for ic in is_current], 
              alpha=0.7, label='最大誤差')
    
    for i, length in enumerate(lengths):
        ax.annotate(f'{length}', (reduction_percent[i], rmse_values[i]), 
                   xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax.set_xlabel('削減率 (%)')
    ax.set_ylabel('相対誤差 (%)')
    ax.set_title('削減効果 vs 性能トレードオフ')
    ax.legend()
    ax.grid(True)
    
    # 6. 帯域別性能比較
    ax = axes[1, 2]
    band_names = ['10-100Hz', '100-1kHz', '1k-10kHz', '10k-22kHz']
    
    selected_results = [r for r in results if r['length'] in selected_lengths]
    x = np.arange(len(band_names))
    width = 0.25
    
    for i, result in enumerate(selected_results):
        band_errors = [err*100 for err in result['performance']['band_rmse']]
        color = 'green' if result['is_current'] else f'C{i}'
        label = f"{result['length']}係数{'(現在)' if result['is_current'] else ''}"
        ax.bar(x + i*width, band_errors, width, label=label, color=color, alpha=0.7)
    
    ax.set_xlabel('周波数帯域')
    ax.set_ylabel('相対誤差RMSE (%)')
    ax.set_title('帯域別性能比較')
    ax.set_xticks(x + width)
    ax.set_xticklabels(band_names, rotation=45)
    ax.legend()
    ax.grid(True)
    
    # 7. 係数の対称性確認（現在の係数）
    ax = axes[2, 0]
    current_result = next(r for r in results if r['is_current'])
    fir_coeffs = current_result['fir_coeffs']
    
    center = len(fir_coeffs) // 2
    left_half = fir_coeffs[:center]
    right_half = fir_coeffs[center+1:][::-1]
    
    ax.plot(left_half, 'bo-', label='左半分', markersize=4)
    ax.plot(right_half, 'r^--', label='右半分（反転）', markersize=4)
    ax.set_title(f'{current_length}係数の対称性確認')
    ax.set_xlabel('サンプル')
    ax.set_ylabel('係数値')
    ax.legend()
    ax.grid(True)
    
    # 8. 統計サマリー
    ax = axes[2, 1]
    ax.axis('off')
    
    # 最適化結果の表示
    target_rmse = 0.003
    target_max_error = 0.02
    
    optimal_candidates = []
    for result in results:
        length = result['length']
        rmse = result['performance']['rmse_relative']
        max_error = result['performance']['max_relative_error']
        
        if rmse < target_rmse and max_error < target_max_error:
            reduction = (current_length - length) / current_length * 100
            optimal_candidates.append((length, rmse, max_error, reduction))
    
    if optimal_candidates:
        optimal_length = min(optimal_candidates)[0]
        optimal_rmse = min(optimal_candidates)[1]
        reduction = (current_length - optimal_length) / current_length * 100
        
        ax.text(0.1, 0.8, f'現在の係数数: {current_length}', fontsize=12, transform=ax.transAxes)
        ax.text(0.1, 0.6, f'推奨係数数: {optimal_length}', fontsize=12, 
                transform=ax.transAxes, color='green', weight='bold')
        if reduction > 0:
            ax.text(0.1, 0.4, f'削減可能: {current_length-optimal_length}個', fontsize=12, 
                    transform=ax.transAxes, color='blue')
            ax.text(0.1, 0.2, f'削減率: {reduction:.1f}%', fontsize=12, 
                    transform=ax.transAxes, color='blue')
        else:
            ax.text(0.1, 0.4, f'増加必要: {optimal_length-current_length}個', fontsize=12, 
                    transform=ax.transAxes, color='red')
        ax.text(0.1, 0.0, f'性能: {optimal_rmse*100:.3f}%', fontsize=12, 
                transform=ax.transAxes, color='green')
    else:
        ax.text(0.1, 0.5, '目標性能を満たす\n係数数なし', fontsize=12, 
                transform=ax.transAxes, color='red', weight='bold')
    
    ax.set_title('最適化結果')
    
    # 9. 空きスペース
    ax = axes[2, 2]
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(save_filename, dpi=150, bbox_inches='tight')
    plt.show()

def main():
    """メイン実行"""
    
    # 分析実行
    results, optimal_result = analyze_coefficients(
        test_lengths=None,  # 自動設定
        target_rmse=0.003,   # 0.3%
        target_max_error=0.02  # 2%
    )
    
    if results:
        current_length = next(r['length'] for r in results if r['is_current'])
        
        # 結果の可視化
        visualize_results(results, current_length)
        
        print("\n=== 分析完了 ===")
        print("グラフが保存されました: fir_optimization_analysis.png")
    else:
        print("分析に失敗しました")

if __name__ == "__main__":
    main()
