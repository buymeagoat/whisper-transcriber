/**
 * T029 Enhanced User Experience: Mobile Interface Service
 * Service for mobile-specific optimizations and responsive design utilities
 */

class MobileInterfaceService {
  constructor() {
    this.deviceInfo = this.detectDevice();
    this.touchSupport = this.detectTouchSupport();
    this.viewport = this.getViewportInfo();
    this.orientation = this.getOrientation();
    this.platform = this.detectPlatform();
    
    this.setupEventListeners();
  }

  /**
   * Detect device type and capabilities
   */
  detectDevice() {
    const userAgent = navigator.userAgent.toLowerCase();
    const width = window.screen.width;
    const height = window.screen.height;
    const pixelRatio = window.devicePixelRatio || 1;

    return {
      isMobile: /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent),
      isTablet: /(ipad|tablet|(android(?!.*mobile))|(windows(?!.*phone)(.*touch))|kindle|playbook|silk|(puffin(?!.*(ip|ap|wp))))/.test(userAgent),
      isDesktop: !/android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent),
      isIOS: /ipad|iphone|ipod/.test(userAgent),
      isAndroid: /android/.test(userAgent),
      isSmallScreen: width < 768,
      isMediumScreen: width >= 768 && width < 1024,
      isLargeScreen: width >= 1024,
      screenWidth: width,
      screenHeight: height,
      pixelRatio: pixelRatio,
      isRetina: pixelRatio > 1
    };
  }

  /**
   * Detect touch support
   */
  detectTouchSupport() {
    return {
      hasTouch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
      maxTouchPoints: navigator.maxTouchPoints || 0,
      touchEventSupport: 'TouchEvent' in window,
      pointerEventSupport: 'PointerEvent' in window
    };
  }

  /**
   * Get viewport information
   */
  getViewportInfo() {
    return {
      width: window.innerWidth,
      height: window.innerHeight,
      availableWidth: window.screen.availWidth,
      availableHeight: window.screen.availHeight,
      colorDepth: window.screen.colorDepth,
      pixelDepth: window.screen.pixelDepth
    };
  }

  /**
   * Get orientation information
   */
  getOrientation() {
    const orientation = window.screen.orientation || window.orientation;
    return {
      angle: orientation?.angle || 0,
      type: orientation?.type || 'unknown',
      isPortrait: window.innerHeight > window.innerWidth,
      isLandscape: window.innerWidth > window.innerHeight
    };
  }

  /**
   * Detect platform-specific features
   */
  detectPlatform() {
    const userAgent = navigator.userAgent;
    
    return {
      isIOS: /iPad|iPhone|iPod/.test(userAgent),
      isAndroid: /Android/.test(userAgent),
      isChrome: /Chrome/.test(userAgent),
      isSafari: /Safari/.test(userAgent) && !/Chrome/.test(userAgent),
      isFirefox: /Firefox/.test(userAgent),
      isEdge: /Edge/.test(userAgent),
      supportsServiceWorker: 'serviceWorker' in navigator,
      supportsWebGL: !!window.WebGLRenderingContext,
      supportsWebAudio: !!(window.AudioContext || window.webkitAudioContext),
      supportsFileAPI: window.File && window.FileReader && window.FileList && window.Blob,
      supportsGeolocation: 'geolocation' in navigator,
      supportsVibration: 'vibrate' in navigator,
      supportsFullscreen: document.fullscreenEnabled || document.webkitFullscreenEnabled,
      supportsSharing: 'share' in navigator
    };
  }

  /**
   * Setup event listeners for mobile-specific events
   */
  setupEventListeners() {
    // Orientation change
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.orientation = this.getOrientation();
        this.viewport = this.getViewportInfo();
        this.notifyOrientationChange();
      }, 100);
    });

    // Resize
    window.addEventListener('resize', () => {
      this.viewport = this.getViewportInfo();
      this.notifyViewportChange();
    });

    // Visibility change (for PWA background handling)
    document.addEventListener('visibilitychange', () => {
      this.notifyVisibilityChange();
    });

    // Network status
    window.addEventListener('online', () => this.notifyNetworkChange(true));
    window.addEventListener('offline', () => this.notifyNetworkChange(false));
  }

  /**
   * Get responsive breakpoint
   */
  getBreakpoint() {
    const width = this.viewport.width;
    
    if (width < 640) return 'xs';
    if (width < 768) return 'sm';
    if (width < 1024) return 'md';
    if (width < 1280) return 'lg';
    if (width < 1536) return 'xl';
    return '2xl';
  }

  /**
   * Check if device is in mobile breakpoint
   */
  isMobileBreakpoint() {
    return ['xs', 'sm'].includes(this.getBreakpoint());
  }

  /**
   * Get mobile-specific CSS classes
   */
  getMobileClasses() {
    const classes = [];
    
    if (this.deviceInfo.isMobile) classes.push('is-mobile');
    if (this.deviceInfo.isTablet) classes.push('is-tablet');
    if (this.deviceInfo.isIOS) classes.push('is-ios');
    if (this.deviceInfo.isAndroid) classes.push('is-android');
    if (this.touchSupport.hasTouch) classes.push('has-touch');
    if (this.orientation.isPortrait) classes.push('is-portrait');
    if (this.orientation.isLandscape) classes.push('is-landscape');
    if (this.deviceInfo.isRetina) classes.push('is-retina');
    if (this.isMobileBreakpoint()) classes.push('is-mobile-breakpoint');
    
    return classes;
  }

  /**
   * Optimize touch interactions
   */
  optimizeTouchInteractions(element) {
    if (!this.touchSupport.hasTouch) return;

    // Disable double-tap zoom on buttons and interactive elements
    element.style.touchAction = 'manipulation';
    
    // Add touch feedback
    element.addEventListener('touchstart', () => {
      element.classList.add('touch-active');
    }, { passive: true });
    
    element.addEventListener('touchend', () => {
      setTimeout(() => {
        element.classList.remove('touch-active');
      }, 150);
    }, { passive: true });
    
    element.addEventListener('touchcancel', () => {
      element.classList.remove('touch-active');
    }, { passive: true });
  }

  /**
   * Setup swipe gesture detection
   */
  setupSwipeGestures(element, callbacks) {
    if (!this.touchSupport.hasTouch) return null;

    let startX, startY, startTime;
    const threshold = 50; // Minimum distance for swipe
    const restraint = 100; // Maximum distance perpendicular to swipe
    const allowedTime = 300; // Maximum time for swipe

    const handleTouchStart = (e) => {
      const touch = e.touches[0];
      startX = touch.clientX;
      startY = touch.clientY;
      startTime = new Date().getTime();
    };

    const handleTouchEnd = (e) => {
      const touch = e.changedTouches[0];
      const endX = touch.clientX;
      const endY = touch.clientY;
      const endTime = new Date().getTime();
      
      const distX = endX - startX;
      const distY = endY - startY;
      const elapsedTime = endTime - startTime;
      
      if (elapsedTime <= allowedTime) {
        if (Math.abs(distX) >= threshold && Math.abs(distY) <= restraint) {
          // Horizontal swipe
          if (distX > 0) {
            callbacks.onSwipeRight?.(distX);
          } else {
            callbacks.onSwipeLeft?.(Math.abs(distX));
          }
        } else if (Math.abs(distY) >= threshold && Math.abs(distX) <= restraint) {
          // Vertical swipe
          if (distY > 0) {
            callbacks.onSwipeDown?.(distY);
          } else {
            callbacks.onSwipeUp?.(Math.abs(distY));
          }
        }
      }
    };

    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });

    // Return cleanup function
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }

  /**
   * Setup pull-to-refresh
   */
  setupPullToRefresh(element, onRefresh) {
    if (!this.touchSupport.hasTouch) return null;

    let startY, currentY, pulling = false;
    const threshold = 100;
    
    const handleTouchStart = (e) => {
      if (element.scrollTop === 0) {
        startY = e.touches[0].clientY;
      }
    };

    const handleTouchMove = (e) => {
      if (startY && element.scrollTop === 0) {
        currentY = e.touches[0].clientY;
        const pullDistance = currentY - startY;
        
        if (pullDistance > 0) {
          pulling = true;
          element.style.transform = `translateY(${Math.min(pullDistance * 0.5, threshold)}px)`;
          
          if (pullDistance > threshold) {
            element.classList.add('pull-to-refresh-ready');
          } else {
            element.classList.remove('pull-to-refresh-ready');
          }
        }
      }
    };

    const handleTouchEnd = () => {
      if (pulling) {
        const pullDistance = currentY - startY;
        
        if (pullDistance > threshold) {
          onRefresh?.();
        }
        
        element.style.transform = '';
        element.classList.remove('pull-to-refresh-ready');
        pulling = false;
        startY = null;
        currentY = null;
      }
    };

    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }

  /**
   * Optimize scrolling performance
   */
  optimizeScrolling(element) {
    // Enable hardware acceleration
    element.style.transform = 'translateZ(0)';
    element.style.webkitOverflowScrolling = 'touch';
    
    // Momentum scrolling for iOS
    if (this.deviceInfo.isIOS) {
      element.style.webkitOverflowScrolling = 'touch';
    }
  }

  /**
   * Handle iOS safe area insets
   */
  handleSafeAreaInsets() {
    if (!this.deviceInfo.isIOS) return;

    // Add CSS custom properties for safe area insets
    const style = document.createElement('style');
    style.textContent = `
      :root {
        --safe-area-inset-top: env(safe-area-inset-top);
        --safe-area-inset-right: env(safe-area-inset-right);
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        --safe-area-inset-left: env(safe-area-inset-left);
      }
      
      .safe-area-padding {
        padding-top: env(safe-area-inset-top);
        padding-right: env(safe-area-inset-right);
        padding-bottom: env(safe-area-inset-bottom);
        padding-left: env(safe-area-inset-left);
      }
      
      .safe-area-margin {
        margin-top: env(safe-area-inset-top);
        margin-right: env(safe-area-inset-right);
        margin-bottom: env(safe-area-inset-bottom);
        margin-left: env(safe-area-inset-left);
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Optimize images for mobile
   */
  optimizeImages() {
    const images = document.querySelectorAll('img[data-mobile-src]');
    
    images.forEach(img => {
      if (this.deviceInfo.isMobile) {
        const mobileSrc = img.getAttribute('data-mobile-src');
        if (mobileSrc) {
          img.src = mobileSrc;
        }
      }
      
      // Add loading optimization
      if ('loading' in HTMLImageElement.prototype) {
        img.loading = 'lazy';
      }
    });
  }

  /**
   * Setup haptic feedback
   */
  hapticFeedback(type = 'light') {
    if (!this.platform.supportsVibration) return;

    const patterns = {
      light: [10],
      medium: [20],
      heavy: [50],
      success: [10, 50, 10],
      error: [100, 50, 100],
      warning: [50, 25, 50],
      swipe: [5],
      tap: [8],
      longPress: [25],
      selection: [12],
      navigation: [15],
      toggle: [10, 10, 10]
    };

    const pattern = patterns[type] || patterns.light;
    navigator.vibrate(pattern);
  }

  /**
   * Advanced gesture recognition for settings interface
   */
  setupAdvancedGestures(element, callbacks = {}) {
    if (!element || !this.touchSupport.hasTouch) return null;
    
    let touchStartX = 0;
    let touchStartY = 0;
    let touchStartTime = 0;
    let isDragging = false;
    let longPressTimer = null;
    let multiTouch = false;
    
    const handleTouchStart = (e) => {
      const touch = e.touches[0];
      touchStartX = touch.clientX;
      touchStartY = touch.clientY;
      touchStartTime = Date.now();
      isDragging = false;
      multiTouch = e.touches.length > 1;
      
      // Setup long press detection
      if (!multiTouch) {
        longPressTimer = setTimeout(() => {
          if (!isDragging && callbacks.onLongPress) {
            this.hapticFeedback('longPress');
            callbacks.onLongPress(e, { x: touchStartX, y: touchStartY });
          }
        }, 500); // 500ms for long press
      }
      
      if (callbacks.onTouchStart) {
        callbacks.onTouchStart(e, { 
          x: touchStartX, 
          y: touchStartY,
          multiTouch 
        });
      }
    };
    
    const handleTouchMove = (e) => {
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
      }
      
      const touch = e.touches[0];
      const deltaX = touch.clientX - touchStartX;
      const deltaY = touch.clientY - touchStartY;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      
      if (distance > 10) {
        isDragging = true;
      }
      
      if (callbacks.onTouchMove) {
        callbacks.onTouchMove(e, { 
          deltaX, 
          deltaY, 
          distance, 
          currentX: touch.clientX, 
          currentY: touch.clientY,
          isDragging
        });
      }
    };
    
    const handleTouchEnd = (e) => {
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
      }
      
      const touch = e.changedTouches[0];
      const deltaX = touch.clientX - touchStartX;
      const deltaY = touch.clientY - touchStartY;
      const duration = Date.now() - touchStartTime;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      
      // Determine gesture type
      if (!isDragging && duration < 200 && distance < 10) {
        // Tap
        this.hapticFeedback('tap');
        if (callbacks.onTap) {
          callbacks.onTap(e, { 
            x: touch.clientX, 
            y: touch.clientY, 
            duration 
          });
        }
      } else if (isDragging && distance > 50) {
        // Swipe
        const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
        let direction = 'unknown';
        
        if (Math.abs(angle) < 45) direction = 'right';
        else if (Math.abs(angle) > 135) direction = 'left';
        else if (angle > 0) direction = 'down';
        else direction = 'up';
        
        this.hapticFeedback('swipe');
        if (callbacks.onSwipe) {
          callbacks.onSwipe(e, { 
            direction, 
            distance, 
            deltaX, 
            deltaY, 
            velocity: distance / duration 
          });
        }
      }
      
      if (callbacks.onTouchEnd) {
        callbacks.onTouchEnd(e, { 
          deltaX, 
          deltaY, 
          duration, 
          distance, 
          wasDragging: isDragging 
        });
      }
      
      isDragging = false;
      multiTouch = false;
    };
    
    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: false });
    
    // Return cleanup function
    return () => {
      if (longPressTimer) {
        clearTimeout(longPressTimer);
      }
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }

  /**
   * Enhanced pull-to-refresh with visual feedback
   */
  setupEnhancedPullToRefresh(element, onRefresh, options = {}) {
    if (!element || !this.isMobileBreakpoint()) return null;
    
    const {
      threshold = 80,
      resistance = 0.5,
      snapBackDuration = 300,
      refreshIndicator = true
    } = options;
    
    let startY = 0;
    let currentY = 0;
    let refreshTriggered = false;
    let indicator = null;
    
    // Create refresh indicator
    if (refreshIndicator) {
      indicator = document.createElement('div');
      indicator.className = 'pull-refresh-indicator';
      indicator.innerHTML = '↓ Pull to refresh';
      indicator.style.cssText = `
        position: absolute;
        top: -40px;
        left: 50%;
        transform: translateX(-50%);
        padding: 8px 16px;
        background: rgba(0,0,0,0.7);
        color: white;
        border-radius: 20px;
        font-size: 12px;
        opacity: 0;
        transition: opacity 0.2s;
        z-index: 1000;
      `;
      element.style.position = 'relative';
      element.appendChild(indicator);
    }
    
    const handleTouchStart = (e) => {
      if (element.scrollTop === 0) {
        startY = e.touches[0].clientY;
      }
    };
    
    const handleTouchMove = (e) => {
      if (element.scrollTop === 0 && startY) {
        currentY = e.touches[0].clientY;
        const pullDistance = currentY - startY;
        
        if (pullDistance > 0) {
          e.preventDefault();
          
          // Apply resistance
          const resistedDistance = pullDistance * resistance;
          const progress = Math.min(resistedDistance / threshold, 1);
          
          // Visual feedback
          element.style.transform = `translateY(${resistedDistance}px)`;
          
          if (indicator) {
            indicator.style.opacity = progress;
            indicator.style.top = `${-40 + resistedDistance * 0.3}px`;
            
            if (resistedDistance > threshold && !refreshTriggered) {
              indicator.innerHTML = '↑ Release to refresh';
              indicator.style.background = 'rgba(34, 197, 94, 0.8)';
            } else {
              indicator.innerHTML = '↓ Pull to refresh';
              indicator.style.background = 'rgba(0,0,0,0.7)';
            }
          }
          
          if (resistedDistance > threshold && !refreshTriggered) {
            refreshTriggered = true;
            this.hapticFeedback('medium');
          } else if (resistedDistance <= threshold && refreshTriggered) {
            refreshTriggered = false;
            this.hapticFeedback('light');
          }
        }
      }
    };
    
    const handleTouchEnd = (e) => {
      if (refreshTriggered && onRefresh) {
        onRefresh();
        if (indicator) {
          indicator.innerHTML = '⟳ Refreshing...';
          indicator.style.background = 'rgba(59, 130, 246, 0.8)';
        }
      }
      
      // Animate back
      element.style.transition = `transform ${snapBackDuration}ms ease-out`;
      element.style.transform = '';
      
      if (indicator) {
        indicator.style.opacity = 0;
        indicator.style.top = '-40px';
      }
      
      setTimeout(() => {
        element.style.transition = '';
      }, snapBackDuration);
      
      // Reset
      startY = 0;
      currentY = 0;
      refreshTriggered = false;
    };
    
    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: false });
    
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
      if (indicator) {
        indicator.remove();
      }
    };
  }

  /**
   * Mobile keyboard and safe area utilities
   */
  handleVirtualKeyboard() {
    if (!this.isMobileBreakpoint()) return;
    
    let initialViewportHeight = window.innerHeight;
    let keyboardHeight = 0;
    
    const handleViewportChange = () => {
      const currentHeight = window.innerHeight;
      const difference = initialViewportHeight - currentHeight;
      
      if (difference > 150) {
        // Keyboard likely opened
        keyboardHeight = difference;
        document.body.classList.add('keyboard-open');
        document.documentElement.style.setProperty('--keyboard-height', `${keyboardHeight}px`);
        
        // Scroll focused element into view
        const focused = document.activeElement;
        if (focused && (focused.tagName === 'INPUT' || focused.tagName === 'TEXTAREA')) {
          setTimeout(() => {
            focused.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }, 100);
        }
        
        this.notifySubscribers('keyboard-opened', { height: keyboardHeight });
      } else {
        // Keyboard likely closed
        keyboardHeight = 0;
        document.body.classList.remove('keyboard-open');
        document.documentElement.style.removeProperty('--keyboard-height');
        this.notifySubscribers('keyboard-closed', {});
      }
    };
    
    window.addEventListener('resize', handleViewportChange);
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        initialViewportHeight = window.innerHeight;
        handleViewportChange();
      }, 500);
    });
    
    return () => {
      window.removeEventListener('resize', handleViewportChange);
      document.body.classList.remove('keyboard-open');
      document.documentElement.style.removeProperty('--keyboard-height');
    };
  }

  /**
   * Safe area inset utilities for notched devices
   */
  getSafeAreaInsets() {
    const style = getComputedStyle(document.documentElement);
    
    return {
      top: parseInt(style.getPropertyValue('--safe-area-inset-top')) || 0,
      right: parseInt(style.getPropertyValue('--safe-area-inset-right')) || 0,
      bottom: parseInt(style.getPropertyValue('--safe-area-inset-bottom')) || 0,
      left: parseInt(style.getPropertyValue('--safe-area-inset-left')) || 0
    };
  }

  /**
   * Optimize touch targets for mobile settings
   */
  optimizeTouchTargets() {
    const minTouchSize = 44; // iOS HIG minimum
    const elements = document.querySelectorAll('button, [role="button"], input, select, textarea, a, [tabindex]');
    
    elements.forEach(element => {
      const rect = element.getBoundingClientRect();
      
      if (rect.width < minTouchSize || rect.height < minTouchSize) {
        // Only apply if element is visible and in settings interface
        if (rect.width > 0 && rect.height > 0) {
          element.style.minWidth = `${minTouchSize}px`;
          element.style.minHeight = `${minTouchSize}px`;
          element.style.display = element.style.display || 'inline-flex';
          element.style.alignItems = 'center';
          element.style.justifyContent = 'center';
          element.style.padding = element.style.padding || '8px';
        }
      }
    });
  }

  /**
   * Settings-specific mobile preferences
   */
  getSettingsPreferences() {
    return {
      enableSwipeNavigation: true,
      enableHapticFeedback: this.platform.supportsVibration,
      compactMode: this.deviceInfo.isSmallScreen,
      showSearchSuggestions: true,
      autoCollapseSections: this.deviceInfo.isSmallScreen,
      pullToRefresh: true,
      gestureThresholds: {
        swipe: this.deviceInfo.isSmallScreen ? 30 : 50,
        longPress: 500,
        doubleTap: 300
      }
    };
  }

  /**
   * Add mobile-specific CSS classes for settings
   */
  addSettingsMobileClasses() {
    const classes = [
      'mobile-settings',
      this.deviceInfo.isMobile ? 'is-mobile' : 'is-desktop',
      this.deviceInfo.isSmallScreen ? 'small-screen' : 'large-screen',
      this.touchSupport.hasTouch ? 'has-touch' : 'no-touch',
      this.isPortraitOrientation() ? 'portrait' : 'landscape',
      this.platform.supportsVibration ? 'has-haptic' : 'no-haptic'
    ];
    
    document.body.classList.add(...classes);
    
    return () => {
      document.body.classList.remove(...classes);
    };
  }

  /**
   * Check if app is running in standalone mode (PWA)
   */
  isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }

  /**
   * Get device memory information
   */
  getMemoryInfo() {
    if ('memory' in performance) {
      return {
        usedJSMemory: performance.memory.usedJSMemory,
        totalJSMemory: performance.memory.totalJSMemory,
        jsMemoryLimit: performance.memory.jsMemoryLimit
      };
    }
    return null;
  }

  /**
   * Optimize for low-memory devices
   */
  optimizeForLowMemory() {
    const memoryInfo = this.getMemoryInfo();
    
    if (memoryInfo && memoryInfo.jsMemoryLimit < 1073741824) { // Less than 1GB
      // Reduce image quality
      this.reduceImageQuality();
      
      // Disable animations on low memory
      document.body.classList.add('low-memory');
      
      // Reduce concurrent operations
      return true;
    }
    
    return false;
  }

  /**
   * Reduce image quality for performance
   */
  reduceImageQuality() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    document.querySelectorAll('img').forEach(img => {
      if (img.naturalWidth > 800) {
        canvas.width = Math.min(img.naturalWidth, 800);
        canvas.height = (img.naturalHeight * canvas.width) / img.naturalWidth;
        
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        img.src = canvas.toDataURL('image/jpeg', 0.8);
      }
    });
  }

  /**
   * Event notification methods
   */
  notifyOrientationChange() {
    window.dispatchEvent(new CustomEvent('mobile:orientationchange', {
      detail: this.orientation
    }));
  }

  notifyViewportChange() {
    window.dispatchEvent(new CustomEvent('mobile:viewportchange', {
      detail: this.viewport
    }));
  }

  notifyVisibilityChange() {
    window.dispatchEvent(new CustomEvent('mobile:visibilitychange', {
      detail: { hidden: document.hidden }
    }));
  }

  notifyNetworkChange(online) {
    window.dispatchEvent(new CustomEvent('mobile:networkchange', {
      detail: { online }
    }));
  }

  /**
   * Get comprehensive device information
   */
  getDeviceInfo() {
    return {
      device: this.deviceInfo,
      touch: this.touchSupport,
      viewport: this.viewport,
      orientation: this.orientation,
      platform: this.platform,
      breakpoint: this.getBreakpoint(),
      isStandalone: this.isStandalone(),
      memoryInfo: this.getMemoryInfo()
    };
  }

  /**
   * Apply mobile optimizations to the app
   */
  applyMobileOptimizations() {
    // Add mobile classes to body
    document.body.classList.add(...this.getMobileClasses());
    
    // Handle safe area insets for iOS
    this.handleSafeAreaInsets();
    
    // Optimize images
    this.optimizeImages();
    
    // Check for low memory and optimize if needed
    if (this.optimizeForLowMemory()) {
      console.log('Low memory device detected, applying optimizations');
    }
    
    // Prevent zoom on input focus (iOS)
    if (this.deviceInfo.isIOS) {
      const meta = document.querySelector('meta[name="viewport"]');
      if (meta) {
        meta.content = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no';
      }
    }
    
    // Add touch optimizations to interactive elements
    const interactiveElements = document.querySelectorAll('button, a, [role="button"]');
    interactiveElements.forEach(el => this.optimizeTouchInteractions(el));
  }
}

// Create singleton instance
const mobileInterfaceService = new MobileInterfaceService();

export default mobileInterfaceService;