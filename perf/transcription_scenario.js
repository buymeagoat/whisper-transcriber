import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { SharedArray } from 'k6/data';
import { b64decode } from 'k6/encoding';

const baseUrl = __ENV.BASE_URL || 'http://localhost:8001';
const uploadEndpoint = `${baseUrl}/uploads`;
const jobEndpoint = `${baseUrl}/jobs`;
const pollInterval = Number(__ENV.POLL_INTERVAL || 1);
const maxPolls = Number(__ENV.MAX_POLLS || 40);
const selectedModel = __ENV.WHISPER_MODEL || 'tiny';
const userIdHeader = __ENV.UPLOAD_USER_ID || 'perf-tester';

const audioFile = new SharedArray('sample-audio', () => {
  const encoded = open('./perf/assets/sample.wav.b64').replace(/\s+/g, '');
  const binary = b64decode(encoded, 'binary');
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

function initializeUpload(fileSize, filename) {
  const payload = JSON.stringify({
    filename,
    file_size: fileSize,
    model_name: selectedModel,
  });

  const res = http.post(`${uploadEndpoint}/initialize`, payload, {
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userIdHeader,
    },
  });

  const ok = check(res, {
    'upload initialized': (r) => r.status === 200,
    'session id present': (r) => Boolean(r.json('session_id')),
  });

  if (!ok) {
    transcriptionFailures.add(1);
    return null;
  }

  return {
    sessionId: res.json('session_id'),
    chunkSize: Number(res.json('chunk_size')),
    totalChunks: Number(res.json('total_chunks')),
  };
}

function getChunkData(buffer, chunkSize, chunkNumber) {
  const start = chunkNumber * chunkSize;
  const end = Math.min(start + chunkSize, buffer.byteLength || buffer.length || 0);

  if (buffer instanceof ArrayBuffer && typeof buffer.slice === 'function') {
    return buffer.slice(start, end);
  }

  if (ArrayBuffer.isView(buffer) && typeof buffer.buffer?.slice === 'function') {
    return buffer.buffer.slice(start, end);
  }

  if (typeof buffer === 'string') {
    return buffer.substring(start, end);
  }

  return buffer;
}

function uploadChunk(sessionId, chunkNumber, chunkData, audio) {
  const params = {
    headers: {
      'X-User-ID': userIdHeader,
    },
  };

  const res = http.post(
    `${uploadEndpoint}/${sessionId}/chunks/${chunkNumber}`,
    {
      chunk_data: http.file(chunkData, audio.name, audio.type),
    },
    params,
  );

  const ok = check(res, {
    'chunk uploaded': (r) => r.status === 200,
  });

  if (!ok) {
    transcriptionFailures.add(1);
    return false;
  }

  return true;
}

function finalizeUpload(sessionId) {
  const res = http.post(
    `${uploadEndpoint}/${sessionId}/finalize`,
    null,
    {
      headers: {
        'X-User-ID': userIdHeader,
      },
    },
  );

  const ok = check(res, {
    'upload finalized': (r) => r.status === 200,
    'job id returned': (r) => Boolean(r.json('job_id')),
  });

  if (!ok) {
    transcriptionFailures.add(1);
    return null;
  }

  return res.json('job_id');
}

function submitJob() {
  const audio = audioFile[0];
  const fileSize = audio.data.byteLength || audio.data.length || 0;

  const initResult = initializeUpload(fileSize, audio.name);
  if (!initResult) {
    return null;
  }

  const { sessionId, totalChunks, chunkSize } = initResult;
  const resolvedChunkSize = Number.isFinite(chunkSize) && chunkSize > 0 ? chunkSize : fileSize;
  const chunksToSend = Number.isFinite(totalChunks) && totalChunks > 0
    ? totalChunks
    : Math.max(1, Math.ceil(fileSize / resolvedChunkSize));

  for (let chunk = 0; chunk < chunksToSend; chunk += 1) {
    const chunkData = getChunkData(audio.data, resolvedChunkSize, chunk);
    const uploaded = uploadChunk(sessionId, chunk, chunkData, audio);
    if (!uploaded) {
      return null;
    }
  }

  return finalizeUpload(sessionId);
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
