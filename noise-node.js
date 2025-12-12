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
							for (let i = 0; i < chData.length; i += 2) {
								// Box-Muller transform: generate two independent standard normal random variables
								// Math.random() returns [0, 1), use || to avoid log(0) = -Infinity
								const a = Math.random() || Number.MIN_VALUE;
								const b = Math.random();
								const r = Math.sqrt(-2 * Math.log(a));
								chData[i+0] = r * Math.sin(2 * Math.PI * b);
								chData[i+1] = r * Math.cos(2 * Math.PI * b);
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
