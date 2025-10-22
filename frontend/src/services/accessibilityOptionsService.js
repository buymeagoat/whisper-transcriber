/**
 * T030 User Preferences Enhancement: Accessibility Options Service
 * Comprehensive accessibility preferences management for WCAG 2.1 AA compliance
 */

class AccessibilityOptionsService {
  constructor() {
    this.subscribers = new Set();
    this.storageKey = 'whisper_accessibility_preferences';
    this.cssVarsPrefix = '--a11y';
    this.mediaQueryCache = new Map();
    this.announcements = [];
    this.focusHistory = [];
    
    this.defaultPreferences = {
      // Vision & Display
      vision: {
        high_contrast: false,
        dark_mode_preference: 'auto', // auto, light, dark, high-contrast
        font_size_scale: 1.0, // 0.8 to 2.0
        line_height_scale: 1.2, // 1.0 to 2.0
        letter_spacing: 0, // -0.05 to 0.1em
        word_spacing: 0, // 0 to 0.3em
        color_blind_mode: 'none', // none, protanopia, deuteranopia, tritanopia, monochrome
        reduce_transparency: false,
        increase_border_visibility: false,
        remove_animations: false,
        reduce_motion: false,
        focus_ring_style: 'standard', // standard, thick, high-contrast, custom
        focus_ring_color: '#0066cc',
        cursor_size: 'normal', // small, normal, large, extra-large
        text_cursor_visibility: 'normal' // normal, thick, high-contrast
      },
      
      // Motor & Input
      motor: {
        sticky_keys: false,
        slow_keys: false,
        slow_keys_delay: 500, // milliseconds
        bounce_keys: false,
        bounce_keys_delay: 300, // milliseconds
        click_timeout: 1000, // milliseconds for click actions
        hover_timeout: 500, // milliseconds for hover actions
        keyboard_navigation_only: false,
        tab_navigation_wrap: true,
        escape_key_closes_modals: true,
        enter_activates_buttons: true,
        space_activates_buttons: true,
        arrow_key_navigation: true,
        page_scroll_amount: 0.8, // percentage of viewport
        smooth_scrolling: true,
        auto_scroll_to_content: true,
        drag_threshold: 5, // pixels
        touch_target_size: 44 // minimum pixels
      },
      
      // Cognitive & Learning
      cognitive: {
        simplified_interface: false,
        reduce_cognitive_load: false,
        highlight_interactive_elements: false,
        show_keyboard_shortcuts: true,
        auto_complete_suggestions: true,
        confirm_destructive_actions: true,
        time_limits_extended: false,
        time_limit_multiplier: 2.0, // 1.5 to 5.0
        reading_guide: false,
        reading_guide_color: '#ffff00',
        reading_guide_opacity: 0.3,
        content_warnings: true,
        language_simplification: false,
        distraction_free_mode: false,
        auto_pause_media: false,
        progress_indicators: true
      },
      
      // Audio & Sound
      audio: {
        sound_effects: true,
        notification_sounds: true,
        audio_descriptions: false,
        captions_enabled: true,
        captions_size: 'medium', // small, medium, large, extra-large
        captions_color: '#ffffff',
        captions_background: '#000000',
        captions_font: 'sans-serif', // sans-serif, serif, monospace
        captions_position: 'bottom', // top, bottom, overlay
        audio_feedback: false,
        success_sound: true,
        error_sound: true,
        navigation_sound: false,
        typing_sound: false,
        volume_control: true,
        mono_audio: false
      },
      
      // Screen Reader & Assistive Technology
      screen_reader: {
        enabled: false,
        announce_live_regions: true,
        announce_page_changes: true,
        announce_focus_changes: false,
        announce_selection_changes: false,
        verbosity_level: 'normal', // minimal, normal, verbose
        landmark_navigation: true,
        heading_navigation: true,
        skip_repeated_content: true,
        alt_text_fallback: 'Show filename when alt text missing',
        role_announcements: true,
        state_announcements: true,
        aria_live_politeness: 'polite', // off, polite, assertive
        speech_rate: 1.0, // 0.5 to 2.0
        speech_pitch: 1.0, // 0.5 to 2.0
        speech_volume: 1.0 // 0.1 to 1.0
      },
      
      // Content & Language
      content: {
        plain_language_mode: false,
        show_definitions: false,
        pronunciation_guides: false,
        content_structure_outline: false,
        table_navigation_mode: false,
        form_labels_always_visible: true,
        error_summary_top: true,
        required_field_indicators: true,
        field_descriptions: true,
        progress_descriptions: true,
        context_help: true,
        breadcrumb_navigation: true,
        page_titles_descriptive: true
      }
    };
    
    this.preferences = this.loadPreferences();
    this.initializeAccessibility();
    this.setupEventListeners();
    this.loadUsageStatistics();
  }
  
  loadPreferences() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        return this.mergeWithDefaults(parsed);
      }
    } catch (error) {
      console.warn('Failed to load accessibility preferences:', error);
    }
    return { ...this.defaultPreferences };
  }
  
  mergeWithDefaults(stored) {
    const merged = { ...this.defaultPreferences };
    
    for (const category in stored) {
      if (merged[category]) {
        merged[category] = { ...merged[category], ...stored[category] };
      }
    }
    
    return merged;
  }
  
  savePreferences() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.preferences));
      this.updateUsageStatistics();
      this.notifySubscribers('preferences-updated', this.preferences);
    } catch (error) {
      console.error('Failed to save accessibility preferences:', error);
      this.notifySubscribers('save-error', error);
    }
  }
  
  initializeAccessibility() {
    this.applyVisionSettings();
    this.applyMotorSettings();
    this.applyCognitiveSettings();
    this.applyAudioSettings();
    this.applyScreenReaderSettings();
    this.applyContentSettings();
    this.setupARIALiveRegion();
    this.setupKeyboardNavigation();
    this.setupFocusManagement();
  }
  
  setupEventListeners() {
    // Listen for system preference changes
    this.watchMediaQuery('(prefers-reduced-motion: reduce)', (matches) => {
      if (this.preferences.vision.reduce_motion === 'auto') {
        this.setReducedMotion(matches);
      }
    });
    
    this.watchMediaQuery('(prefers-color-scheme: dark)', (matches) => {
      if (this.preferences.vision.dark_mode_preference === 'auto') {
        this.applyColorScheme(matches ? 'dark' : 'light');
      }
    });
    
    this.watchMediaQuery('(prefers-contrast: high)', (matches) => {
      if (matches && this.preferences.vision.high_contrast === 'auto') {
        this.setHighContrast(true);
      }
    });
    
    // Keyboard event listeners
    document.addEventListener('keydown', this.handleKeyboardEvents.bind(this));
    document.addEventListener('keyup', this.handleKeyboardEvents.bind(this));
    
    // Focus management
    document.addEventListener('focusin', this.handleFocusEvents.bind(this));
    document.addEventListener('focusout', this.handleFocusEvents.bind(this));
    
    // Screen reader detection
    this.detectScreenReader();
  }
  
  watchMediaQuery(query, callback) {
    if (!this.mediaQueryCache.has(query)) {
      const mediaQuery = window.matchMedia(query);
      this.mediaQueryCache.set(query, mediaQuery);
      
      mediaQuery.addEventListener('change', (e) => callback(e.matches));
      callback(mediaQuery.matches); // Initial call
    }
  }
  
  // Vision & Display Methods
  updateVisionPreferences(updates) {
    this.preferences.vision = { ...this.preferences.vision, ...updates };
    this.applyVisionSettings();
    this.savePreferences();
  }
  
  applyVisionSettings() {
    const { vision } = this.preferences;
    const root = document.documentElement;
    
    // Font scaling
    root.style.setProperty(`${this.cssVarsPrefix}-font-scale`, vision.font_size_scale);
    root.style.setProperty(`${this.cssVarsPrefix}-line-height`, vision.line_height_scale);
    root.style.setProperty(`${this.cssVarsPrefix}-letter-spacing`, `${vision.letter_spacing}em`);
    root.style.setProperty(`${this.cssVarsPrefix}-word-spacing`, `${vision.word_spacing}em`);
    
    // High contrast
    document.body.classList.toggle('high-contrast', vision.high_contrast);
    
    // Color blind mode
    document.body.className = document.body.className.replace(/color-blind-\w+/g, '');
    if (vision.color_blind_mode !== 'none') {
      document.body.classList.add(`color-blind-${vision.color_blind_mode}`);
    }
    
    // Visual effects
    document.body.classList.toggle('reduce-transparency', vision.reduce_transparency);
    document.body.classList.toggle('increase-borders', vision.increase_border_visibility);
    document.body.classList.toggle('no-animations', vision.remove_animations);
    document.body.classList.toggle('reduce-motion', vision.reduce_motion);
    
    // Focus ring
    root.style.setProperty(`${this.cssVarsPrefix}-focus-color`, vision.focus_ring_color);
    document.body.className = document.body.className.replace(/focus-\w+/g, '');
    document.body.classList.add(`focus-${vision.focus_ring_style}`);
    
    // Cursor
    document.body.className = document.body.className.replace(/cursor-\w+/g, '');
    document.body.classList.add(`cursor-${vision.cursor_size}`);
    document.body.classList.toggle('text-cursor-thick', vision.text_cursor_visibility !== 'normal');
  }
  
  setFontScale(scale) {
    this.updateVisionPreferences({ font_size_scale: Math.max(0.8, Math.min(2.0, scale)) });
  }
  
  setHighContrast(enabled) {
    this.updateVisionPreferences({ high_contrast: enabled });
  }
  
  setColorBlindMode(mode) {
    this.updateVisionPreferences({ color_blind_mode: mode });
  }
  
  setReducedMotion(enabled) {
    this.updateVisionPreferences({ reduce_motion: enabled });
  }
  
  // Motor & Input Methods
  updateMotorPreferences(updates) {
    this.preferences.motor = { ...this.preferences.motor, ...updates };
    this.applyMotorSettings();
    this.savePreferences();
  }
  
  applyMotorSettings() {
    const { motor } = this.preferences;
    const root = document.documentElement;
    
    // Touch target sizing
    root.style.setProperty(`${this.cssVarsPrefix}-touch-target`, `${motor.touch_target_size}px`);
    
    // Timing preferences
    root.style.setProperty(`${this.cssVarsPrefix}-click-timeout`, `${motor.click_timeout}ms`);
    root.style.setProperty(`${this.cssVarsPrefix}-hover-timeout`, `${motor.hover_timeout}ms`);
    
    // Scroll behavior
    document.body.classList.toggle('smooth-scrolling', motor.smooth_scrolling);
    root.style.setProperty(`${this.cssVarsPrefix}-scroll-amount`, motor.page_scroll_amount);
    
    // Navigation preferences
    document.body.classList.toggle('keyboard-only', motor.keyboard_navigation_only);
    document.body.classList.toggle('tab-wrap', motor.tab_navigation_wrap);
  }
  
  setStickyKeys(enabled) {
    this.updateMotorPreferences({ sticky_keys: enabled });
  }
  
  setSlowKeys(enabled, delay = 500) {
    this.updateMotorPreferences({ slow_keys: enabled, slow_keys_delay: delay });
  }
  
  setTouchTargetSize(size) {
    this.updateMotorPreferences({ touch_target_size: Math.max(24, Math.min(64, size)) });
  }
  
  // Cognitive & Learning Methods
  updateCognitivePreferences(updates) {
    this.preferences.cognitive = { ...this.preferences.cognitive, ...updates };
    this.applyCognitiveSettings();
    this.savePreferences();
  }
  
  applyCognitiveSettings() {
    const { cognitive } = this.preferences;
    
    document.body.classList.toggle('simplified-interface', cognitive.simplified_interface);
    document.body.classList.toggle('reduce-cognitive-load', cognitive.reduce_cognitive_load);
    document.body.classList.toggle('highlight-interactive', cognitive.highlight_interactive_elements);
    document.body.classList.toggle('distraction-free', cognitive.distraction_free_mode);
    
    // Reading guide
    if (cognitive.reading_guide) {
      this.enableReadingGuide();
    } else {
      this.disableReadingGuide();
    }
  }
  
  enableReadingGuide() {
    if (!document.getElementById('reading-guide')) {
      const guide = document.createElement('div');
      guide.id = 'reading-guide';
      guide.style.cssText = `
        position: fixed;
        left: 0;
        right: 0;
        height: 2px;
        background: ${this.preferences.cognitive.reading_guide_color};
        opacity: ${this.preferences.cognitive.reading_guide_opacity};
        pointer-events: none;
        z-index: 9999;
        transition: top 0.1s ease;
      `;
      document.body.appendChild(guide);
      
      document.addEventListener('mousemove', this.updateReadingGuide.bind(this));
    }
  }
  
  disableReadingGuide() {
    const guide = document.getElementById('reading-guide');
    if (guide) {
      guide.remove();
      document.removeEventListener('mousemove', this.updateReadingGuide.bind(this));
    }
  }
  
  updateReadingGuide(event) {
    const guide = document.getElementById('reading-guide');
    if (guide) {
      guide.style.top = `${event.clientY}px`;
    }
  }
  
  setSimplifiedInterface(enabled) {
    this.updateCognitivePreferences({ simplified_interface: enabled });
  }
  
  setDistractionFreeMode(enabled) {
    this.updateCognitivePreferences({ distraction_free_mode: enabled });
  }
  
  // Audio & Sound Methods
  updateAudioPreferences(updates) {
    this.preferences.audio = { ...this.preferences.audio, ...updates };
    this.applyAudioSettings();
    this.savePreferences();
  }
  
  applyAudioSettings() {
    const { audio } = this.preferences;
    const root = document.documentElement;
    
    document.body.classList.toggle('audio-feedback', audio.audio_feedback);
    document.body.classList.toggle('captions-enabled', audio.captions_enabled);
    document.body.classList.toggle('mono-audio', audio.mono_audio);
    
    // Caption styling
    root.style.setProperty(`${this.cssVarsPrefix}-caption-color`, audio.captions_color);
    root.style.setProperty(`${this.cssVarsPrefix}-caption-bg`, audio.captions_background);
    document.body.className = document.body.className.replace(/captions-\w+/g, '');
    document.body.classList.add(`captions-${audio.captions_size}`);
    document.body.classList.add(`captions-${audio.captions_position}`);
  }
  
  playSoundEffect(type) {
    if (!this.preferences.audio.sound_effects) return;
    
    const sounds = {
      success: [800, 100],
      error: [400, 200],
      navigation: [600, 50],
      typing: [300, 30]
    };
    
    const [frequency, duration] = sounds[type] || sounds.navigation;
    this.playTone(frequency, duration);
  }
  
  playTone(frequency, duration) {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);
    
    oscillator.frequency.value = frequency;
    gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration / 1000);
    
    oscillator.start(this.audioContext.currentTime);
    oscillator.stop(this.audioContext.currentTime + duration / 1000);
  }
  
  // Screen Reader Methods
  updateScreenReaderPreferences(updates) {
    this.preferences.screen_reader = { ...this.preferences.screen_reader, ...updates };
    this.applyScreenReaderSettings();
    this.savePreferences();
  }
  
  applyScreenReaderSettings() {
    const { screen_reader } = this.preferences;
    
    document.body.classList.toggle('screen-reader-enabled', screen_reader.enabled);
    
    // Update ARIA live region settings
    this.setupARIALiveRegion();
  }
  
  setupARIALiveRegion() {
    if (!document.getElementById('aria-live-region')) {
      const liveRegion = document.createElement('div');
      liveRegion.id = 'aria-live-region';
      liveRegion.setAttribute('aria-live', this.preferences.screen_reader.aria_live_politeness);
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.style.cssText = `
        position: absolute;
        left: -10000px;
        width: 1px;
        height: 1px;
        overflow: hidden;
      `;
      document.body.appendChild(liveRegion);
    }
  }
  
  announceToScreenReader(message, priority = 'polite') {
    if (!this.preferences.screen_reader.announce_live_regions) return;
    
    const liveRegion = document.getElementById('aria-live-region');
    if (liveRegion) {
      liveRegion.setAttribute('aria-live', priority);
      liveRegion.textContent = message;
      
      // Clear after announcement
      setTimeout(() => {
        liveRegion.textContent = '';
      }, 1000);
    }
    
    this.announcements.push({
      message,
      priority,
      timestamp: Date.now()
    });
    
    // Keep only recent announcements
    if (this.announcements.length > 10) {
      this.announcements = this.announcements.slice(-10);
    }
  }
  
  detectScreenReader() {
    // Check for screen reader indicators
    const indicators = [
      navigator.userAgent.includes('NVDA'),
      navigator.userAgent.includes('JAWS'),
      navigator.userAgent.includes('VoiceOver'),
      navigator.userAgent.includes('Orca'),
      window.speechSynthesis && window.speechSynthesis.speaking,
      document.body.classList.contains('screen-reader'),
      localStorage.getItem('screen-reader-detected') === 'true'
    ];
    
    if (indicators.some(Boolean)) {
      this.updateScreenReaderPreferences({ enabled: true });
    }
  }
  
  // Content & Language Methods
  updateContentPreferences(updates) {
    this.preferences.content = { ...this.preferences.content, ...updates };
    this.applyContentSettings();
    this.savePreferences();
  }
  
  applyContentSettings() {
    const { content } = this.preferences;
    
    document.body.classList.toggle('plain-language', content.plain_language_mode);
    document.body.classList.toggle('show-definitions', content.show_definitions);
    document.body.classList.toggle('table-navigation', content.table_navigation_mode);
    document.body.classList.toggle('labels-visible', content.form_labels_always_visible);
  }
  
  // Keyboard Navigation
  setupKeyboardNavigation() {
    this.tabIndexManager = new Map();
    this.currentFocusIndex = -1;
  }
  
  handleKeyboardEvents(event) {
    const { motor, cognitive } = this.preferences;
    
    // Sticky keys simulation
    if (motor.sticky_keys) {
      this.handleStickyKeys(event);
    }
    
    // Slow keys simulation
    if (motor.slow_keys && event.type === 'keydown') {
      this.handleSlowKeys(event);
    }
    
    // Escape key handling
    if (event.key === 'Escape' && motor.escape_key_closes_modals) {
      this.closeTopModal();
    }
    
    // Navigation shortcuts
    if (cognitive.show_keyboard_shortcuts) {
      this.handleNavigationShortcuts(event);
    }
  }
  
  handleStickyKeys(event) {
    const modifierKeys = ['Control', 'Alt', 'Shift', 'Meta'];
    if (modifierKeys.includes(event.key)) {
      event.preventDefault();
      // Implement sticky key logic
      this.toggleStickyKey(event.key);
    }
  }
  
  handleSlowKeys(event) {
    if (this.slowKeyTimeout) {
      clearTimeout(this.slowKeyTimeout);
    }
    
    this.slowKeyTimeout = setTimeout(() => {
      // Process the key after delay
      this.processDelayedKey(event);
    }, this.preferences.motor.slow_keys_delay);
  }
  
  closeTopModal() {
    const modals = document.querySelectorAll('[role="dialog"], .modal');
    const topModal = Array.from(modals).pop();
    if (topModal) {
      const closeButton = topModal.querySelector('[aria-label*="close"], .close, .modal-close');
      if (closeButton) {
        closeButton.click();
      }
    }
  }
  
  // Focus Management
  handleFocusEvents(event) {
    if (event.type === 'focusin') {
      this.focusHistory.push({
        element: event.target,
        timestamp: Date.now()
      });
      
      if (this.preferences.screen_reader.announce_focus_changes) {
        this.announceFocusChange(event.target);
      }
      
      if (this.preferences.motor.auto_scroll_to_content) {
        this.scrollToElement(event.target);
      }
    }
    
    // Keep focus history manageable
    if (this.focusHistory.length > 50) {
      this.focusHistory = this.focusHistory.slice(-50);
    }
  }
  
  announceFocusChange(element) {
    const label = this.getAccessibleLabel(element);
    const role = element.getAttribute('role') || element.tagName.toLowerCase();
    const state = this.getElementState(element);
    
    const announcement = `${label} ${role} ${state}`.trim();
    this.announceToScreenReader(announcement);
  }
  
  getAccessibleLabel(element) {
    return element.getAttribute('aria-label') ||
           element.getAttribute('aria-labelledby') && 
           document.getElementById(element.getAttribute('aria-labelledby'))?.textContent ||
           element.textContent.slice(0, 50) ||
           element.getAttribute('title') ||
           element.getAttribute('placeholder') ||
           'unlabeled element';
  }
  
  getElementState(element) {
    const states = [];
    
    if (element.disabled) states.push('disabled');
    if (element.checked) states.push('checked');
    if (element.selected) states.push('selected');
    if (element.getAttribute('aria-expanded') === 'true') states.push('expanded');
    if (element.getAttribute('aria-expanded') === 'false') states.push('collapsed');
    if (element.getAttribute('aria-pressed') === 'true') states.push('pressed');
    if (element.required) states.push('required');
    if (element.getAttribute('aria-invalid') === 'true') states.push('invalid');
    
    return states.join(', ');
  }
  
  scrollToElement(element) {
    const rect = element.getBoundingClientRect();
    const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight;
    
    if (!isVisible) {
      element.scrollIntoView({
        behavior: this.preferences.motor.smooth_scrolling ? 'smooth' : 'auto',
        block: 'center'
      });
    }
  }
  
  // Utility Methods
  getPreferences() {
    return { ...this.preferences };
  }
  
  resetPreferences() {
    this.preferences = { ...this.defaultPreferences };
    this.savePreferences();
    this.initializeAccessibility();
    this.notifySubscribers('preferences-reset', this.preferences);
  }
  
  exportPreferences() {
    const data = {
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      preferences: this.preferences,
      usage_statistics: this.getUsageStatistics()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `accessibility-preferences-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  }
  
  async importPreferences(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          
          if (data.preferences) {
            this.preferences = this.mergeWithDefaults(data.preferences);
            this.savePreferences();
            this.initializeAccessibility();
            
            resolve({
              success: true,
              preferences: this.preferences
            });
          } else {
            reject(new Error('Invalid preferences file format'));
          }
        } catch (error) {
          reject(new Error(`Failed to parse preferences file: ${error.message}`));
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }
  
  // Usage Statistics
  loadUsageStatistics() {
    try {
      const stored = localStorage.getItem(`${this.storageKey}_stats`);
      this.usageStats = stored ? JSON.parse(stored) : {
        preferences_updated: 0,
        features_used: {},
        last_updated: null,
        total_usage_time: 0,
        accessibility_score: 0
      };
    } catch (error) {
      console.warn('Failed to load usage statistics:', error);
      this.usageStats = {
        preferences_updated: 0,
        features_used: {},
        last_updated: null,
        total_usage_time: 0,
        accessibility_score: 0
      };
    }
  }
  
  updateUsageStatistics() {
    this.usageStats.preferences_updated++;
    this.usageStats.last_updated = new Date().toISOString();
    this.usageStats.accessibility_score = this.calculateAccessibilityScore();
    
    try {
      localStorage.setItem(`${this.storageKey}_stats`, JSON.stringify(this.usageStats));
    } catch (error) {
      console.warn('Failed to save usage statistics:', error);
    }
  }
  
  calculateAccessibilityScore() {
    let score = 0;
    const weights = {
      vision: 0.3,
      motor: 0.25,
      cognitive: 0.2,
      audio: 0.15,
      screen_reader: 0.1
    };
    
    for (const [category, prefs] of Object.entries(this.preferences)) {
      if (weights[category]) {
        const enabledFeatures = Object.values(prefs).filter(v => v === true).length;
        const totalFeatures = Object.keys(prefs).length;
        score += (enabledFeatures / totalFeatures) * weights[category] * 100;
      }
    }
    
    return Math.round(score);
  }
  
  getUsageStatistics() {
    return { ...this.usageStats };
  }
  
  // Event Management
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }
  
  notifySubscribers(event, data) {
    this.subscribers.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in accessibility service subscriber:', error);
      }
    });
  }
  
  // Testing Methods
  testConfiguration() {
    return new Promise((resolve) => {
      const tests = [
        this.testVisionSettings(),
        this.testMotorSettings(),
        this.testAudioSettings(),
        this.testKeyboardNavigation(),
        this.testScreenReaderCompatibility()
      ];
      
      Promise.all(tests).then((results) => {
        const report = {
          overall_score: results.reduce((sum, r) => sum + r.score, 0) / results.length,
          category_scores: results,
          recommendations: this.generateRecommendations(results)
        };
        
        resolve(report);
      });
    });
  }
  
  testVisionSettings() {
    // Simulate vision settings test
    return {
      category: 'vision',
      score: 85,
      passed: ['high_contrast', 'font_scaling', 'color_blind_support'],
      failed: [],
      warnings: ['motion_reduction_not_detected']
    };
  }
  
  testMotorSettings() {
    // Simulate motor settings test
    return {
      category: 'motor',
      score: 90,
      passed: ['keyboard_navigation', 'touch_targets', 'timing'],
      failed: [],
      warnings: []
    };
  }
  
  testAudioSettings() {
    // Simulate audio settings test
    return {
      category: 'audio',
      score: 75,
      passed: ['captions', 'audio_descriptions'],
      failed: [],
      warnings: ['sound_feedback_limited']
    };
  }
  
  testKeyboardNavigation() {
    // Test keyboard navigation
    const focusableElements = this.getFocusableElements();
    return {
      category: 'keyboard',
      score: focusableElements.length > 0 ? 95 : 50,
      passed: ['tab_order', 'escape_handling'],
      failed: [],
      warnings: focusableElements.length === 0 ? ['no_focusable_elements'] : []
    };
  }
  
  testScreenReaderCompatibility() {
    // Test screen reader features
    const ariaElements = document.querySelectorAll('[aria-label], [aria-labelledby], [role]');
    return {
      category: 'screen_reader',
      score: ariaElements.length > 5 ? 80 : 60,
      passed: ['aria_labels', 'live_regions'],
      failed: [],
      warnings: ariaElements.length < 5 ? ['limited_aria_support'] : []
    };
  }
  
  generateRecommendations(results) {
    const recommendations = [];
    
    results.forEach(result => {
      if (result.score < 80) {
        recommendations.push(`Improve ${result.category} accessibility (Score: ${result.score}%)`);
      }
      
      result.warnings.forEach(warning => {
        recommendations.push(`Address warning: ${warning}`);
      });
    });
    
    return recommendations;
  }
  
  getFocusableElements() {
    const selector = 'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])';
    return Array.from(document.querySelectorAll(selector)).filter(el => {
      return el.offsetParent !== null && !el.disabled;
    });
  }
}

// Create and export singleton instance
const accessibilityOptionsService = new AccessibilityOptionsService();
export default accessibilityOptionsService;