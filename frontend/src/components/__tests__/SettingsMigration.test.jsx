/**
 * T030 User Preferences Enhancement: Settings Migration System Tests
 * Comprehensive test suite for settingsMigrationService.js and SettingsMigrationManager.jsx
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import SettingsMigrationManager from '../src/components/SettingsMigrationManager.jsx';
import settingsMigrationService from '../src/services/settingsMigrationService.js';

// Mock the migration service
jest.mock('../src/services/settingsMigrationService.js', () => ({
  getMigrationStatus: jest.fn(),
  getMigrationHistory: jest.fn(),
  getAvailableBackups: jest.fn(),
  subscribe: jest.fn(),
  forceMigration: jest.fn(),
  createMigrationBackup: jest.fn(),
  restoreFromBackup: jest.fn(),
  setAutoMigrate: jest.fn(),
  checkForPendingMigrations: jest.fn(),
  getCurrentSettingsVersion: jest.fn(),
  compareVersions: jest.fn(),
  isUpgradeNeeded: jest.fn(),
  findMigrationPath: jest.fn(),
  executeMigrationPath: jest.fn(),
  validateMigratedSettings: jest.fn(),
  getAllCurrentSettings: jest.fn(),
  applyMigratedSettings: jest.fn(),
  updateSettingsVersion: jest.fn(),
  rollbackMigration: jest.fn()
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

describe('Settings Migration System', () => {
  const mockMigrationStatus = {
    status: 'idle',
    currentVersion: '1.0.0',
    targetVersion: '1.2.0',
    lastMigration: {
      timestamp: '2023-12-15T10:30:00Z',
      fromVersion: '1.0.0',
      toVersion: '1.1.0',
      steps: 2
    },
    historyCount: 3,
    autoMigrate: true
  };

  const mockMigrationHistory = [
    {
      timestamp: '2023-12-15T10:30:00Z',
      fromVersion: '1.0.0',
      toVersion: '1.1.0',
      status: 'completed'
    },
    {
      timestamp: '2023-12-10T14:15:00Z',
      fromVersion: '0.9.0',
      toVersion: '1.0.0',
      status: 'completed'
    },
    {
      timestamp: '2023-12-08T09:45:00Z',
      fromVersion: '0.8.0',
      toVersion: '0.9.0',
      status: 'failed',
      error: 'Network timeout'
    }
  ];

  const mockAvailableBackups = [
    {
      key: 'backup-20231215-103000.json',
      timestamp: '2023-12-15T10:30:00Z',
      version: '1.0.0',
      size: 15432,
      created: '2023-12-15T10:30:00Z'
    },
    {
      key: 'backup-20231210-141500.json',
      timestamp: '2023-12-10T14:15:00Z',
      version: '0.9.0',
      size: 12876,
      created: '2023-12-10T14:15:00Z'
    }
  ];

  const mockUnsubscribe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    settingsMigrationService.getMigrationStatus.mockReturnValue(mockMigrationStatus);
    settingsMigrationService.getMigrationHistory.mockReturnValue(mockMigrationHistory);
    settingsMigrationService.getAvailableBackups.mockReturnValue(mockAvailableBackups);
    settingsMigrationService.subscribe.mockReturnValue(mockUnsubscribe);
    settingsMigrationService.getCurrentSettingsVersion.mockReturnValue('1.0.0');
    settingsMigrationService.compareVersions.mockImplementation((v1, v2) => {
      // Simple version comparison for testing
      return v1.localeCompare(v2, undefined, { numeric: true, sensitivity: 'base' });
    });
    settingsMigrationService.isUpgradeNeeded.mockReturnValue(true);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('SettingsMigrationManager Component', () => {
    const mockOnClose = jest.fn();

    beforeEach(() => {
      mockOnClose.mockClear();
    });

    describe('Component Rendering', () => {
      test('renders migration manager component', () => {
        render(<SettingsMigrationManager onClose={mockOnClose} />);
        
        expect(screen.getByText('Settings Migration Manager')).toBeInTheDocument();
        expect(screen.getByText('Status')).toBeInTheDocument();
        expect(screen.getByText('History (3)')).toBeInTheDocument();
        expect(screen.getByText('Backups (2)')).toBeInTheDocument();
      });

      test('displays migration status information', () => {
        render(<SettingsMigrationManager onClose={mockOnClose} />);
        
        expect(screen.getByText('1.0.0')).toBeInTheDocument(); // Current version
        expect(screen.getByText('1.2.0')).toBeInTheDocument(); // Target version
        expect(screen.getByText('idle')).toBeInTheDocument(); // Status
        expect(screen.getByText('Enabled')).toBeInTheDocument(); // Auto-migration
      });

      test('displays last migration information', () => {
        render(<SettingsMigrationManager onClose={mockOnClose} />);
        
        expect(screen.getByText('1.0.0 → 1.1.0')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument(); // Steps
      });

      test('shows force migration button when upgrade needed', () => {
        render(<SettingsMigrationManager onClose={mockOnClose} />);
        
        expect(screen.getByText('Force Migration')).toBeInTheDocument();
      });

      test('hides force migration button when no upgrade needed', () => {
        settingsMigrationService.getMigrationStatus.mockReturnValue({
          ...mockMigrationStatus,
          currentVersion: '1.2.0',
          targetVersion: '1.2.0'
        });

        render(<SettingsMigrationManager onClose={mockOnClose} />);
        
        expect(screen.queryByText('Force Migration')).not.toBeInTheDocument();
      });
    });

    describe('Tab Navigation', () => {
      test('switches between tabs', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const historyTab = screen.getByText('History (3)');
        await user.click(historyTab);

        expect(screen.getByText('Migration History')).toBeInTheDocument();

        const backupsTab = screen.getByText('Backups (2)');
        await user.click(backupsTab);

        expect(screen.getByText('Available Backups')).toBeInTheDocument();
      });

      test('displays correct content for each tab', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        // Status tab (default)
        expect(screen.getByText('Migration Status')).toBeInTheDocument();

        // History tab
        const historyTab = screen.getByText('History (3)');
        await user.click(historyTab);
        expect(screen.getByText('0.8.0 → 0.9.0')).toBeInTheDocument();
        expect(screen.getByText('failed')).toBeInTheDocument();

        // Backups tab
        const backupsTab = screen.getByText('Backups (2)');
        await user.click(backupsTab);
        expect(screen.getByText('Version 1.0.0')).toBeInTheDocument();
        expect(screen.getByText('15.1 KB')).toBeInTheDocument();
      });
    });

    describe('Migration Actions', () => {
      test('forces migration with confirmation', async () => {
        const user = userEvent.setup();
        settingsMigrationService.forceMigration.mockResolvedValue();
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const forceMigrationButton = screen.getByText('Force Migration');
        await user.click(forceMigrationButton);

        // Should show confirmation dialog
        expect(screen.getByText('Force Migration')).toBeInTheDocument();
        expect(screen.getByText(/This will migrate your settings from 1.0.0 to 1.2.0/)).toBeInTheDocument();

        const confirmButton = screen.getByText('Confirm');
        await user.click(confirmButton);

        expect(settingsMigrationService.forceMigration).toHaveBeenCalled();
      });

      test('cancels migration on dialog cancel', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const forceMigrationButton = screen.getByText('Force Migration');
        await user.click(forceMigrationButton);

        const cancelButton = screen.getByText('Cancel');
        await user.click(cancelButton);

        expect(settingsMigrationService.forceMigration).not.toHaveBeenCalled();
      });

      test('creates backup', async () => {
        const user = userEvent.setup();
        settingsMigrationService.createMigrationBackup.mockResolvedValue('backup-123.json');
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const createBackupButton = screen.getByText('Create Backup');
        await user.click(createBackupButton);

        expect(settingsMigrationService.createMigrationBackup).toHaveBeenCalled();
      });

      test('toggles auto-migration', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const toggleButton = screen.getByText('Disable Auto-Migration');
        await user.click(toggleButton);

        expect(settingsMigrationService.setAutoMigrate).toHaveBeenCalledWith(false);
      });

      test('refreshes migration data', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const refreshButton = screen.getByText('Refresh');
        await user.click(refreshButton);

        expect(settingsMigrationService.getMigrationStatus).toHaveBeenCalled();
        expect(settingsMigrationService.getMigrationHistory).toHaveBeenCalled();
        expect(settingsMigrationService.getAvailableBackups).toHaveBeenCalled();
      });
    });

    describe('Backup Management', () => {
      test('restores from backup with confirmation', async () => {
        const user = userEvent.setup();
        settingsMigrationService.restoreFromBackup.mockResolvedValue();
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        // Switch to backups tab
        const backupsTab = screen.getByText('Backups (2)');
        await user.click(backupsTab);

        const restoreButton = screen.getByText('Restore');
        await user.click(restoreButton);

        // Should show confirmation dialog
        expect(screen.getByText('Restore Backup')).toBeInTheDocument();
        expect(screen.getByText(/This will restore your settings to version 1.0.0/)).toBeInTheDocument();

        const confirmButton = screen.getByText('Confirm');
        await user.click(confirmButton);

        expect(settingsMigrationService.restoreFromBackup).toHaveBeenCalledWith('backup-20231215-103000.json');
      });

      test('displays backup information correctly', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const backupsTab = screen.getByText('Backups (2)');
        await user.click(backupsTab);

        expect(screen.getByText('Version 1.0.0')).toBeInTheDocument();
        expect(screen.getByText('Version 0.9.0')).toBeInTheDocument();
        expect(screen.getByText('15.1 KB')).toBeInTheDocument();
        expect(screen.getByText('12.6 KB')).toBeInTheDocument();
      });

      test('shows empty state when no backups available', async () => {
        const user = userEvent.setup();
        settingsMigrationService.getAvailableBackups.mockReturnValue([]);
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const backupsTab = screen.getByText('Backups (0)');
        await user.click(backupsTab);

        expect(screen.getByText('No backups available.')).toBeInTheDocument();
        expect(screen.getByText('Create First Backup')).toBeInTheDocument();
      });
    });

    describe('Migration History', () => {
      test('displays migration history correctly', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const historyTab = screen.getByText('History (3)');
        await user.click(historyTab);

        expect(screen.getByText('1.0.0 → 1.1.0')).toBeInTheDocument();
        expect(screen.getByText('0.9.0 → 1.0.0')).toBeInTheDocument();
        expect(screen.getByText('0.8.0 → 0.9.0')).toBeInTheDocument();
        expect(screen.getByText('Network timeout')).toBeInTheDocument();
      });

      test('shows empty state when no history available', async () => {
        const user = userEvent.setup();
        settingsMigrationService.getMigrationHistory.mockReturnValue([]);
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const historyTab = screen.getByText('History (0)');
        await user.click(historyTab);

        expect(screen.getByText('No migration history available.')).toBeInTheDocument();
      });

      test('displays migration status badges correctly', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const historyTab = screen.getByText('History (3)');
        await user.click(historyTab);

        const completedBadges = screen.getAllByText('✓ completed');
        const failedBadge = screen.getByText('✗ failed');

        expect(completedBadges).toHaveLength(2);
        expect(failedBadge).toBeInTheDocument();
      });
    });

    describe('Event Handling', () => {
      test('handles migration events', async () => {
        const mockCallback = jest.fn();
        settingsMigrationService.subscribe.mockImplementation(callback => {
          mockCallback.current = callback;
          return mockUnsubscribe;
        });

        render(<SettingsMigrationManager onClose={mockOnClose} />);

        // Simulate migration completed event
        act(() => {
          if (mockCallback.current) {
            mockCallback.current('migration-completed', {
              fromVersion: '1.0.0',
              toVersion: '1.2.0'
            });
          }
        });

        await waitFor(() => {
          expect(screen.getByText(/Migration completed successfully/)).toBeInTheDocument();
        });
      });

      test('handles migration failure events', async () => {
        const mockCallback = jest.fn();
        settingsMigrationService.subscribe.mockImplementation(callback => {
          mockCallback.current = callback;
          return mockUnsubscribe;
        });

        render(<SettingsMigrationManager onClose={mockOnClose} />);

        // Simulate migration failed event
        act(() => {
          if (mockCallback.current) {
            mockCallback.current('migration-failed', {
              error: 'Network timeout'
            });
          }
        });

        await waitFor(() => {
          expect(screen.getByText(/Migration failed: Network timeout/)).toBeInTheDocument();
        });
      });

      test('handles backup events', async () => {
        const mockCallback = jest.fn();
        settingsMigrationService.subscribe.mockImplementation(callback => {
          mockCallback.current = callback;
          return mockUnsubscribe;
        });

        render(<SettingsMigrationManager onClose={mockOnClose} />);

        // Simulate backup created event
        act(() => {
          if (mockCallback.current) {
            mockCallback.current('backup-created', {
              key: 'backup-new.json'
            });
          }
        });

        await waitFor(() => {
          expect(screen.getByText(/Backup created successfully/)).toBeInTheDocument();
        });
      });
    });

    describe('Loading States', () => {
      test('shows loading overlay during migration', async () => {
        const user = userEvent.setup();
        settingsMigrationService.forceMigration.mockImplementation(
          () => new Promise(resolve => setTimeout(resolve, 100))
        );
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const forceMigrationButton = screen.getByText('Force Migration');
        await user.click(forceMigrationButton);

        const confirmButton = screen.getByText('Confirm');
        await user.click(confirmButton);

        expect(screen.getByText('Processing migration...')).toBeInTheDocument();
        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      });

      test('disables buttons during loading', async () => {
        const user = userEvent.setup();
        settingsMigrationService.createMigrationBackup.mockImplementation(
          () => new Promise(resolve => setTimeout(resolve, 100))
        );
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const createBackupButton = screen.getByText('Create Backup');
        await user.click(createBackupButton);

        expect(createBackupButton).toBeDisabled();
        expect(screen.getByText('Force Migration')).toBeDisabled();
      });
    });

    describe('Error Handling', () => {
      test('displays error messages', async () => {
        const user = userEvent.setup();
        settingsMigrationService.forceMigration.mockRejectedValue(new Error('Migration failed'));
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const forceMigrationButton = screen.getByText('Force Migration');
        await user.click(forceMigrationButton);

        const confirmButton = screen.getByText('Confirm');
        await user.click(confirmButton);

        await waitFor(() => {
          expect(screen.getByText(/Force migration failed: Migration failed/)).toBeInTheDocument();
        });
      });

      test('handles backup errors', async () => {
        const user = userEvent.setup();
        settingsMigrationService.createMigrationBackup.mockRejectedValue(new Error('Backup failed'));
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const createBackupButton = screen.getByText('Create Backup');
        await user.click(createBackupButton);

        await waitFor(() => {
          expect(screen.getByText(/Failed to create backup: Backup failed/)).toBeInTheDocument();
        });
      });

      test('allows dismissing error messages', async () => {
        const user = userEvent.setup();
        settingsMigrationService.forceMigration.mockRejectedValue(new Error('Migration failed'));
        
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const forceMigrationButton = screen.getByText('Force Migration');
        await user.click(forceMigrationButton);

        const confirmButton = screen.getByText('Confirm');
        await user.click(confirmButton);

        await waitFor(() => {
          expect(screen.getByText(/Force migration failed/)).toBeInTheDocument();
        });

        const dismissButton = screen.getByLabelText('Close');
        await user.click(dismissButton);

        expect(screen.queryByText(/Force migration failed/)).not.toBeInTheDocument();
      });
    });

    describe('Component Lifecycle', () => {
      test('subscribes to migration service on mount', () => {
        render(<SettingsMigrationManager onClose={mockOnClose} />);
        expect(settingsMigrationService.subscribe).toHaveBeenCalled();
      });

      test('unsubscribes from migration service on unmount', () => {
        const { unmount } = render(<SettingsMigrationManager onClose={mockOnClose} />);
        unmount();
        expect(mockUnsubscribe).toHaveBeenCalled();
      });

      test('loads initial data on mount', () => {
        render(<SettingsMigrationManager onClose={mockOnClose} />);
        
        expect(settingsMigrationService.getMigrationStatus).toHaveBeenCalled();
        expect(settingsMigrationService.getMigrationHistory).toHaveBeenCalled();
        expect(settingsMigrationService.getAvailableBackups).toHaveBeenCalled();
      });

      test('closes component when close button clicked', async () => {
        const user = userEvent.setup();
        render(<SettingsMigrationManager onClose={mockOnClose} />);

        const closeButton = screen.getByLabelText('Close');
        await user.click(closeButton);

        expect(mockOnClose).toHaveBeenCalled();
      });
    });
  });

  describe('Settings Migration Service', () => {
    describe('Version Detection', () => {
      test('detects current settings version', () => {
        mockLocalStorage.getItem.mockImplementation(key => {
          if (key === 'whisper_theme_preferences') {
            return JSON.stringify({
              metadata: { version: '1.1.0' }
            });
          }
          return null;
        });

        const version = settingsMigrationService.getCurrentSettingsVersion();
        expect(version).toBe('1.1.0');
      });

      test('falls back to default version when none found', () => {
        mockLocalStorage.getItem.mockReturnValue(null);
        
        const version = settingsMigrationService.getCurrentSettingsVersion();
        expect(version).toBe('0.9.0');
      });

      test('compares versions correctly', () => {
        expect(settingsMigrationService.compareVersions('1.0.0', '1.1.0')).toBe(-1);
        expect(settingsMigrationService.compareVersions('1.1.0', '1.0.0')).toBe(1);
        expect(settingsMigrationService.compareVersions('1.0.0', '1.0.0')).toBe(0);
      });

      test('determines if upgrade is needed', () => {
        expect(settingsMigrationService.isUpgradeNeeded('1.0.0', '1.2.0')).toBe(true);
        expect(settingsMigrationService.isUpgradeNeeded('1.2.0', '1.2.0')).toBe(false);
        expect(settingsMigrationService.isUpgradeNeeded('1.3.0', '1.2.0')).toBe(false);
      });
    });

    describe('Migration Path Planning', () => {
      test('finds migration path between versions', () => {
        const mockPath = [
          { fromVersion: '1.0.0', toVersion: '1.1.0' },
          { fromVersion: '1.1.0', toVersion: '1.2.0' }
        ];

        settingsMigrationService.findMigrationPath.mockReturnValue(mockPath);
        
        const path = settingsMigrationService.findMigrationPath('1.0.0', '1.2.0');
        expect(path).toEqual(mockPath);
        expect(path).toHaveLength(2);
      });

      test('returns empty path when no migration needed', () => {
        settingsMigrationService.findMigrationPath.mockReturnValue([]);
        
        const path = settingsMigrationService.findMigrationPath('1.2.0', '1.2.0');
        expect(path).toEqual([]);
      });
    });

    describe('Migration Execution', () => {
      test('executes migration path successfully', async () => {
        const mockPath = [
          { fromVersion: '1.0.0', toVersion: '1.1.0' },
          { fromVersion: '1.1.0', toVersion: '1.2.0' }
        ];

        settingsMigrationService.executeMigrationPath.mockResolvedValue();
        
        await settingsMigrationService.executeMigrationPath(mockPath);
        expect(settingsMigrationService.executeMigrationPath).toHaveBeenCalledWith(mockPath);
      });

      test('handles migration failure with rollback', async () => {
        settingsMigrationService.executeMigrationPath.mockRejectedValue(new Error('Migration failed'));
        settingsMigrationService.rollbackMigration.mockResolvedValue();
        
        try {
          await settingsMigrationService.executeMigrationPath([]);
          fail('Should have thrown error');
        } catch (error) {
          expect(error.message).toBe('Migration failed');
        }
      });
    });

    describe('Backup Management', () => {
      test('creates migration backup', async () => {
        settingsMigrationService.createMigrationBackup.mockResolvedValue('backup-123.json');
        
        const backupKey = await settingsMigrationService.createMigrationBackup();
        expect(backupKey).toBe('backup-123.json');
      });

      test('restores from backup', async () => {
        settingsMigrationService.restoreFromBackup.mockResolvedValue();
        
        await settingsMigrationService.restoreFromBackup('backup-123.json');
        expect(settingsMigrationService.restoreFromBackup).toHaveBeenCalledWith('backup-123.json');
      });

      test('gets available backups', () => {
        settingsMigrationService.getAvailableBackups.mockReturnValue(mockAvailableBackups);
        
        const backups = settingsMigrationService.getAvailableBackups();
        expect(backups).toEqual(mockAvailableBackups);
        expect(backups).toHaveLength(2);
      });
    });

    describe('Settings Validation', () => {
      test('validates migrated settings', async () => {
        const mockValidation = {
          valid: true,
          errors: [],
          version: '1.2.0'
        };

        settingsMigrationService.validateMigratedSettings.mockResolvedValue(mockValidation);
        
        const result = await settingsMigrationService.validateMigratedSettings();
        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      test('reports validation errors', async () => {
        const mockValidation = {
          valid: false,
          errors: ['Theme settings missing', 'Invalid color format'],
          version: '1.2.0'
        };

        settingsMigrationService.validateMigratedSettings.mockResolvedValue(mockValidation);
        
        const result = await settingsMigrationService.validateMigratedSettings();
        expect(result.valid).toBe(false);
        expect(result.errors).toHaveLength(2);
      });
    });

    describe('Event System', () => {
      test('subscribes to migration events', () => {
        const callback = jest.fn();
        settingsMigrationService.subscribe.mockReturnValue(mockUnsubscribe);
        
        const unsubscribe = settingsMigrationService.subscribe(callback);
        expect(typeof unsubscribe).toBe('function');
      });

      test('unsubscribes from migration events', () => {
        const callback = jest.fn();
        const unsubscribe = settingsMigrationService.subscribe(callback);
        
        unsubscribe();
        expect(mockUnsubscribe).toHaveBeenCalled();
      });
    });

    describe('Settings Management', () => {
      test('gets all current settings', async () => {
        const mockSettings = {
          theme: { appearance: { theme: 'light' } },
          notifications: { categories: {} },
          upload: { general: {} }
        };

        settingsMigrationService.getAllCurrentSettings.mockResolvedValue(mockSettings);
        
        const settings = await settingsMigrationService.getAllCurrentSettings();
        expect(settings).toEqual(mockSettings);
      });

      test('applies migrated settings', async () => {
        const mockSettings = {
          theme: { appearance: { theme: 'dark' } }
        };

        settingsMigrationService.applyMigratedSettings.mockResolvedValue();
        
        await settingsMigrationService.applyMigratedSettings(mockSettings);
        expect(settingsMigrationService.applyMigratedSettings).toHaveBeenCalledWith(mockSettings);
      });

      test('updates settings version', () => {
        settingsMigrationService.updateSettingsVersion.mockImplementation(() => {});
        
        settingsMigrationService.updateSettingsVersion('1.2.0');
        expect(settingsMigrationService.updateSettingsVersion).toHaveBeenCalledWith('1.2.0');
      });
    });
  });

  describe('Integration Tests', () => {
    test('complete migration workflow', async () => {
      // Mock the entire migration workflow
      settingsMigrationService.checkForPendingMigrations.mockResolvedValue();
      settingsMigrationService.forceMigration.mockResolvedValue();
      settingsMigrationService.createMigrationBackup.mockResolvedValue('backup-test.json');
      
      const user = userEvent.setup();
      render(<SettingsMigrationManager onClose={jest.fn()} />);

      // Start migration
      const forceMigrationButton = screen.getByText('Force Migration');
      await user.click(forceMigrationButton);

      const confirmButton = screen.getByText('Confirm');
      await user.click(confirmButton);

      // Verify migration was triggered
      expect(settingsMigrationService.forceMigration).toHaveBeenCalled();
    });

    test('backup and restore workflow', async () => {
      settingsMigrationService.createMigrationBackup.mockResolvedValue('backup-test.json');
      settingsMigrationService.restoreFromBackup.mockResolvedValue();
      
      const user = userEvent.setup();
      render(<SettingsMigrationManager onClose={jest.fn()} />);

      // Create backup
      const createBackupButton = screen.getByText('Create Backup');
      await user.click(createBackupButton);

      expect(settingsMigrationService.createMigrationBackup).toHaveBeenCalled();

      // Switch to backups tab and restore
      const backupsTab = screen.getByText('Backups (2)');
      await user.click(backupsTab);

      const restoreButton = screen.getByText('Restore');
      await user.click(restoreButton);

      const confirmButton = screen.getByText('Confirm');
      await user.click(confirmButton);

      expect(settingsMigrationService.restoreFromBackup).toHaveBeenCalled();
    });
  });
});