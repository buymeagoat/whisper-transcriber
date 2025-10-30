import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { SharedArray } from 'k6/data';
import { b64decode } from 'k6/encoding';

const baseUrl = __ENV.BASE_URL || 'http://localhost:8001';
const jobEndpoint = `${baseUrl}/jobs`;
const pollInterval = Number(__ENV.POLL_INTERVAL || 1);
const maxPolls = Number(__ENV.MAX_POLLS || 40);
const selectedModel = __ENV.WHISPER_MODEL || 'tiny';

const audioFile = new SharedArray('sample-audio', () => {
  const encoded = open('./perf/assets/sample.wav.b64').replace(/\s+/g, '');
  const binary = b64decode(encoded);
  return [{
    data: binary,
    name: 'sample.wav',
    type: 'audio/wav',
  }];
});

const transcriptionLatency = new Trend('transcription_latency_seconds');
const transcriptionSuccess = new Rate('transcription_success_rate');
const transcriptionFailures = new Rate('transcription_failure_rate');

export const options = {
  summaryTrendStats: ['avg', 'min', 'max', 'p(90)', 'p(95)'],
  scenarios: {
    submit_and_poll: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.ARRIVAL_RATE || 3),
      timeUnit: '1s',
      duration: __ENV.DURATION || '2m',
      preAllocatedVUs: Number(__ENV.PRE_ALLOCATED_VUS || 4),
      maxVUs: Number(__ENV.MAX_VUS || 12),
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['avg<3000', 'p(95)<5000'],
    transcription_success_rate: ['rate>0.95'],
    transcription_failure_rate: ['rate<0.05'],
    transcription_latency_seconds: ['p(95)<120'],
  },
};

function submitJob() {
  const audio = audioFile[0];
  const payload = {
    file: http.file(audio.data, audio.name, audio.type),
    model: selectedModel,
  };

  const res = http.post(`${jobEndpoint}/`, payload);

  const ok = check(res, {
    'job created': (r) => r.status === 200,
    'job id present': (r) => Boolean(r.json('job_id')),
  });

  if (!ok) {
    transcriptionFailures.add(1);
    return null;
  }

  return res.json('job_id');
}

function pollJob(jobId) {
  for (let attempt = 0; attempt < maxPolls; attempt += 1) {
    const res = http.get(`${jobEndpoint}/${jobId}`);
    const status = res.json('status');

    if (status === 'COMPLETED' || status === 'completed') {
      check(res, {
        'transcript returned': (r) => r.json('transcript') && r.json('transcript').length > 0,
      });
      transcriptionSuccess.add(1);
      return true;
    }

    if (status === 'FAILED' || status === 'failed') {
      transcriptionFailures.add(1);
      return false;
    }

    sleep(pollInterval);
  }

  transcriptionFailures.add(1);
  return false;
}

export default function () {
  const start = Date.now();
  const jobId = submitJob();
  if (!jobId) {
    return;
  }

  const finished = pollJob(jobId);
  const latency = (Date.now() - start) / 1000;
  transcriptionLatency.add(latency);

  check({ finished, latency }, {
    'job completed before timeout': (result) => result.finished === true,
    'latency under 2 minutes': (result) => result.latency < 120,
  });
}
