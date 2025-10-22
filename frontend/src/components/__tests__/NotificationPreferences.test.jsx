/**
 * T030 User Preferences Enhancement: Notification Preferences Component Tests
 * Comprehensive test suite for NotificationPreferences.jsx
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import NotificationPreferences from '../src/components/NotificationPreferences.jsx';
import notificationService from '../src/services/notificationService.js';

// Mock the notification service
jest.mock('../src/services/notificationService.js', () => ({
  getNotificationPreferences: jest.fn(),
  updateNotificationPreferences: jest.fn(),
  subscribe: jest.fn(),
  testNotification: jest.fn(),
  requestPermission: jest.fn(),
  getPermissionStatus: jest.fn(),
  scheduleNotification: jest.fn(),
  cancelNotification: jest.fn(),
  getNotificationHistory: jest.fn(),
  clearNotificationHistory: jest.fn()
}));

// Mock browser Notification API
Object.defineProperty(window, 'Notification', {
  value: {
    permission: 'default',
    requestPermission: jest.fn(() => Promise.resolve('granted'))
  },
  writable: true
});

describe('NotificationPreferences Component', () => {
  const defaultPreferences = {
    categories: {
      transcription: {
        enabled: true,
        priority: 'high',
        sound: true,
        vibration: true
      },
      batch: {
        enabled: true,
        priority: 'medium',
        sound: false,
        vibration: false
      },
      system: {
        enabled: true,
        priority: 'low',
        sound: false,
        vibration: false
      },
      account: {
        enabled: false,
        priority: 'medium',
        sound: false,
        vibration: false
      }
    },
    delivery_methods: {
      browser: true,
      email: false,
      push: false
    },
    timing: {
      quiet_hours: {
        enabled: false,
        start_time: '22:00',
        end_time: '08:00'
      },
      batch_digest: {
        enabled: false,
        frequency: 'daily',
        time: '09:00'
      }
    },
    metadata: {
      version: '1.2.0',
      lastModified: '2023-12-15T10:30:00Z'
    }
  };

  const mockUnsubscribe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    notificationService.getNotificationPreferences.mockReturnValue(defaultPreferences);
    notificationService.subscribe.mockReturnValue(mockUnsubscribe);
    notificationService.getPermissionStatus.mockReturnValue('granted');
    notificationService.getNotificationHistory.mockReturnValue([]);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    test('renders notification preferences component', () => {
      render(<NotificationPreferences />);
      
      expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
      expect(screen.getByText('Categories')).toBeInTheDocument();
      expect(screen.getByText('Delivery Methods')).toBeInTheDocument();
      expect(screen.getByText('Timing')).toBeInTheDocument();
    });

    test('displays all notification categories', () => {
      render(<NotificationPreferences />);
      
      expect(screen.getByText('Transcription Complete')).toBeInTheDocument();
      expect(screen.getByText('Batch Processing')).toBeInTheDocument();
      expect(screen.getByText('System Updates')).toBeInTheDocument();
      expect(screen.getByText('Account Notifications')).toBeInTheDocument();
    });

    test('displays delivery method options', () => {
      render(<NotificationPreferences />);
      
      expect(screen.getByLabelText(/Browser Notifications/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Email Notifications/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Push Notifications/i)).toBeInTheDocument();
    });

    test('displays timing configuration', () => {
      render(<NotificationPreferences />);
      
      expect(screen.getByLabelText(/Quiet Hours/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Batch Digest/i)).toBeInTheDocument();
    });
  });

  describe('Category Management', () => {
    test('toggles notification category', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      await user.click(transcriptionToggle);

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          categories: expect.objectContaining({
            transcription: expect.objectContaining({
              enabled: false
            })
          })
        })
      );
    });

    test('changes notification priority', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const prioritySelect = screen.getByLabelText(/Priority for Transcription Complete/i);
      await user.selectOptions(prioritySelect, 'low');

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          categories: expect.objectContaining({
            transcription: expect.objectContaining({
              priority: 'low'
            })
          })
        })
      );
    });

    test('toggles sound for category', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const soundToggle = screen.getByLabelText(/Sound for Transcription Complete/i);
      await user.click(soundToggle);

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          categories: expect.objectContaining({
            transcription: expect.objectContaining({
              sound: false
            })
          })
        })
      );
    });

    test('toggles vibration for category', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const vibrationToggle = screen.getByLabelText(/Vibration for Transcription Complete/i);
      await user.click(vibrationToggle);

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          categories: expect.objectContaining({
            transcription: expect.objectContaining({
              vibration: false
            })
          })
        })
      );
    });
  });

  describe('Delivery Methods', () => {
    test('toggles browser notifications', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const browserToggle = screen.getByLabelText(/Browser Notifications/i);
      await user.click(browserToggle);

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          delivery_methods: expect.objectContaining({
            browser: false
          })
        })
      );
    });

    test('requests permission for browser notifications', async () => {
      const user = userEvent.setup();
      notificationService.getPermissionStatus.mockReturnValue('default');
      
      render(<NotificationPreferences />);

      const enableButton = screen.getByText(/Enable Browser Notifications/i);
      await user.click(enableButton);

      expect(notificationService.requestPermission).toHaveBeenCalled();
    });

    test('shows permission status', () => {
      notificationService.getPermissionStatus.mockReturnValue('denied');
      
      render(<NotificationPreferences />);

      expect(screen.getByText(/Browser notifications are blocked/i)).toBeInTheDocument();
    });

    test('toggles email notifications', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const emailToggle = screen.getByLabelText(/Email Notifications/i);
      await user.click(emailToggle);

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          delivery_methods: expect.objectContaining({
            email: true
          })
        })
      );
    });

    test('configures email frequency', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      // First enable email notifications
      const emailToggle = screen.getByLabelText(/Email Notifications/i);
      await user.click(emailToggle);

      // Then configure frequency
      const frequencySelect = screen.getByLabelText(/Email Frequency/i);
      await user.selectOptions(frequencySelect, 'weekly');

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          delivery_methods: expect.objectContaining({
            email_frequency: 'weekly'
          })
        })
      );
    });
  });

  describe('Timing Configuration', () => {
    test('enables quiet hours', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const quietHoursToggle = screen.getByLabelText(/Enable Quiet Hours/i);
      await user.click(quietHoursToggle);

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          timing: expect.objectContaining({
            quiet_hours: expect.objectContaining({
              enabled: true
            })
          })
        })
      );
    });

    test('configures quiet hours time range', async () => {
      const user = userEvent.setup();
      // First enable quiet hours
      notificationService.getNotificationPreferences.mockReturnValue({
        ...defaultPreferences,
        timing: {
          ...defaultPreferences.timing,
          quiet_hours: {
            ...defaultPreferences.timing.quiet_hours,
            enabled: true
          }
        }
      });

      render(<NotificationPreferences />);

      const startTimeInput = screen.getByLabelText(/Start Time/i);
      await user.clear(startTimeInput);
      await user.type(startTimeInput, '23:00');

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          timing: expect.objectContaining({
            quiet_hours: expect.objectContaining({
              start_time: '23:00'
            })
          })
        })
      );
    });

    test('enables batch digest', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const batchDigestToggle = screen.getByLabelText(/Enable Batch Digest/i);
      await user.click(batchDigestToggle);

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          timing: expect.objectContaining({
            batch_digest: expect.objectContaining({
              enabled: true
            })
          })
        })
      );
    });

    test('configures batch digest frequency', async () => {
      const user = userEvent.setup();
      // First enable batch digest
      notificationService.getNotificationPreferences.mockReturnValue({
        ...defaultPreferences,
        timing: {
          ...defaultPreferences.timing,
          batch_digest: {
            ...defaultPreferences.timing.batch_digest,
            enabled: true
          }
        }
      });

      render(<NotificationPreferences />);

      const frequencySelect = screen.getByLabelText(/Digest Frequency/i);
      await user.selectOptions(frequencySelect, 'weekly');

      expect(notificationService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          timing: expect.objectContaining({
            batch_digest: expect.objectContaining({
              frequency: 'weekly'
            })
          })
        })
      );
    });
  });

  describe('Notification Testing', () => {
    test('sends test notification', async () => {
      const user = userEvent.setup();
      notificationService.testNotification.mockResolvedValue(true);
      
      render(<NotificationPreferences />);

      const testButton = screen.getByText(/Send Test Notification/i);
      await user.click(testButton);

      expect(notificationService.testNotification).toHaveBeenCalledWith('transcription');
    });

    test('tests specific category notification', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const testBatchButton = screen.getByTestId('test-batch-notification');
      await user.click(testBatchButton);

      expect(notificationService.testNotification).toHaveBeenCalledWith('batch');
    });

    test('shows test notification result', async () => {
      const user = userEvent.setup();
      notificationService.testNotification.mockResolvedValue(true);
      
      render(<NotificationPreferences />);

      const testButton = screen.getByText(/Send Test Notification/i);
      await user.click(testButton);

      await waitFor(() => {
        expect(screen.getByText(/Test notification sent successfully/i)).toBeInTheDocument();
      });
    });

    test('handles test notification failure', async () => {
      const user = userEvent.setup();
      notificationService.testNotification.mockRejectedValue(new Error('Permission denied'));
      
      render(<NotificationPreferences />);

      const testButton = screen.getByText(/Send Test Notification/i);
      await user.click(testButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to send test notification/i)).toBeInTheDocument();
      });
    });
  });

  describe('Notification History', () => {
    test('displays notification history', () => {
      const mockHistory = [
        {
          id: '1',
          category: 'transcription',
          title: 'Transcription Complete',
          timestamp: '2023-12-15T10:30:00Z',
          delivered: true
        },
        {
          id: '2',
          category: 'batch',
          title: 'Batch Processing Complete',
          timestamp: '2023-12-15T09:15:00Z',
          delivered: false
        }
      ];

      notificationService.getNotificationHistory.mockReturnValue(mockHistory);
      
      render(<NotificationPreferences />);

      expect(screen.getByText('Notification History')).toBeInTheDocument();
      expect(screen.getByText('Transcription Complete')).toBeInTheDocument();
      expect(screen.getByText('Batch Processing Complete')).toBeInTheDocument();
    });

    test('clears notification history', async () => {
      const user = userEvent.setup();
      const mockHistory = [
        { id: '1', category: 'transcription', title: 'Test', timestamp: '2023-12-15T10:30:00Z' }
      ];

      notificationService.getNotificationHistory.mockReturnValue(mockHistory);
      
      render(<NotificationPreferences />);

      const clearButton = screen.getByText(/Clear History/i);
      await user.click(clearButton);

      expect(notificationService.clearNotificationHistory).toHaveBeenCalled();
    });

    test('filters history by category', async () => {
      const user = userEvent.setup();
      const mockHistory = [
        { id: '1', category: 'transcription', title: 'Transcription Complete', timestamp: '2023-12-15T10:30:00Z' },
        { id: '2', category: 'batch', title: 'Batch Complete', timestamp: '2023-12-15T09:15:00Z' }
      ];

      notificationService.getNotificationHistory.mockReturnValue(mockHistory);
      
      render(<NotificationPreferences />);

      const filterSelect = screen.getByLabelText(/Filter by Category/i);
      await user.selectOptions(filterSelect, 'transcription');

      expect(screen.getByText('Transcription Complete')).toBeInTheDocument();
      expect(screen.queryByText('Batch Complete')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('provides keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const firstToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      const secondToggle = screen.getByLabelText(/Enable Batch Processing notifications/i);

      firstToggle.focus();
      await user.keyboard('{Tab}');
      expect(secondToggle).toHaveFocus();
    });

    test('has proper ARIA labels', () => {
      render(<NotificationPreferences />);

      expect(screen.getByRole('group', { name: /Categories/i })).toBeInTheDocument();
      expect(screen.getByRole('group', { name: /Delivery Methods/i })).toBeInTheDocument();
      expect(screen.getByRole('group', { name: /Timing/i })).toBeInTheDocument();
    });

    test('announces changes to screen readers', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      await user.click(transcriptionToggle);

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/Transcription notifications disabled/i);
      });
    });

    test('provides help text for complex settings', () => {
      render(<NotificationPreferences />);

      expect(screen.getByText(/Quiet hours prevent notifications during specified times/i)).toBeInTheDocument();
      expect(screen.getByText(/Batch digest combines multiple notifications/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('handles service errors gracefully', async () => {
      const user = userEvent.setup();
      notificationService.updateNotificationPreferences.mockRejectedValue(new Error('Save failed'));

      render(<NotificationPreferences />);

      const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      await user.click(transcriptionToggle);

      await waitFor(() => {
        expect(screen.getByText(/Failed to save notification preferences/i)).toBeInTheDocument();
      });
    });

    test('shows loading state during operations', async () => {
      const user = userEvent.setup();
      notificationService.updateNotificationPreferences.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(<NotificationPreferences />);

      const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      await user.click(transcriptionToggle);

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
      });
    });

    test('validates time inputs', async () => {
      const user = userEvent.setup();
      // First enable quiet hours
      notificationService.getNotificationPreferences.mockReturnValue({
        ...defaultPreferences,
        timing: {
          ...defaultPreferences.timing,
          quiet_hours: {
            ...defaultPreferences.timing.quiet_hours,
            enabled: true
          }
        }
      });

      render(<NotificationPreferences />);

      const startTimeInput = screen.getByLabelText(/Start Time/i);
      await user.clear(startTimeInput);
      await user.type(startTimeInput, '25:00'); // Invalid time

      await waitFor(() => {
        expect(screen.getByText(/Invalid time format/i)).toBeInTheDocument();
      });
    });
  });

  describe('Integration', () => {
    test('subscribes to notification service updates', () => {
      render(<NotificationPreferences />);
      expect(notificationService.subscribe).toHaveBeenCalled();
    });

    test('unsubscribes on component unmount', () => {
      const { unmount } = render(<NotificationPreferences />);
      unmount();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });

    test('updates when service notifies changes', async () => {
      const mockCallback = jest.fn();
      notificationService.subscribe.mockImplementation(callback => {
        mockCallback.current = callback;
        return mockUnsubscribe;
      });

      render(<NotificationPreferences />);

      // Simulate service update
      act(() => {
        if (mockCallback.current) {
          mockCallback.current('preferences-updated', {
            categories: {
              transcription: { enabled: false }
            }
          });
        }
      });

      await waitFor(() => {
        const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
        expect(transcriptionToggle).not.toBeChecked();
      });
    });

    test('handles permission changes', async () => {
      const mockCallback = jest.fn();
      notificationService.subscribe.mockImplementation(callback => {
        mockCallback.current = callback;
        return mockUnsubscribe;
      });

      render(<NotificationPreferences />);

      // Simulate permission change
      act(() => {
        if (mockCallback.current) {
          mockCallback.current('permission-changed', { permission: 'denied' });
        }
      });

      await waitFor(() => {
        expect(screen.getByText(/Browser notifications are blocked/i)).toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    test('debounces rapid setting changes', async () => {
      const user = userEvent.setup();
      render(<NotificationPreferences />);

      const transcriptionToggle = screen.getByLabelText(/Enable Transcription Complete notifications/i);
      
      // Rapidly toggle multiple times
      await user.click(transcriptionToggle);
      await user.click(transcriptionToggle);
      await user.click(transcriptionToggle);

      // Should only call update once after debounce delay
      await waitFor(() => {
        expect(notificationService.updateNotificationPreferences).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    test('renders efficiently with many history items', () => {
      const manyHistoryItems = Array.from({ length: 1000 }, (_, i) => ({
        id: `${i}`,
        category: 'transcription',
        title: `Notification ${i}`,
        timestamp: new Date().toISOString()
      }));

      notificationService.getNotificationHistory.mockReturnValue(manyHistoryItems);

      const startTime = performance.now();
      render(<NotificationPreferences />);
      const endTime = performance.now();
      
      expect(endTime - startTime).toBeLessThan(500); // Should handle 1000 items in under 500ms
    });
  });
});