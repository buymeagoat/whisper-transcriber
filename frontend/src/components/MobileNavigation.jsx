/**
 * T029 Enhanced User Experience: Mobile Navigation Component
 * Mobile-optimized navigation with touch gestures and responsive design
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Menu, X, Home, Upload, Settings, Activity, 
  History, Bell, User, ChevronLeft, ChevronRight,
  Download, FileAudio, Zap, HelpCircle
} from 'lucide-react';
import mobileInterfaceService from '../services/mobileInterfaceService.js';

const MobileNavigation = ({ 
  currentPage = 'home',
  onNavigate,
  notifications = 0,
  isProcessing = false,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [deviceInfo, setDeviceInfo] = useState(mobileInterfaceService.getDeviceInfo());
  const navRef = useRef(null);
  const overlayRef = useRef(null);
  const swipeCleanupRef = useRef(null);

  useEffect(() => {
    // Update device info on viewport changes
    const handleViewportChange = () => {
      setDeviceInfo(mobileInterfaceService.getDeviceInfo());
    };

    window.addEventListener('mobile:viewportchange', handleViewportChange);
    window.addEventListener('mobile:orientationchange', handleViewportChange);

    return () => {
      window.removeEventListener('mobile:viewportchange', handleViewportChange);
      window.removeEventListener('mobile:orientationchange', handleViewportChange);
    };
  }, []);

  useEffect(() => {
    if (navRef.current && deviceInfo.touch.hasTouch) {
      // Setup swipe gesture for navigation
      swipeCleanupRef.current = mobileInterfaceService.setupSwipeGestures(
        navRef.current,
        {
          onSwipeLeft: () => {
            if (isOpen) {
              setIsOpen(false);
              mobileInterfaceService.hapticFeedback('light');
            }
          },
          onSwipeRight: () => {
            if (!isOpen && deviceInfo.device.isMobile) {
              setIsOpen(true);
              mobileInterfaceService.hapticFeedback('light');
            }
          }
        }
      );
    }

    return () => {
      if (swipeCleanupRef.current) {
        swipeCleanupRef.current();
      }
    };
  }, [isOpen, deviceInfo.touch.hasTouch, deviceInfo.device.isMobile]);

  useEffect(() => {
    // Close navigation on outside click
    const handleClickOutside = (event) => {
      if (
        isOpen && 
        navRef.current && 
        !navRef.current.contains(event.target) &&
        !event.target.closest('.mobile-nav-trigger')
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('touchstart', handleClickOutside);
    document.addEventListener('click', handleClickOutside);

    return () => {
      document.removeEventListener('touchstart', handleClickOutside);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isOpen]);

  const navigationItems = [
    {
      id: 'home',
      label: 'Home',
      icon: Home,
      description: 'Dashboard and overview'
    },
    {
      id: 'upload',
      label: 'Upload',
      icon: Upload,
      description: 'Upload audio files',
      badge: isProcessing ? 'Processing' : null
    },
    {
      id: 'history',
      label: 'History',
      icon: History,
      description: 'View transcription history'
    },
    {
      id: 'activity',
      label: 'Activity',
      icon: Activity,
      description: 'Real-time activity monitor'
    },
    {
      id: 'downloads',
      label: 'Downloads',
      icon: Download,
      description: 'Download completed files'
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: Bell,
      description: 'View notifications',
      badge: notifications > 0 ? notifications.toString() : null
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      description: 'App settings and preferences'
    },
    {
      id: 'help',
      label: 'Help',
      icon: HelpCircle,
      description: 'Help and documentation'
    }
  ];

  const handleNavigation = (pageId) => {
    onNavigate?.(pageId);
    setIsOpen(false);
    mobileInterfaceService.hapticFeedback('light');
  };

  const toggleNavigation = () => {
    setIsOpen(!isOpen);
    mobileInterfaceService.hapticFeedback('light');
  };

  // Get current breakpoint for responsive behavior
  const isMobileBreakpoint = deviceInfo.breakpoint === 'xs' || deviceInfo.breakpoint === 'sm';

  return (
    <>
      {/* Mobile Header Bar */}
      {isMobileBreakpoint && (
        <div className={`
          fixed top-0 left-0 right-0 z-40 bg-white dark:bg-gray-900 
          border-b border-gray-200 dark:border-gray-700 safe-area-padding
          ${className}
        `}>
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={toggleNavigation}
              className="mobile-nav-trigger p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle navigation menu"
            >
              <Menu className="w-6 h-6" />
            </button>
            
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              Whisper Transcriber
            </h1>
            
            <div className="flex items-center space-x-2">
              {isProcessing && (
                <div className="flex items-center space-x-1 text-blue-600 dark:text-blue-400">
                  <Zap className="w-4 h-4 animate-pulse" />
                  <span className="text-sm font-medium">Processing</span>
                </div>
              )}
              
              {notifications > 0 && (
                <button
                  onClick={() => handleNavigation('notifications')}
                  className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <Bell className="w-5 h-5" />
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {notifications > 9 ? '9+' : notifications}
                  </span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Overlay */}
      {isOpen && isMobileBreakpoint && (
        <div
          ref={overlayRef}
          className="fixed inset-0 bg-black bg-opacity-50 z-50 transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Navigation Drawer */}
      <nav
        ref={navRef}
        className={`
          fixed top-0 left-0 h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 z-50
          transition-transform duration-300 ease-in-out safe-area-padding
          ${isMobileBreakpoint ? 'w-80' : 'w-64'}
          ${isOpen || !isMobileBreakpoint ? 'translate-x-0' : '-translate-x-full'}
          ${className}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <FileAudio className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Whisper
            </h2>
          </div>
          
          {isMobileBreakpoint && (
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Close navigation"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-3">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              
              return (
                <li key={item.id}>
                  <button
                    onClick={() => handleNavigation(item.id)}
                    className={`
                      w-full flex items-center space-x-3 px-3 py-3 rounded-lg text-left
                      transition-all duration-200 group
                      ${isActive 
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800' 
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                      }
                    `}
                  >
                    <div className="relative">
                      <Icon className={`
                        w-5 h-5 transition-colors
                        ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300'}
                      `} />
                      
                      {item.badge && (
                        <span className={`
                          absolute -top-2 -right-2 px-1.5 py-0.5 text-xs font-medium rounded-full
                          ${item.id === 'notifications' 
                            ? 'bg-red-500 text-white' 
                            : 'bg-blue-500 text-white'
                          }
                        `}>
                          {item.badge}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className={`
                        font-medium
                        ${isActive ? 'text-blue-700 dark:text-blue-300' : 'text-gray-900 dark:text-white'}
                      `}>
                        {item.label}
                      </div>
                      {isMobileBreakpoint && (
                        <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          {item.description}
                        </div>
                      )}
                    </div>
                    
                    {isActive && (
                      <ChevronRight className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* User Profile Section */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <button className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group">
            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-gray-600 dark:text-gray-300" />
            </div>
            <div className="flex-1 text-left">
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                User Profile
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Manage account
              </div>
            </div>
          </button>
        </div>

        {/* Device Info (Development Mode) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="border-t border-gray-200 dark:border-gray-700 p-4 text-xs text-gray-500 dark:text-gray-400">
            <div>Breakpoint: {deviceInfo.breakpoint}</div>
            <div>Touch: {deviceInfo.touch.hasTouch ? 'Yes' : 'No'}</div>
            <div>Orientation: {deviceInfo.orientation.isPortrait ? 'Portrait' : 'Landscape'}</div>
          </div>
        )}
      </nav>

      {/* Bottom Tab Bar for Mobile */}
      {isMobileBreakpoint && !isOpen && (
        <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 safe-area-padding z-40">
          <div className="flex items-center justify-around px-2 py-1">
            {['home', 'upload', 'history', 'notifications'].map((itemId) => {
              const item = navigationItems.find(nav => nav.id === itemId);
              if (!item) return null;
              
              const Icon = item.icon;
              const isActive = currentPage === itemId;
              
              return (
                <button
                  key={itemId}
                  onClick={() => handleNavigation(itemId)}
                  className={`
                    flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition-colors relative
                    ${isActive 
                      ? 'text-blue-600 dark:text-blue-400' 
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    }
                  `}
                >
                  <div className="relative">
                    <Icon className="w-5 h-5" />
                    {item.badge && (
                      <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                        {item.badge.length > 2 ? '9+' : item.badge}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
};

export default MobileNavigation;