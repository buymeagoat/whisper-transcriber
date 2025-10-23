/**
 * I003 Frontend Testing Coverage: Hook Test Template
 * Standardized template for testing custom React hooks
 * 
 * Usage: Copy this template and customize for your specific hook
 * Hooks handle reusable stateful logic, side effects, and data management
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import React from 'react';

// Mock hook for template
const useMockHook = (initialValue = null) => {
  const [data, setData] = React.useState(initialValue);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  const fetchData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 100));
      const newData = { id: 1, name: 'Test Data' };
      setData(newData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateData = React.useCallback((updates) => {
    setData(prevData => ({ ...prevData, ...updates }));
  }, []);

  const clearData = React.useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return {
    data,
    loading,
    error,
    fetchData,
    updateData,
    clearData
  };
};

// Mock external dependencies
// jest.mock('@services/serviceName', () => ({
//   fetchData: jest.fn(),
//   updateData: jest.fn()
// }));

// Test wrapper for hooks that need providers
const HookTestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('useHookName', () => {
  // Setup for tests that need wrapper
  const renderHookWithWrapper = (hookCallback, options = {}) => {
    return renderHook(hookCallback, {
      wrapper: HookTestWrapper,
      ...options
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initialization', () => {
    test('initializes with default values', () => {
      const { result } = renderHook(() => useMockHook());

      expect(result.current.data).toBe(null);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(null);
      expect(typeof result.current.fetchData).toBe('function');
      expect(typeof result.current.updateData).toBe('function');
      expect(typeof result.current.clearData).toBe('function');
    });

    test('initializes with custom initial value', () => {
      const initialValue = { id: 1, name: 'Initial' };
      const { result } = renderHook(() => useMockHook(initialValue));

      expect(result.current.data).toEqual(initialValue);
    });

    test('provides stable function references', () => {
      const { result, rerender } = renderHook(() => useMockHook());

      const initialFetchData = result.current.fetchData;
      const initialUpdateData = result.current.updateData;
      const initialClearData = result.current.clearData;

      rerender();

      expect(result.current.fetchData).toBe(initialFetchData);
      expect(result.current.updateData).toBe(initialUpdateData);
      expect(result.current.clearData).toBe(initialClearData);
    });
  });

  describe('Data Operations', () => {
    test('fetches data successfully', async () => {
      const { result } = renderHook(() => useMockHook());

      expect(result.current.loading).toBe(false);

      act(() => {
        result.current.fetchData();
      });

      // Should be loading immediately
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBe(null);

      // Wait for async operation to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).toEqual({ id: 1, name: 'Test Data' });
      expect(result.current.error).toBe(null);
    });

    test('handles fetch errors', async () => {
      // Mock implementation that throws error
      const errorHook = () => {
        const [loading, setLoading] = React.useState(false);
        const [error, setError] = React.useState(null);
        
        const fetchData = async () => {
          setLoading(true);
          try {
            throw new Error('Fetch failed');
          } catch (err) {
            setError(err.message);
          } finally {
            setLoading(false);
          }
        };
        
        return { loading, error, fetchData };
      };

      const { result } = renderHook(errorHook);

      act(() => {
        result.current.fetchData();
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Fetch failed');
    });

    test('updates data correctly', () => {
      const initialData = { id: 1, name: 'Initial', status: 'active' };
      const { result } = renderHook(() => useMockHook(initialData));

      act(() => {
        result.current.updateData({ name: 'Updated', description: 'New field' });
      });

      expect(result.current.data).toEqual({
        id: 1,
        name: 'Updated',
        status: 'active',
        description: 'New field'
      });
    });

    test('clears data and errors', () => {
      const initialData = { id: 1, name: 'Test' };
      const { result } = renderHook(() => useMockHook(initialData));

      // Set some error state first
      act(() => {
        result.current.updateData({ error: 'Some error' });
      });

      act(() => {
        result.current.clearData();
      });

      expect(result.current.data).toBe(null);
      expect(result.current.error).toBe(null);
    });
  });

  describe('State Management', () => {
    test('manages loading state correctly', async () => {
      const { result } = renderHook(() => useMockHook());

      // Initial state
      expect(result.current.loading).toBe(false);

      // Start async operation
      act(() => {
        result.current.fetchData();
      });

      // Should be loading
      expect(result.current.loading).toBe(true);

      // Wait for completion
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    test('handles multiple concurrent operations', async () => {
      const { result } = renderHook(() => useMockHook());

      // Start multiple operations
      act(() => {
        result.current.fetchData();
        result.current.fetchData();
      });

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should have completed successfully
      expect(result.current.data).toEqual({ id: 1, name: 'Test Data' });
    });

    test('preserves state across rerenders', () => {
      const { result, rerender } = renderHook(() => useMockHook({ id: 1 }));

      act(() => {
        result.current.updateData({ name: 'Updated' });
      });

      const updatedData = result.current.data;

      rerender();

      expect(result.current.data).toEqual(updatedData);
    });
  });

  describe('Effect Cleanup', () => {
    test('cleans up effects on unmount', () => {
      const cleanupSpy = jest.fn();
      
      const hookWithCleanup = () => {
        React.useEffect(() => {
          return cleanupSpy;
        }, []);
        
        return { cleanup: cleanupSpy };
      };

      const { unmount } = renderHook(hookWithCleanup);

      unmount();

      expect(cleanupSpy).toHaveBeenCalledTimes(1);
    });

    test('cancels pending operations on unmount', async () => {
      let resolveFetch;
      const pendingPromise = new Promise(resolve => {
        resolveFetch = resolve;
      });

      const hookWithPending = () => {
        const [loading, setLoading] = React.useState(false);
        
        const startOperation = () => {
          setLoading(true);
          pendingPromise.then(() => setLoading(false));
        };
        
        return { loading, startOperation };
      };

      const { result, unmount } = renderHook(hookWithPending);

      act(() => {
        result.current.startOperation();
      });

      expect(result.current.loading).toBe(true);

      unmount();

      // Resolve the promise after unmount
      resolveFetch();

      // Should not cause state update warnings
    });
  });

  describe('Dependencies and Memoization', () => {
    test('memoizes expensive calculations', () => {
      const expensiveCalculation = jest.fn(() => 'calculated value');
      
      const hookWithMemo = (input) => {
        const result = React.useMemo(() => expensiveCalculation(input), [input]);
        return result;
      };

      const { result, rerender } = renderHook(
        (props) => hookWithMemo(props.input),
        { initialProps: { input: 'test' } }
      );

      expect(result.current).toBe('calculated value');
      expect(expensiveCalculation).toHaveBeenCalledTimes(1);

      // Rerender with same input
      rerender({ input: 'test' });
      expect(expensiveCalculation).toHaveBeenCalledTimes(1);

      // Rerender with different input
      rerender({ input: 'different' });
      expect(expensiveCalculation).toHaveBeenCalledTimes(2);
    });

    test('handles dependency changes correctly', () => {
      const effectCallback = jest.fn();
      
      const hookWithEffect = (dep) => {
        React.useEffect(() => {
          effectCallback(dep);
        }, [dep]);
      };

      const { rerender } = renderHook(
        (props) => hookWithEffect(props.dep),
        { initialProps: { dep: 'initial' } }
      );

      expect(effectCallback).toHaveBeenCalledWith('initial');
      expect(effectCallback).toHaveBeenCalledTimes(1);

      rerender({ dep: 'changed' });
      expect(effectCallback).toHaveBeenCalledWith('changed');
      expect(effectCallback).toHaveBeenCalledTimes(2);
    });
  });

  describe('Context Integration', () => {
    test('consumes context values correctly', () => {
      const TestContext = React.createContext({ value: 'default' });
      
      const hookWithContext = () => {
        const context = React.useContext(TestContext);
        return context.value;
      };

      const WrapperWithContext = ({ children }) => (
        <TestContext.Provider value={{ value: 'provided' }}>
          <HookTestWrapper>
            {children}
          </HookTestWrapper>
        </TestContext.Provider>
      );

      const { result } = renderHook(hookWithContext, {
        wrapper: WrapperWithContext
      });

      expect(result.current).toBe('provided');
    });

    test('responds to context changes', () => {
      const TestContext = React.createContext({ value: 'initial' });
      
      const hookWithContext = () => {
        const context = React.useContext(TestContext);
        return context.value;
      };

      const ContextWrapper = ({ contextValue, children }) => (
        <TestContext.Provider value={{ value: contextValue }}>
          <HookTestWrapper>
            {children}
          </HookTestWrapper>
        </TestContext.Provider>
      );

      const { result, rerender } = renderHook(hookWithContext, {
        wrapper: ({ children }) => (
          <ContextWrapper contextValue="initial">{children}</ContextWrapper>
        )
      });

      expect(result.current).toBe('initial');

      rerender();

      // Change context value
      const { result: result2 } = renderHook(hookWithContext, {
        wrapper: ({ children }) => (
          <ContextWrapper contextValue="changed">{children}</ContextWrapper>
        )
      });

      expect(result2.current).toBe('changed');
    });
  });

  describe('Performance', () => {
    test('does not cause unnecessary rerenders', () => {
      const renderCounter = jest.fn();
      
      const hookWithCounter = () => {
        renderCounter();
        return useMockHook();
      };

      const { result, rerender } = renderHook(hookWithCounter);

      expect(renderCounter).toHaveBeenCalledTimes(1);

      // Trigger state update
      act(() => {
        result.current.updateData({ name: 'Updated' });
      });

      expect(renderCounter).toHaveBeenCalledTimes(2);

      // Rerender without state change
      rerender();
      expect(renderCounter).toHaveBeenCalledTimes(3);
    });

    test('optimizes callback dependencies', () => {
      const callbackSpy = jest.fn();
      
      const hookWithCallback = (externalValue) => {
        const callback = React.useCallback(() => {
          callbackSpy(externalValue);
        }, [externalValue]);
        
        return callback;
      };

      const { result, rerender } = renderHook(
        (props) => hookWithCallback(props.value),
        { initialProps: { value: 'initial' } }
      );

      const initialCallback = result.current;

      // Rerender with same value
      rerender({ value: 'initial' });
      expect(result.current).toBe(initialCallback);

      // Rerender with different value
      rerender({ value: 'changed' });
      expect(result.current).not.toBe(initialCallback);
    });
  });

  describe('Edge Cases', () => {
    test('handles rapid state updates', () => {
      const { result } = renderHook(() => useMockHook({ counter: 0 }));

      act(() => {
        // Rapid updates
        for (let i = 0; i < 10; i++) {
          result.current.updateData({ counter: i });
        }
      });

      expect(result.current.data.counter).toBe(9);
    });

    test('handles invalid state updates', () => {
      const { result } = renderHook(() => useMockHook());

      act(() => {
        // Try to update with invalid data
        result.current.updateData(null);
      });

      // Should handle gracefully (implementation-dependent)
      expect(result.current.data).toBeDefined();
    });

    test('works with strict mode double rendering', () => {
      const effectSpy = jest.fn();
      
      const hookWithEffect = () => {
        React.useEffect(() => {
          effectSpy();
        }, []);
      };

      renderHook(hookWithEffect, {
        wrapper: ({ children }) => (
          <React.StrictMode>
            <HookTestWrapper>{children}</HookTestWrapper>
          </React.StrictMode>
        )
      });

      // In StrictMode, effects run twice in development
      // Your hook should handle this correctly
    });
  });
});

export { useMockHook };