import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const frames=[];
let Processor;
vm.runInNewContext(readFileSync(new URL('../examples/browser/pcm-worklet.js',import.meta.url),'utf8'), {
  AudioWorkletProcessor:class {constructor(){this.port={postMessage:value=>frames.push(value)};}},
  Int16Array,
  registerProcessor:(_name,implementation)=>{Processor=implementation;},
});
const worklet=new Processor();
worklet.process([[Float32Array.from([-1,0,1,0.5])]]);
assert.equal(frames.length,0);
worklet.port.onmessage({data:'flush'});
assert.deepEqual(Array.from(new Int16Array(frames[0])),[-32768,0,32767,16383]);
assert.equal(frames[1],'flushed');
console.log('PCM16 clipping, signed samples and final partial frame preserved');
