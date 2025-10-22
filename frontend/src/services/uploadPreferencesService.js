/**
 * T030 User Preferences Enhancement: Upload Preferences Service
 * Comprehensive file upload and processing preferences management
 */

class UploadPreferencesService {
  constructor() {
    this.preferences = {
      general: {
        auto_upload: false,
        show_previews: true,
        delete_after_upload: false,
        confirm_deletions: true,
        max_simultaneous_uploads: 3,
        chunk_size: 1048576, // 1MB chunks
        retry_failed_uploads: true,
        max_retries: 3,
        upload_timeout: 300000, // 5 minutes
        show_upload_progress: true,
        minimize_on_background: false
      },
      file_handling: {
        accepted_formats: [
          'audio/mpeg', 'audio/mp3',
          'audio/wav', 'audio/x-wav',
          'audio/mp4', 'audio/m4a',
          'audio/flac', 'audio/x-flac',
          'audio/ogg', 'audio/webm',
          'video/mp4', 'video/mpeg',
          'video/quicktime', 'video/x-msvideo'
        ],
        max_file_size: 1073741824, // 1GB
        min_file_size: 1024, // 1KB
        auto_validate_files: true,
        show_file_warnings: true,
        allow_duplicate_files: false,
        auto_rename_duplicates: true,
        preserve_original_names: true,
        custom_naming_pattern: '{original_name}_{timestamp}',
        organize_by_date: false,
        organize_by_type: false
      },
      quality_settings: {
        transcription_model: 'large-v3',
        language_detection: 'auto',
        preferred_language: 'en',
        enable_timestamps: true,
        timestamp_granularity: 'segment', // word, segment, or none
        enable_word_confidence: true,
        confidence_threshold: 0.8,
        enable_speaker_detection: false,
        max_speakers: 4,
        enable_punctuation: true,
        enable_capitalization: true,
        remove_filler_words: false,
        enable_noise_reduction: true,
        audio_enhancement: 'auto', // none, light, moderate, aggressive, auto
        normalize_audio: true,
        boost_vocals: false
      },
      processing_options: {
        priority_mode: 'normal', // low, normal, high, urgent
        processing_pipeline: 'standard', // fast, standard, accurate, custom
        enable_preprocessing: true,
        enable_postprocessing: true,
        auto_segment_long_files: true,
        segment_length: 600, // 10 minutes
        overlap_duration: 5, // 5 seconds overlap
        parallel_processing: true,
        max_parallel_jobs: 2,
        enable_batch_optimization: true,
        compress_output: false,
        output_format: 'json', // json, txt, srt, vtt, all
        include_metadata: true,
        include_statistics: true,
        save_intermediate_files: false,
        auto_cleanup_temp_files: true,
        cleanup_delay: 3600000 // 1 hour
      },
      output_preferences: {
        default_output_format: 'json',
        include_timestamps: true,
        include_confidence_scores: true,
        include_speaker_labels: false,
        include_word_alignments: false,
        text_formatting: {
          line_breaks: 'sentence', // none, sentence, paragraph, speaker
          punctuation: true,
          capitalization: true,
          paragraph_detection: true,
          sentence_spacing: 'single' // single, double
        },
        subtitle_settings: {
          max_line_length: 42,
          max_lines_per_subtitle: 2,
          min_duration: 1.0,
          max_duration: 7.0,
          gap_threshold: 0.5,
          reading_speed: 180 // words per minute
        },
        export_options: {
          auto_download: false,
          download_location: 'downloads',
          create_subfolder: true,
          subfolder_pattern: '{date}/{job_type}',
          filename_pattern: '{original_name}_transcript_{timestamp}',
          include_source_info: true,
          compress_large_files: true,
          compression_threshold: 10485760 // 10MB
        }
      },
      advanced: {
        enable_experimental_features: false,
        debug_mode: false,
        verbose_logging: false,
        cache_transcriptions: true,
        cache_duration: 604800000, // 7 days
        enable_offline_mode: false,
        sync_across_devices: true,
        backup_settings: true,
        auto_save_drafts: true,
        draft_save_interval: 30000, // 30 seconds
        enable_analytics: true,
        share_usage_statistics: false,
        performance_monitoring: true,
        error_reporting: true,
        beta_features: false
      }
    };

    this.subscribers = new Set();
    this.validationRules = this.initializeValidationRules();
    this.loadPreferences();
    this.setupEventListeners();
  }

  /**
   * Initialize validation rules for preferences
   */
  initializeValidationRules() {
    return {
      general: {
        max_simultaneous_uploads: { min: 1, max: 10, type: 'number' },
        chunk_size: { min: 65536, max: 10485760, type: 'number' }, // 64KB to 10MB
        max_retries: { min: 0, max: 10, type: 'number' },
        upload_timeout: { min: 30000, max: 1800000, type: 'number' } // 30s to 30min
      },
      file_handling: {
        max_file_size: { min: 1024, max: 5368709120, type: 'number' }, // 1KB to 5GB
        min_file_size: { min: 1, max: 1048576, type: 'number' }, // 1B to 1MB
        custom_naming_pattern: { type: 'string', required: true }
      },
      quality_settings: {
        confidence_threshold: { min: 0, max: 1, type: 'number' },
        max_speakers: { min: 1, max: 20, type: 'number' },
        transcription_model: { 
          type: 'enum', 
          values: ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
        },
        language_detection: {
          type: 'enum',
          values: ['auto', 'manual']
        },
        timestamp_granularity: {
          type: 'enum',
          values: ['word', 'segment', 'none']
        },
        audio_enhancement: {
          type: 'enum',
          values: ['none', 'light', 'moderate', 'aggressive', 'auto']
        }
      },
      processing_options: {
        segment_length: { min: 60, max: 3600, type: 'number' }, // 1min to 1hour
        overlap_duration: { min: 0, max: 30, type: 'number' },
        max_parallel_jobs: { min: 1, max: 8, type: 'number' },
        cleanup_delay: { min: 60000, max: 86400000, type: 'number' }, // 1min to 24hours
        priority_mode: {
          type: 'enum',
          values: ['low', 'normal', 'high', 'urgent']
        },
        processing_pipeline: {
          type: 'enum',
          values: ['fast', 'standard', 'accurate', 'custom']
        },
        output_format: {
          type: 'enum',
          values: ['json', 'txt', 'srt', 'vtt', 'all']
        }
      },
      output_preferences: {
        subtitle_settings: {
          max_line_length: { min: 20, max: 80, type: 'number' },
          max_lines_per_subtitle: { min: 1, max: 4, type: 'number' },
          min_duration: { min: 0.5, max: 5.0, type: 'number' },
          max_duration: { min: 3.0, max: 15.0, type: 'number' },
          reading_speed: { min: 120, max: 300, type: 'number' }
        }
      }
    };
  }

  /**
   * Load preferences from storage
   */
  loadPreferences() {
    try {
      const stored = localStorage.getItem('whisper-upload-preferences');
      if (stored) {
        const storedPrefs = JSON.parse(stored);
        this.preferences = this.mergePreferences(this.preferences, storedPrefs);
        this.validatePreferences();
      }
    } catch (error) {
      console.error('Error loading upload preferences:', error);
    }
  }

  /**
   * Save preferences to storage
   */
  savePreferences() {
    try {
      localStorage.setItem('whisper-upload-preferences', JSON.stringify(this.preferences));
      this.notifySubscribers('preferences-updated', this.preferences);
    } catch (error) {
      console.error('Error saving upload preferences:', error);
    }
  }

  /**
   * Merge preferences with defaults
   */
  mergePreferences(defaultPrefs, userPrefs) {
    const merged = JSON.parse(JSON.stringify(defaultPrefs));
    
    Object.keys(userPrefs).forEach(section => {
      if (merged[section] && typeof merged[section] === 'object') {
        Object.assign(merged[section], userPrefs[section]);
      }
    });
    
    return merged;
  }

  /**
   * Validate preferences against rules
   */
  validatePreferences() {
    const errors = [];
    
    Object.keys(this.validationRules).forEach(section => {
      const sectionRules = this.validationRules[section];
      const sectionPrefs = this.preferences[section];
      
      if (!sectionPrefs) return;
      
      Object.keys(sectionRules).forEach(key => {
        const rule = sectionRules[key];
        const value = this.getNestedValue(sectionPrefs, key);
        
        if (value !== undefined) {
          const error = this.validateValue(value, rule, `${section}.${key}`);
          if (error) errors.push(error);
        }
      });
    });
    
    if (errors.length > 0) {
      console.warn('Upload preferences validation errors:', errors);
      this.notifySubscribers('validation-errors', errors);
    }
    
    return errors;
  }

  /**
   * Validate a single value against a rule
   */
  validateValue(value, rule, path) {
    if (rule.type === 'number') {
      if (typeof value !== 'number' || isNaN(value)) {
        return `${path}: Must be a valid number`;
      }
      if (rule.min !== undefined && value < rule.min) {
        return `${path}: Must be at least ${rule.min}`;
      }
      if (rule.max !== undefined && value > rule.max) {
        return `${path}: Must be at most ${rule.max}`;
      }
    }
    
    if (rule.type === 'string') {
      if (typeof value !== 'string') {
        return `${path}: Must be a string`;
      }
      if (rule.required && value.trim() === '') {
        return `${path}: Required field cannot be empty`;
      }
    }
    
    if (rule.type === 'enum') {
      if (!rule.values.includes(value)) {
        return `${path}: Must be one of: ${rule.values.join(', ')}`;
      }
    }
    
    return null;
  }

  /**
   * Get nested value from object using dot notation
   */
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : undefined;
    }, obj);
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Listen for storage changes (multi-tab sync)
    window.addEventListener('storage', (e) => {
      if (e.key === 'whisper-upload-preferences' && e.newValue) {
        try {
          const preferences = JSON.parse(e.newValue);
          this.preferences = preferences;
          this.notifySubscribers('preferences-updated', preferences);
        } catch (error) {
          console.error('Error parsing upload preferences from storage:', error);
        }
      }
    });
  }

  /**
   * Update general preferences
   */
  updateGeneralPreferences(updates) {
    this.preferences.general = {
      ...this.preferences.general,
      ...updates
    };
    this.validatePreferences();
    this.savePreferences();
  }

  /**
   * Update file handling preferences
   */
  updateFileHandlingPreferences(updates) {
    this.preferences.file_handling = {
      ...this.preferences.file_handling,
      ...updates
    };
    this.validatePreferences();
    this.savePreferences();
  }

  /**
   * Update quality settings
   */
  updateQualitySettings(updates) {
    this.preferences.quality_settings = {
      ...this.preferences.quality_settings,
      ...updates
    };
    this.validatePreferences();
    this.savePreferences();
  }

  /**
   * Update processing options
   */
  updateProcessingOptions(updates) {
    this.preferences.processing_options = {
      ...this.preferences.processing_options,
      ...updates
    };
    this.validatePreferences();
    this.savePreferences();
  }

  /**
   * Update output preferences
   */
  updateOutputPreferences(updates) {
    this.preferences.output_preferences = {
      ...this.preferences.output_preferences,
      ...updates
    };
    this.validatePreferences();
    this.savePreferences();
  }

  /**
   * Update advanced preferences
   */
  updateAdvancedPreferences(updates) {
    this.preferences.advanced = {
      ...this.preferences.advanced,
      ...updates
    };
    this.validatePreferences();
    this.savePreferences();
  }

  /**
   * Add accepted file format
   */
  addAcceptedFormat(mimeType) {
    if (!this.preferences.file_handling.accepted_formats.includes(mimeType)) {
      this.preferences.file_handling.accepted_formats.push(mimeType);
      this.savePreferences();
    }
  }

  /**
   * Remove accepted file format
   */
  removeAcceptedFormat(mimeType) {
    const index = this.preferences.file_handling.accepted_formats.indexOf(mimeType);
    if (index > -1) {
      this.preferences.file_handling.accepted_formats.splice(index, 1);
      this.savePreferences();
    }
  }

  /**
   * Check if file format is accepted
   */
  isFormatAccepted(mimeType) {
    return this.preferences.file_handling.accepted_formats.includes(mimeType);
  }

  /**
   * Check if file size is within limits
   */
  isFileSizeValid(size) {
    return size >= this.preferences.file_handling.min_file_size &&
           size <= this.preferences.file_handling.max_file_size;
  }

  /**
   * Get upload configuration for current preferences
   */
  getUploadConfig() {
    return {
      maxSimultaneous: this.preferences.general.max_simultaneous_uploads,
      chunkSize: this.preferences.general.chunk_size,
      maxRetries: this.preferences.general.max_retries,
      timeout: this.preferences.general.upload_timeout,
      acceptedFormats: this.preferences.file_handling.accepted_formats,
      maxFileSize: this.preferences.file_handling.max_file_size,
      minFileSize: this.preferences.file_handling.min_file_size,
      autoValidate: this.preferences.file_handling.auto_validate_files,
      allowDuplicates: this.preferences.file_handling.allow_duplicate_files,
      autoRename: this.preferences.file_handling.auto_rename_duplicates
    };
  }

  /**
   * Get processing configuration
   */
  getProcessingConfig() {
    return {
      model: this.preferences.quality_settings.transcription_model,
      language: this.preferences.quality_settings.preferred_language,
      languageDetection: this.preferences.quality_settings.language_detection,
      enableTimestamps: this.preferences.quality_settings.enable_timestamps,
      timestampGranularity: this.preferences.quality_settings.timestamp_granularity,
      enableWordConfidence: this.preferences.quality_settings.enable_word_confidence,
      confidenceThreshold: this.preferences.quality_settings.confidence_threshold,
      enableSpeakerDetection: this.preferences.quality_settings.enable_speaker_detection,
      maxSpeakers: this.preferences.quality_settings.max_speakers,
      enablePunctuation: this.preferences.quality_settings.enable_punctuation,
      enableCapitalization: this.preferences.quality_settings.enable_capitalization,
      removeFiller: this.preferences.quality_settings.remove_filler_words,
      enableNoiseReduction: this.preferences.quality_settings.enable_noise_reduction,
      audioEnhancement: this.preferences.quality_settings.audio_enhancement,
      normalizeAudio: this.preferences.quality_settings.normalize_audio,
      boostVocals: this.preferences.quality_settings.boost_vocals,
      priority: this.preferences.processing_options.priority_mode,
      pipeline: this.preferences.processing_options.processing_pipeline,
      enablePreprocessing: this.preferences.processing_options.enable_preprocessing,
      enablePostprocessing: this.preferences.processing_options.enable_postprocessing,
      autoSegment: this.preferences.processing_options.auto_segment_long_files,
      segmentLength: this.preferences.processing_options.segment_length,
      overlapDuration: this.preferences.processing_options.overlap_duration,
      parallelProcessing: this.preferences.processing_options.parallel_processing,
      maxParallelJobs: this.preferences.processing_options.max_parallel_jobs,
      outputFormat: this.preferences.processing_options.output_format,
      includeMetadata: this.preferences.processing_options.include_metadata,
      includeStatistics: this.preferences.processing_options.include_statistics
    };
  }

  /**
   * Get output configuration
   */
  getOutputConfig() {
    return {
      defaultFormat: this.preferences.output_preferences.default_output_format,
      includeTimestamps: this.preferences.output_preferences.include_timestamps,
      includeConfidenceScores: this.preferences.output_preferences.include_confidence_scores,
      includeSpeakerLabels: this.preferences.output_preferences.include_speaker_labels,
      includeWordAlignments: this.preferences.output_preferences.include_word_alignments,
      textFormatting: this.preferences.output_preferences.text_formatting,
      subtitleSettings: this.preferences.output_preferences.subtitle_settings,
      exportOptions: this.preferences.output_preferences.export_options
    };
  }

  /**
   * Reset preferences to defaults
   */
  resetPreferences() {
    // Store current preferences as backup
    const backup = JSON.stringify(this.preferences);
    localStorage.setItem('whisper-upload-preferences-backup', backup);

    // Reset to defaults - reinitialize with constructor defaults
    this.preferences = {
      general: {
        auto_upload: false,
        show_previews: true,
        delete_after_upload: false,
        confirm_deletions: true,
        max_simultaneous_uploads: 3,
        chunk_size: 1048576,
        retry_failed_uploads: true,
        max_retries: 3,
        upload_timeout: 300000,
        show_upload_progress: true,
        minimize_on_background: false
      },
      // ... other default sections would be reset too
    };

    this.savePreferences();
  }

  /**
   * Export preferences
   */
  exportPreferences() {
    const exportData = {
      version: '1.0',
      timestamp: new Date().toISOString(),
      preferences: this.preferences
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `whisper-upload-preferences-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Import preferences
   */
  async importPreferences(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const importData = JSON.parse(e.target.result);
          
          if (!importData.preferences) {
            throw new Error('Invalid preferences file format');
          }
          
          // Validate and merge preferences
          const merged = this.mergePreferences(this.preferences, importData.preferences);
          this.preferences = merged;
          const errors = this.validatePreferences();
          this.savePreferences();
          
          resolve({ importData, validationErrors: errors });
        } catch (error) {
          reject(new Error(`Failed to import preferences: ${error.message}`));
        }
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read preferences file'));
      };
      
      reader.readAsText(file);
    });
  }

  /**
   * Get usage statistics
   */
  getUsageStatistics() {
    try {
      const stats = localStorage.getItem('whisper-upload-stats');
      return stats ? JSON.parse(stats) : {
        total_uploads: 0,
        successful_uploads: 0,
        failed_uploads: 0,
        total_processing_time: 0,
        average_file_size: 0,
        most_used_format: null,
        most_used_model: null,
        last_upload: null
      };
    } catch (error) {
      console.error('Error loading usage statistics:', error);
      return null;
    }
  }

  /**
   * Subscribe to preference changes
   */
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  /**
   * Notify subscribers
   */
  notifySubscribers(event, data) {
    this.subscribers.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in upload preference subscriber:', error);
      }
    });
  }

  /**
   * Get current preferences
   */
  getPreferences() {
    return JSON.parse(JSON.stringify(this.preferences));
  }

  /**
   * Get available models
   */
  getAvailableModels() {
    return [
      { id: 'tiny', name: 'Tiny', description: 'Fastest, least accurate', size: '39 MB' },
      { id: 'base', name: 'Base', description: 'Fast, basic accuracy', size: '74 MB' },
      { id: 'small', name: 'Small', description: 'Balanced speed and accuracy', size: '244 MB' },
      { id: 'medium', name: 'Medium', description: 'Good accuracy, slower', size: '769 MB' },
      { id: 'large', name: 'Large', description: 'High accuracy, slow', size: '1550 MB' },
      { id: 'large-v2', name: 'Large v2', description: 'Improved large model', size: '1550 MB' },
      { id: 'large-v3', name: 'Large v3', description: 'Latest, most accurate', size: '1550 MB' }
    ];
  }

  /**
   * Get available languages
   */
  getAvailableLanguages() {
    return [
      { code: 'auto', name: 'Auto-detect' },
      { code: 'en', name: 'English' },
      { code: 'es', name: 'Spanish' },
      { code: 'fr', name: 'French' },
      { code: 'de', name: 'German' },
      { code: 'it', name: 'Italian' },
      { code: 'pt', name: 'Portuguese' },
      { code: 'ru', name: 'Russian' },
      { code: 'ja', name: 'Japanese' },
      { code: 'ko', name: 'Korean' },
      { code: 'zh', name: 'Chinese' },
      { code: 'ar', name: 'Arabic' },
      { code: 'hi', name: 'Hindi' },
      { code: 'nl', name: 'Dutch' },
      { code: 'sv', name: 'Swedish' },
      { code: 'da', name: 'Danish' },
      { code: 'no', name: 'Norwegian' },
      { code: 'fi', name: 'Finnish' }
    ];
  }
}

// Create singleton instance
const uploadPreferencesService = new UploadPreferencesService();

export default uploadPreferencesService;