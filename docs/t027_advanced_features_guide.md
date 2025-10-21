# T027 Advanced Features Usage Guide

## Overview

T027 Advanced Features introduces three major enhancements to the Whisper Transcriber platform:

1. **API Key Management**: Secure programmatic access with comprehensive permissions and monitoring
2. **Batch Processing**: Upload and transcribe multiple files simultaneously with progress tracking
3. **Mobile PWA Enhancements**: Offline capabilities, push notifications, and improved mobile experience

## API Key Management System

### Getting Started

1. **Create an API Key:**
   ```bash
   curl -X POST "https://your-domain.com/api/v1/keys" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Production Integration",
       "permissions": ["transcribe_audio", "batch_upload"],
       "expires_in_days": 90,
       "rate_limit_per_minute": 100
     }'
   ```

2. **Use Your API Key:**
   ```bash
   curl -X POST "https://your-domain.com/api/v1/transcribe" \
     -H "X-API-Key: wt_prod_your_api_key_here" \
     -F "audio_file=@recording.wav" \
     -F "model=medium"
   ```

### Permission System

API keys support granular permissions:

- **`transcribe_audio`**: Submit individual transcription jobs
- **`batch_upload`**: Submit batch processing jobs  
- **`pwa_notifications`**: Manage push notifications and offline jobs
- **`admin_access`**: Full administrative access (admin users only)

### Rate Limiting and Quotas

Each API key has configurable limits:

- **Rate Limit**: Requests per minute (default: 60)
- **Daily Quota**: Total requests per day (default: 10,000)
- **Concurrent Jobs**: Maximum simultaneous transcriptions (default: 5)

Monitor usage through the dashboard:
```bash
GET /api/v1/keys/{key_id}/statistics
```

### Security Best Practices

1. **Environment-Specific Keys**: Use different keys for dev/staging/production
2. **Principle of Least Privilege**: Grant only necessary permissions
3. **Regular Rotation**: Regenerate keys periodically
4. **Monitor Usage**: Review usage logs for anomalies
5. **Secure Storage**: Store keys in environment variables or secure vaults

## Batch Processing System

### Creating Batches

Upload multiple audio files for simultaneous transcription:

```bash
curl -X POST "https://your-domain.com/api/v1/batch/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "batch_name=Conference Recordings Q4" \
  -F "description=All sessions from the quarterly conference" \
  -F "model=medium" \
  -F "language=en" \
  -F "priority=normal" \
  -F "auto_start=true" \
  -F "max_parallel_jobs=5" \
  -F "files=@session1.wav" \
  -F "files=@session2.mp3" \
  -F "files=@session3.m4a"
```

### Monitoring Progress

Track batch processing in real-time:

```bash
# Get overall progress
curl "https://your-domain.com/api/v1/batch/{batch_id}/progress" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get detailed batch information
curl "https://your-domain.com/api/v1/batch/{batch_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Batch Management

Control batch execution:

```bash
# Start a batch (if auto_start=false)
curl -X POST "https://your-domain.com/api/v1/batch/{batch_id}/start" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Cancel processing
curl -X POST "https://your-domain.com/api/v1/batch/{batch_id}/cancel" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Delete batch and files
curl -X DELETE "https://your-domain.com/api/v1/batch/{batch_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Batch Limits

- **Files per batch**: Maximum 50 files
- **File size**: Maximum 100MB per file
- **Total batch size**: Maximum 1GB
- **Parallel processing**: 1-10 concurrent jobs per batch
- **Active batches**: Maximum 10 per user

### WebSocket Updates

Receive real-time batch progress updates:

```javascript
const ws = new WebSocket('wss://your-domain.com/ws/batch');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.type === 'batch_progress') {
    console.log(`Batch ${update.batch_id}: ${update.progress_percentage}% complete`);
  }
};
```

## Mobile PWA Enhancements

### Push Notifications

Enable push notifications for job updates:

```javascript
// Register service worker
navigator.serviceWorker.register('/api/v1/pwa/service-worker.js');

// Request notification permission
const permission = await Notification.requestPermission();

// Subscribe to push notifications
const registration = await navigator.serviceWorker.ready;
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: 'your-vapid-public-key'
});

// Register subscription with server
await fetch('/api/v1/pwa/push/subscribe', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    endpoint: subscription.endpoint,
    keys: {
      p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')))),
      auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth'))))
    }
  })
});
```

### Offline Job Submission

Submit transcription jobs while offline:

```javascript
// Check if online
if (!navigator.onLine) {
  // Convert file to base64
  const fileReader = new FileReader();
  fileReader.onload = async (e) => {
    const base64Data = e.target.result.split(',')[1];
    
    // Store offline job
    await fetch('/api/v1/pwa/offline/jobs', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer YOUR_JWT_TOKEN',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        original_filename: file.name,
        file_data: base64Data,
        file_size: file.size,
        model: 'small',
        language: 'en'
      })
    });
  };
  fileReader.readAsDataURL(audioFile);
}
```

### Background Sync

Automatically sync offline jobs when connectivity returns:

```javascript
// In service worker
self.addEventListener('sync', (event) => {
  if (event.tag === 'offline-jobs-sync') {
    event.waitUntil(syncOfflineJobs());
  }
});

async function syncOfflineJobs() {
  const jobs = await getOfflineJobs(); // From IndexedDB
  
  for (const job of jobs) {
    try {
      const response = await fetch(`/api/v1/pwa/offline/jobs/${job.id}/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${job.token}`
        }
      });
      
      if (response.ok) {
        await removeOfflineJob(job.id);
      }
    } catch (error) {
      console.error('Sync failed for job:', job.id, error);
    }
  }
}
```

### PWA Installation

Make your app installable:

```javascript
// Listen for install prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  
  // Show install button
  const installButton = document.getElementById('install-button');
  installButton.style.display = 'block';
  
  installButton.addEventListener('click', () => {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('App installed');
      }
      deferredPrompt = null;
    });
  });
});
```

## Integration Examples

### Python SDK

```python
import requests
import time

class WhisperTranscriberClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {'X-API-Key': api_key}
    
    def create_batch(self, files, batch_name, **options):
        """Create a batch transcription job."""
        data = {'batch_name': batch_name, **options}
        files_data = [('files', open(f, 'rb')) for f in files]
        
        response = requests.post(
            f"{self.base_url}/api/v1/batch/upload",
            headers=self.headers,
            data=data,
            files=files_data
        )
        
        for _, file_obj in files_data:
            file_obj.close()
        
        return response.json()
    
    def wait_for_batch(self, batch_id, poll_interval=10):
        """Wait for batch to complete."""
        while True:
            response = requests.get(
                f"{self.base_url}/api/v1/batch/{batch_id}/progress",
                headers=self.headers
            )
            
            progress = response.json()
            print(f"Progress: {progress['progress_percentage']:.1f}%")
            
            if progress['status'] in ['completed', 'failed', 'cancelled']:
                return progress
            
            time.sleep(poll_interval)

# Usage
client = WhisperTranscriberClient(
    base_url="https://your-domain.com",
    api_key="wt_prod_your_api_key_here"
)

# Create batch
batch = client.create_batch(
    files=['audio1.wav', 'audio2.mp3'],
    batch_name="My Audio Collection",
    model="medium",
    language="en"
)

# Wait for completion
result = client.wait_for_batch(batch['batch_id'])
print(f"Batch completed: {result['successful_files']}/{result['total_files']} successful")
```

### Node.js SDK

```javascript
const FormData = require('form-data');
const fs = require('fs');
const fetch = require('node-fetch');

class WhisperTranscriberClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.headers = { 'X-API-Key': apiKey };
  }

  async createBatch(files, batchName, options = {}) {
    const formData = new FormData();
    formData.append('batch_name', batchName);
    
    Object.entries(options).forEach(([key, value]) => {
      formData.append(key, value);
    });
    
    files.forEach(file => {
      formData.append('files', fs.createReadStream(file));
    });

    const response = await fetch(`${this.baseUrl}/api/v1/batch/upload`, {
      method: 'POST',
      headers: this.headers,
      body: formData
    });

    return response.json();
  }

  async waitForBatch(batchId, pollInterval = 10000) {
    while (true) {
      const response = await fetch(
        `${this.baseUrl}/api/v1/batch/${batchId}/progress`,
        { headers: this.headers }
      );
      
      const progress = await response.json();
      console.log(`Progress: ${progress.progress_percentage.toFixed(1)}%`);
      
      if (['completed', 'failed', 'cancelled'].includes(progress.status)) {
        return progress;
      }
      
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }
}

// Usage
const client = new WhisperTranscriberClient(
  'https://your-domain.com',
  'wt_prod_your_api_key_here'
);

(async () => {
  const batch = await client.createBatch(
    ['audio1.wav', 'audio2.mp3'],
    'My Audio Collection',
    { model: 'medium', language: 'en' }
  );
  
  const result = await client.waitForBatch(batch.batch_id);
  console.log(`Batch completed: ${result.successful_files}/${result.total_files} successful`);
})();
```

## Troubleshooting

### Common Issues

**API Key Authentication Failures:**
- Verify key format: `wt_{env}_{32+_chars}`
- Check key permissions for the endpoint
- Ensure key hasn't expired
- Verify rate limits aren't exceeded

**Batch Upload Failures:**
- Check individual file size limits (100MB)
- Verify total batch size (1GB)
- Ensure supported audio formats
- Check available disk space

**PWA Notification Issues:**
- Verify VAPID keys configuration
- Check notification permissions
- Ensure HTTPS deployment
- Validate service worker registration

### Performance Optimization

**Batch Processing:**
- Use parallel jobs (3-5 recommended)
- Choose appropriate model size
- Pre-process audio files (normalize, compress)
- Monitor queue depth

**API Key Usage:**
- Implement exponential backoff for rate limits
- Cache responses when appropriate
- Use batch endpoints for multiple files
- Monitor quota usage

### Support

For technical support:
- Check system logs: `/api/v1/logs`
- Monitor health status: `/api/v1/health`
- Review API documentation: `/docs`
- Contact support with API key details (never share the actual key)