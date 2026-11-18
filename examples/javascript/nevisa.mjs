// Node.js 22+; no npm packages. Run `node nevisa.mjs --help`.
import { readFile, writeFile } from 'node:fs/promises';
import { basename } from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';

const usage = `Usage: node examples/javascript/nevisa.mjs <command> [arguments]
  balance
  discover
  asr AUDIO [nevisa-file|nevisa-live|nevisa-fusion]
  tts TEXT [pocket-nova|ariana-ava] [SPEAKER_NUMBER] [speech.mp3]
  ocr DOCUMENT [PAGES]
  chat PROMPT
Set NEVISA_API_KEY; optionally NEVISA_BASE_URL and NEVISA_TIMEOUT (seconds).
For WebSocket streaming, use examples/python/nevisa.py live.`;

async function main() {
  const [command, ...args] = process.argv.slice(2);
  if (!command || command === '--help') { console.log(usage); return; }
  const base = (process.env.NEVISA_BASE_URL || 'https://persianspeech.com').replace(/\/+$/, '');
  const key = process.env.NEVISA_API_KEY?.trim();
  if (!key) throw new Error('Set NEVISA_API_KEY to your personal API key.');
  const timeout = Number(process.env.NEVISA_TIMEOUT || 600) * 1000;
  const headers = { 'X-API-Key': key };
  const request = async (path, init = {}) => {
    const response = await fetch(base + path, {
      ...init, headers: { ...headers, ...init.headers }, redirect: 'error',
      signal: AbortSignal.timeout(Math.min(timeout, 180000)),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${(await response.text()).slice(0, 1000)}`);
    return response;
  };
  const json = async (path, init) => (await request(path, init)).json();
  const created = (body, array = true) => {
    if (body.errors?.length) throw new Error(JSON.stringify(body.errors));
    const job = array ? body.created?.[0] : body.created;
    if (!job) throw new Error('No job was accepted.');
    return job;
  };
  const wait = async (prefix, job) => {
    const deadline = Date.now() + timeout;
    while (!['completed', 'failed', 'canceled'].includes(job.status)) {
      if (Date.now() >= deadline) throw new Error(`Polling deadline reached. Resume with GET ${prefix}${job.job_key}/`);
      await sleep(2000);
      job = await json(`${prefix}${job.job_key}/`);
    }
    if (job.status !== 'completed') throw new Error(job.error_message || job.status);
    return job;
  };
  const upload = async (field, filename) => {
    if (!filename) throw new Error('Provide a file path.');
    const form = new FormData();
    form.append(field, new Blob([await readFile(filename)]), basename(filename));
    return form;
  };
  switch (command) {
    case 'balance': console.log(await json('/api/billing/balance/')); break;
    case 'discover':
      for (const path of ['/api/jobs/engines/', '/api/tts/jobs/models/', '/api/ocr/jobs/engines/', '/api/llm/v1/models']) {
        try { console.log(path, JSON.stringify(await json(path), null, 2)); }
        catch (error) { console.error(path, error.message); }
      }
      break;
    case 'asr': {
      const engine = args[1] || 'nevisa-file';
      if (!['nevisa-file', 'nevisa-live', 'nevisa-fusion'].includes(engine)) throw new Error('Unknown ASR engine.');
      const form = await upload('audio', args[0]);
      form.set('language', 'fa'); form.set('engine', engine);
      const job = await wait('/api/jobs/', created(await json('/api/jobs/upload/', { method: 'POST', body: form })));
      console.log(job.result_text); break;
    }
    case 'tts': {
      if (!args[0]) throw new Error('Provide the text to synthesize.');
      const model = args[1] || 'pocket-nova';
      const selected = (await json('/api/tts/jobs/models/')).find(item => item.id === model || item.pricing_key === model);
      const speaker = Number(args[2] || 1);
      if (!selected || !Number.isInteger(speaker) || speaker < 1 || speaker > selected.voices.length) {
        throw new Error('Model/speaker unavailable. Run discover first.');
      }
      const form = new FormData();
      form.set('text', args[0]); form.set('model', selected.id);
      form.set('voice', selected.voices[speaker - 1]); form.set('language', 'fa');
      const job = await wait('/api/tts/jobs/', created(await json('/api/tts/jobs/synthesize/', { method: 'POST', body: form }), false));
      const response = await request(`/api/tts/jobs/${job.job_key}/audio/?format=mp3&download=1`);
      const output = args[3] || 'speech.mp3';
      await writeFile(output, Buffer.from(await response.arrayBuffer()));
      console.log(`Saved ${output}`); break;
    }
    case 'ocr': {
      const form = await upload('document', args[0]);
      form.set('engine', 'bina'); form.set('language', 'fa'); form.set('pages', args[1] || '');
      const job = await wait('/api/ocr/jobs/', created(await json('/api/ocr/jobs/upload/', { method: 'POST', body: form })));
      console.log(job.result_text); break;
    }
    case 'chat': {
      if (!args[0]) throw new Error('Provide a prompt.');
      const models = (await json('/api/llm/v1/models')).data;
      if (!models.length) throw new Error('No language model is available for this account.');
      const body = await json('/api/llm/v1/chat/completions', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: models[0].id, messages: [{ role: 'user', content: args[0] }], max_tokens: 128, stream: false }),
      });
      console.log(body.choices[0].message.content); break;
    }
    default: throw new Error(usage);
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
