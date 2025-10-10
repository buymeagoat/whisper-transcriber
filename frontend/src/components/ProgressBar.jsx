import React from 'react';

export default function ProgressBar({ 
  progress = 0, 
  showPercentage = true, 
  height = '8px',
  backgroundColor = '#374151',
  progressColor = '#3b82f6',
  textColor = '#fff',
  animated = true
}) {
  const progressPercent = Math.min(100, Math.max(0, progress));
  
  return (
    <div style={{ width: '100%', margin: '0.5rem 0' }}>
      {showPercentage && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '0.25rem',
          fontSize: '0.875rem',
          color: textColor
        }}>
          <span>Upload Progress</span>
          <span>{progressPercent.toFixed(1)}%</span>
        </div>
      )}
      
      <div style={{
        width: '100%',
        height,
        backgroundColor,
        borderRadius: '4px',
        overflow: 'hidden',
        position: 'relative'
      }}>
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            backgroundColor: progressColor,
            borderRadius: '4px',
            transition: animated ? 'width 0.3s ease-in-out' : 'none',
            position: 'relative'
          }}
        >
          {animated && progressPercent > 0 && progressPercent < 100 && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                background: `linear-gradient(
                  90deg,
                  transparent,
                  rgba(255, 255, 255, 0.2),
                  transparent
                )`,
                animation: 'progress-shimmer 2s infinite'
              }}
            />
          )}
        </div>
      </div>
      
      <style jsx>{`
        @keyframes progress-shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}
