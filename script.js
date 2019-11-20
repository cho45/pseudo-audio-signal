
import { NoiseNode } from "./noise-node.js";

Vue.use(VueMaterial.default)

new Vue({
	el: '#app',
	data: {
		gainValue: -20,
		avg: 0.0,
		rms: 0.0,
		peak: 0.0,
		waveType: "pseudoAudio",
		offset10dB: false, // F3E, F1E, G1E のときは 正弦波に対して +10dB の音声入力が必要
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

					requestAnimationFrame(draw);
				};
				requestAnimationFrame(draw);
			}
			this.applySetting();
		},

		applySetting: function () {
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
				case "pseudoAudio":
					this.pseudoAudioGain.gain.value = 6.666;
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
		},
	},

	computed: {
		gainValueRate: function () {
			return Math.pow(10, +this.gainValue / 20);
		}
	},

	mounted: async function () {
		this.coeffsPromise = (await fetch('./coeffs.json')).json();

		this.$watch('gainValue', (n) => {
			this.applySetting();
		});

		this.$watch('waveType', () => {
			this.applySetting();
		});

		this.$watch('offset10dB', () => {
			this.applySetting();
		});
	},
})

