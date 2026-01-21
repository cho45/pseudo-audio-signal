export class NoiseNode extends AudioWorkletNode {
	constructor(context, opts) {
		super(context, 'noise-processor', {
			numberOfInputs: 0,
			numberOfOutputs: 1,
			channelCount: 1,
			channelCountMode: "explicit",
			channelInterpretation: "discrete",
			outputChannelCount: [1],
			processorOptions: {
				type: opts.type || 'whitenoise'
			}
		});
	}

	static async addModule(context) {
		const processor = (() => {
			// AudioWorkletGlobalScope
			class NoiseProcessor extends AudioWorkletProcessor {
				constructor(opts) {
					super();
					this.type = opts.processorOptions.type;

					this.func = {
						whitenoise: function (chData) {
							const variance = 1;
							const average = 0;
							for (let i = 0; i < chData.length; i += 2) {
								// Whitenoise by Box-Muller transform
								// Use 1.0 - Math.random() to avoid Math.log(0)
								const a = 1.0 - Math.random(), b = Math.random();
								const x = Math.sqrt(-2 * Math.log(a)) * Math.sin(2 * Math.PI * b) * variance + average;
								const y = Math.sqrt(-2 * Math.log(a)) * Math.cos(2 * Math.PI * b) * variance + average;
								chData[i+0] = x;
								chData[i+1] = y;
							}
						}
					}[this.type];
					
					if (!this.func) throw `unsupported noise type ${this.type}`;
				}

				process(inputs, outputs, _parameters) {
					const output = outputs[0];

					for (let ch = 0; ch < output.length; ch++) {
						const chData = output[ch];
						this.func(chData);
					}

					return true;
				}
			}

			registerProcessor('noise-processor', NoiseProcessor);
		}).toString();

		const url = URL.createObjectURL(new Blob(['(', processor, ')()'], { type: 'application/javascript' }));
		return Promise.all([
			context.audioWorklet.addModule(url),
		]);
	}
}
