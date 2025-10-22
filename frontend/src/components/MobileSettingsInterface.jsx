/**
 * T030 User Preferences Enhancement: Mobile Settings Interface Component
 * Touch-optimized settings navigation with swipe gestures and haptic feedback
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Settings, ChevronRight, ChevronLeft, Search, Filter, Menu,
  X, Check, Star, Heart, Zap, Shield, Smartphone, Tablet,
  Volume2, Eye, Upload, Accessibility, Cloud, TestTube,
  ArrowLeft, MoreHorizontal, Grid, List, Sliders
} from 'lucide-react';
import mobileInterfaceService from '../services/mobileInterfaceService.js';
import ThemeCustomizer from './ThemeCustomizer.jsx';
import NotificationPreferences from './NotificationPreferences.jsx';
import UploadPreferences from './UploadPreferences.jsx';
import AccessibilityOptions from './AccessibilityOptions.jsx';

const MobileSettingsInterface = ({ 
  isOpen = false,
  onClose,
  initialCategory = null,
  className = ''
}) => {
  const [activeCategory, setActiveCategory] = useState(initialCategory || 'overview');
  const [previousCategory, setPreviousCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [viewMode, setViewMode] = useState('cards'); // cards, list, grid
  const [favorites, setFavorites] = useState(new Set());
  const [recentlyUsed, setRecentlyUsed] = useState([]);
  const [swipeStartX, setSwipeStartX] = useState(null);
  const [swipeCurrentX, setSwipeCurrentX] = useState(null);
  const [isSwipingBack, setIsSwipingBack] = useState(false);
  const [openModal, setOpenModal] = useState(null);
  const [collapsedSections, setCollapsedSections] = useState(new Set());
  
  const containerRef = useRef(null);
  const searchInputRef = useRef(null);
  const categoryRefs = useRef({});

  const isMobile = mobileInterfaceService.isMobileBreakpoint();
  const isPortrait = mobileInterfaceService.isPortraitOrientation();

  useEffect(() => {
    // Load favorites and recent settings from localStorage
    loadUserPreferences();
    
    // Set up gesture listeners
    if (isMobile) {
      setupGestureListeners();
    }
    
    return () => {
      cleanupGestureListeners();
    };
  }, [isMobile]);

  useEffect(() => {
    // Auto-focus search when opened
    if (showSearch && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [showSearch]);

  const loadUserPreferences = () => {
    try {
      const storedFavorites = localStorage.getItem('mobile_settings_favorites');
      const storedRecent = localStorage.getItem('mobile_settings_recent');
      
      if (storedFavorites) {
        setFavorites(new Set(JSON.parse(storedFavorites)));
      }
      
      if (storedRecent) {
        setRecentlyUsed(JSON.parse(storedRecent));
      }
    } catch (error) {
      console.warn('Failed to load mobile settings preferences:', error);
    }
  };

  const saveUserPreferences = () => {
    try {
      localStorage.setItem('mobile_settings_favorites', JSON.stringify([...favorites]));
      localStorage.setItem('mobile_settings_recent', JSON.stringify(recentlyUsed));
    } catch (error) {
      console.warn('Failed to save mobile settings preferences:', error);
    }
  };

  const setupGestureListeners = () => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('touchstart', handleTouchStart, { passive: false });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd, { passive: false });
  };

  const cleanupGestureListeners = () => {
    const container = containerRef.current;
    if (!container) return;

    container.removeEventListener('touchstart', handleTouchStart);
    container.removeEventListener('touchmove', handleTouchMove);
    container.removeEventListener('touchend', handleTouchEnd);
  };

  const handleTouchStart = (e) => {
    const touch = e.touches[0];
    setSwipeStartX(touch.clientX);
    setSwipeCurrentX(touch.clientX);
  };

  const handleTouchMove = (e) => {
    if (!swipeStartX) return;
    
    const touch = e.touches[0];
    const currentX = touch.clientX;
    const deltaX = currentX - swipeStartX;
    
    setSwipeCurrentX(currentX);
    
    // Only handle horizontal swipes
    if (Math.abs(deltaX) > 20) {
      // Right swipe (back gesture)
      if (deltaX > 50 && activeCategory !== 'overview') {
        setIsSwipingBack(true);
        mobileInterfaceService.hapticFeedback('light');
      }
    }
  };

  const handleTouchEnd = (e) => {
    if (!swipeStartX || !swipeCurrentX) {
      setSwipeStartX(null);
      setSwipeCurrentX(null);
      setIsSwipingBack(false);
      return;
    }
    
    const deltaX = swipeCurrentX - swipeStartX;
    
    // Right swipe threshold for back navigation
    if (deltaX > 100 && activeCategory !== 'overview') {
      handleBack();
      mobileInterfaceService.hapticFeedback('medium');
    }
    
    setSwipeStartX(null);
    setSwipeCurrentX(null);
    setIsSwipingBack(false);
  };

  const handleCategorySelect = useCallback((categoryId) => {
    setPreviousCategory(activeCategory);
    setActiveCategory(categoryId);
    
    // Add to recently used
    const newRecent = [categoryId, ...recentlyUsed.filter(id => id !== categoryId)].slice(0, 5);
    setRecentlyUsed(newRecent);
    
    // Haptic feedback
    mobileInterfaceService.hapticFeedback('light');
    
    // Scroll to top
    if (containerRef.current) {
      containerRef.current.scrollTop = 0;
    }
  }, [activeCategory, recentlyUsed]);

  const handleBack = useCallback(() => {
    if (previousCategory) {
      setActiveCategory(previousCategory);
      setPreviousCategory(null);
    } else {
      setActiveCategory('overview');
    }
    mobileInterfaceService.hapticFeedback('light');
  }, [previousCategory]);

  const toggleFavorite = (categoryId) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(categoryId)) {
      newFavorites.delete(categoryId);
    } else {
      newFavorites.add(categoryId);
    }
    setFavorites(newFavorites);
    mobileInterfaceService.hapticFeedback('light');
  };

  const toggleSection = (sectionId) => {
    const newCollapsed = new Set(collapsedSections);
    if (newCollapsed.has(sectionId)) {
      newCollapsed.delete(sectionId);
    } else {
      newCollapsed.add(sectionId);
    }
    setCollapsedSections(newCollapsed);
    mobileInterfaceService.hapticFeedback('light');
  };

  const filteredCategories = settingsCategories.filter(category =>
    category.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    category.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    category.keywords?.some(keyword => keyword.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (!isOpen) return null;

  const settingsCategories = [
    {
      id: 'theme',
      title: 'Theme & Appearance',
      description: 'Customize colors, fonts, and visual styling',
      icon: Eye,
      color: 'bg-purple-100 text-purple-600',
      keywords: ['theme', 'dark', 'light', 'appearance', 'colors'],
      component: ThemeCustomizer
    },
    {
      id: 'notifications',
      title: 'Notifications',
      description: 'Manage alerts, sounds, and delivery preferences',
      icon: Volume2,
      color: 'bg-blue-100 text-blue-600',
      keywords: ['notifications', 'alerts', 'sounds', 'push'],
      component: NotificationPreferences
    },
    {
      id: 'upload',
      title: 'Upload & Processing',
      description: 'Configure file uploads and transcription settings',
      icon: Upload,
      color: 'bg-green-100 text-green-600',
      keywords: ['upload', 'files', 'transcription', 'processing'],
      component: UploadPreferences
    },
    {
      id: 'accessibility',
      title: 'Accessibility',
      description: 'Vision, motor, and cognitive accessibility options',
      icon: Accessibility,
      color: 'bg-orange-100 text-orange-600',
      keywords: ['accessibility', 'vision', 'motor', 'screen reader'],
      component: AccessibilityOptions
    },
    {
      id: 'sync',
      title: 'Sync & Backup',
      description: 'Cloud sync, backups, and data management',
      icon: Cloud,
      color: 'bg-cyan-100 text-cyan-600',
      keywords: ['sync', 'backup', 'cloud', 'data']
    },
    {
      id: 'mobile',
      title: 'Mobile Experience',
      description: 'Touch gestures, haptics, and mobile optimizations',
      icon: Smartphone,
      color: 'bg-pink-100 text-pink-600',
      keywords: ['mobile', 'touch', 'gestures', 'haptic']
    }
  ];

  const CategoryCard = ({ category, isCompact = false }) => {
    const Icon = category.icon;
    const isFavorite = favorites.has(category.id);
    const isRecent = recentlyUsed.includes(category.id);

    return (
      <div
        className={`
          relative rounded-lg border-2 transition-all duration-200 cursor-pointer
          ${isCompact ? 'p-3' : 'p-4'}
          hover:shadow-md active:scale-95
          bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700
          hover:border-gray-300 dark:hover:border-gray-600
        `}
        onClick={() => handleCategorySelect(category.id)}
      >
        {/* Favorite Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            toggleFavorite(category.id);
          }}
          className={`
            absolute top-2 right-2 p-1 rounded-full transition-colors
            ${isFavorite ? 'text-yellow-500' : 'text-gray-400 hover:text-gray-600'}
          `}
        >
          <Star className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
        </button>

        {/* Recent Badge */}
        {isRecent && (
          <div className="absolute top-2 left-2 w-2 h-2 bg-blue-500 rounded-full" />
        )}

        <div className="flex items-start space-x-3">
          <div className={`
            p-2 rounded-lg ${category.color}
            ${isCompact ? 'w-10 h-10' : 'w-12 h-12'} 
            flex items-center justify-center
          `}>
            <Icon className={`${isCompact ? 'w-5 h-5' : 'w-6 h-6'}`} />
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className={`
              font-medium text-gray-900 dark:text-white
              ${isCompact ? 'text-sm' : 'text-base'}
            `}>
              {category.title}
            </h3>
            {!isCompact && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 leading-tight">
                {category.description}
              </p>
            )}
          </div>
          
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </div>
      </div>
    );
  };

  const QuickActions = () => (
    <div className="grid grid-cols-2 gap-3 mb-6">
      <button
        onClick={() => handleCategorySelect('theme')}
        className="flex items-center space-x-2 p-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg active:scale-95 transition-transform"
      >
        <Eye className="w-5 h-5" />
        <span className="font-medium">Quick Theme</span>
      </button>
      
      <button
        onClick={() => setOpenModal('search')}
        className="flex items-center space-x-2 p-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg active:scale-95 transition-transform"
      >
        <Search className="w-5 h-5" />
        <span className="font-medium">Search Settings</span>
      </button>
    </div>
  );

  const RecentlyUsedSection = () => {
    if (recentlyUsed.length === 0) return null;

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
          Recently Used
        </h3>
        <div className="space-y-2">
          {recentlyUsed.slice(0, 3).map(categoryId => {
            const category = settingsCategories.find(c => c.id === categoryId);
            return category ? (
              <CategoryCard key={categoryId} category={category} isCompact />
            ) : null;
          })}
        </div>
      </div>
    );
  };

  const FavoritesSection = () => {
    const favoriteCategories = settingsCategories.filter(c => favorites.has(c.id));
    
    if (favoriteCategories.length === 0) return null;

    return (
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
          Favorites
        </h3>
        <div className="space-y-2">
          {favoriteCategories.map(category => (
            <CategoryCard key={category.id} category={category} isCompact />
          ))}
        </div>
      </div>
    );
  };

  const AllCategoriesSection = () => (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          All Settings
        </h3>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode(viewMode === 'cards' ? 'list' : 'cards')}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {viewMode === 'cards' ? <List className="w-4 h-4" /> : <Grid className="w-4 h-4" />}
          </button>
        </div>
      </div>
      
      <div className={`
        ${viewMode === 'cards' ? 'space-y-3' : 'grid grid-cols-1 gap-2'}
      `}>
        {filteredCategories.map(category => (
          <CategoryCard 
            key={category.id} 
            category={category} 
            isCompact={viewMode === 'list'} 
          />
        ))}
      </div>
    </div>
  );

  // Overview screen content
  if (activeCategory === 'overview') {
    return (
      <div className={`
        fixed inset-0 z-50 bg-white dark:bg-gray-900
        ${className}
      `}>
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-3">
              <Settings className="w-6 h-6 text-gray-700 dark:text-gray-300" />
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Settings
              </h1>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowSearch(!showSearch)}
                className={`
                  p-2 rounded-lg transition-colors
                  ${showSearch 
                    ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400' 
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <Search className="w-5 h-5" />
              </button>
              
              <button
                onClick={onClose}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          
          {/* Search Bar */}
          {showSearch && (
            <div className="px-4 pb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search settings..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div 
          ref={containerRef}
          className={`
            flex-1 overflow-y-auto p-4 pb-20
            ${isSwipingBack ? 'transform transition-transform duration-200' : ''}
          `}
          style={{
            transform: isSwipingBack ? 'translateX(20px)' : 'translateX(0)'
          }}
        >
          {!showSearch && <QuickActions />}
          
          {!searchQuery && (
            <>
              <RecentlyUsedSection />
              <FavoritesSection />
            </>
          )}
          
          <AllCategoriesSection />
        </div>
      </div>
    );
  }

  // Category detail screen
  const currentCategory = settingsCategories.find(c => c.id === activeCategory);
  const CategoryComponent = currentCategory?.component;

  return (
    <div className={`
      fixed inset-0 z-50 bg-white dark:bg-gray-900
      ${className}
    `}>
      {/* Header with Back Navigation */}
      <div className="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={handleBack}
              className="p-2 -ml-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            
            {currentCategory && (
              <>
                <div className={`p-2 rounded-lg ${currentCategory.color}`}>
                  <currentCategory.icon className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {currentCategory.title}
                  </h1>
                  {isPortrait && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {currentCategory.description}
                    </p>
                  )}
                </div>
              </>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {currentCategory && (
              <button
                onClick={() => toggleFavorite(currentCategory.id)}
                className={`
                  p-2 rounded-lg transition-colors
                  ${favorites.has(currentCategory.id) 
                    ? 'text-yellow-500' 
                    : 'text-gray-400 hover:text-gray-600'
                  }
                `}
              >
                <Star className={`w-5 h-5 ${favorites.has(currentCategory.id) ? 'fill-current' : ''}`} />
              </button>
            )}
            
            <button
              onClick={onClose}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Category Content */}
      <div 
        ref={containerRef}
        className={`
          flex-1 overflow-y-auto
          ${isSwipingBack ? 'transform transition-transform duration-200' : ''}
        `}
        style={{
          transform: isSwipingBack ? 'translateX(20px)' : 'translateX(0)'
        }}
      >
        {CategoryComponent ? (
          <CategoryComponent 
            isOpen={true}
            onClose={() => setActiveCategory('overview')}
            isMobileInterface={true}
          />
        ) : (
          <div className="p-4">
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <Settings className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Coming Soon
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                This settings category is currently under development.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Mobile Modal Components */}
      {openModal && (
        <div className="fixed inset-0 z-60 bg-black bg-opacity-50 flex items-end">
          <div className="w-full bg-white dark:bg-gray-800 rounded-t-xl max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {openModal === 'search' ? 'Search Settings' : 'Options'}
              </h3>
              <button
                onClick={() => setOpenModal(null)}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-4">
              {openModal === 'search' && (
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Search settings..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    autoFocus
                  />
                  
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {filteredCategories.map(category => (
                      <div
                        key={category.id}
                        onClick={() => {
                          handleCategorySelect(category.id);
                          setOpenModal(null);
                        }}
                        className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                      >
                        <div className={`p-2 rounded-lg ${category.color}`}>
                          <category.icon className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {category.title}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {category.description}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MobileSettingsInterface;