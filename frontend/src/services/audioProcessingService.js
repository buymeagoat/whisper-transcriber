/**
 * T035: Audio Processing Service
 * Frontend service for audio processing API integration
 */

import { apiRequest } from './api';

class AudioProcessingService {
  constructor() {
    this.baseUrl = '/audio-processing';
  }

  /**
   * Get audio processing configuration options
   */
  async getProcessingConfig() {
    try {
      const response = await apiRequest(`${this.baseUrl}/config`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error('Failed to get processing config:', error);
      throw new Error('Failed to load processing configuration');
    }
  }

  /**
   * Analyze audio file quality
   */
  async analyzeAudio(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiRequest(`${this.baseUrl}/analyze`, {
        method: 'POST',
        body: formData
      });
      return response;
    } catch (error) {
      console.error('Failed to analyze audio:', error);
      throw new Error('Failed to analyze audio file');
    }
  }

  /**
   * Get processing recommendations for a file
   */
  async getProcessingRecommendations(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiRequest(`${this.baseUrl}/analyze/recommendations`, {
        method: 'POST',
        body: formData
      });
      return response;
    } catch (error) {
      console.error('Failed to get recommendations:', error);
      throw new Error('Failed to get processing recommendations');
    }
  }

  /**
   * Process audio file with specified configuration
   */
  async processAudio(file, config) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('config', JSON.stringify(config));

      const response = await apiRequest(`${this.baseUrl}/process`, {
        method: 'POST',
        body: formData
      });
      return response;
    } catch (error) {
      console.error('Failed to process audio:', error);
      throw new Error('Failed to process audio file');
    }
  }

  /**
   * Download processed audio file
   */
  async downloadProcessedFile(fileId) {
    try {
      const response = await fetch(`/api${this.baseUrl}/download/${fileId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `processed_audio_${fileId}.wav`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      return true;
    } catch (error) {
      console.error('Failed to download file:', error);
      throw new Error('Failed to download processed file');
    }
  }

  /**
   * Get supported audio formats information
   */
  async getSupportedFormats() {
    try {
      const response = await apiRequest(`${this.baseUrl}/formats`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error('Failed to get supported formats:', error);
      return this.getMockFormatsData();
    }
  }

  /**
   * Get audio quality metrics information
   */
  async getQualityMetricsInfo() {
    try {
      const response = await apiRequest(`${this.baseUrl}/quality-metrics`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error('Failed to get quality metrics info:', error);
      return this.getMockQualityMetricsData();
    }
  }

  /**
   * Validate audio file before processing
   */
  validateAudioFile(file) {
    const supportedFormats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aac', '.opus'];
    const maxSize = 100 * 1024 * 1024; // 100MB
    
    // Check file extension
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    if (!supportedFormats.includes(extension)) {
      throw new Error(`Unsupported file format. Supported formats: ${supportedFormats.join(', ')}`);
    }

    // Check file size
    if (file.size > maxSize) {
      throw new Error('File size too large. Maximum size is 100MB.');
    }

    // Check if it's actually an audio file
    if (!file.type.startsWith('audio/')) {
      throw new Error('File is not an audio file.');
    }

    return true;
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
   * Get quality score description
   */
  getQualityDescription(score) {
    if (score >= 0.8) return { label: 'Excellent', color: 'success' };
    if (score >= 0.6) return { label: 'Good', color: 'info' };
    if (score >= 0.4) return { label: 'Fair', color: 'warning' };
    return { label: 'Poor', color: 'error' };
  }

  /**
   * Get SNR description
   */
  getSNRDescription(snr) {
    if (snr >= 30) return 'Excellent (>30 dB)';
    if (snr >= 20) return 'Good (20-30 dB)';
    if (snr >= 10) return 'Fair (10-20 dB)';
    return 'Poor (<10 dB)';
  }

  /**
   * Get recommended processing settings based on analysis
   */
  getRecommendedSettings(analysis) {
    const recommendations = {
      enable_noise_reduction: analysis.recommended_noise_reduction,
      enable_normalization: analysis.recommended_normalization,
      enable_compression: analysis.dynamic_range > 0.7,
      enable_eq: analysis.quality_score < 0.6,
      noise_reduction_strength: analysis.snr_estimate < 10 ? 0.8 : 0.5,
      quality_level: analysis.sample_rate >= 44100 ? 'high' : 'medium'
    };

    return recommendations;
  }

  /**
   * Mock data for development/fallback
   */
  getMockFormatsData() {
    return {
      supported_formats: {
        wav: {
          extension: '.wav',
          description: 'Uncompressed, highest quality',
          quality: 'excellent',
          compression: 'none'
        },
        flac: {
          extension: '.flac',
          description: 'Lossless compression, high quality',
          quality: 'excellent',
          compression: 'lossless'
        },
        mp3: {
          extension: '.mp3',
          description: 'Lossy compression, widely supported',
          quality: 'fair',
          compression: 'lossy'
        },
        m4a: {
          extension: '.m4a',
          description: 'Modern lossy compression, good quality',
          quality: 'good',
          compression: 'lossy'
        },
        ogg: {
          extension: '.ogg',
          description: 'Open source lossy compression',
          quality: 'fair',
          compression: 'lossy'
        }
      },
      recommended_input_formats: ['wav', 'flac', 'm4a'],
      optimal_output_format: 'wav',
      transcription_requirements: {
        sample_rate: 16000,
        channels: 1,
        bit_depth: 16,
        format: 'wav'
      }
    };
  }

  getMockQualityMetricsData() {
    return {
      quality_metrics: {
        quality_score: {
          description: 'Overall audio quality score from 0.0 to 1.0',
          excellent: '> 0.8',
          good: '0.6 - 0.8',
          fair: '0.4 - 0.6',
          poor: '< 0.4'
        },
        snr_estimate: {
          description: 'Estimated Signal-to-Noise Ratio in decibels',
          excellent: '> 30 dB',
          good: '20 - 30 dB',
          fair: '10 - 20 dB',
          poor: '< 10 dB'
        },
        dynamic_range: {
          description: 'Difference between peak and RMS levels',
          excellent: '> 0.5',
          good: '0.3 - 0.5',
          fair: '0.1 - 0.3',
          poor: '< 0.1'
        },
        peak_level: {
          description: 'Maximum audio level (0.0 to 1.0)',
          optimal: '0.7 - 0.9',
          acceptable: '0.5 - 0.95',
          too_quiet: '< 0.5',
          clipping_risk: '> 0.95'
        }
      },
      processing_recommendations: {
        noise_reduction: 'Recommended when SNR < 20 dB',
        normalization: 'Recommended when peak level < 0.5 or > 0.95',
        compression: 'Recommended when dynamic range > 0.7',
        eq: 'Optional for speech enhancement'
      }
    };
  }

  /**
   * Get default processing configuration
   */
  getDefaultConfig() {
    return {
      enable_noise_reduction: true,
      noise_reduction_method: 'spectral_gating',
      noise_reduction_strength: 0.5,
      enable_normalization: true,
      enable_compression: true,
      enable_eq: false,
      high_pass_cutoff: 80.0,
      low_pass_cutoff: 8000.0,
      target_sample_rate: 16000,
      target_channels: 1,
      quality_level: 'medium',
      preserve_dynamics: true
    };
  }

  /**
   * Generate processing preview description
   */
  generateProcessingDescription(config) {
    const steps = [];
    
    if (config.enable_noise_reduction) {
      steps.push(`Noise reduction (${config.noise_reduction_method})`);
    }
    
    if (config.enable_normalization) {
      steps.push('Audio normalization');
    }
    
    if (config.enable_compression) {
      steps.push('Dynamic range compression');
    }
    
    if (config.enable_eq) {
      steps.push('EQ processing');
    }
    
    if (config.high_pass_cutoff > 0) {
      steps.push(`High-pass filter (${config.high_pass_cutoff} Hz)`);
    }
    
    if (config.low_pass_cutoff < 20000) {
      steps.push(`Low-pass filter (${config.low_pass_cutoff} Hz)`);
    }
    
    steps.push(`Convert to ${config.target_sample_rate} Hz, ${config.target_channels === 1 ? 'mono' : 'stereo'}`);
    
    return steps.length > 0 ? steps.join(' → ') : 'No processing applied';
  }

  /**
   * Estimate processing time based on file size and configuration
   */
  estimateProcessingTime(fileSize, config) {
    // Base processing time (seconds per MB)
    let baseTime = 2;
    
    // Add time for different processing steps
    if (config.enable_noise_reduction) {
      baseTime += config.noise_reduction_method === 'spectral_gating' ? 3 : 2;
    }
    
    if (config.enable_compression) {
      baseTime += 1;
    }
    
    if (config.enable_eq) {
      baseTime += 1;
    }
    
    const fileSizeMB = fileSize / (1024 * 1024);
    const estimatedSeconds = fileSizeMB * baseTime;
    
    return Math.max(5, Math.min(estimatedSeconds, 300)); // 5 seconds to 5 minutes
  }

  /**
   * Check if processing is recommended based on analysis
   */
  isProcessingRecommended(analysis) {
    return analysis.recommended_noise_reduction || 
           analysis.recommended_normalization || 
           analysis.quality_score < 0.6;
  }

  /**
   * Get processing benefits description
   */
  getProcessingBenefits(analysis, config) {
    const benefits = [];
    
    if (config.enable_noise_reduction && analysis.recommended_noise_reduction) {
      benefits.push('Improved signal-to-noise ratio');
    }
    
    if (config.enable_normalization && analysis.recommended_normalization) {
      benefits.push('Optimal audio levels');
    }
    
    if (config.enable_compression && analysis.dynamic_range > 0.7) {
      benefits.push('Better dynamic range');
    }
    
    if (config.target_sample_rate === 16000) {
      benefits.push('Optimized for transcription');
    }
    
    if (config.target_channels === 1) {
      benefits.push('Reduced file size');
    }
    
    return benefits;
  }
}

// Create and export service instance
const audioProcessingService = new AudioProcessingService();
export default audioProcessingService;