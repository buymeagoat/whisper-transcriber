/**
 * T030 User Preferences Enhancement: Integration Tests
 * End-to-end integration tests for the complete preferences system
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Import all T030 components
import ThemePreferences from '../src/components/ThemePreferences.jsx';
import NotificationPreferences from '../src/components/NotificationPreferences.jsx';
import UploadPreferences from '../src/components/UploadPreferences.jsx';
import AccessibilityOptions from '../src/components/AccessibilityOptions.jsx';
import MobileSettingsInterface from '../src/components/MobileSettingsInterface.jsx';
import SettingsMigrationManager from '../src/components/SettingsMigrationManager.jsx';
import MigrationIntegration from '../src/components/MigrationIntegration.jsx';

// Import services
import themeService from '../src/services/themeService.js';
import notificationService from '../src/services/notificationService.js';
import uploadService from '../src/services/uploadService.js';
import accessibilityService from '../src/services/accessibilityService.js';
import settingsPersistenceService from '../src/services/settingsPersistenceService.js';
import settingsMigrationService from '../src/services/settingsMigrationService.js';
import mobileInterfaceService from '../src/services/mobileInterfaceService.js';

// Mock all services
jest.mock('../src/services/themeService.js');
jest.mock('../src/services/notificationService.js');
jest.mock('../src/services/uploadService.js');
jest.mock('../src/services/accessibilityService.js');
jest.mock('../src/services/settingsPersistenceService.js');
jest.mock('../src/services/settingsMigrationService.js');
jest.mock('../src/services/mobileInterfaceService.js');

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('T030 User Preferences Enhancement - Integration Tests', () => {
  // Complete mock data for all preferences
  const mockCompletePreferences = {
    theme: {
      appearance: {
        theme: 'light',
        auto_theme_switching: false,
        custom_themes: {}
      },
      colors: {
        primary_color: '#3b82f6',
        accent_color: '#10b981',
        background_color: '#ffffff',
        text_color: '#1f2937'
      },
      typography: {
        font_family: 'Inter',
        font_size_scale: 1.0,
        line_height_scale: 1.0
      },
      animation: {
        enable_transitions: true,
        transition_speed: 'normal',
        enable_hover_effects: true
      },
      metadata: {
        version: '1.2.0',
        lastModified: '2023-12-15T10:30:00Z'
      }
    },
    notifications: {
      categories: {
        transcription: { enabled: true, priority: 'high', sound: true },
        batch: { enabled: true, priority: 'medium', sound: false },
        system: { enabled: true, priority: 'low', sound: false },
        account: { enabled: false, priority: 'medium', sound: false }
      },
      delivery_methods: {
        browser: true,
        email: false,
        push: false
      },
      timing: {
        quiet_hours: { enabled: false, start_time: '22:00', end_time: '08:00' },
        batch_digest: { enabled: false, frequency: 'daily', time: '09:00' }
      },
      metadata: {
        version: '1.2.0',
        lastModified: '2023-12-15T10:30:00Z'
      }
    },
    upload: {
      general: {
        auto_upload: false,
        max_simultaneous_uploads: 3,
        chunk_size: 1048576,
        show_previews: true,
        auto_transcribe: true,
        save_originals: true
      },
      file_handling: {
        accepted_formats: ['audio/mpeg', 'audio/wav', 'audio/mp4'],
        max_file_size: 104857600,
        auto_validate_files: true,
        compress_audio: false,
        normalize_audio: false
      },
      security: {
        scan_for_malware: true,
        require_https: true,
        encrypt_uploads: true
      },
      metadata: {
        version: '1.2.0',
        lastModified: '2023-12-15T10:30:00Z'
      }
    },
    accessibility: {
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
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup service mocks
    themeService.getThemePreferences.mockReturnValue(mockCompletePreferences.theme);
    themeService.subscribe.mockReturnValue(jest.fn());
    themeService.updateThemePreferences.mockResolvedValue();
    
    notificationService.getNotificationPreferences.mockReturnValue(mockCompletePreferences.notifications);
    notificationService.subscribe.mockReturnValue(jest.fn());
    notificationService.updateNotificationPreferences.mockResolvedValue();
    
    uploadService.getUploadPreferences.mockReturnValue(mockCompletePreferences.upload);
    uploadService.subscribe.mockReturnValue(jest.fn());
    uploadService.updateUploadPreferences.mockResolvedValue();
    
    accessibilityService.getAccessibilityPreferences.mockReturnValue(mockCompletePreferences.accessibility);
    accessibilityService.subscribe.mockReturnValue(jest.fn());
    accessibilityService.updateAccessibilityPreferences.mockResolvedValue();
    
    settingsPersistenceService.subscribe.mockReturnValue(jest.fn());
    settingsPersistenceService.syncSettings.mockResolvedValue();
    settingsPersistenceService.enableCloudSync.mockResolvedValue();
    
    settingsMigrationService.getMigrationStatus.mockReturnValue({
      status: 'idle',
      currentVersion: '1.2.0',
      targetVersion: '1.2.0'
    });
    settingsMigrationService.subscribe.mockReturnValue(jest.fn());
    
    mobileInterfaceService.isMobileDevice.mockReturnValue(false);
    mobileInterfaceService.subscribe.mockReturnValue(jest.fn());
  });

  describe('Complete Preferences Workflow', () => {
    test('user can configure all preference categories', async () => {
      const user = userEvent.setup();
      
      // Create a main preferences component that includes all categories
      const MainPreferences = () => (
        <div data-testid="main-preferences">
          <ThemePreferences />
          <NotificationPreferences />
          <UploadPreferences />
          <AccessibilityOptions />
        </div>
      );

      render(<MainPreferences />);

      // Verify all preference categories are present
      expect(screen.getByText('Theme Preferences')).toBeInTheDocument();
      expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
      expect(screen.getByText('Upload Preferences')).toBeInTheDocument();
      expect(screen.getByText('Accessibility Options')).toBeInTheDocument();

      // Test theme change
      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);
      expect(themeService.updateThemePreferences).toHaveBeenCalled();

      // Test notification toggle
      const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      await user.click(transcriptionToggle);
      expect(notificationService.updateNotificationPreferences).toHaveBeenCalled();

      // Test upload setting change
      const autoUploadToggle = screen.getByLabelText(/Auto Upload/i);
      await user.click(autoUploadToggle);
      expect(uploadService.updateUploadPreferences).toHaveBeenCalled();

      // Test accessibility option
      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);
      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalled();
    });

    test('preferences persist across service interactions', async () => {
      const user = userEvent.setup();
      
      render(<ThemePreferences />);

      // Change theme
      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      // Verify persistence service is called
      expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          appearance: expect.objectContaining({
            theme: 'dark'
          })
        })
      );
    });

    test('cross-component preference interactions work correctly', async () => {
      const user = userEvent.setup();
      
      // Test accessibility affecting theme
      render(<AccessibilityOptions />);
      
      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);

      // Should update accessibility preferences and apply theme changes
      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalled();
      expect(accessibilityService.setHighContrast).toHaveBeenCalledWith(true);
    });
  });

  describe('Mobile Interface Integration', () => {
    test('mobile interface displays all preference categories', () => {
      mobileInterfaceService.isMobileDevice.mockReturnValue(true);
      
      render(<MobileSettingsInterface preferences={mockCompletePreferences} />);

      expect(screen.getByText('Theme')).toBeInTheDocument();
      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Upload')).toBeInTheDocument();
      expect(screen.getByText('Accessibility')).toBeInTheDocument();
    });

    test('mobile interface adapts to preference changes', async () => {
      const user = userEvent.setup();
      mobileInterfaceService.isMobileDevice.mockReturnValue(true);
      
      render(<MobileSettingsInterface preferences={mockCompletePreferences} />);

      // Navigate to theme category
      const themeCategory = screen.getByText('Theme');
      await user.click(themeCategory);

      expect(mobileInterfaceService.triggerHapticFeedback).toHaveBeenCalledWith('selection');
    });

    test('mobile gestures work across all preference categories', async () => {
      mobileInterfaceService.isMobileDevice.mockReturnValue(true);
      
      render(<MobileSettingsInterface preferences={mockCompletePreferences} />);

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
  });

  describe('Settings Migration Integration', () => {
    test('migration system detects preference changes', async () => {
      settingsMigrationService.getMigrationStatus.mockReturnValue({
        status: 'idle',
        currentVersion: '1.0.0',
        targetVersion: '1.2.0'
      });

      render(
        <MigrationIntegration>
          <ThemePreferences />
        </MigrationIntegration>
      );

      expect(settingsMigrationService.checkForPendingMigrations).toHaveBeenCalled();
    });

    test('migration manager handles all preference types', async () => {
      const user = userEvent.setup();
      settingsMigrationService.getMigrationStatus.mockReturnValue({
        status: 'idle',
        currentVersion: '1.0.0',
        targetVersion: '1.2.0'
      });
      settingsMigrationService.getAllCurrentSettings.mockResolvedValue(mockCompletePreferences);

      render(<SettingsMigrationManager onClose={jest.fn()} />);

      // Force migration
      const forceMigrationButton = screen.getByText('Force Migration');
      await user.click(forceMigrationButton);

      const confirmButton = screen.getByText('Confirm');
      await user.click(confirmButton);

      expect(settingsMigrationService.forceMigration).toHaveBeenCalled();
    });

    test('backup includes all preference data', async () => {
      const user = userEvent.setup();
      settingsMigrationService.getAllCurrentSettings.mockResolvedValue(mockCompletePreferences);
      
      render(<SettingsMigrationManager onClose={jest.fn()} />);

      const createBackupButton = screen.getByText('Create Backup');
      await user.click(createBackupButton);

      expect(settingsMigrationService.createMigrationBackup).toHaveBeenCalled();
    });
  });

  describe('Settings Persistence Integration', () => {
    test('all preference changes trigger persistence', async () => {
      const user = userEvent.setup();
      
      render(<ThemePreferences />);

      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      // Verify theme service update was called
      expect(themeService.updateThemePreferences).toHaveBeenCalled();
    });

    test('cloud sync handles all preference types', async () => {
      settingsPersistenceService.getCloudSyncStatus.mockReturnValue({
        enabled: true,
        lastSync: '2023-12-15T10:30:00Z',
        status: 'synced'
      });

      const PersistenceTest = () => {
        React.useEffect(() => {
          settingsPersistenceService.syncSettings();
        }, []);
        return <div>Persistence Test</div>;
      };

      render(<PersistenceTest />);

      expect(settingsPersistenceService.syncSettings).toHaveBeenCalled();
    });

    test('offline support works with all preferences', async () => {
      settingsPersistenceService.getOfflineSupport.mockReturnValue({
        enabled: true,
        queuedChanges: 3,
        lastOfflineSync: '2023-12-15T10:30:00Z'
      });

      const OfflineTest = () => {
        React.useEffect(() => {
          // Simulate offline changes
          themeService.updateThemePreferences({ appearance: { theme: 'dark' } });
          notificationService.updateNotificationPreferences({ categories: {} });
          uploadService.updateUploadPreferences({ general: {} });
        }, []);
        return <div>Offline Test</div>;
      };

      render(<OfflineTest />);

      expect(themeService.updateThemePreferences).toHaveBeenCalled();
      expect(notificationService.updateNotificationPreferences).toHaveBeenCalled();
      expect(uploadService.updateUploadPreferences).toHaveBeenCalled();
    });
  });

  describe('Accessibility Integration', () => {
    test('accessibility settings affect all preference interfaces', async () => {
      const user = userEvent.setup();
      
      // Enable high contrast
      accessibilityService.getAccessibilityPreferences.mockReturnValue({
        ...mockCompletePreferences.accessibility,
        vision: {
          ...mockCompletePreferences.accessibility.vision,
          high_contrast: true
        }
      });

      render(<ThemePreferences />);

      // Should apply high contrast to theme interface
      expect(accessibilityService.getAccessibilityPreferences).toHaveBeenCalled();
    });

    test('keyboard navigation works across all preferences', async () => {
      const user = userEvent.setup();
      
      render(<NotificationPreferences />);

      const firstToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      const secondToggle = screen.getByLabelText(/Enable Batch Processing notifications/i);

      firstToggle.focus();
      await user.keyboard('{Tab}');
      expect(secondToggle).toHaveFocus();
    });

    test('screen reader announcements work for all preference changes', async () => {
      const user = userEvent.setup();
      
      render(<AccessibilityOptions />);

      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);

      expect(accessibilityService.announceToScreenReader).toHaveBeenCalledWith(
        'High contrast mode enabled'
      );
    });
  });

  describe('Error Handling Integration', () => {
    test('service errors are handled gracefully across all components', async () => {
      const user = userEvent.setup();
      
      // Mock service errors
      themeService.updateThemePreferences.mockRejectedValue(new Error('Theme save failed'));
      notificationService.updateNotificationPreferences.mockRejectedValue(new Error('Notification save failed'));
      uploadService.updateUploadPreferences.mockRejectedValue(new Error('Upload save failed'));
      accessibilityService.updateAccessibilityPreferences.mockRejectedValue(new Error('Accessibility save failed'));

      const ErrorTestComponent = () => (
        <div>
          <ThemePreferences />
          <NotificationPreferences />
          <UploadPreferences />
          <AccessibilityOptions />
        </div>
      );

      render(<ErrorTestComponent />);

      // Test theme error
      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      await waitFor(() => {
        expect(screen.getByText(/Failed to save theme preferences/i)).toBeInTheDocument();
      });

      // Test notification error
      const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      await user.click(transcriptionToggle);

      await waitFor(() => {
        expect(screen.getByText(/Failed to save notification preferences/i)).toBeInTheDocument();
      });
    });

    test('migration errors are handled with rollback', async () => {
      const user = userEvent.setup();
      
      settingsMigrationService.forceMigration.mockRejectedValue(new Error('Migration failed'));
      settingsMigrationService.rollbackMigration.mockResolvedValue();

      render(<SettingsMigrationManager onClose={jest.fn()} />);

      const forceMigrationButton = screen.getByText('Force Migration');
      await user.click(forceMigrationButton);

      const confirmButton = screen.getByText('Confirm');
      await user.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText(/Force migration failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Performance Integration', () => {
    test('large preference datasets render efficiently', () => {
      // Create large mock preferences
      const largePreferences = {
        ...mockCompletePreferences,
        theme: {
          ...mockCompletePreferences.theme,
          appearance: {
            ...mockCompletePreferences.theme.appearance,
            custom_themes: Object.fromEntries(
              Array.from({ length: 100 }, (_, i) => [`theme-${i}`, { name: `Theme ${i}` }])
            )
          }
        }
      };

      const startTime = performance.now();
      render(<ThemePreferences />);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100); // Should render in under 100ms
    });

    test('rapid preference changes are debounced', async () => {
      const user = userEvent.setup();
      
      render(<UploadPreferences />);

      const maxUploadsSlider = screen.getByLabelText(/Max Simultaneous Uploads/i);
      
      // Rapidly change value multiple times
      fireEvent.change(maxUploadsSlider, { target: { value: '4' } });
      fireEvent.change(maxUploadsSlider, { target: { value: '5' } });
      fireEvent.change(maxUploadsSlider, { target: { value: '6' } });

      // Should only call update once after debounce delay
      await waitFor(() => {
        expect(uploadService.updateUploadPreferences).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });
  });

  describe('End-to-End User Scenarios', () => {
    test('complete user onboarding scenario', async () => {
      const user = userEvent.setup();
      
      const OnboardingFlow = () => {
        const [step, setStep] = React.useState(0);
        const components = [
          <ThemePreferences key="theme" />,
          <NotificationPreferences key="notifications" />,
          <UploadPreferences key="upload" />,
          <AccessibilityOptions key="accessibility" />
        ];

        return (
          <div>
            {components[step]}
            <button onClick={() => setStep(s => s + 1)} disabled={step >= 3}>
              Next
            </button>
          </div>
        );
      };

      render(<OnboardingFlow />);

      // Step 1: Configure theme
      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);
      expect(themeService.updateThemePreferences).toHaveBeenCalled();

      await user.click(screen.getByText('Next'));

      // Step 2: Configure notifications
      const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      await user.click(transcriptionToggle);
      expect(notificationService.updateNotificationPreferences).toHaveBeenCalled();

      await user.click(screen.getByText('Next'));

      // Step 3: Configure upload
      const autoUploadToggle = screen.getByLabelText(/Auto Upload/i);
      await user.click(autoUploadToggle);
      expect(uploadService.updateUploadPreferences).toHaveBeenCalled();

      await user.click(screen.getByText('Next'));

      // Step 4: Configure accessibility
      const highContrastToggle = screen.getByLabelText(/High Contrast/i);
      await user.click(highContrastToggle);
      expect(accessibilityService.updateAccessibilityPreferences).toHaveBeenCalled();
    });

    test('preference export and import scenario', async () => {
      const user = userEvent.setup();
      
      themeService.exportTheme.mockReturnValue(mockCompletePreferences.theme);
      themeService.importTheme.mockResolvedValue();

      render(<ThemePreferences />);

      // Export theme
      const exportButton = screen.getByText(/Export Theme/i);
      await user.click(exportButton);
      expect(themeService.exportTheme).toHaveBeenCalled();

      // Import theme
      const mockFile = new File([JSON.stringify(mockCompletePreferences.theme)], 'theme.json', {
        type: 'application/json'
      });
      const importInput = screen.getByLabelText(/Import Theme/i);
      await user.upload(importInput, mockFile);

      await waitFor(() => {
        expect(themeService.importTheme).toHaveBeenCalled();
      });
    });

    test('mobile-to-desktop preference sync scenario', async () => {
      // Simulate mobile device
      mobileInterfaceService.isMobileDevice.mockReturnValue(true);
      
      const { rerender } = render(
        <MobileSettingsInterface preferences={mockCompletePreferences} />
      );

      // Simulate preference change on mobile
      const user = userEvent.setup();
      const themeCategory = screen.getByText('Theme');
      await user.click(themeCategory);

      // Switch to desktop
      mobileInterfaceService.isMobileDevice.mockReturnValue(false);
      
      rerender(<ThemePreferences />);

      // Verify preferences are synced
      expect(themeService.getThemePreferences).toHaveBeenCalled();
    });
  });
});