/**
 * T029 Enhanced User Experience: Responsive Layout Component
 * Adaptive layout that responds to device capabilities and screen sizes
 */

import React, { useState, useEffect, useRef } from 'react';
import mobileInterfaceService from '../services/mobileInterfaceService.js';
import MobileNavigation from './MobileNavigation.jsx';

const ResponsiveLayout = ({ 
  children, 
  currentPage = 'home',
  onNavigate,
  notifications = 0,
  isProcessing = false,
  showNavigation = true,
  className = ''
}) => {
  const [deviceInfo, setDeviceInfo] = useState(mobileInterfaceService.getDeviceInfo());
  const [isNavigationOpen, setIsNavigationOpen] = useState(false);
  const layoutRef = useRef(null);
  const contentRef = useRef(null);

  useEffect(() => {
    // Initialize mobile optimizations
    mobileInterfaceService.applyMobileOptimizations();

    // Listen for device changes
    const handleDeviceChange = () => {
      setDeviceInfo(mobileInterfaceService.getDeviceInfo());
    };

    window.addEventListener('mobile:viewportchange', handleDeviceChange);
    window.addEventListener('mobile:orientationchange', handleDeviceChange);

    return () => {
      window.removeEventListener('mobile:viewportchange', handleDeviceChange);
      window.removeEventListener('mobile:orientationchange', handleDeviceChange);
    };
  }, []);

  useEffect(() => {
    // Apply responsive classes to body
    const classes = mobileInterfaceService.getMobileClasses();
    document.body.className = document.body.className
      .split(' ')
      .filter(cls => !cls.startsWith('is-') && !cls.startsWith('has-'))
      .concat(classes)
      .join(' ');

    // Add layout-specific classes
    if (deviceInfo.device.isMobile) {
      document.body.classList.add('mobile-layout');
    } else {
      document.body.classList.remove('mobile-layout');
    }
  }, [deviceInfo]);

  useEffect(() => {
    // Setup pull-to-refresh for mobile
    if (contentRef.current && deviceInfo.touch.hasTouch) {
      const cleanup = mobileInterfaceService.setupPullToRefresh(
        contentRef.current,
        () => {
          // Handle refresh action
          window.location.reload();
        }
      );

      return cleanup;
    }
  }, [deviceInfo.touch.hasTouch]);

  const isMobileBreakpoint = mobileInterfaceService.isMobileBreakpoint();
  const isTabletBreakpoint = deviceInfo.breakpoint === 'md';
  const isDesktopBreakpoint = ['lg', 'xl', '2xl'].includes(deviceInfo.breakpoint);

  // Calculate content padding based on layout
  const getContentPadding = () => {
    if (isMobileBreakpoint) {
      return {
        paddingTop: showNavigation ? '64px' : '0', // Header height
        paddingBottom: '80px', // Bottom tab bar height
        paddingLeft: '0',
        paddingRight: '0'
      };
    } else if (isTabletBreakpoint) {
      return {
        paddingTop: '0',
        paddingBottom: '0',
        paddingLeft: showNavigation ? '256px' : '0', // Navigation width
        paddingRight: '0'
      };
    } else {
      return {
        paddingTop: '0',
        paddingBottom: '0',
        paddingLeft: showNavigation ? '256px' : '0', // Navigation width
        paddingRight: '0'
      };
    }
  };

  const contentPadding = getContentPadding();

  return (
    <div 
      ref={layoutRef}
      className={`
        min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200
        ${deviceInfo.device.isMobile ? 'mobile-layout' : ''}
        ${deviceInfo.device.isIOS ? 'ios-layout' : ''}
        ${deviceInfo.device.isAndroid ? 'android-layout' : ''}
        ${deviceInfo.orientation.isPortrait ? 'portrait-layout' : 'landscape-layout'}
        ${className}
      `}
    >
      {/* Navigation */}
      {showNavigation && (
        <MobileNavigation
          currentPage={currentPage}
          onNavigate={onNavigate}
          notifications={notifications}
          isProcessing={isProcessing}
        />
      )}

      {/* Main Content Area */}
      <main 
        ref={contentRef}
        className="relative min-h-screen transition-all duration-300"
        style={contentPadding}
      >
        {/* Pull-to-refresh indicator */}
        {deviceInfo.touch.hasTouch && (
          <div className="pull-to-refresh-indicator absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-full transition-transform">
            <div className="bg-blue-500 text-white px-4 py-2 rounded-full text-sm font-medium">
              Pull to refresh
            </div>
          </div>
        )}

        {/* Content Container */}
        <div className={`
          w-full max-w-none
          ${isMobileBreakpoint ? 'px-4 py-4' : 'px-6 py-6'}
          ${isTabletBreakpoint ? 'max-w-none' : ''}
          ${isDesktopBreakpoint ? 'max-w-7xl mx-auto' : ''}
        `}>
          {children}
        </div>

        {/* Mobile-specific UI elements */}
        {isMobileBreakpoint && (
          <>
            {/* Scroll to top button */}
            <ScrollToTopButton />
            
            {/* Mobile keyboard spacer */}
            <div className="mobile-keyboard-spacer h-0 transition-all duration-300" />
          </>
        )}
      </main>

      {/* Global mobile styles */}
      <style jsx global>{`
        /* Touch optimizations */
        .touch-active {
          opacity: 0.7;
          transform: scale(0.98);
          transition: all 0.1s ease;
        }

        /* Pull-to-refresh styles */
        .pull-to-refresh-ready .pull-to-refresh-indicator {
          transform: translateX(-50%) translateY(0);
        }

        /* Low memory optimizations */
        .low-memory * {
          animation: none !important;
          transition: none !important;
        }

        /* Safe area support */
        .safe-area-padding {
          padding-top: env(safe-area-inset-top);
          padding-right: env(safe-area-inset-right);
          padding-bottom: env(safe-area-inset-bottom);
          padding-left: env(safe-area-inset-left);
        }

        /* iOS-specific styles */
        .ios-layout input,
        .ios-layout textarea {
          border-radius: 8px;
        }

        /* Android-specific styles */
        .android-layout {
          --shadow-color: rgba(0, 0, 0, 0.2);
        }

        /* Mobile keyboard handling */
        @media (max-height: 500px) and (orientation: landscape) {
          .mobile-keyboard-spacer {
            height: 200px;
          }
        }

        /* High contrast mode support */
        @media (prefers-contrast: high) {
          .mobile-layout {
            --border-color: #000;
            --text-color: #000;
            --bg-color: #fff;
          }
        }

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
          .mobile-layout * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }

        /* Large text support */
        @media (prefers-font-size: large) {
          .mobile-layout {
            font-size: 1.1em;
          }
        }

        /* High DPI optimizations */
        @media (-webkit-min-device-pixel-ratio: 2) {
          .is-retina .crisp-edges {
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
          }
        }
      `}</style>
    </div>
  );
};

// Scroll to top button component
const ScrollToTopButton = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const toggleVisibility = () => {
      if (window.pageYOffset > 300) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    window.addEventListener('scroll', toggleVisibility);
    return () => window.removeEventListener('scroll', toggleVisibility);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
    mobileInterfaceService.hapticFeedback('light');
  };

  if (!isVisible) return null;

  return (
    <button
      onClick={scrollToTop}
      className={`
        fixed bottom-24 right-4 z-30 w-12 h-12 bg-blue-600 text-white rounded-full shadow-lg
        flex items-center justify-center transition-all duration-300 hover:bg-blue-700
        ${isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-75'}
      `}
      aria-label="Scroll to top"
    >
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    </button>
  );
};

export default ResponsiveLayout;