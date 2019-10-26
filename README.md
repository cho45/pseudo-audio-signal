ITU-T G.227 疑似音声信号発生器
==============================

無線機の特性試験の試験方法に登場する「疑似音声信号発生器」を WebAudio で実現します。

「擬似音声発生器は、白色雑音をＩＴＵ－Ｔ勧告Ｇ．227の特性を有するフィルタによって帯域制限したものとする。」

## 仕組みや利用技術

WebAudio で音声を生成しています。白色雑音を生成するために AudioWorkletNode を使っているため、2019-10-25 の時点では Google Chrome でのみ動作します。

## ITU-T G.227 のフィルタ設計

ITU-T G.227 記載のアナログフィルタを双一次変換してデジタルIIRフィルタとし、さらにFIRを補正しています。係数の算出は以下の通り Jupyter Notebook で行いました。

- https://nbviewer.jupyter.org/github/cho45/pseudo-audio-signal/blob/master/docs/03-iir-fir.ipynb

## 参考資料

 * <a href="https://www.tele.soumu.go.jp/resource/j/equ/tech/betu/35.pdf">別表第三十五 証明規則第２条第１項第12号に掲げる無線設備の試験方法</a> (アマチュア無線機の試験方法)
 * <a href="https://www.itu.int/rec/T-REC-G.227-198811-I/en">ITU-T Recommendation G.227</a>

