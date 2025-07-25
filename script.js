import { createApp } from 'https://cdn.jsdelivr.net/npm/vue@3.5.17/dist/vue.esm-browser.js';
import { NoiseNode } from "./noise-node.js";

const appOptions = {
	data() {
		return {
			gainValue: -20,
			avg: 0.0,
			rms: 0.0,
			rmsMovingAvg: 0.0,
			peak: 0.0,
			waveType: "pseudoAudio",
			offset10dB: false, // F3E, F1E, G1E のときは 正弦波に対して +10dB の音声入力が必要
			isStarted: false,
			rmsHistory: [], // 移動平均用のRMS履歴
			customFreq: 1000, // カスタム正弦波の周波数
		};
	},

	methods: {
		start: async function () {
			if (!this.audioContext) {
				this.audioContext = new AudioContext();

				await Promise.all([
					NoiseNode.addModule(this.audioContext),
				]);

				this.oscillatorNode = this.audioContext.createOscillator();
				this.oscillatorNode.type = "sine";
				this.oscillatorNode.frequency.value = 1000;
				this.oscillatorNode.start();
				this.oscillatorGain = this.audioContext.createGain();
				this.oscillatorGain.gain.value = 0;

				this.noiseNode = new NoiseNode(this.audioContext, {});
				this.pseudoAudioGain = this.audioContext.createGain();
				this.pseudoAudioGain.gain.value = 0;

				this.whitenoiseGain = this.audioContext.createGain();
				this.whitenoiseGain.gain.value = 0;

				const [iir1, coeffs] = await this.coeffsPromise;
				console.log(iir1);

				this.iirFilterNode1 = this.audioContext.createIIRFilter(iir1.num, iir1.den);

				const firBuffer = this.audioContext.createBuffer(1, coeffs.length, this.audioContext.sampleRate);
				const firData = firBuffer.getChannelData(0);
				for (var i = 0, len = coeffs.length; i < len; i++) {
					firData[i] = coeffs[i];
				}

				this.firFilterNode = this.audioContext.createConvolver();
				this.firFilterNode.normalize = false;
				this.firFilterNode.buffer = firBuffer;

				this.offset10dBGain = this.audioContext.createGain();
				this.offset10dBGain.gain.value = 1;

				this.outGain = this.audioContext.createGain();

				[
					this.noiseNode,
					this.iirFilterNode1,
					this.firFilterNode,
					this.pseudoAudioGain,
					this.outGain
				].reduce( (r, i) => (r.connect(i), i));

				[
					this.noiseNode,
					this.whitenoiseGain,
					this.outGain
				].reduce( (r, i) => (r.connect(i), i));

				[
					this.oscillatorNode,
					this.oscillatorGain,
					this.outGain
				].reduce( (r, i) => (r.connect(i), i));

				[
					this.outGain,
					this.offset10dBGain,
					this.audioContext.destination
				].reduce( (r, i) => (r.connect(i), i));

				this.analyser = this.audioContext.createAnalyser();
				this.analyser.maxDecibels = -20;
				this.analyser.minDecibels = -120;
				console.log(this.analyser);
				this.analyser.fftSize = 2**13;
				console.log(this.analyser.fftSize);
				this.offset10dBGain.connect(this.analyser);
				const data = new Float32Array(this.analyser.fftSize);
				const range = this.analyser.minDecibels - this.analyser.maxDecibels; // -70
				const freqMax = Math.log(this.audioContext.sampleRate / 2);

				{
					const canvas = this.$refs.spectrumGrid;
					const ctx = canvas.getContext('2d');
					ctx.strokeStyle = "#cccccc";
					ctx.fillStyle = "#cccccc";
					ctx.font = "20px sans-serif";
					ctx.textBaseline = "top";
					for (let f of [33, 50, 100, 500, 1000, 5000, 10000]) {
						const freq = Math.log(f);
						const x = freq / freqMax * canvas.width;
						ctx.moveTo(x, 0);
						ctx.lineTo(x, canvas.height);
						ctx.fillText(`${f}`, x + 2, 0);
					}
					ctx.stroke();

					ctx.beginPath();
					for (let dB of [-10, -20, -30, -40, -50, -60, -70, -80, -90, -100]) {
						const y = (dB - this.analyser.maxDecibels) / range;
						ctx.moveTo(0, canvas.height * y)
						ctx.lineTo(canvas.width, canvas.height * y);
						ctx.fillText(`${dB} dB`, 0, canvas.height * y);
					}
					ctx.stroke();

				};

				const canvas = this.$refs.spectrum;
				const ctx = canvas.getContext('2d');
				ctx.strokeStyle = "#000000";
				ctx.fillStyle = "#000000";
				const freqLog = new Float32Array(this.analyser.frequencyBinCount).map( (_, i) => Math.log( this.audioContext.sampleRate / this.analyser.fftSize * i) );
				const draw = () => {
					this.analyser.getFloatFrequencyData(data);
					ctx.clearRect(0, 0, canvas.width, canvas.height);

					ctx.beginPath();
					for (var i = 0, len = this.analyser.frequencyBinCount; i < len; i++) {
						const x = freqLog[i] / freqMax * canvas.width;
						const y = (data[i] - this.analyser.maxDecibels) / range;
						if (i === 0) {
							ctx.moveTo(x, (canvas.height * y));
						} else {
							ctx.lineTo(x, (canvas.height * y));
						}
					}
					ctx.stroke();

					this.analyser.getFloatTimeDomainData(data);
					this.avg = data.reduce( (r, i) => r + Math.abs(i), 0) / data.length;
					this.rms = Math.sqrt( data.reduce( (r, i) => r + (i * i), 0) / data.length );
					this.peak = Math.max(...data);
					
					// 移動平均の計算（5秒間、約60FPS）
					this.rmsHistory.push(this.rms);
					if (this.rmsHistory.length > 120) {
						this.rmsHistory.shift();
					}
					this.rmsMovingAvg = this.rmsHistory.reduce((sum, val) => sum + val, 0) / this.rmsHistory.length;

					requestAnimationFrame(draw);
				};
				requestAnimationFrame(draw);
			}
			this.isStarted = true;
			this.applySetting();
		},

		applySetting: function () {
			if (!this.isStarted) {
				return;
			}
			this.oscillatorGain.gain.value = 0;
			this.pseudoAudioGain.gain.value = 0;
			this.whitenoiseGain.gain.value = 0;
			switch (this.waveType) {
				case "sine1000Hz":
					this.oscillatorNode.frequency.value = 1000;
					this.oscillatorGain.gain.value = Math.sqrt(2);
					break;
				case "sine1500Hz":
					this.oscillatorNode.frequency.value = 1500;
					this.oscillatorGain.gain.value = Math.sqrt(2);
					break;
				case "sineCustom":
					this.oscillatorNode.frequency.value = Math.max(20, Math.min(20000, this.customFreq));
					this.oscillatorGain.gain.value = Math.sqrt(2);
					break;
				case "pseudoAudio":
					// see also: docs/calculate_rms_normalization.py
					this.pseudoAudioGain.gain.value = 6.69283
					console.log(this.pseudoAudioGain.gain.value);
					break;
				case "whitenoise":
					this.whitenoiseGain.gain.value = 1;
					break;
			}
			this.outGain.gain.value = this.gainValueRate;
			this.offset10dBGain.gain.value = this.offset10dB ? Math.pow(10, 10 / 20) : 1;
		},

		stop: async function () {
			this.outGain.gain.value = 0;
			this.isStarted = false;
		},

		toggleStartStop: function () {
			if (this.isStarted) {
				this.stop();
			} else {
				this.start();
			}
		},

		handleKeyDown: function (event) {
			// 入力フィールドにフォーカスがある場合はスキップ
			if (event.target.tagName === 'INPUT') {
				return;
			}

			const keyActions = {
				'Space': () => this.toggleStartStop(),
				'ArrowUp': () => this.gainValue = Math.min(0, this.gainValue + 1),
				'ArrowDown': () => this.gainValue = Math.max(-100, this.gainValue - 1),
				'Digit1': () => this.waveType = 'pseudoAudio',
				'Digit2': () => this.waveType = 'whitenoise',
				'Digit3': () => this.waveType = 'sine1000Hz',
				'Digit4': () => this.waveType = 'sine1500Hz',
				'Digit5': () => this.waveType = 'sineCustom',
				'KeyO': () => this.offset10dB = !this.offset10dB,
				'Equal': () => this.offset10dB = !this.offset10dB, // + key (without shift)
				'KeyF': () => {
					if (this.waveType === 'sineCustom') {
						const freqInput = document.getElementById('customFreq');
						if (freqInput) freqInput.focus();
					}
				}
			};

			const action = keyActions[event.code];
			if (action) {
				event.preventDefault();
				action();
			}
		},
	},

	computed: {
		gainValueRate: function () {
			return Math.pow(10, +this.gainValue / 20);
		}
	},

	async mounted() {
		this.coeffsPromise = (await fetch('./coeffs.json')).json();

		// キーボードイベントリスナーの追加
		document.addEventListener('keydown', this.handleKeyDown);

		this.$watch('gainValue', (n) => {
			this.applySetting();
		});

		this.$watch('waveType', () => {
			this.applySetting();
		});

		this.$watch('offset10dB', () => {
			this.applySetting();
		});

		this.$watch('customFreq', () => {
			if (this.waveType === 'sineCustom') {
				this.applySetting();
			}
		});
	},

	unmounted() {
		// キーボードイベントリスナーの削除
		document.removeEventListener('keydown', this.handleKeyDown);
	}
};

createApp(appOptions).mount('#app');

