class PCM16 extends AudioWorkletProcessor {
  constructor() {
    super(); this.samples = new Int16Array(3200); this.offset = 0;
    this.port.onmessage = () => {
      if (this.offset) {
        const tail = this.samples.slice(0, this.offset);
        this.port.postMessage(tail.buffer, [tail.buffer]); this.offset = 0;
      }
      this.port.postMessage('flushed');
    };
  }
  process(inputs) {
    const channels = inputs[0];
    if (!channels?.length) return true;
    for (let i = 0; i < channels[0].length; i++) {
      let sample = 0;
      for (const channel of channels) sample += channel[i];
      sample = Math.max(-1, Math.min(1, sample / channels.length));
      this.samples[this.offset++] = sample < 0 ? sample * 32768 : sample * 32767;
      if (this.offset === this.samples.length) {
        this.port.postMessage(this.samples.buffer, [this.samples.buffer]);
        this.samples = new Int16Array(3200); this.offset = 0;
      }
    }
    return true;
  }
}
registerProcessor('pcm16', PCM16);
