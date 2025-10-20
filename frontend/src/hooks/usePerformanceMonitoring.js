import { useEffect, useRef, useCallback } from 'react'

/**
 * Performance monitoring hook for tracking Core Web Vitals and custom metrics
 */
export const usePerformanceMonitoring = () => {
  const metricsRef = useRef({})

  // Track navigation timing
  const trackNavigationTiming = useCallback(() => {
    if ('performance' in window && 'getEntriesByType' in performance) {
      const navigation = performance.getEntriesByType('navigation')[0]
      if (navigation) {
        const metrics = {
          dns: navigation.domainLookupEnd - navigation.domainLookupStart,
          connection: navigation.connectEnd - navigation.connectStart,
          request: navigation.responseStart - navigation.requestStart,
          response: navigation.responseEnd - navigation.responseStart,
          domParsing: navigation.domContentLoadedEventStart - navigation.responseEnd,
          totalLoadTime: navigation.loadEventEnd - navigation.navigationStart,
        }
        metricsRef.current.navigation = metrics
        console.log('Navigation Timing:', metrics)
      }
    }
  }, [])

  // Track Core Web Vitals
  const trackCoreWebVitals = useCallback(() => {
    // First Contentful Paint (FCP)
    const observeFCP = () => {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === 'first-contentful-paint') {
            metricsRef.current.fcp = entry.startTime
            console.log('FCP:', entry.startTime)
          }
        }
      }).observe({ type: 'paint', buffered: true })
    }

    // Largest Contentful Paint (LCP)
    const observeLCP = () => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1]
        metricsRef.current.lcp = lastEntry.startTime
        console.log('LCP:', lastEntry.startTime)
      }).observe({ type: 'largest-contentful-paint', buffered: true })
    }

    // First Input Delay (FID)
    const observeFID = () => {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          metricsRef.current.fid = entry.processingStart - entry.startTime
          console.log('FID:', entry.processingStart - entry.startTime)
        }
      }).observe({ type: 'first-input', buffered: true })
    }

    // Cumulative Layout Shift (CLS)
    const observeCLS = () => {
      let clsValue = 0
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            clsValue += entry.value
          }
        }
        metricsRef.current.cls = clsValue
        console.log('CLS:', clsValue)
      }).observe({ type: 'layout-shift', buffered: true })
    }

    // Check for support and observe
    if ('PerformanceObserver' in window) {
      observeFCP()
      observeLCP()
      observeFID()
      observeCLS()
    }
  }, [])

  // Track resource loading
  const trackResourceTiming = useCallback(() => {
    if ('performance' in window) {
      const resources = performance.getEntriesByType('resource')
      const resourceMetrics = {
        totalResources: resources.length,
        slowResources: resources.filter(r => r.duration > 1000),
        largeResources: resources.filter(r => r.transferSize > 100000),
        cachedResources: resources.filter(r => r.transferSize === 0),
      }
      metricsRef.current.resources = resourceMetrics
      console.log('Resource Timing:', resourceMetrics)
    }
  }, [])

  // Track memory usage
  const trackMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit,
      }
      metricsRef.current.memory = memory
      console.log('Memory Usage:', memory)
    }
  }, [])

  // Send metrics to analytics
  const sendMetrics = useCallback((customMetrics = {}) => {
    const allMetrics = {
      ...metricsRef.current,
      ...customMetrics,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    }

    // Send to your analytics service
    if (process.env.NODE_ENV === 'production') {
      // Example: send to your backend analytics endpoint
      fetch('/api/analytics/performance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(allMetrics),
      }).catch(err => console.warn('Failed to send performance metrics:', err))
    }

    return allMetrics
  }, [])

  // Initialize monitoring
  useEffect(() => {
    // Track navigation timing after page load
    if (document.readyState === 'complete') {
      trackNavigationTiming()
    } else {
      window.addEventListener('load', trackNavigationTiming)
    }

    // Track Core Web Vitals
    trackCoreWebVitals()

    // Track resources periodically
    const resourceInterval = setInterval(trackResourceTiming, 10000)
    
    // Track memory usage periodically
    const memoryInterval = setInterval(trackMemoryUsage, 30000)

    // Send metrics before page unload
    const handleBeforeUnload = () => {
      sendMetrics()
    }
    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      window.removeEventListener('load', trackNavigationTiming)
      window.removeEventListener('beforeunload', handleBeforeUnload)
      clearInterval(resourceInterval)
      clearInterval(memoryInterval)
    }
  }, [trackNavigationTiming, trackCoreWebVitals, trackResourceTiming, trackMemoryUsage, sendMetrics])

  return {
    getMetrics: () => metricsRef.current,
    sendMetrics,
    trackCustomMetric: (name, value) => {
      metricsRef.current[name] = value
    }
  }
}

/**
 * Component performance wrapper for measuring render times
 */
export const withPerformanceTracking = (Component, componentName) => {
  return function PerformanceTrackedComponent(props) {
    const startTime = useRef(performance.now())
    
    useEffect(() => {
      const endTime = performance.now()
      const renderTime = endTime - startTime.current
      
      console.log(`${componentName} render time:`, renderTime, 'ms')
      
      // Track slow renders
      if (renderTime > 100) {
        console.warn(`Slow render detected in ${componentName}:`, renderTime, 'ms')
      }
    })

    return <Component {...props} />
  }
}

/**
 * Hook for tracking component lifecycle performance
 */
export const useComponentPerformance = (componentName) => {
  const mountTime = useRef(performance.now())
  const renderCount = useRef(0)
  const lastRenderTime = useRef(performance.now())

  useEffect(() => {
    renderCount.current += 1
    const now = performance.now()
    const renderTime = now - lastRenderTime.current
    lastRenderTime.current = now

    // Log performance data
    console.log(`${componentName} performance:`, {
      renderCount: renderCount.current,
      renderTime,
      totalMountTime: now - mountTime.current,
    })
  })

  return {
    getRenderCount: () => renderCount.current,
    getMountTime: () => performance.now() - mountTime.current,
  }
}
