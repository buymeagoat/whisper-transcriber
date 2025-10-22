/**
 * T030 User Preferences Enhancement: Upload Preferences Component Tests
 * Comprehensive test suite for UploadPreferences.jsx
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import UploadPreferences from '../src/components/UploadPreferences.jsx';
import uploadService from '../src/services/uploadService.js';

// Mock the upload service
jest.mock('../src/services/uploadService.js', () => ({
  getUploadPreferences: jest.fn(),
  updateUploadPreferences: jest.fn(),
  subscribe: jest.fn(),
  validateFileType: jest.fn(),
  validateFileSize: jest.fn(),
  getSupportedFormats: jest.fn(),
  getUploadHistory: jest.fn(),
  clearUploadHistory: jest.fn(),
  getUploadStats: jest.fn(),
  testUpload: jest.fn()
}));

describe('UploadPreferences Component', () => {
  const defaultPreferences = {
    general: {
      auto_upload: false,
      max_simultaneous_uploads: 3,
      chunk_size: 1048576, // 1MB
      show_previews: true,
      auto_transcribe: true,
      save_originals: true
    },
    file_handling: {
      accepted_formats: ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/webm'],
      max_file_size: 104857600, // 100MB
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
  };

  const mockUnsubscribe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    uploadService.getUploadPreferences.mockReturnValue(defaultPreferences);
    uploadService.subscribe.mockReturnValue(mockUnsubscribe);
    uploadService.getSupportedFormats.mockReturnValue([
      { format: 'audio/mpeg', extension: '.mp3', description: 'MP3 Audio' },
      { format: 'audio/wav', extension: '.wav', description: 'WAV Audio' },
      { format: 'audio/mp4', extension: '.mp4', description: 'MP4 Audio' },
      { format: 'audio/webm', extension: '.webm', description: 'WebM Audio' }
    ]);
    uploadService.getUploadStats.mockReturnValue({
      totalUploads: 42,
      totalSize: 1024000000,
      averageSize: 24285714,
      successRate: 0.95
    });
    uploadService.getUploadHistory.mockReturnValue([]);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    test('renders upload preferences component', () => {
      render(<UploadPreferences />);
      
      expect(screen.getByText('Upload Preferences')).toBeInTheDocument();
      expect(screen.getByText('General Settings')).toBeInTheDocument();
      expect(screen.getByText('File Handling')).toBeInTheDocument();
      expect(screen.getByText('Security')).toBeInTheDocument();
    });

    test('displays general upload settings', () => {
      render(<UploadPreferences />);
      
      expect(screen.getByLabelText(/Auto Upload/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Max Simultaneous Uploads/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Chunk Size/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Show Previews/i)).toBeInTheDocument();
    });

    test('displays file handling settings', () => {
      render(<UploadPreferences />);
      
      expect(screen.getByText(/Accepted Formats/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Max File Size/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Auto Validate Files/i)).toBeInTheDocument();
    });

    test('displays security settings', () => {
      render(<UploadPreferences />);
      
      expect(screen.getByLabelText(/Scan for Malware/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Require HTTPS/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Encrypt Uploads/i)).toBeInTheDocument();
    });

    test('displays upload statistics', () => {
      render(<UploadPreferences />);
      
      expect(screen.getByText('Upload Statistics')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument(); // Total uploads
      expect(screen.getByText('95%')).toBeInTheDocument(); // Success rate
    });
  });

  describe('General Settings', () => {
    test('toggles auto upload', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const autoUploadToggle = screen.getByLabelText(/Auto Upload/i);
      await user.click(autoUploadToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          general: expect.objectContaining({
            auto_upload: true
          })
        })
      );
    });

    test('changes max simultaneous uploads', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const maxUploadsSlider = screen.getByLabelText(/Max Simultaneous Uploads/i);
      fireEvent.change(maxUploadsSlider, { target: { value: '5' } });

      await waitFor(() => {
        expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
          expect.objectContaining({
            general: expect.objectContaining({
              max_simultaneous_uploads: 5
            })
          })
        );
      });
    });

    test('changes chunk size', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const chunkSizeSelect = screen.getByLabelText(/Chunk Size/i);
      await user.selectOptions(chunkSizeSelect, '2097152'); // 2MB

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          general: expect.objectContaining({
            chunk_size: 2097152
          })
        })
      );
    });

    test('toggles show previews', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const previewsToggle = screen.getByLabelText(/Show Previews/i);
      await user.click(previewsToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          general: expect.objectContaining({
            show_previews: false
          })
        })
      );
    });

    test('toggles auto transcribe', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const autoTranscribeToggle = screen.getByLabelText(/Auto Transcribe/i);
      await user.click(autoTranscribeToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          general: expect.objectContaining({
            auto_transcribe: false
          })
        })
      );
    });

    test('validates max uploads range', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const maxUploadsSlider = screen.getByLabelText(/Max Simultaneous Uploads/i);
      fireEvent.change(maxUploadsSlider, { target: { value: '15' } });

      await waitFor(() => {
        expect(screen.getByText(/Maximum 10 simultaneous uploads allowed/i)).toBeInTheDocument();
      });
    });
  });

  describe('File Handling', () => {
    test('toggles accepted file formats', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const mp3Checkbox = screen.getByLabelText(/MP3 Audio/i);
      await user.click(mp3Checkbox);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          file_handling: expect.objectContaining({
            accepted_formats: ['audio/wav', 'audio/mp4', 'audio/webm']
          })
        })
      );
    });

    test('changes max file size', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const maxSizeSelect = screen.getByLabelText(/Max File Size/i);
      await user.selectOptions(maxSizeSelect, '209715200'); // 200MB

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          file_handling: expect.objectContaining({
            max_file_size: 209715200
          })
        })
      );
    });

    test('toggles auto validate files', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const autoValidateToggle = screen.getByLabelText(/Auto Validate Files/i);
      await user.click(autoValidateToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          file_handling: expect.objectContaining({
            auto_validate_files: false
          })
        })
      );
    });

    test('toggles compress audio', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const compressToggle = screen.getByLabelText(/Compress Audio/i);
      await user.click(compressToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          file_handling: expect.objectContaining({
            compress_audio: true
          })
        })
      );
    });

    test('toggles normalize audio', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const normalizeToggle = screen.getByLabelText(/Normalize Audio/i);
      await user.click(normalizeToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          file_handling: expect.objectContaining({
            normalize_audio: true
          })
        })
      );
    });

    test('requires at least one accepted format', async () => {
      const user = userEvent.setup();
      // Set up state with only one format selected
      uploadService.getUploadPreferences.mockReturnValue({
        ...defaultPreferences,
        file_handling: {
          ...defaultPreferences.file_handling,
          accepted_formats: ['audio/mpeg']
        }
      });

      render(<UploadPreferences />);

      const mp3Checkbox = screen.getByLabelText(/MP3 Audio/i);
      await user.click(mp3Checkbox);

      await waitFor(() => {
        expect(screen.getByText(/At least one format must be selected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Security Settings', () => {
    test('toggles malware scanning', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const malwareScanToggle = screen.getByLabelText(/Scan for Malware/i);
      await user.click(malwareScanToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          security: expect.objectContaining({
            scan_for_malware: false
          })
        })
      );
    });

    test('toggles HTTPS requirement', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const httpsToggle = screen.getByLabelText(/Require HTTPS/i);
      await user.click(httpsToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          security: expect.objectContaining({
            require_https: false
          })
        })
      );
    });

    test('toggles upload encryption', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const encryptToggle = screen.getByLabelText(/Encrypt Uploads/i);
      await user.click(encryptToggle);

      expect(uploadService.updateUploadPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          security: expect.objectContaining({
            encrypt_uploads: false
          })
        })
      );
    });

    test('shows security warnings when disabled', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const malwareScanToggle = screen.getByLabelText(/Scan for Malware/i);
      await user.click(malwareScanToggle);

      await waitFor(() => {
        expect(screen.getByText(/Disabling malware scanning reduces security/i)).toBeInTheDocument();
      });
    });
  });

  describe('Upload Testing', () => {
    test('tests upload functionality', async () => {
      const user = userEvent.setup();
      uploadService.testUpload.mockResolvedValue({ success: true, latency: 150 });
      
      render(<UploadPreferences />);

      const testButton = screen.getByText(/Test Upload/i);
      await user.click(testButton);

      expect(uploadService.testUpload).toHaveBeenCalled();

      await waitFor(() => {
        expect(screen.getByText(/Upload test successful/i)).toBeInTheDocument();
        expect(screen.getByText(/150ms/i)).toBeInTheDocument();
      });
    });

    test('handles upload test failure', async () => {
      const user = userEvent.setup();
      uploadService.testUpload.mockRejectedValue(new Error('Network error'));
      
      render(<UploadPreferences />);

      const testButton = screen.getByText(/Test Upload/i);
      await user.click(testButton);

      await waitFor(() => {
        expect(screen.getByText(/Upload test failed/i)).toBeInTheDocument();
      });
    });

    test('shows test progress', async () => {
      const user = userEvent.setup();
      uploadService.testUpload.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );
      
      render(<UploadPreferences />);

      const testButton = screen.getByText(/Test Upload/i);
      await user.click(testButton);

      expect(screen.getByText(/Testing upload.../i)).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText(/Upload test successful/i)).toBeInTheDocument();
      });
    });
  });

  describe('Upload History', () => {
    test('displays upload history', () => {
      const mockHistory = [
        {
          id: '1',
          filename: 'audio1.mp3',
          size: 5242880,
          uploadTime: '2023-12-15T10:30:00Z',
          status: 'completed',
          transcriptionId: 'trans-1'
        },
        {
          id: '2',
          filename: 'audio2.wav',
          size: 10485760,
          uploadTime: '2023-12-15T09:15:00Z',
          status: 'failed',
          error: 'File too large'
        }
      ];

      uploadService.getUploadHistory.mockReturnValue(mockHistory);
      
      render(<UploadPreferences />);

      expect(screen.getByText('Upload History')).toBeInTheDocument();
      expect(screen.getByText('audio1.mp3')).toBeInTheDocument();
      expect(screen.getByText('audio2.wav')).toBeInTheDocument();
      expect(screen.getByText('5.0 MB')).toBeInTheDocument();
      expect(screen.getByText('10.0 MB')).toBeInTheDocument();
    });

    test('clears upload history', async () => {
      const user = userEvent.setup();
      const mockHistory = [
        { id: '1', filename: 'test.mp3', size: 1000, uploadTime: '2023-12-15T10:30:00Z', status: 'completed' }
      ];

      uploadService.getUploadHistory.mockReturnValue(mockHistory);
      
      render(<UploadPreferences />);

      const clearButton = screen.getByText(/Clear History/i);
      await user.click(clearButton);

      expect(uploadService.clearUploadHistory).toHaveBeenCalled();
    });

    test('filters history by status', async () => {
      const user = userEvent.setup();
      const mockHistory = [
        { id: '1', filename: 'success.mp3', status: 'completed', uploadTime: '2023-12-15T10:30:00Z' },
        { id: '2', filename: 'failed.mp3', status: 'failed', uploadTime: '2023-12-15T09:15:00Z' }
      ];

      uploadService.getUploadHistory.mockReturnValue(mockHistory);
      
      render(<UploadPreferences />);

      const filterSelect = screen.getByLabelText(/Filter by Status/i);
      await user.selectOptions(filterSelect, 'completed');

      expect(screen.getByText('success.mp3')).toBeInTheDocument();
      expect(screen.queryByText('failed.mp3')).not.toBeInTheDocument();
    });

    test('shows upload details', async () => {
      const user = userEvent.setup();
      const mockHistory = [
        {
          id: '1',
          filename: 'audio1.mp3',
          size: 5242880,
          uploadTime: '2023-12-15T10:30:00Z',
          status: 'completed',
          transcriptionId: 'trans-1',
          duration: 30000
        }
      ];

      uploadService.getUploadHistory.mockReturnValue(mockHistory);
      
      render(<UploadPreferences />);

      const detailsButton = screen.getByTestId('upload-details-1');
      await user.click(detailsButton);

      expect(screen.getByText(/30 seconds/i)).toBeInTheDocument();
      expect(screen.getByText(/trans-1/i)).toBeInTheDocument();
    });
  });

  describe('File Validation', () => {
    test('validates file type', async () => {
      uploadService.validateFileType.mockReturnValue({ valid: false, error: 'Unsupported format' });
      
      render(<UploadPreferences />);

      const testFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      const fileInput = screen.getByTestId('file-validation-test');
      
      await userEvent.upload(fileInput, testFile);

      expect(uploadService.validateFileType).toHaveBeenCalledWith(testFile);
      expect(screen.getByText(/Unsupported format/i)).toBeInTheDocument();
    });

    test('validates file size', async () => {
      uploadService.validateFileSize.mockReturnValue({ valid: false, error: 'File too large' });
      
      render(<UploadPreferences />);

      const largeFile = new File(['x'.repeat(200000000)], 'large.mp3', { type: 'audio/mpeg' });
      const fileInput = screen.getByTestId('file-validation-test');
      
      await userEvent.upload(fileInput, largeFile);

      expect(uploadService.validateFileSize).toHaveBeenCalledWith(largeFile);
      expect(screen.getByText(/File too large/i)).toBeInTheDocument();
    });

    test('shows validation success', async () => {
      uploadService.validateFileType.mockReturnValue({ valid: true });
      uploadService.validateFileSize.mockReturnValue({ valid: true });
      
      render(<UploadPreferences />);

      const validFile = new File(['test'], 'test.mp3', { type: 'audio/mpeg' });
      const fileInput = screen.getByTestId('file-validation-test');
      
      await userEvent.upload(fileInput, validFile);

      expect(screen.getByText(/File validation passed/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('provides keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const autoUploadToggle = screen.getByLabelText(/Auto Upload/i);
      const maxUploadsSlider = screen.getByLabelText(/Max Simultaneous Uploads/i);

      autoUploadToggle.focus();
      await user.keyboard('{Tab}');
      expect(maxUploadsSlider).toHaveFocus();
    });

    test('has proper ARIA labels', () => {
      render(<UploadPreferences />);

      expect(screen.getByRole('group', { name: /General Settings/i })).toBeInTheDocument();
      expect(screen.getByRole('group', { name: /File Handling/i })).toBeInTheDocument();
      expect(screen.getByRole('group', { name: /Security/i })).toBeInTheDocument();
    });

    test('announces changes to screen readers', async () => {
      const user = userEvent.setup();
      render(<UploadPreferences />);

      const autoUploadToggle = screen.getByLabelText(/Auto Upload/i);
      await user.click(autoUploadToggle);

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/Auto upload enabled/i);
      });
    });

    test('provides help text for complex settings', () => {
      render(<UploadPreferences />);

      expect(screen.getByText(/Chunk size affects upload performance/i)).toBeInTheDocument();
      expect(screen.getByText(/Malware scanning provides additional security/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('handles service errors gracefully', async () => {
      const user = userEvent.setup();
      uploadService.updateUploadPreferences.mockRejectedValue(new Error('Save failed'));

      render(<UploadPreferences />);

      const autoUploadToggle = screen.getByLabelText(/Auto Upload/i);
      await user.click(autoUploadToggle);

      await waitFor(() => {
        expect(screen.getByText(/Failed to save upload preferences/i)).toBeInTheDocument();
      });
    });

    test('shows loading state during operations', async () => {
      const user = userEvent.setup();
      uploadService.updateUploadPreferences.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(<UploadPreferences />);

      const autoUploadToggle = screen.getByLabelText(/Auto Upload/i);
      await user.click(autoUploadToggle);

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
      });
    });

    test('handles network errors during upload test', async () => {
      const user = userEvent.setup();
      uploadService.testUpload.mockRejectedValue(new Error('Network timeout'));

      render(<UploadPreferences />);

      const testButton = screen.getByText(/Test Upload/i);
      await user.click(testButton);

      await waitFor(() => {
        expect(screen.getByText(/Network timeout/i)).toBeInTheDocument();
      });
    });
  });

  describe('Integration', () => {
    test('subscribes to upload service updates', () => {
      render(<UploadPreferences />);
      expect(uploadService.subscribe).toHaveBeenCalled();
    });

    test('unsubscribes on component unmount', () => {
      const { unmount } = render(<UploadPreferences />);
      unmount();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });

    test('updates when service notifies changes', async () => {
      const mockCallback = jest.fn();
      uploadService.subscribe.mockImplementation(callback => {
        mockCallback.current = callback;
        return mockUnsubscribe;
      });

      render(<UploadPreferences />);

      // Simulate service update
      act(() => {
        if (mockCallback.current) {
          mockCallback.current('preferences-updated', {
            general: { auto_upload: true }
          });
        }
      });

      await waitFor(() => {
        const autoUploadToggle = screen.getByLabelText(/Auto Upload/i);
        expect(autoUploadToggle).toBeChecked();
      });
    });
  });

  describe('Performance', () => {
    test('debounces rapid setting changes', async () => {
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

    test('handles large history efficiently', () => {
      const largeHistory = Array.from({ length: 1000 }, (_, i) => ({
        id: `${i}`,
        filename: `file${i}.mp3`,
        size: 1000000,
        uploadTime: new Date().toISOString(),
        status: 'completed'
      }));

      uploadService.getUploadHistory.mockReturnValue(largeHistory);

      const startTime = performance.now();
      render(<UploadPreferences />);
      const endTime = performance.now();
      
      expect(endTime - startTime).toBeLessThan(500); // Should handle 1000 items in under 500ms
    });
  });
});