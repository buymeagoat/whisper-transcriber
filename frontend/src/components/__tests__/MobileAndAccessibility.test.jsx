/**
 * T030 User Preferences Enhancement: Mobile Settings Interface & Accessibility Tests
 * Comprehensive test suite for MobileSettingsInterface.jsx and AccessibilityOptions.jsx
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import MobileSettingsInterface from '../src/components/MobileSettingsInterface.jsx';
import AccessibilityOptions from '../src/components/AccessibilityOptions.jsx';
import mobileInterfaceService from '../src/services/mobileInterfaceService.js';
import accessibilityService from '../src/services/accessibilityService.js';

// Mock the services
jest.mock('../src/services/mobileInterfaceService.js', () => ({
  isMobileDevice: jest.fn(),
  isTabletDevice: jest.fn(),
  getTouchCapabilities: jest.fn(),
  setupGestureRecognition: jest.fn(),
  setupAdvancedGestures: jest.fn(),
  enableHapticFeedback: jest.fn(),
  disableHapticFeedback: jest.fn(),
  triggerHapticFeedback: jest.fn(),
  optimizeTouchTargets: jest.fn(),
  handleVirtualKeyboard: jest.fn(),
  getSafeAreaInsets: jest.fn(),
  subscribe: jest.fn()
}));

jest.mock('../src/services/accessibilityService.js', () => ({
  getAccessibilityPreferences: jest.fn(),
  updateAccessibilityPreferences: jest.fn(),
  subscribe: jest.fn(),
  applyAccessibilitySettings: jest.fn(),
  getScreenReaderSupport: jest.fn(),
  announceToScreenReader: jest.fn(),
  setHighContrast: jest.fn(),
  setFontScale: jest.fn(),
  setReducedMotion: jest.fn(),
  enableKeyboardNavigation: jest.fn(),
  adjustTouchTargets: jest.fn(),
  enableSimplifiedInterface: jest.fn()
}));

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

// Mock intersection observer
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

// Mock touch events
Object.defineProperty(window, 'ontouchstart', { value: null, writable: true });

describe('Mobile Settings Interface', () => {
  const mockMobileCapabilities = {
    hasTouch: true,
    hasGestures: true,
    hasHaptics: true,
    screenSize: { width: 375, height: 812 },
    safeArea: { top: 44, bottom: 34, left: 0, right: 0 }
  };

  const mockPreferences = {
    theme: { appearance: { theme: 'light' } },
    notifications: { categories: { transcription: { enabled: true } } },
    upload: { general: { auto_upload: false } },
    accessibility: { vision: { high_contrast: false } }
  };

  const mockUnsubscribe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mobileInterfaceService.isMobileDevice.mockReturnValue(true);
    mobileInterfaceService.isTabletDevice.mockReturnValue(false);
    mobileInterfaceService.getTouchCapabilities.mockReturnValue(mockMobileCapabilities);
    mobileInterfaceService.getSafeAreaInsets.mockReturnValue(mockMobileCapabilities.safeArea);
    mobileInterfaceService.subscribe.mockReturnValue(mockUnsubscribe);
    
    // Mock window.matchMedia for responsive tests
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query.includes('max-width: 768px'),
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn()
      }))
    });
  });

  describe('Component Rendering', () => {
    test('renders mobile settings interface', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByTestId('mobile-settings-interface')).toBeInTheDocument();
    });

    test('adapts to mobile viewport', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      const container = screen.getByTestId('mobile-settings-interface');
      expect(container).toHaveClass('mobile-interface');
    });

    test('displays category navigation', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(screen.getByText('Theme')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Upload')).toBeInTheDocument();
      expect(screen.getByText('Accessibility')).toBeInTheDocument();
    });

    test('shows search functionality', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(screen.getByPlaceholderText(/Search settings/i)).toBeInTheDocument();
    });

    test('displays favorites section', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(screen.getByText('Favorites')).toBeInTheDocument();
    });
  });

  describe('Touch Interactions', () => {
    test('handles swipe gestures', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const container = screen.getByTestId('mobile-settings-interface');
      
      // Simulate swipe gesture
      fireEvent.touchStart(container, {
        touches: [{ clientX: 100, clientY: 100 }]
      });
      
      fireEvent.touchMove(container, {
        touches: [{ clientX: 200, clientY: 100 }]
      });
      
      fireEvent.touchEnd(container, {
        changedTouches: [{ clientX: 200, clientY: 100 }]
      });

      expect(mobileInterfaceService.setupAdvancedGestures).toHaveBeenCalled();
    });

    test('triggers haptic feedback on interactions', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const themeCategory = screen.getByText('Theme');
      await user.click(themeCategory);

      expect(mobileInterfaceService.triggerHapticFeedback).toHaveBeenCalledWith('selection');
    });

    test('optimizes touch targets', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(mobileInterfaceService.optimizeTouchTargets).toHaveBeenCalled();
    });

    test('handles pull-to-refresh', async () => {
      const mockOnRefresh = jest.fn();
      render(<MobileSettingsInterface preferences={mockPreferences} onRefresh={mockOnRefresh} />);

      const container = screen.getByTestId('mobile-settings-interface');
      
      // Simulate pull down gesture
      fireEvent.touchStart(container, {
        touches: [{ clientX: 100, clientY: 50 }]
      });
      
      fireEvent.touchMove(container, {
        touches: [{ clientX: 100, clientY: 150 }]
      });
      
      fireEvent.touchEnd(container, {
        changedTouches: [{ clientX: 100, clientY: 150 }]
      });

      await waitFor(() => {
        expect(mockOnRefresh).toHaveBeenCalled();
      });
    });
  });

  describe('Navigation', () => {
    test('navigates between categories', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const notificationsCategory = screen.getByText('Notifications');
      await user.click(notificationsCategory);

      expect(screen.getByText('Notification Settings')).toBeInTheDocument();
    });

    test('shows back button in category view', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const themeCategory = screen.getByText('Theme');
      await user.click(themeCategory);

      expect(screen.getByLabelText(/Back/i)).toBeInTheDocument();
    });

    test('returns to overview from category', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      // Navigate to category
      const themeCategory = screen.getByText('Theme');
      await user.click(themeCategory);

      // Navigate back
      const backButton = screen.getByLabelText(/Back/i);
      await user.click(backButton);

      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    test('filters settings by search term', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const searchInput = screen.getByPlaceholderText(/Search settings/i);
      await user.type(searchInput, 'theme');

      expect(screen.getByText('Theme')).toBeInTheDocument();
      expect(screen.queryByText('Upload')).not.toBeInTheDocument();
    });

    test('shows search results', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const searchInput = screen.getByPlaceholderText(/Search settings/i);
      await user.type(searchInput, 'notification');

      expect(screen.getByText('Search Results')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    test('clears search results', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const searchInput = screen.getByPlaceholderText(/Search settings/i);
      await user.type(searchInput, 'theme');
      
      const clearButton = screen.getByLabelText(/Clear search/i);
      await user.click(clearButton);

      expect(searchInput.value).toBe('');
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
  });

  describe('Favorites Management', () => {
    test('adds setting to favorites', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const favoriteButton = screen.getByTestId('favorite-theme');
      await user.click(favoriteButton);

      expect(mobileInterfaceService.triggerHapticFeedback).toHaveBeenCalledWith('toggle');
    });

    test('removes setting from favorites', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      // Add to favorites first
      const favoriteButton = screen.getByTestId('favorite-theme');
      await user.click(favoriteButton);
      
      // Remove from favorites
      await user.click(favoriteButton);

      expect(mobileInterfaceService.triggerHapticFeedback).toHaveBeenCalledWith('toggle');
    });

    test('displays favorite settings', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      // Add theme to favorites
      const favoriteButton = screen.getByTestId('favorite-theme');
      await user.click(favoriteButton);

      // Check favorites section
      const favoritesSection = screen.getByText('Favorites').closest('section');
      expect(favoritesSection).toContainElement(screen.getByText('Theme'));
    });
  });

  describe('Responsive Design', () => {
    test('adapts to tablet layout', () => {
      mobileInterfaceService.isTabletDevice.mockReturnValue(true);
      
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      const container = screen.getByTestId('mobile-settings-interface');
      expect(container).toHaveClass('tablet-layout');
    });

    test('handles orientation changes', () => {
      const { rerender } = render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      // Simulate orientation change
      Object.defineProperty(window.screen, 'orientation', {
        value: { angle: 90 },
        writable: true
      });
      
      fireEvent(window, new Event('orientationchange'));
      rerender(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(mobileInterfaceService.handleVirtualKeyboard).toHaveBeenCalled();
    });

    test('adjusts for safe areas', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(mobileInterfaceService.getSafeAreaInsets).toHaveBeenCalled();
    });
  });

  describe('Accessibility Integration', () => {
    test('supports screen reader navigation', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    test('provides proper ARIA labels', () => {
      render(<MobileSettingsInterface preferences={mockPreferences} />);
      
      expect(screen.getByLabelText(/Settings navigation/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Search settings/i)).toBeInTheDocument();
    });

    test('supports keyboard navigation on mobile', async () => {
      const user = userEvent.setup();
      render(<MobileSettingsInterface preferences={mockPreferences} />);

      const firstCategory = screen.getByText('Theme');
      firstCategory.focus();
      
      await user.keyboard('{Tab}');
      
      const secondCategory = screen.getByText('Notifications');
      expect(secondCategory).toHaveFocus();
    });
  });
});

describe('Accessibility Options Component', () => {
  const defaultAccessibilityPreferences = {
    vision: {
      high_contrast: false,
      font_size_scale: 1.0,
      reduce_motion: false,
      color_adjustments: {
        brightness: 1.0,
        contrast: 1.0,
        saturation: 1.0
      }
    },
    motor: {
      keyboard_navigation_only: false,
      touch_target_size: 44,
      gesture_timeout: 1000,
      sticky_keys: false
    },
    cognitive: {
      simplified_interface: false,
      reduce_cognitive_load: false,
      focus_indicators: true,
      reading_guide: false
    },
    metadata: {
      version: '1.2.0',
      lastModified: '2023-12-15T10:30:00Z'
    }
  };

  const mockUnsubscribe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    accessibilityService.getAccessibilityPreferences.mockReturnValue(defaultAccessibilityPreferences);
    accessibilityService.subscribe.mockReturnValue(mockUnsubscribe);
    accessibilityService.getScreenReaderSupport.mockReturnValue({
      available: true,
      active: false,
      name: 'NVDA'
    });
  });

  describe('Component Rendering', () => {
    test('renders accessibility options component', () => {
      render(<AccessibilityOptions />);
      
      expect(screen.getByText('Accessibility Options')).toBeInTheDocument();
      expect(screen.getByText('Vision')).toBeInTheDocument();
      expect(screen.getByText('Motor')).toBeInTheDocument();
      expect(screen.getByText('Cognitive')).toBeInTheDocument();
    });

    test('displays vision accessibility options', () => {
      render(<AccessibilityOptions />);
      
      expect(screen.getByLabelText(/High Contrast/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Font Size Scale/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Reduce Motion/i)).toBeInTheDocument();
    });

    test('displays motor accessibility options', () => {
      render(<AccessibilityOptions />);
      
      expect(screen.getByLabelText(/Keyboard Navigation Only/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Touch Target Size/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Sticky Keys/i)).toBeInTheDocument();
    });

    test('displays cognitive accessibility options', () => {
      render(<AccessibilityOptions />);
      
      expect(screen.getByLabelText(/Simplified Interface/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Reduce Cognitive Load/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Focus Indicators/i)).toBeInTheDocument();
    });
  });

  describe('Vision Accessibility', () => {
    test('toggles high contrast mode', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);

      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          vision: expect.objectContaining({
            high_contrast: true
          })
        })
      );
      expect(accessibilityService.setHighContrast).toHaveBeenCalledWith(true);
    });

    test('adjusts font size scale', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const fontSizeSlider = screen.getByLabelText(/Font Size Scale/i);
      fireEvent.change(fontSizeSlider, { target: { value: '1.5' } });

      await waitFor(() => {
        expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
          expect.objectContaining({
            vision: expect.objectContaining({
              font_size_scale: 1.5
            })
          })
        );
        expect(accessibilityService.setFontScale).toHaveBeenCalledWith(1.5);
      });
    });

    test('toggles reduced motion', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const reducedMotionToggle = screen.getByLabelText(/Reduce Motion/i);
      await user.click(reducedMotionToggle);

      expect(accessibilityService.setReducedMotion).toHaveBeenCalledWith(true);
    });

    test('adjusts color settings', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const brightnessSlider = screen.getByLabelText(/Brightness/i);
      fireEvent.change(brightnessSlider, { target: { value: '1.2' } });

      await waitFor(() => {
        expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
          expect.objectContaining({
            vision: expect.objectContaining({
              color_adjustments: expect.objectContaining({
                brightness: 1.2
              })
            })
          })
        );
      });
    });

    test('shows preview of vision changes', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);

      expect(screen.getByTestId('vision-preview')).toHaveClass('high-contrast');
    });
  });

  describe('Motor Accessibility', () => {
    test('enables keyboard navigation only', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const keyboardOnlyToggle = screen.getByLabelText(/Keyboard Navigation Only/i);
      await user.click(keyboardOnlyToggle);

      expect(accessibilityService.enableKeyboardNavigation).toHaveBeenCalledWith(true);
    });

    test('adjusts touch target size', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const touchTargetSlider = screen.getByLabelText(/Touch Target Size/i);
      fireEvent.change(touchTargetSlider, { target: { value: '48' } });

      await waitFor(() => {
        expect(accessibilityService.adjustTouchTargets).toHaveBeenCalledWith(48);
      });
    });

    test('configures gesture timeout', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const timeoutSlider = screen.getByLabelText(/Gesture Timeout/i);
      fireEvent.change(timeoutSlider, { target: { value: '2000' } });

      await waitFor(() => {
        expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
          expect.objectContaining({
            motor: expect.objectContaining({
              gesture_timeout: 2000
            })
          })
        );
      });
    });

    test('enables sticky keys', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const stickyKeysToggle = screen.getByLabelText(/Sticky Keys/i);
      await user.click(stickyKeysToggle);

      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          motor: expect.objectContaining({
            sticky_keys: true
          })
        })
      );
    });
  });

  describe('Cognitive Accessibility', () => {
    test('enables simplified interface', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const simplifiedToggle = screen.getByLabelText(/Simplified Interface/i);
      await user.click(simplifiedToggle);

      expect(accessibilityService.enableSimplifiedInterface).toHaveBeenCalledWith(true);
    });

    test('reduces cognitive load', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const cognitiveLoadToggle = screen.getByLabelText(/Reduce Cognitive Load/i);
      await user.click(cognitiveLoadToggle);

      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          cognitive: expect.objectContaining({
            reduce_cognitive_load: true
          })
        })
      );
    });

    test('toggles focus indicators', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const focusIndicatorsToggle = screen.getByLabelText(/Focus Indicators/i);
      await user.click(focusIndicatorsToggle);

      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          cognitive: expect.objectContaining({
            focus_indicators: false
          })
        })
      );
    });

    test('enables reading guide', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const readingGuideToggle = screen.getByLabelText(/Reading Guide/i);
      await user.click(readingGuideToggle);

      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          cognitive: expect.objectContaining({
            reading_guide: true
          })
        })
      );
    });
  });

  describe('Screen Reader Support', () => {
    test('detects screen reader availability', () => {
      render(<AccessibilityOptions />);
      
      expect(accessibilityService.getScreenReaderSupport).toHaveBeenCalled();
      expect(screen.getByText(/Screen reader detected/i)).toBeInTheDocument();
    });

    test('announces changes to screen reader', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);

      expect(accessibilityService.announceToScreenReader).toHaveBeenCalledWith(
        'High contrast mode enabled'
      );
    });

    test('provides screen reader instructions', () => {
      render(<AccessibilityOptions />);
      
      expect(screen.getByText(/Use Tab to navigate between options/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility Testing', () => {
    test('tests accessibility settings', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const testButton = screen.getByText(/Test Accessibility/i);
      await user.click(testButton);

      expect(accessibilityService.applyAccessibilitySettings).toHaveBeenCalled();
    });

    test('resets to defaults', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const resetButton = screen.getByText(/Reset to Defaults/i);
      await user.click(resetButton);

      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          vision: expect.objectContaining({
            high_contrast: false,
            font_size_scale: 1.0,
            reduce_motion: false
          })
        })
      );
    });

    test('validates accessibility compliance', async () => {
      render(<AccessibilityOptions />);
      
      // Check for proper ARIA labels
      expect(screen.getByRole('group', { name: /Vision/i })).toBeInTheDocument();
      expect(screen.getByRole('group', { name: /Motor/i })).toBeInTheDocument();
      expect(screen.getByRole('group', { name: /Cognitive/i })).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('handles service errors gracefully', async () => {
      const user = userEvent.setup();
      accessibilityService.updateAccessibilityPreferences.mockRejectedValue(new Error('Save failed'));

      render(<AccessibilityOptions />);

      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);

      await waitFor(() => {
        expect(screen.getByText(/Failed to save accessibility preferences/i)).toBeInTheDocument();
      });
    });

    test('shows loading state during operations', async () => {
      const user = userEvent.setup();
      accessibilityService.updateAccessibilityPreferences.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(<AccessibilityOptions />);

      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });
  });

  describe('Integration', () => {
    test('subscribes to accessibility service updates', () => {
      render(<AccessibilityOptions />);
      expect(accessibilityService.subscribe).toHaveBeenCalled();
    });

    test('unsubscribes on component unmount', () => {
      const { unmount } = render(<AccessibilityOptions />);
      unmount();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });

    test('applies settings immediately', async () => {
      const user = userEvent.setup();
      render(<AccessibilityOptions />);

      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);

      expect(accessibilityService.applyAccessibilitySettings).toHaveBeenCalled();
    });
  });
});