/**
 * T029 Enhanced User Experience: Advanced File Upload Service
 * Service for enhanced file upload with preview, validation, and metadata extraction
 */

class AdvancedFileUploadService {
  constructor() {
    this.supportedFormats = [
      // Audio formats
      { ext: 'mp3', mime: 'audio/mpeg', category: 'audio' },
      { ext: 'wav', mime: 'audio/wav', category: 'audio' },
      { ext: 'flac', mime: 'audio/flac', category: 'audio' },
      { ext: 'm4a', mime: 'audio/mp4', category: 'audio' },
      { ext: 'ogg', mime: 'audio/ogg', category: 'audio' },
      { ext: 'wma', mime: 'audio/x-ms-wma', category: 'audio' },
      { ext: 'aac', mime: 'audio/aac', category: 'audio' },
      { ext: 'opus', mime: 'audio/opus', category: 'audio' },
      
      // Video formats (audio will be extracted)
      { ext: 'mp4', mime: 'video/mp4', category: 'video' },
      { ext: 'mov', mime: 'video/quicktime', category: 'video' },
      { ext: 'avi', mime: 'video/x-msvideo', category: 'video' },
      { ext: 'mkv', mime: 'video/x-matroska', category: 'video' },
      { ext: 'webm', mime: 'video/webm', category: 'video' },
      { ext: 'wmv', mime: 'video/x-ms-wmv', category: 'video' }
    ];
    
    this.audioContext = null;
    this.analyserNode = null;
  }

  /**
   * Validate file with comprehensive checks
   */
  async validateFile(file) {
    const validation = {
      isValid: true,
      errors: [],
      warnings: [],
      metadata: {},
      health: 'unknown'
    };

    // Basic file checks
    if (!file) {
      validation.errors.push('No file provided');
      validation.isValid = false;
      return validation;
    }

    // File size validation
    const maxSize = 1024 * 1024 * 1024; // 1GB
    if (file.size > maxSize) {
      validation.errors.push(`File size (${this.formatFileSize(file.size)}) exceeds maximum allowed (1GB)`);
      validation.isValid = false;
    }

    if (file.size < 1024) {
      validation.warnings.push(`File size is very small (${file.size} bytes)`);
    }

    // Format validation
    const format = this.detectFileFormat(file);
    if (!format) {
      validation.errors.push(`Unsupported file format: ${file.name.split('.').pop()}`);
      validation.isValid = false;
    } else {
      validation.metadata.format = format;
    }

    // File name validation
    if (file.name.length > 255) {
      validation.errors.push('File name too long (max 255 characters)');
      validation.isValid = false;
    }

    if (!/^[\w\-. ()]+\.\w+$/.test(file.name)) {
      validation.warnings.push('File name contains special characters that may cause issues');
    }

    // Extract metadata
    try {
      const metadata = await this.extractMetadata(file);
      validation.metadata = { ...validation.metadata, ...metadata };
    } catch (error) {
      validation.warnings.push(`Could not extract metadata: ${error.message}`);
    }

    // File health check
    try {
      const health = await this.checkFileHealth(file);
      validation.health = health;
      
      if (health === 'corrupted') {
        validation.errors.push('File appears to be corrupted');
        validation.isValid = false;
      } else if (health === 'suspicious') {
        validation.warnings.push('File may have issues - proceed with caution');
      }
    } catch (error) {
      validation.warnings.push(`Could not verify file integrity: ${error.message}`);
    }

    return validation;
  }

  /**
   * Detect file format based on name and MIME type
   */
  detectFileFormat(file) {
    const extension = file.name.split('.').pop()?.toLowerCase();
    const mimeType = file.type.toLowerCase();

    // First try by MIME type
    let format = this.supportedFormats.find(f => f.mime === mimeType);
    
    // Fallback to extension
    if (!format) {
      format = this.supportedFormats.find(f => f.ext === extension);
    }

    return format;
  }

  /**
   * Extract metadata from audio/video file
   */
  async extractMetadata(file) {
    return new Promise((resolve) => {
      const metadata = {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: new Date(file.lastModified),
        extension: file.name.split('.').pop()?.toLowerCase()
      };

      // Try to extract audio metadata using Web Audio API
      if (file.type.startsWith('audio/') || file.type.startsWith('video/')) {
        const audio = new Audio();
        const url = URL.createObjectURL(file);
        
        audio.addEventListener('loadedmetadata', () => {
          metadata.duration = audio.duration;
          metadata.audioTracks = audio.audioTracks?.length || 1;
          
          URL.revokeObjectURL(url);
          resolve(metadata);
        });

        audio.addEventListener('error', () => {
          URL.revokeObjectURL(url);
          resolve(metadata); // Return basic metadata even if audio loading fails
        });

        audio.src = url;
      } else {
        resolve(metadata);
      }
    });
  }

  /**
   * Generate audio preview and waveform data
   */
  async generateAudioPreview(file) {
    try {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }

      const arrayBuffer = await file.arrayBuffer();
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      
      // Generate waveform data
      const waveformData = this.generateWaveformData(audioBuffer);
      
      // Create preview audio blob (first 30 seconds)
      const previewBuffer = this.createPreviewBuffer(audioBuffer, 30);
      const previewBlob = await this.audioBufferToBlob(previewBuffer);
      
      return {
        duration: audioBuffer.duration,
        sampleRate: audioBuffer.sampleRate,
        channels: audioBuffer.numberOfChannels,
        waveform: waveformData,
        previewUrl: URL.createObjectURL(previewBlob),
        peaks: this.calculateAudioPeaks(audioBuffer)
      };
    } catch (error) {
      console.warn('Could not generate audio preview:', error);
      return null;
    }
  }

  /**
   * Generate waveform visualization data
   */
  generateWaveformData(audioBuffer, samples = 1000) {
    const rawData = audioBuffer.getChannelData(0);
    const blockSize = Math.floor(rawData.length / samples);
    const waveformData = [];

    for (let i = 0; i < samples; i++) {
      let blockStart = blockSize * i;
      let sum = 0;
      let max = 0;

      for (let j = 0; j < blockSize; j++) {
        const sample = Math.abs(rawData[blockStart + j]);
        sum += sample;
        max = Math.max(max, sample);
      }

      waveformData.push({
        average: sum / blockSize,
        peak: max
      });
    }

    return waveformData;
  }

  /**
   * Create preview buffer (first N seconds)
   */
  createPreviewBuffer(audioBuffer, seconds) {
    const previewLength = Math.min(
      seconds * audioBuffer.sampleRate,
      audioBuffer.length
    );

    const previewBuffer = this.audioContext.createBuffer(
      audioBuffer.numberOfChannels,
      previewLength,
      audioBuffer.sampleRate
    );

    for (let channel = 0; channel < audioBuffer.numberOfChannels; channel++) {
      const originalData = audioBuffer.getChannelData(channel);
      const previewData = previewBuffer.getChannelData(channel);
      
      for (let i = 0; i < previewLength; i++) {
        previewData[i] = originalData[i];
      }
    }

    return previewBuffer;
  }

  /**
   * Convert audio buffer to blob
   */
  async audioBufferToBlob(audioBuffer) {
    const length = audioBuffer.length;
    const numberOfChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    
    // Create WAV file
    const buffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
    const view = new DataView(buffer);
    
    // WAV header
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * numberOfChannels * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numberOfChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numberOfChannels * 2, true);
    view.setUint16(32, numberOfChannels * 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * numberOfChannels * 2, true);
    
    // Convert audio data
    let offset = 44;
    for (let i = 0; i < length; i++) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const sample = Math.max(-1, Math.min(1, audioBuffer.getChannelData(channel)[i]));
        view.setInt16(offset, sample * 0x7FFF, true);
        offset += 2;
      }
    }
    
    return new Blob([buffer], { type: 'audio/wav' });
  }

  /**
   * Calculate audio peaks for visualization
   */
  calculateAudioPeaks(audioBuffer) {
    const channelData = audioBuffer.getChannelData(0);
    const peaks = [];
    const peakDistance = Math.floor(channelData.length / 100); // 100 peaks across the file
    
    for (let i = 0; i < 100; i++) {
      const start = i * peakDistance;
      const end = Math.min(start + peakDistance, channelData.length);
      let peak = 0;
      
      for (let j = start; j < end; j++) {
        peak = Math.max(peak, Math.abs(channelData[j]));
      }
      
      peaks.push(peak);
    }
    
    return peaks;
  }

  /**
   * Check file health and integrity
   */
  async checkFileHealth(file) {
    try {
      // Read first few bytes to check file signature
      const header = await this.readFileHeader(file, 16);
      
      // Check for common file signatures
      const signatures = {
        // Audio signatures
        'ID3': 'mp3',
        'fff': 'mp3', // MP3 frame sync
        'RIFF': 'wav',
        'fLaC': 'flac',
        'ftypM4A': 'm4a',
        'OggS': 'ogg',
        
        // Video signatures
        'ftypmp4': 'mp4',
        'ftypisom': 'mp4',
        'ftypqt': 'mov',
        'RIFF': 'avi' // AVI also uses RIFF
      };

      // Convert header to string for signature checking
      const headerStr = Array.from(header)
        .map(byte => String.fromCharCode(byte))
        .join('');

      // Check if file starts with expected signature
      const expectedFormat = this.detectFileFormat(file);
      if (expectedFormat) {
        // Look for matching signature
        const hasValidSignature = Object.keys(signatures).some(sig => 
          headerStr.includes(sig) && signatures[sig] === expectedFormat.ext
        );

        if (!hasValidSignature) {
          return 'suspicious';
        }
      }

      // Additional checks for specific formats
      if (file.type.startsWith('audio/') || file.type.startsWith('video/')) {
        return await this.checkMediaFileHealth(file);
      }

      return 'healthy';
    } catch (error) {
      console.warn('File health check failed:', error);
      return 'unknown';
    }
  }

  /**
   * Read file header bytes
   */
  async readFileHeader(file, bytes) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = () => {
        resolve(new Uint8Array(reader.result));
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read file header'));
      };
      
      const blob = file.slice(0, bytes);
      reader.readAsArrayBuffer(blob);
    });
  }

  /**
   * Check media file health by attempting to load it
   */
  async checkMediaFileHealth(file) {
    return new Promise((resolve) => {
      const audio = new Audio();
      const url = URL.createObjectURL(file);
      let healthCheckTimer;
      
      const cleanup = () => {
        URL.revokeObjectURL(url);
        clearTimeout(healthCheckTimer);
      };
      
      audio.addEventListener('loadedmetadata', () => {
        cleanup();
        resolve('healthy');
      });
      
      audio.addEventListener('error', (e) => {
        cleanup();
        // Different error codes indicate different issues
        switch (e.target.error?.code) {
          case MediaError.MEDIA_ERR_ABORTED:
            resolve('suspicious');
            break;
          case MediaError.MEDIA_ERR_NETWORK:
            resolve('unknown');
            break;
          case MediaError.MEDIA_ERR_DECODE:
          case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
            resolve('corrupted');
            break;
          default:
            resolve('suspicious');
        }
      });
      
      // Timeout after 5 seconds
      healthCheckTimer = setTimeout(() => {
        cleanup();
        resolve('suspicious');
      }, 5000);
      
      audio.src = url;
    });
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Format duration for display
   */
  formatDuration(seconds) {
    if (!seconds || seconds < 0) return '--:--';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  }

  /**
   * Get file quality assessment
   */
  assessFileQuality(metadata, audioPreview) {
    const quality = {
      score: 0,
      issues: [],
      recommendations: []
    };

    // Start with base score
    quality.score = 70;

    // Check duration
    if (metadata.duration) {
      if (metadata.duration < 5) {
        quality.issues.push('Very short audio file (< 5 seconds)');
        quality.score -= 20;
      } else if (metadata.duration > 3600) {
        quality.issues.push('Very long audio file (> 1 hour)');
        quality.recommendations.push('Consider splitting into smaller segments');
        quality.score -= 5;
      } else {
        quality.score += 10;
      }
    }

    // Check audio properties
    if (audioPreview) {
      // Check sample rate
      if (audioPreview.sampleRate < 16000) {
        quality.issues.push('Low sample rate (< 16kHz)');
        quality.score -= 15;
      } else if (audioPreview.sampleRate >= 44100) {
        quality.score += 10;
      }

      // Check channels
      if (audioPreview.channels > 2) {
        quality.recommendations.push('Multi-channel audio will be converted to mono');
        quality.score -= 5;
      }

      // Check audio levels
      const avgPeak = audioPreview.peaks.reduce((a, b) => a + b, 0) / audioPreview.peaks.length;
      if (avgPeak < 0.1) {
        quality.issues.push('Audio levels are very low');
        quality.score -= 15;
      } else if (avgPeak > 0.9) {
        quality.issues.push('Audio may be clipping');
        quality.score -= 10;
      }
    }

    // Check file size vs duration ratio
    if (metadata.duration && metadata.size) {
      const bitrate = (metadata.size * 8) / metadata.duration; // bits per second
      if (bitrate < 32000) {
        quality.issues.push('Very low bitrate - may affect transcription quality');
        quality.score -= 20;
      } else if (bitrate > 320000) {
        quality.recommendations.push('High bitrate - file could be compressed to save space');
      }
    }

    // Ensure score stays within bounds
    quality.score = Math.max(0, Math.min(100, quality.score));

    return quality;
  }

  /**
   * Get supported formats for display
   */
  getSupportedFormats() {
    return this.supportedFormats;
  }

  /**
   * Get format info by extension
   */
  getFormatInfo(extension) {
    return this.supportedFormats.find(f => f.ext === extension.toLowerCase());
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }
  }
}

export default new AdvancedFileUploadService();