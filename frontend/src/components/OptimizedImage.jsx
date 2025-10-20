import React, { useState, useRef, useEffect } from 'react'

/**
 * Optimized Image component with lazy loading, progressive loading, and WebP support
 */
const OptimizedImage = ({ 
  src, 
  alt, 
  className = '', 
  fallback = '/assets/images/placeholder.svg',
  sizes = '100vw',
  priority = false,
  onLoad,
  onError,
  ...props 
}) => {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [isInView, setIsInView] = useState(priority) // Load immediately if priority
  const imgRef = useRef(null)
  const observerRef = useRef(null)

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (priority || isInView) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px', // Start loading 50px before the image enters viewport
      }
    )

    if (imgRef.current) {
      observer.observe(imgRef.current)
    }

    observerRef.current = observer

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [priority, isInView])

  // Generate WebP and fallback sources
  const generateSources = (baseSrc) => {
    if (!baseSrc) return { webp: null, fallback: baseSrc }
    
    const ext = baseSrc.split('.').pop()
    const basePath = baseSrc.replace(`.${ext}`, '')
    
    return {
      webp: `${basePath}.webp`,
      fallback: baseSrc
    }
  }

  const { webp, fallback: fallbackSrc } = generateSources(src)

  const handleLoad = (event) => {
    setIsLoaded(true)
    onLoad?.(event)
  }

  const handleError = (event) => {
    setHasError(true)
    onError?.(event)
  }

  const shouldLoad = priority || isInView

  return (
    <div 
      ref={imgRef}
      className={`relative overflow-hidden ${className}`}
      {...props}
    >
      {/* Loading placeholder */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse dark:bg-gray-700" />
      )}

      {/* Progressive enhancement with WebP support */}
      {shouldLoad && (
        <picture>
          {/* WebP source for modern browsers */}
          {webp && (
            <source 
              srcSet={webp} 
              type="image/webp"
              sizes={sizes}
            />
          )}
          
          {/* Fallback image */}
          <img
            src={hasError ? fallback : fallbackSrc}
            alt={alt}
            className={`
              w-full h-full object-cover transition-opacity duration-300
              ${isLoaded ? 'opacity-100' : 'opacity-0'}
              ${hasError ? 'opacity-50' : ''}
            `}
            onLoad={handleLoad}
            onError={handleError}
            loading={priority ? 'eager' : 'lazy'}
            decoding="async"
          />
        </picture>
      )}

      {/* Error state */}
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Failed to load image
          </span>
        </div>
      )}
    </div>
  )
}

export default OptimizedImage
