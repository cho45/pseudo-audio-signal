# scripts/

フィルタ係数の生成・分析用スクリプト。

## 必要環境

- Python 3.12+
- uv（パッケージ管理）

## スクリプト一覧

| スクリプト | 説明 |
|-----------|------|
| generate_coeffs.py | フィルタ係数を生成し `coeffs.json` に出力 |
| verify_coeffs.py | 生成された `coeffs.json` の検証（理論特性との誤差評価） |
| calculate_power_error.py | 帯域別総パワー誤差の計算・評価 |
| fir_optimization_analysis.py | FIR係数の最適化分析・可視化 |

## 実行方法

### フィルタ係数の生成

```bash
uv run --python 3.12 --with numpy --with scipy scripts/generate_coeffs.py
```

`coeffs.json` が生成される。

### フィルタ係数の検証

```bash
# レポートモード（グラフ出力）
uv run --python 3.12 --with numpy --with scipy --with matplotlib scripts/verify_coeffs.py

# テストモード（CI用、基準値チェック）
uv run --python 3.12 --with numpy --with scipy scripts/verify_coeffs.py --test
```

- レポートモード: ITU-T G.227 理論特性との誤差を評価し、`scripts/verification_result.png` に出力
- テストモード: 基準値を超えた場合 exit code 1 を返す（CI向け）

### 帯域別総パワー誤差の評価

```bash
uv run --python 3.12 --with numpy --with scipy scripts/calculate_power_error.py
```

理論特性と実装フィルタ（IIR+FIR）の帯域別総パワーを比較し、誤差を出力する。

### FIR係数の最適化分析

```bash
uv run --python 3.12 --with numpy --with scipy --with matplotlib scripts/fir_optimization_analysis.py
```

以下の PNG ファイルが `scripts/` に出力される：

- `fir_optimization_analysis_44100.png`
- `fir_optimization_analysis_48000.png`

## 出力形式

`coeffs.json` の形式：

```json
{
  "44100": {
    "iir": { "num": [...], "den": [...] },
    "fir": [...]
  },
  "48000": {
    "iir": { "num": [...], "den": [...] },
    "fir": [...]
  }
}
```
