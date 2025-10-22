/**
 * T029 Enhanced User Experience: Enhanced Progress Bar Component
 * Advanced progress visualization with stages, animations, and mobile optimization
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Clock, AlertCircle, CheckCircle, XCircle, 
  Pause, Play, RotateCcw, Zap, Users, Timer
} from 'lucide-react';
import enhancedStatusService from '../services/enhancedStatusService.js';
import mobileInterfaceService from '../services/mobileInterfaceService.js';

const EnhancedProgressBar = ({ 
  jobId,
  showDetails = true,
  showQueue = true,
  showETA = true,
  compact = false,
  className = ''
}) => {
  const [jobStatus, setJobStatus] = useState(null);
  const [progressInfo, setProgressInfo] = useState(null);
  const [queueInfo, setQueueInfo] = useState(null);
  const [isVisible, setIsVisible] = useState(true);
  const progressRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    // Get initial status
    const initialStatus = enhancedStatusService.getJobStatus(jobId);
    if (initialStatus) {
      setJobStatus(initialStatus);
      setProgressInfo(enhancedStatusService.getJobProgressInfo(jobId));
    }

    // Subscribe to status updates
    const unsubscribe = enhancedStatusService.subscribe(jobId, (status) => {
      if (status.removed) {
        setIsVisible(false);
        return;
      }
      
      setJobStatus(status);
      setProgressInfo(enhancedStatusService.getJobProgressInfo(jobId));
    });

    // Subscribe to queue updates
    const unsubscribeQueue = enhancedStatusService.subscribe('queue', (queue) => {
      setQueueInfo(queue);
    });

    return () => {
      unsubscribe();
      unsubscribeQueue();
    };
  }, [jobId]);

  useEffect(() => {
    // Animate progress bar changes
    if (progressRef.current && progressInfo?.overallProgress !== undefined) {
      const progress = progressInfo.overallProgress;
      
      if (animationRef.current) {
        animationRef.current.cancel();
      }
      
      animationRef.current = progressRef.current.animate([
        { width: progressRef.current.style.width || '0%' },
        { width: `${progress}%` }
      ], {
        duration: 800,
        easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
        fill: 'forwards'
      });
    }
  }, [progressInfo?.overallProgress]);

  if (!isVisible || !jobStatus || !progressInfo) {
    return null;
  }

  const getStatusColor = (stage) => {
    switch (stage) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'cancelled':
        return 'bg-gray-500';
      case 'transcribing':
        return 'bg-blue-500';
      case 'preprocessing':
      case 'postprocessing':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusIcon = (stage) => {
    switch (stage) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'cancelled':
        return <XCircle className="w-4 h-4 text-gray-600" />;
      case 'transcribing':
        return <Zap className="w-4 h-4 text-blue-600 animate-pulse" />;
      case 'queued':
        return <Timer className="w-4 h-4 text-orange-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const formatProgress = (progress) => {
    return Math.round(progress);
  };

  const formatETA = () => {
    if (!progressInfo.estimatedTimeRemaining) return null;
    
    const completion = enhancedStatusService.estimateCompletionTime(jobId);
    return completion?.remainingFormatted || null;
  };

  const getQueueDisplay = () => {
    if (!showQueue || !progressInfo.queuePosition) return null;
    
    return (
      <div className="flex items-center space-x-1 text-sm text-orange-600 dark:text-orange-400">
        <Users className="w-4 h-4" />
        <span>#{progressInfo.queuePosition} in queue</span>
      </div>
    );
  };

  const getProcessingSpeed = () => {
    if (!progressInfo.processingSpeed) return null;
    
    return (
      <div className="text-sm text-gray-500 dark:text-gray-400">
        {progressInfo.processingSpeed}x speed
      </div>
    );
  };

  if (compact) {
    return (
      <div className={`flex items-center space-x-3 ${className}`}>
        {getStatusIcon(progressInfo.stage)}
        <div className="flex-1 min-w-0">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              ref={progressRef}
              className={`h-2 rounded-full transition-all duration-300 ${getStatusColor(progressInfo.stage)}`}
              style={{ width: `${progressInfo.overallProgress}%` }}
            />
          </div>
        </div>
        <span className="text-sm font-medium text-gray-900 dark:text-white">
          {formatProgress(progressInfo.overallProgress)}%
        </span>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getStatusIcon(progressInfo.stage)}
          <div>
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">
              {progressInfo.stageLabel}
            </h3>
            {showDetails && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {progressInfo.stageDescription}
              </p>
            )}
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatProgress(progressInfo.overallProgress)}%
          </div>
          {showETA && formatETA() && (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {formatETA()} remaining
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
          <div
            ref={progressRef}
            className={`h-3 rounded-full transition-all duration-300 relative ${getStatusColor(progressInfo.stage)}`}
            style={{ width: `${progressInfo.overallProgress}%` }}
          >
            {/* Animated shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white via-transparent opacity-30 animate-pulse" />
          </div>
        </div>
        
        {/* Stage Progress */}
        {showDetails && progressInfo.stageProgress > 0 && (
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>Stage: {formatProgress(progressInfo.stageProgress)}%</span>
            {getProcessingSpeed()}
          </div>
        )}
      </div>

      {/* Additional Info */}
      {showDetails && (
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            {getQueueDisplay()}
            
            {progressInfo.startTime && (
              <div className="text-gray-500 dark:text-gray-400">
                Started {new Date(progressInfo.startTime).toLocaleTimeString()}
              </div>
            )}
          </div>
          
          {progressInfo.lastUpdated && (
            <div className="text-gray-400 dark:text-gray-500 text-xs">
              Updated {new Date(progressInfo.lastUpdated).toLocaleTimeString()}
            </div>
          )}
        </div>
      )}

      {/* Mobile-specific touches */}
      {mobileInterfaceService.deviceInfo.device.isMobile && (
        <style jsx>{`
          .progress-bar-mobile {
            min-height: 44px; /* iOS touch target minimum */
          }
        `}</style>
      )}
    </div>
  );
};

export default EnhancedProgressBar;