/**
 * Route preloading utility for performance optimization
 * Preloads components based on user interaction patterns
 */

// Preload functions for lazy-loaded components
export const preloadAuth = () => {
  return Promise.all([
    import('../pages/auth/LoginPage'),
    import('../pages/auth/RegisterPage')
  ])
}

export const preloadUserPages = () => {
  return Promise.all([
    import('../pages/user/Dashboard'),
    import('../pages/user/TranscribePage'),
    import('../pages/user/JobsPage'),
    import('../pages/user/SettingsPage')
  ])
}

export const preloadAdminPages = () => {
  return Promise.all([
    import('../components/admin/AdminLayout'),
    import('../pages/admin/AdminDashboard'),
    import('../pages/AdminPanel')
  ])
}

// Preload critical user flow components after initial load
export const preloadCriticalFlow = () => {
  // Preload dashboard and transcribe page as they're most commonly accessed
  return Promise.all([
    import('../pages/user/Dashboard'),
    import('../pages/user/TranscribePage')
  ])
}

// Intelligent preloading based on user state
export const intelligentPreload = (user) => {
  if (!user) {
    // Unauthenticated users likely to visit auth pages
    return preloadAuth()
  } else if (user.role === 'admin') {
    // Admin users need both user and admin pages
    return Promise.all([
      preloadUserPages(),
      preloadAdminPages()
    ])
  } else {
    // Regular users need user pages
    return preloadUserPages()
  }
}

// Preload on user interaction (hover, focus)
export const preloadOnInteraction = (routePath) => {
  const preloadMap = {
    '/login': () => import('../pages/auth/LoginPage'),
    '/register': () => import('../pages/auth/RegisterPage'),
    '/dashboard': () => import('../pages/user/Dashboard'),
    '/transcribe': () => import('../pages/user/TranscribePage'),
    '/jobs': () => import('../pages/user/JobsPage'),
    '/settings': () => import('../pages/user/SettingsPage'),
    '/admin': () => import('../pages/admin/AdminDashboard'),
  }

  const preloadFn = preloadMap[routePath]
  if (preloadFn) {
    return preloadFn()
  }
}

// Cache for tracking preloaded components
const preloadCache = new Set()

// Preload with caching to avoid duplicate requests
export const preloadWithCache = (importFn, cacheKey) => {
  if (preloadCache.has(cacheKey)) {
    return Promise.resolve()
  }

  preloadCache.add(cacheKey)
  return importFn().catch(err => {
    // Remove from cache on error so we can retry
    preloadCache.delete(cacheKey)
    console.warn('Failed to preload component:', cacheKey, err)
  })
}

// Preload based on route patterns
export const preloadByRoute = (currentPath) => {
  if (currentPath === '/') {
    // On landing page, preload auth components
    return preloadWithCache(preloadAuth, 'auth-pages')
  } else if (currentPath.startsWith('/admin')) {
    // On admin pages, preload other admin components
    return preloadWithCache(preloadAdminPages, 'admin-pages')
  } else if (['/dashboard', '/transcribe', '/jobs', '/settings'].includes(currentPath)) {
    // On user pages, preload other user components
    return preloadWithCache(preloadUserPages, 'user-pages')
  }
}

// Preload on idle (when browser is not busy)
export const preloadOnIdle = (preloadFn, timeout = 2000) => {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => preloadFn(), { timeout })
  } else {
    // Fallback for browsers without requestIdleCallback
    setTimeout(preloadFn, timeout)
  }
}
