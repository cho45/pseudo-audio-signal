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
| fir_optimization_analysis.py | FIR係数の最適化分析・可視化 |

## 実行方法

### フィルタ係数の生成

```bash
uv run --python 3.12 --with numpy --with scipy scripts/generate_coeffs.py
```

`coeffs.json` が生成される。

### フィルタ係数の検証

```bash
uv run --python 3.12 --with numpy --with scipy --with matplotlib scripts/verify_coeffs.py
```

ITU-T G.227 理論特性との誤差を評価し、`scripts/verification_result.png` に出力。

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
