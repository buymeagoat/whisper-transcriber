/**
 * T030 User Preferences Enhancement: Theme Preferences Component Tests
 * Comprehensive test suite for ThemePreferences.jsx
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ThemePreferences from '../src/components/ThemePreferences.jsx';
import themeService from '../src/services/themeService.js';

// Mock the theme service
jest.mock('../src/services/themeService.js', () => ({
  getThemePreferences: jest.fn(),
  updateThemePreferences: jest.fn(),
  subscribe: jest.fn(),
  applyTheme: jest.fn(),
  getAvailableThemes: jest.fn(),
  createCustomTheme: jest.fn(),
  deleteCustomTheme: jest.fn(),
  exportTheme: jest.fn(),
  importTheme: jest.fn(),
  previewTheme: jest.fn(),
  resetToDefaults: jest.fn()
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

describe('ThemePreferences Component', () => {
  const defaultPreferences = {
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
  };

  const mockUnsubscribe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    themeService.getThemePreferences.mockReturnValue(defaultPreferences);
    themeService.subscribe.mockReturnValue(mockUnsubscribe);
    themeService.getAvailableThemes.mockReturnValue([
      { id: 'light', name: 'Light', type: 'built-in' },
      { id: 'dark', name: 'Dark', type: 'built-in' },
      { id: 'auto', name: 'Auto', type: 'built-in' }
    ]);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    test('renders theme preferences component', () => {
      render(<ThemePreferences />);
      
      expect(screen.getByText('Theme Preferences')).toBeInTheDocument();
      expect(screen.getByText('Appearance')).toBeInTheDocument();
      expect(screen.getByText('Colors')).toBeInTheDocument();
      expect(screen.getByText('Typography')).toBeInTheDocument();
      expect(screen.getByText('Animation')).toBeInTheDocument();
    });

    test('displays current theme selection', () => {
      render(<ThemePreferences />);
      
      const lightThemeOption = screen.getByLabelText('Light');
      expect(lightThemeOption).toBeChecked();
    });

    test('displays color customization controls', () => {
      render(<ThemePreferences />);
      
      expect(screen.getByLabelText(/Primary Color/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Accent Color/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Background Color/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Text Color/i)).toBeInTheDocument();
    });

    test('displays typography controls', () => {
      render(<ThemePreferences />);
      
      expect(screen.getByLabelText(/Font Family/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Font Size Scale/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Line Height Scale/i)).toBeInTheDocument();
    });

    test('displays animation controls', () => {
      render(<ThemePreferences />);
      
      expect(screen.getByLabelText(/Enable Transitions/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Transition Speed/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Enable Hover Effects/i)).toBeInTheDocument();
    });
  });

  describe('Theme Selection', () => {
    test('allows switching between light and dark themes', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          appearance: expect.objectContaining({
            theme: 'dark'
          })
        })
      );
    });

    test('enables auto theme switching', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const autoSwitchToggle = screen.getByLabelText(/Auto Theme Switching/i);
      await user.click(autoSwitchToggle);

      expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          appearance: expect.objectContaining({
            auto_theme_switching: true
          })
        })
      );
    });

    test('previews theme changes before applying', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      expect(themeService.previewTheme).toHaveBeenCalledWith('dark');
    });
  });

  describe('Color Customization', () => {
    test('updates primary color', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const primaryColorInput = screen.getByLabelText(/Primary Color/i);
      await user.clear(primaryColorInput);
      await user.type(primaryColorInput, '#ff0000');

      await waitFor(() => {
        expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
          expect.objectContaining({
            colors: expect.objectContaining({
              primary_color: '#ff0000'
            })
          })
        );
      });
    });

    test('validates color format', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const primaryColorInput = screen.getByLabelText(/Primary Color/i);
      await user.clear(primaryColorInput);
      await user.type(primaryColorInput, 'invalid-color');

      await waitFor(() => {
        expect(screen.getByText(/Invalid color format/i)).toBeInTheDocument();
      });
    });

    test('resets colors to defaults', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const resetButton = screen.getByText(/Reset Colors/i);
      await user.click(resetButton);

      expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          colors: expect.objectContaining({
            primary_color: '#3b82f6'
          })
        })
      );
    });
  });

  describe('Custom Themes', () => {
    test('creates a new custom theme', async () => {
      const user = userEvent.setup();
      themeService.createCustomTheme.mockResolvedValue({ id: 'custom-1', name: 'My Theme' });
      
      render(<ThemePreferences />);

      const createThemeButton = screen.getByText(/Create Custom Theme/i);
      await user.click(createThemeButton);

      const themeNameInput = screen.getByLabelText(/Theme Name/i);
      await user.type(themeNameInput, 'My Custom Theme');

      const saveButton = screen.getByText(/Save Theme/i);
      await user.click(saveButton);

      await waitFor(() => {
        expect(themeService.createCustomTheme).toHaveBeenCalledWith(
          'My Custom Theme',
          expect.any(Object)
        );
      });
    });

    test('deletes a custom theme', async () => {
      const user = userEvent.setup();
      const customThemes = {
        'custom-1': { id: 'custom-1', name: 'My Theme', type: 'custom' }
      };

      themeService.getThemePreferences.mockReturnValue({
        ...defaultPreferences,
        appearance: {
          ...defaultPreferences.appearance,
          custom_themes: customThemes
        }
      });

      render(<ThemePreferences />);

      const deleteButton = screen.getByTestId('delete-theme-custom-1');
      await user.click(deleteButton);

      const confirmButton = screen.getByText(/Delete Theme/i);
      await user.click(confirmButton);

      expect(themeService.deleteCustomTheme).toHaveBeenCalledWith('custom-1');
    });

    test('exports a custom theme', async () => {
      const user = userEvent.setup();
      const mockThemeData = { name: 'My Theme', colors: {} };
      themeService.exportTheme.mockReturnValue(mockThemeData);

      render(<ThemePreferences />);

      const exportButton = screen.getByText(/Export Theme/i);
      await user.click(exportButton);

      expect(themeService.exportTheme).toHaveBeenCalled();
    });

    test('imports a custom theme', async () => {
      const user = userEvent.setup();
      const mockFile = new File(['{"name":"Imported Theme"}'], 'theme.json', {
        type: 'application/json'
      });

      render(<ThemePreferences />);

      const importInput = screen.getByLabelText(/Import Theme/i);
      await user.upload(importInput, mockFile);

      await waitFor(() => {
        expect(themeService.importTheme).toHaveBeenCalled();
      });
    });
  });

  describe('Typography Settings', () => {
    test('changes font family', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const fontSelect = screen.getByLabelText(/Font Family/i);
      await user.selectOptions(fontSelect, 'Roboto');

      expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          typography: expect.objectContaining({
            font_family: 'Roboto'
          })
        })
      );
    });

    test('adjusts font size scale', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const fontSizeSlider = screen.getByLabelText(/Font Size Scale/i);
      fireEvent.change(fontSizeSlider, { target: { value: '1.2' } });

      await waitFor(() => {
        expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
          expect.objectContaining({
            typography: expect.objectContaining({
              font_size_scale: 1.2
            })
          })
        );
      });
    });

    test('adjusts line height scale', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const lineHeightSlider = screen.getByLabelText(/Line Height Scale/i);
      fireEvent.change(lineHeightSlider, { target: { value: '1.5' } });

      await waitFor(() => {
        expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
          expect.objectContaining({
            typography: expect.objectContaining({
              line_height_scale: 1.5
            })
          })
        );
      });
    });
  });

  describe('Animation Settings', () => {
    test('toggles transitions', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const transitionsToggle = screen.getByLabelText(/Enable Transitions/i);
      await user.click(transitionsToggle);

      expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          animation: expect.objectContaining({
            enable_transitions: false
          })
        })
      );
    });

    test('changes transition speed', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const speedSelect = screen.getByLabelText(/Transition Speed/i);
      await user.selectOptions(speedSelect, 'fast');

      expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          animation: expect.objectContaining({
            transition_speed: 'fast'
          })
        })
      );
    });

    test('toggles hover effects', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const hoverToggle = screen.getByLabelText(/Enable Hover Effects/i);
      await user.click(hoverToggle);

      expect(themeService.updateThemePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          animation: expect.objectContaining({
            enable_hover_effects: false
          })
        })
      );
    });
  });

  describe('Theme Preview', () => {
    test('shows live preview of changes', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const previewContainer = screen.getByTestId('theme-preview');
      expect(previewContainer).toBeInTheDocument();

      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      expect(themeService.previewTheme).toHaveBeenCalledWith('dark');
    });

    test('applies theme changes', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const applyButton = screen.getByText(/Apply Changes/i);
      await user.click(applyButton);

      expect(themeService.applyTheme).toHaveBeenCalled();
    });

    test('cancels theme changes', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      // Make a change
      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      // Cancel changes
      const cancelButton = screen.getByText(/Cancel/i);
      await user.click(cancelButton);

      expect(themeService.resetToDefaults).not.toHaveBeenCalled();
      // Should revert to original theme
      expect(themeService.previewTheme).toHaveBeenCalledWith('light');
    });
  });

  describe('Accessibility', () => {
    test('provides keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const lightThemeOption = screen.getByLabelText('Light');
      const darkThemeOption = screen.getByLabelText('Dark');

      // Test keyboard navigation
      lightThemeOption.focus();
      await user.keyboard('{ArrowDown}');
      expect(darkThemeOption).toHaveFocus();
    });

    test('has proper ARIA labels', () => {
      render(<ThemePreferences />);

      expect(screen.getByLabelText(/Primary Color/i)).toHaveAttribute('aria-label');
      expect(screen.getByLabelText(/Font Size Scale/i)).toHaveAttribute('aria-label');
      expect(screen.getByRole('group', { name: /Appearance/i })).toBeInTheDocument();
    });

    test('announces theme changes to screen readers', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/Theme changed to Dark/i);
      });
    });
  });

  describe('Error Handling', () => {
    test('handles service errors gracefully', async () => {
      const user = userEvent.setup();
      themeService.updateThemePreferences.mockRejectedValue(new Error('Save failed'));

      render(<ThemePreferences />);

      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      await waitFor(() => {
        expect(screen.getByText(/Failed to save theme preferences/i)).toBeInTheDocument();
      });
    });

    test('shows loading state during operations', async () => {
      const user = userEvent.setup();
      themeService.updateThemePreferences.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(<ThemePreferences />);

      const darkThemeOption = screen.getByLabelText('Dark');
      await user.click(darkThemeOption);

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
      });
    });

    test('validates color inputs', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const primaryColorInput = screen.getByLabelText(/Primary Color/i);
      await user.clear(primaryColorInput);
      await user.type(primaryColorInput, '#gg0000'); // Invalid hex

      await waitFor(() => {
        expect(screen.getByText(/Invalid color format/i)).toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    test('debounces rapid color changes', async () => {
      const user = userEvent.setup();
      render(<ThemePreferences />);

      const primaryColorInput = screen.getByLabelText(/Primary Color/i);
      
      // Rapidly change color multiple times
      await user.clear(primaryColorInput);
      await user.type(primaryColorInput, '#ff0000');
      await user.clear(primaryColorInput);
      await user.type(primaryColorInput, '#00ff00');
      await user.clear(primaryColorInput);
      await user.type(primaryColorInput, '#0000ff');

      // Should only call update once after debounce delay
      await waitFor(() => {
        expect(themeService.updateThemePreferences).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });
    });

    test('memoizes theme preview rendering', () => {
      const { rerender } = render(<ThemePreferences />);
      
      const initialPreview = screen.getByTestId('theme-preview');
      
      // Re-render with same props
      rerender(<ThemePreferences />);
      
      const secondPreview = screen.getByTestId('theme-preview');
      expect(initialPreview).toBe(secondPreview);
    });
  });

  describe('Integration', () => {
    test('subscribes to theme service updates', () => {
      render(<ThemePreferences />);
      expect(themeService.subscribe).toHaveBeenCalled();
    });

    test('unsubscribes on component unmount', () => {
      const { unmount } = render(<ThemePreferences />);
      unmount();
      expect(mockUnsubscribe).toHaveBeenCalled();
    });

    test('updates when theme service notifies changes', async () => {
      const mockCallback = jest.fn();
      themeService.subscribe.mockImplementation(callback => {
        mockCallback.current = callback;
        return mockUnsubscribe;
      });

      render(<ThemePreferences />);

      // Simulate theme service update
      act(() => {
        if (mockCallback.current) {
          mockCallback.current('theme-updated', { theme: 'dark' });
        }
      });

      await waitFor(() => {
        expect(screen.getByLabelText('Dark')).toBeChecked();
      });
    });
  });
});

// Performance tests
describe('ThemePreferences Performance', () => {
  test('renders within performance budget', () => {
    const startTime = performance.now();
    render(<ThemePreferences />);
    const endTime = performance.now();
    
    expect(endTime - startTime).toBeLessThan(100); // Should render in under 100ms
  });

  test('handles large number of custom themes efficiently', () => {
    const manyThemes = {};
    for (let i = 0; i < 100; i++) {
      manyThemes[`theme-${i}`] = { id: `theme-${i}`, name: `Theme ${i}` };
    }

    themeService.getThemePreferences.mockReturnValue({
      ...defaultPreferences,
      appearance: {
        ...defaultPreferences.appearance,
        custom_themes: manyThemes
      }
    });

    const startTime = performance.now();
    render(<ThemePreferences />);
    const endTime = performance.now();
    
    expect(endTime - startTime).toBeLessThan(500); // Should handle 100 themes in under 500ms
  });
});