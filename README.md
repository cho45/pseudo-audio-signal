ITU-T G.227 疑似音声信号発生器
==============================

無線機の特性試験の試験方法に登場する「疑似音声信号発生器」を WebAudio で実現します。

「擬似音声発生器は、白色雑音をＩＴＵ－Ｔ勧告Ｇ．227の特性を有するフィルタによって帯域制限したものとする。」

## 仕組みや利用技術

WebAudio で音声を生成しています。白色雑音を生成するために AudioWorkletNode を使っているため、2019-10-25 の時点では Google Chrome でのみ動作します。

## ITU-T G.227 のフィルタ設計

<img src="data:image/png;base64,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j677y1/+cvSYX/3qV7nrrrtYsWIFq1ev5q233uLdd98N6hjtoTNuEZEocrIz4q62ceNGbrjhBmpqarjooot45JFHjrldQ0MD1113Heecc87ngruyspLLL7+c73znO0yePPkz6/bt28f777/PE088ccz9bt68mYaGBq6++uqjy3JycoKq/atf/erR51deeSX33HMPPp8PgA8++IAnn3yS6upqFixYQElJyWfqzc/P5/zzzw/qOG2l4BYRkU4zefJkCgoKKC8vJysri7Fjx7JmzRp+97vfsWrVqmO+p7GxkRtvvJEePXrwy1/+8jPrampquPTSS7ngggv4zne+87n3zp07l4svvpiePXu2udaEhASampqOvm49QUpaWtrR5926dWP27Nk888wzAMyePZvu3btTWVmJmbFy5cpOmc40GGoqFxGRTjNixIijTdOHDh06ury6uvqY2zc1NXHTTTcRHx/PY4899pmJSmpra7nsssuYNm0aP/nJT475/r/85S987WtfO249o0aNIiEhgRdffPHosuaz5uHDh7Ny5UoA5s2bR3Fx8Qk/20033cQTTzzBE088cbSZPD09nbPPPpsHH3zw6Ha7du1i//79J9xXRyi4RUSkUz3xxBOMHj2a008/nXHjxjFjxgxWr17NXXfdBcBrr73G17/+dQDeeustnn76adatW8dpp53GWWedxR133AHAY489xoIFC3j77bePDvv62c9+dvQ4ixcvpqqqigsvvPC4tSQkJPDqq6/yxz/+kQkTJjBx4kTefPNNAH7605/y0EMPMWnSJN544w3y8vJO+LlmzJhBRUUFFRUVzJgx4+jyv/71r2zcuJEJEyYwYcIErr32WsrLy9v3ywuCNY+JC2dTpkxxx2tiEelsCxYsYObMmWGzn0g7diSItu8mPz+fMWPGdOo+vRKNNxlp1pbvycxWO+eOeZm8zrhFREQiiIJbREQkgii4RUSiQCR0e8ayzvx+FNwiIhEuJSUFn8+n8A5Tzjl8Ph8pKSmdsj+N4xYRiXADBgxg9+7dn5kEJFLV1tZ2WsCF07FTUlIYMGBAp+xLwS0iEuESExMZMmSI12V0igULFnxudrRYOHZbqKlcREQkgii4RUREIoiCW0REJIIouEVERCKIgltERCSCKLhFREQiiIJbREQkgii4RUREIoiCW0REJIIouEVERCKIgltE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">

ITU-T G.227 記載のアナログフィルタを双一次変換してデジタルIIRフィルタとし、さらにFIRを補正しています。係数の算出は以下の通り Jupyter Notebook で行いました。

- https://nbviewer.jupyter.org/github/cho45/pseudo-audio-signal/blob/master/docs/03-iir-fir.ipynb

## 参考資料

 * <a href="https://www.tele.soumu.go.jp/resource/j/equ/tech/betu/35.pdf">別表第三十五 証明規則第２条第１項第12号に掲げる無線設備の試験方法</a> (アマチュア無線機の試験方法)
 * <a href="https://www.itu.int/rec/T-REC-G.227-198811-I/en">ITU-T Recommendation G.227</a>

