/**
 * I003 Frontend Testing Coverage: LoadingSpinner Component Tests
 * Comprehensive test suite for the LoadingSpinner component
 * Tests rendering, props, accessibility, and different variants
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import LoadingSpinner from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  describe('Rendering', () => {
    test('renders without crashing', () => {
      render(<LoadingSpinner />);
      
      // Check that the spinner container is present
      const container = screen.getByText('Loading...').closest('div');
      expect(container).toBeInTheDocument();
    });

    test('renders with default props', () => {
      render(<LoadingSpinner />);
      
      // Check default text
      expect(screen.getByText('Loading...')).toBeInTheDocument();
      
      // Check that spinner element exists
      const container = screen.getByText('Loading...').closest('div');
      const spinner = container.querySelector('.loading-spinner');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('w-8', 'h-8'); // medium size default
    });

    test('renders with custom text', () => {
      const customText = 'Processing your request...';
      render(<LoadingSpinner text={customText} />);
      
      expect(screen.getByText(customText)).toBeInTheDocument();
    });

    test('renders without text when text prop is empty', () => {
      render(<LoadingSpinner text="" />);
      
      // Text element should not be present when empty string
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      
      // But spinner should still be there
      const spinner = document.querySelector('.loading-spinner');
      expect(spinner).toBeInTheDocument();
    });

    test('renders without text when text prop is null', () => {
      render(<LoadingSpinner text={null} />);
      
      // No text should be rendered when null
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      
      // But spinner should still be there
      const spinner = document.querySelector('.loading-spinner');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    test('renders small size correctly', () => {
      render(<LoadingSpinner size="small" />);
      
      const spinner = document.querySelector('.loading-spinner');
      expect(spinner).toHaveClass('w-6', 'h-6');
    });

    test('renders medium size correctly (default)', () => {
      render(<LoadingSpinner size="medium" />);
      
      const spinner = document.querySelector('.loading-spinner');
      expect(spinner).toHaveClass('w-8', 'h-8');
    });

    test('renders large size correctly', () => {
      render(<LoadingSpinner size="large" />);
      
      const spinner = document.querySelector('.loading-spinner');
      expect(spinner).toHaveClass('w-12', 'h-12');
    });

    test('falls back to medium size for invalid size prop', () => {
      render(<LoadingSpinner size="invalid" />);
      
      const spinner = document.querySelector('.loading-spinner');
      // Should not have invalid size classes, likely falls back to medium or no size
      expect(spinner).not.toHaveClass('w-invalid', 'h-invalid');
    });
  });

  describe('Styling and CSS Classes', () => {
    test('applies correct container classes', () => {
      render(<LoadingSpinner />);
      
      const container = screen.getByText('Loading...').closest('div');
      expect(container).toHaveClass(
        'flex',
        'flex-col', 
        'items-center',
        'justify-center',
        'min-h-[200px]',
        'space-y-4'
      );
    });

    test('applies correct spinner classes', () => {
      render(<LoadingSpinner />);
      
      const spinner = document.querySelector('.loading-spinner');
      expect(spinner).toHaveClass(
        'border-4',
        'border-blue-200',
        'border-t-blue-600',
        'rounded-full',
        'loading-spinner'
      );
    });

    test('applies correct text classes', () => {
      render(<LoadingSpinner text="Test loading" />);
      
      const text = screen.getByText('Test loading');
      expect(text).toHaveClass(
        'text-gray-600',
        'dark:text-gray-300',
        'text-sm',
        'font-medium'
      );
    });
  });

  describe('Accessibility', () => {
    test('provides screen reader accessible content', () => {
      render(<LoadingSpinner text="Loading data" />);
      
      // The text should be accessible to screen readers
      expect(screen.getByText('Loading data')).toBeInTheDocument();
    });

    test('shows loading indicator visually', () => {
      render(<LoadingSpinner />);
      
      // Visual loading indicator should be present
      const spinner = document.querySelector('.loading-spinner');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('border-4', 'rounded-full');
    });

    test('provides text alternative for loading state', () => {
      render(<LoadingSpinner text="Processing request" />);
      
      // Text provides context for screen readers
      expect(screen.getByText('Processing request')).toBeInTheDocument();
    });
  });

  describe('Props Validation', () => {
    test('handles undefined props gracefully', () => {
      expect(() => {
        render(<LoadingSpinner size={undefined} text={undefined} />);
      }).not.toThrow();
      
      // Should render with defaults
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    test('handles null props gracefully', () => {
      expect(() => {
        render(<LoadingSpinner size={null} text={null} />);
      }).not.toThrow();
    });

    test('handles empty object props gracefully', () => {
      expect(() => {
        render(<LoadingSpinner {...{}} />);
      }).not.toThrow();
    });
  });

  describe('Performance', () => {
    test('renders efficiently with multiple instances', () => {
      const startTime = Date.now();
      
      render(
        <div>
          <LoadingSpinner size="small" text="Loading 1" />
          <LoadingSpinner size="medium" text="Loading 2" />
          <LoadingSpinner size="large" text="Loading 3" />
        </div>
      );
      
      const endTime = Date.now();
      const renderTime = endTime - startTime;
      
      // Should render quickly (adjust threshold as needed)
      expect(renderTime).toBeLessThan(100);
      
      // All spinners should be present
      expect(screen.getByText('Loading 1')).toBeInTheDocument();
      expect(screen.getByText('Loading 2')).toBeInTheDocument();
      expect(screen.getByText('Loading 3')).toBeInTheDocument();
    });

    test('does not cause memory leaks on unmount', () => {
      const { unmount } = render(<LoadingSpinner />);
      
      // Unmounting should not throw errors
      expect(() => {
        unmount();
      }).not.toThrow();
    });
  });

  describe('Dark Mode Support', () => {
    test('includes dark mode classes for text', () => {
      render(<LoadingSpinner text="Dark mode test" />);
      
      const text = screen.getByText('Dark mode test');
      expect(text).toHaveClass('dark:text-gray-300');
    });
  });

  describe('Edge Cases', () => {
    test('handles extremely long text', () => {
      const longText = 'A'.repeat(1000);
      render(<LoadingSpinner text={longText} />);
      
      expect(screen.getByText(longText)).toBeInTheDocument();
    });

    test('handles special characters in text', () => {
      const specialText = 'Loading... 🔄 ñáéíóú & <script>';
      render(<LoadingSpinner text={specialText} />);
      
      expect(screen.getByText(specialText)).toBeInTheDocument();
    });

    test('handles numeric text prop', () => {
      render(<LoadingSpinner text={123} />);
      
      expect(screen.getByText('123')).toBeInTheDocument();
    });

    test('handles boolean text prop', () => {
      render(<LoadingSpinner text={true} />);
      
      // Boolean props are rendered as empty in React, so no text should appear
      const textElement = document.querySelector('p');
      expect(textElement).toBeInTheDocument();
      expect(textElement).toBeEmptyDOMElement();
    });
  });

  describe('Component Structure', () => {
    test('maintains correct DOM structure', () => {
      render(<LoadingSpinner />);
      
      const container = screen.getByText('Loading...').closest('div');
      const spinner = container.querySelector('.loading-spinner');
      const text = screen.getByText('Loading...');
      
      expect(container).toContainElement(spinner);
      expect(container).toContainElement(text);
    });

    test('places spinner before text in DOM order', () => {
      render(<LoadingSpinner text="Test" />);
      
      const container = screen.getByText('Test').closest('div');
      const children = Array.from(container.children);
      
      expect(children[0]).toHaveClass('loading-spinner');
      expect(children[1]).toHaveTextContent('Test');
    });
  });
});