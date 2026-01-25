ITU-T G.227 疑似音声信号発生器
==============================

無線機の特性試験の試験方法に登場する「疑似音声信号発生器」を WebAudio で実現します。

「擬似音声発生器は、白色雑音をＩＴＵ－Ｔ勧告Ｇ．227の特性を有するフィルタによって帯域制限したものとする。」

## 仕組みや利用技術

WebAudio で音声を生成しています。白色雑音を生成するために AudioWorkletNode を使っているため、サポートするブラウザが必要です。

 * Google Chrome 67
 * Mozilla Firefox 76
 * Microsoft Edge 79

## 測定器としての使用方法

実際の無線機測定に使用する場合は、以下のガイドを参照してください：

- **[測定器としての使用ガイド](./MEASUREMENT_GUIDE.md)** - DAC選定、校正方法、セットアップ手順

## ITU-T G.227 のフィルタ設計

<img src="./docs/G.227-curve.png">

ITU-T G.227 記載のアナログフィルタを双一次変換してデジタルIIRフィルタとし、さらにFIRで補正しています。係数の算出は以下の通り Jupyter Notebook で行いました。

理論特性に対する誤差（RMSE）:

| 帯域 | 44100Hz | 48000Hz |
|------|---------|---------|
| 10Hz〜ナイキスト | 0.025 dB (0.29%) | 0.022 dB (0.25%) |
| G.227 Figure 2 範囲 (50Hz-10kHz) | 0.008 dB (0.09%) | 0.007 dB (0.08%) |
| 電話音声帯域 (300Hz-3.4kHz) | 0.007 dB (0.08%) | 0.007 dB (0.08%) |

- https://nbviewer.jupyter.org/github/cho45/pseudo-audio-signal/blob/master/docs/03-iir-fir.ipynb

## 実装アーキテクチャ

### 信号処理フロー

```
White Noise → IIR Filter → FIR Filter → Output
Generator      (4th order)   (Correction)
   |               |             |
AudioWorklet   coeffs.iir    coeffs.fir
```

### 雑音発生方式

ホワイトノイズ生成には **Box-Muller変換** を使用し、正規分布に従う高品質な雑音を生成しています：

### フィルタ係数

すべてのフィルタ係数は `coeffs.json` に事前計算済みで格納されています（44100Hz / 48000Hz 対応）：

```json
{
  "44100": {
    "iir": { "num": [...], "den": [...] },
    "fir": [...]
  },
  "48000": { ... }
}
```

係数の再生成は `scripts/generate_coeffs.py` で行えます。

### WebAudio API実装

```javascript
const sr = audioContext.sampleRate;  // 44100 or 48000
const c = coeffs[sr];

// IIRフィルタ (4次)
const iirFilter = audioContext.createIIRFilter(c.iir.num, c.iir.den);

// FIRフィルタ (畳み込み)
const firFilter = audioContext.createConvolver();
// c.fir をインパルス応答として設定
```

この2段階のフィルタリングにより、ITU-T G.227の理論特性を高精度で実現しています。

## 参考資料

 * <a href="https://www.tele.soumu.go.jp/resource/j/equ/tech/betu/35.pdf">別表第三十五 証明規則第２条第１項第12号に掲げる無線設備の試験方法</a> (アマチュア無線機の試験方法)
 * <a href="https://www.itu.int/rec/T-REC-G.227-198811-I/en">ITU-T Recommendation G.227</a>

